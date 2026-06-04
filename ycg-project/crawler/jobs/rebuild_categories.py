from __future__ import annotations

import argparse

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.categories import GENERIC_CATEGORY_TEXT, infer_category
from onebuy_crawler.services.db import mysql_connection


def main() -> None:
    parser = argparse.ArgumentParser(description="Infer and rebuild product categories from product titles.")
    parser.add_argument("--apply", action="store_true", help="Write category updates to MySQL. Default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Re-infer all products, not only generic categories.")
    args = parser.parse_args()

    settings = get_project_settings()
    updates = []
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT product_id, title, category_name FROM products ORDER BY product_id")
            for product_id, title, category_name in cursor.fetchall():
                if not args.force and str(category_name or "") not in GENERIC_CATEGORY_TEXT:
                    continue
                category = infer_category(title, "" if args.force else category_name)
                if category.category_name != category_name:
                    updates.append((str(product_id), category.category_id, category.category_name, str(title or "")[:80]))

            print(f"category update candidates: {len(updates)}")
            for product_id, category_id, category_name, title in updates[:30]:
                print(f"{product_id} -> {category_id} {category_name} | {title}")

            if not args.apply:
                print("dry-run only. Re-run with --apply to update products.")
                return

            for product_id, category_id, category_name, _title in updates:
                cursor.execute(
                    """
                    UPDATE products
                    SET category_id=%s,
                        category_name=%s,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE product_id=%s
                    """,
                    (category_id, category_name, product_id),
                )
    print(f"categories rebuilt: {len(updates)}")


if __name__ == "__main__":
    main()
