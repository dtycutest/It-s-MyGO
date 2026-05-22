from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from scrapy.utils.project import get_project_settings

from jobs.auto_crawl import _collect_keywords
from onebuy_crawler.services.crawl_tasks import normalize_task_platform
from onebuy_crawler.services.db import mysql_connection
from onebuy_crawler.services.normalizer import clean_text
from onebuy_crawler.services.search_query import title_keyword_clause
from onebuy_crawler.services.seed_data import record_matches_keyword


def main() -> None:
    parser = argparse.ArgumentParser(description="Export cached MySQL products into a portable seed JSON file.")
    parser.add_argument("--output", default="data/exported_seed_products.json")
    parser.add_argument("--keyword", action="append", help="Export rows whose title matches this keyword. Can repeat.")
    parser.add_argument("--keyword-file", default="", help="UTF-8 keyword file, one keyword per line.")
    parser.add_argument("--use-default-keywords", action="store_true")
    parser.add_argument("--platform", default="jd", choices=["jd", "jingdong", "taobao", "all"])
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()

    settings = get_project_settings()
    keywords = _collect_keywords(args.keyword or [], args.keyword_file, args.use_default_keywords)
    records = export_records(settings, keywords, args.platform, args.limit)

    payload = {
        "version": 1,
        "source": "onebuy exported cache",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"seed export finished: records={len(records)}, output={output}")


def export_records(settings, keywords: list[str], platform: str, limit: int) -> list[dict]:
    where = []
    params: list[object] = []
    if platform != "all":
        where.append("o.platform_code = %s")
        params.append(normalize_task_platform(platform))
    if keywords:
        keyword_clauses = []
        for keyword in keywords:
            clause, clause_params = title_keyword_clause(keyword)
            keyword_clauses.append(f"({clause})")
            params.extend(clause_params)
        where.append("(" + " OR ".join(keyword_clauses) + ")")
    params.append(limit)

    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    p.product_id,
                    p.title,
                    p.category_name,
                    p.image_url,
                    p.description,
                    p.specs,
                    o.platform_code,
                    o.platform_name,
                    o.source_sku_id,
                    o.price,
                    o.original_price,
                    o.sales_volume,
                    o.seller_name,
                    o.seller_rating,
                    o.seller_id,
                    o.product_url,
                    o.in_stock,
                    o.stock_quantity,
                    o.update_at
                FROM products p
                JOIN platform_offers o ON p.product_id = o.product_id
                WHERE {' AND '.join(where) if where else '1=1'}
                ORDER BY p.updated_at DESC, o.update_at DESC
                LIMIT %s
                """,
                params,
            )
            rows = cursor.fetchall()

    records = []
    for row in rows:
        title = clean_text(row[1])
        matched_keywords = [keyword for keyword in keywords if record_matches_keyword({"title": title}, keyword)]
        records.append(
            {
                "product_id": row[0],
                "platform_code": row[6],
                "platform_name": row[7],
                "source_sku_id": row[8],
                "keyword": matched_keywords[0] if matched_keywords else "",
                "keywords": matched_keywords,
                "title": title,
                "price_text": str(row[9]),
                "original_price_text": str(row[10]) if row[10] is not None else "",
                "sales_text": str(row[11]) if row[11] is not None else "",
                "seller_name": row[12] or "",
                "seller_rating_text": str(row[13]) if row[13] is not None else "",
                "seller_id": row[14] or "",
                "image_url": row[3] or "",
                "product_url": row[15] or "",
                "category_text": row[2] or "",
                "promo_info": row[4] or "",
                "specs": _json_object(row[5]),
                "in_stock": bool(row[16]),
                "stock_quantity": row[17],
                "crawl_time": row[18],
                "raw_payload": {"source": "exported_cache_seed"},
            }
        )
    return records


def _json_object(value):
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
