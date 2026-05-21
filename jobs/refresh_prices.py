from __future__ import annotations

import argparse

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.db import mysql_connection


def load_offer_urls(settings, limit: int) -> list[tuple[str, str, str]]:
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT platform_code, product_url, source_sku_id
                FROM platform_offers
                WHERE product_url IS NOT NULL AND product_url <> ''
                ORDER BY update_at ASC
                LIMIT %s
                """,
                (limit,),
            )
            return list(cursor.fetchall())


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh prices for stale offers.")
    parser.add_argument("--limit", default=100, type=int)
    args = parser.parse_args()

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    for platform_code, url, source_sku_id in load_offer_urls(settings, args.limit):
        if platform_code == "jingdong":
            process.crawl("jd_detail", url=url, source_sku_id=source_sku_id)
        elif platform_code == "taobao":
            process.crawl("taobao_detail", url=url, source_sku_id=source_sku_id)
    process.start()


if __name__ == "__main__":
    main()
