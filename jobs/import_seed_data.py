from __future__ import annotations

import argparse
import os

from scrapy.utils.project import get_project_settings

from jobs.auto_crawl import _collect_keywords
from jobs.init_schema import main as init_schema
from onebuy_crawler.services.cache_status import count_cached_products
from onebuy_crawler.services.pipeline_runner import PipelineRunner
from onebuy_crawler.services.seed_data import (
    DEFAULT_SEED_FILE,
    build_generated_records,
    load_seed_records,
    record_to_raw_item,
    select_seed_records,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import bundled or exported product seed data into MySQL.")
    parser.add_argument("--seed-file", default=str(DEFAULT_SEED_FILE), help="JSON seed file to import.")
    parser.add_argument("--keyword", action="append", help="Only import records matching this keyword. Can repeat.")
    parser.add_argument("--keyword-file", default="", help="UTF-8 keyword file, one keyword per line.")
    parser.add_argument("--use-default-keywords", action="store_true", help="Use the built-in JD demo keyword set.")
    parser.add_argument("--platform", default="jd", choices=["jd", "jingdong", "taobao"])
    parser.add_argument("--limit-per-keyword", type=int, default=5)
    parser.add_argument("--only-missing", action="store_true", help="Skip keywords that already have enough cached rows.")
    parser.add_argument("--min-count", type=int, default=1, help="Used with --only-missing.")
    parser.add_argument(
        "--generate-missing",
        action="store_true",
        help="Generate clearly marked local demo rows when the seed file has no matching keyword.",
    )
    parser.add_argument("--generated-count", type=int, default=5)
    parser.add_argument("--skip-init-schema", action="store_true")
    args = parser.parse_args()

    os.environ["CRAWLER_ENABLE_MYSQL"] = "1"
    if not args.skip_init_schema:
        init_schema()

    settings = get_project_settings()
    keywords = _collect_keywords(args.keyword or [], args.keyword_file, args.use_default_keywords)
    seed_records = load_seed_records(args.seed_file)
    selected_records = _records_to_import(settings, seed_records, keywords, args)

    runner = PipelineRunner(settings)
    imported = 0
    for record in selected_records:
        runner.process(record_to_raw_item(record))
        imported += 1

    print(f"seed import finished: records={imported}, seed_file={args.seed_file}")


def _records_to_import(settings, seed_records, keywords: list[str], args) -> list[dict]:
    if not keywords:
        return select_seed_records(seed_records, platform=args.platform, limit_per_keyword=args.limit_per_keyword)

    selected: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for keyword in keywords:
        if args.only_missing and count_cached_products(settings, keyword, args.platform) >= args.min_count:
            print(f"cache already warm: keyword={keyword}")
            continue

        keyword_records = select_seed_records(seed_records, [keyword], args.platform, args.limit_per_keyword)
        if not keyword_records and args.generate_missing:
            try:
                keyword_records = build_generated_records(keyword, args.platform, args.generated_count)
            except ValueError as exc:
                print(f"skip generated fallback: keyword={keyword}, reason={exc}")
                keyword_records = []
            else:
                print(f"generated local fallback records: keyword={keyword}, records={len(keyword_records)}")

        for record in keyword_records:
            key = (record.get("platform_code", ""), record.get("source_sku_id", "") or record.get("product_id", ""))
            if key in seen:
                continue
            seen.add(key)
            selected.append(record)
    return selected


if __name__ == "__main__":
    main()
