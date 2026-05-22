from __future__ import annotations

import argparse

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.db import mysql_connection


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit suspicious product groups after cleaning.")
    parser.add_argument("--ratio", type=float, default=0.8, help="Flag groups whose price_diff/min_price exceeds this ratio.")
    parser.add_argument("--min-offers", type=int, default=2, help="Only inspect groups with at least this many offers.")
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    settings = get_project_settings()
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.product_id,
                    COUNT(o.id) AS offer_count,
                    COUNT(DISTINCT o.platform_code) AS platform_count,
                    p.min_price,
                    p.max_price,
                    p.price_diff,
                    p.title
                FROM products p
                JOIN platform_offers o ON p.product_id = o.product_id
                GROUP BY p.product_id
                HAVING offer_count >= %s
                   AND p.min_price > 0
                   AND p.price_diff / p.min_price >= %s
                ORDER BY p.price_diff / p.min_price DESC, offer_count DESC
                LIMIT %s
                """,
                (args.min_offers, args.ratio, args.limit),
            )
            rows = cursor.fetchall()

    if not rows:
        print("no suspicious product groups found")
        return
    for product_id, offer_count, platform_count, min_price, max_price, price_diff, title in rows:
        print(
            f"{product_id} | offers={offer_count} | platforms={platform_count} | "
            f"price={min_price}-{max_price} | diff={price_diff} | {title}"
        )


if __name__ == "__main__":
    main()
