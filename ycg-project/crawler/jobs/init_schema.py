from __future__ import annotations

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.db import SCHEMA_SQL, mysql_connection


MIGRATION_SQL = [
    "ALTER TABLE platform_offers MODIFY product_url TEXT",
    "ALTER TABLE raw_crawl_records MODIFY url TEXT",
]


def main() -> None:
    settings = get_project_settings()
    database = settings.get("MYSQL_DATABASE")
    charset = settings.get("MYSQL_CHARSET", "utf8mb4")
    with mysql_connection(settings, database="") as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                f"DEFAULT CHARACTER SET {charset} COLLATE {charset}_unicode_ci"
            )
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            for statement in SCHEMA_SQL:
                cursor.execute(statement)
            for statement in MIGRATION_SQL:
                _execute_optional(cursor, statement)
    print("Database schema initialized.")


def _execute_optional(cursor, statement: str) -> None:
    try:
        cursor.execute(statement)
    except Exception as exc:
        message = str(exc).lower()
        if "doesn't exist" in message or "unknown column" in message:
            return
        raise


if __name__ == "__main__":
    main()
