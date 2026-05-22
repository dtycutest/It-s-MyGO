from __future__ import annotations

import argparse

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.crawl_tasks import enqueue_tasks, normalize_task_platform
from onebuy_crawler.services.db import mysql_connection
from onebuy_crawler.services.search_query import title_keyword_clause


def main() -> None:
    parser = argparse.ArgumentParser(description="Query cached product offers from MySQL.")
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--limit", type=int, default=20, help="Rows per query. Kept for backward compatibility.")
    parser.add_argument("--page", type=int, default=1, help="Page number, starting from 1.")
    parser.add_argument("--page-size", type=int, default=0, help="Rows per page. Overrides --limit when provided.")
    parser.add_argument(
        "--platform",
        default="jd",
        choices=["jd", "jingdong", "taobao", "all"],
        help="Platform to enqueue when --enqueue-missing is used. Defaults to JD.",
    )
    parser.add_argument(
        "--enqueue-missing",
        action="store_true",
        help="Create JD and Taobao crawl tasks when no cached products are found.",
    )
    args = parser.parse_args()

    settings = get_project_settings()
    limit, offset = _pagination(args.limit, args.page, args.page_size)
    rows = query_products(settings, args.keyword, limit, offset=offset)
    if not rows:
        print(f"no cached products found: keyword={args.keyword}, page={args.page}, page_size={limit}")
        if args.enqueue_missing:
            platforms = ["jingdong", "taobao"] if args.platform == "all" else [normalize_task_platform(args.platform)]
            enqueue_tasks(settings, args.keyword, platforms)
            print(f"crawl tasks enqueued: keyword={args.keyword}, platforms={','.join(platforms)}")
        return

    for row in rows:
        (
            product_id,
            title,
            min_price,
            max_price,
            best_platform,
            platform_name,
            price,
            seller_name,
            product_url,
            update_at,
        ) = row
        print(
            f"{product_id} | {platform_name} | {price} | {title} | "
            f"best={best_platform} | range={min_price}-{max_price} | seller={seller_name or '-'} | updated={update_at}"
        )
        print(f"  {product_url}")


def query_products(settings, keyword: str, limit: int, offset: int = 0):
    title_clause, title_params = title_keyword_clause(keyword)
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    p.product_id,
                    p.title,
                    p.min_price,
                    p.max_price,
                    p.best_platform,
                    o.platform_name,
                    o.price,
                    o.seller_name,
                    o.product_url,
                    o.update_at
                FROM products p
                JOIN platform_offers o ON p.product_id = o.product_id
                WHERE {title_clause}
                ORDER BY p.updated_at DESC, o.price ASC
                LIMIT %s OFFSET %s
                """,
                (*title_params, limit, offset),
            )
            return cursor.fetchall()


def _pagination(limit: int, page: int, page_size: int = 0) -> tuple[int, int]:
    effective_limit = page_size if page_size > 0 else limit
    effective_limit = max(1, effective_limit)
    effective_page = max(1, page)
    return effective_limit, (effective_page - 1) * effective_limit


if __name__ == "__main__":
    main()
