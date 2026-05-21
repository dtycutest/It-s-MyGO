from __future__ import annotations

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.db import SCHEMA_SQL, mysql_connection


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
    print("Database schema initialized.")


if __name__ == "__main__":
    main()
