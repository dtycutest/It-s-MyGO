from __future__ import annotations

from onebuy_crawler.services.crawl_tasks import normalize_task_platform
from onebuy_crawler.services.db import mysql_connection
from onebuy_crawler.services.normalizer import clean_text
from onebuy_crawler.services.search_query import title_keyword_clause


def count_cached_products(settings, keyword: str, platform: str = "") -> int:
    keyword = clean_text(keyword)
    title_clause, title_params = title_keyword_clause(keyword)
    where = [title_clause]
    params: list[object] = list(title_params)
    if platform:
        where.append("o.platform_code = %s")
        params.append(normalize_task_platform(platform))

    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(DISTINCT p.product_id)
                FROM products p
                JOIN platform_offers o ON p.product_id = o.product_id
                WHERE {' AND '.join(where)}
                """,
                params,
            )
            row = cursor.fetchone()
            return int(row[0] or 0)
