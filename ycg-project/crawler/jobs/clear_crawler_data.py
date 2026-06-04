from __future__ import annotations

import argparse

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.db import mysql_connection


TABLES = [
    "raw_crawl_records",
    "price_history",
    "platform_offers",
    "products",
    "crawl_tasks",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Clear crawler-owned MySQL tables.")
    parser.add_argument("--yes", action="store_true", help="Required confirmation flag.")
    args = parser.parse_args()
    if not args.yes:
        raise SystemExit("Refusing to clear data without --yes.")

    settings = get_project_settings()
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")
            for table in TABLES:
                cursor.execute(f"TRUNCATE TABLE {table}")
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    print("cleared crawler tables:", ", ".join(TABLES))


if __name__ == "__main__":
    main()
