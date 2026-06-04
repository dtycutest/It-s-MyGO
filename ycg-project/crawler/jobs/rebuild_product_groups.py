from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.db import mysql_connection
from onebuy_crawler.services.matcher import build_match_fingerprint


@dataclass(frozen=True)
class ProductGroupRow:
    product_id: str
    title: str
    specs: dict[str, Any]
    created_at: object


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild product groups from normalized titles/specs.")
    parser.add_argument("--apply", action="store_true", help="Write regrouping changes to MySQL. Default is dry-run.")
    args = parser.parse_args()

    settings = get_project_settings()
    rows = load_product_rows(settings)
    groups = group_products(rows)
    merge_groups = {fingerprint: group for fingerprint, group in groups.items() if len(group) > 1}

    print(f"products scanned: {len(rows)}")
    print(f"fingerprint groups: {len(groups)}")
    print(f"merge candidate groups: {len(merge_groups)}")
    for fingerprint, group in list(merge_groups.items())[:20]:
        canonical = choose_canonical(group)
        others = [row.product_id for row in group if row.product_id != canonical.product_id]
        print(f"merge {fingerprint}: keep={canonical.product_id}, merge={','.join(others)}")

    if not args.apply:
        print("dry-run only. Re-run with --apply to update platform_offers, price_history, and products.")
        return

    changed = apply_groups(settings, groups)
    print(f"product grouping rebuilt: merged_products={changed}")


def load_product_rows(settings) -> list[ProductGroupRow]:
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT product_id, title, specs, created_at FROM products ORDER BY created_at ASC, product_id ASC")
            rows = []
            for product_id, title, specs_json, created_at in cursor.fetchall():
                rows.append(
                    ProductGroupRow(
                        product_id=str(product_id),
                        title=str(title or ""),
                        specs=_parse_specs(specs_json),
                        created_at=created_at,
                    )
                )
            return rows


def group_products(rows: list[ProductGroupRow]) -> dict[str, list[ProductGroupRow]]:
    groups: dict[str, list[ProductGroupRow]] = defaultdict(list)
    for row in rows:
        groups[build_match_fingerprint(row.title, row.specs)].append(row)
    return dict(groups)


def choose_canonical(group: list[ProductGroupRow]) -> ProductGroupRow:
    return sorted(group, key=lambda row: (str(row.created_at), row.product_id))[0]


def apply_groups(settings, groups: dict[str, list[ProductGroupRow]]) -> int:
    changed = 0
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            for fingerprint, group in groups.items():
                canonical = choose_canonical(group)
                group_ids = [row.product_id for row in group]
                placeholders = ",".join(["%s"] * len(group_ids))
                cursor.execute(
                    f"UPDATE products SET match_fingerprint=%s WHERE product_id IN ({placeholders})",
                    [fingerprint, *group_ids],
                )
                if len(group) <= 1:
                    continue

                others = [row.product_id for row in group if row.product_id != canonical.product_id]
                other_placeholders = ",".join(["%s"] * len(others))
                cursor.execute(
                    f"UPDATE platform_offers SET product_id=%s WHERE product_id IN ({other_placeholders})",
                    [canonical.product_id, *others],
                )
                cursor.execute(
                    f"UPDATE price_history SET product_id=%s WHERE product_id IN ({other_placeholders})",
                    [canonical.product_id, *others],
                )
                cursor.execute(
                    f"DELETE FROM products WHERE product_id IN ({other_placeholders})",
                    others,
                )
                refresh_product_summary(cursor, canonical.product_id)
                changed += len(others)
    return changed


def refresh_product_summary(cursor, product_id: str) -> None:
    cursor.execute(
        """
        UPDATE products p
        JOIN (
            SELECT
                product_id,
                MIN(price) AS min_price,
                MAX(price) AS max_price,
                SUBSTRING_INDEX(
                    GROUP_CONCAT(platform_name ORDER BY price ASC, update_at DESC),
                    ',', 1
                ) AS best_platform
            FROM platform_offers
            WHERE product_id = %s
            GROUP BY product_id
        ) s ON p.product_id = s.product_id
        SET p.min_price = s.min_price,
            p.max_price = s.max_price,
            p.price_diff = s.max_price - s.min_price,
            p.best_platform = s.best_platform,
            p.updated_at = CURRENT_TIMESTAMP
        """,
        (product_id,),
    )


def _parse_specs(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


if __name__ == "__main__":
    main()
