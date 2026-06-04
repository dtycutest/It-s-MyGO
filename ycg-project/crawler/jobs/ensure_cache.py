from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

from scrapy.utils.project import get_project_settings

from jobs.auto_crawl import _collect_keywords
from jobs.init_schema import main as init_schema
from onebuy_crawler.services.cache_status import count_cached_products
from onebuy_crawler.services.crawl_tasks import enqueue_tasks, normalize_task_platform
from onebuy_crawler.services.pipeline_runner import PipelineRunner
from onebuy_crawler.services.seed_data import (
    DEFAULT_SEED_FILE,
    build_generated_records,
    load_seed_records,
    record_to_raw_item,
    select_seed_records,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ensure MySQL has usable product cache for integration demos.")
    parser.add_argument("--keyword", action="append", help="Keyword to ensure. Can be used multiple times.")
    parser.add_argument("--keyword-file", default="", help="UTF-8 keyword file, one keyword per line.")
    parser.add_argument("--use-default-keywords", action="store_true")
    parser.add_argument("--platform", default="jd", choices=["jd", "jingdong"])
    parser.add_argument("--min-count", type=int, default=3, help="Minimum cached product count per keyword.")
    parser.add_argument("--rounds", type=int, default=1, help="Live crawl task-processing rounds before fallback.")
    parser.add_argument("--task-limit", type=int, default=5)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--item-limit", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--no-live", action="store_true", help="Skip live JD capture and only warm cache from seed data.")
    parser.add_argument("--seed-file", default=str(DEFAULT_SEED_FILE))
    parser.add_argument("--no-seed-fallback", action="store_true")
    parser.add_argument("--no-generate-missing", action="store_true")
    parser.add_argument("--generated-count", type=int, default=5)
    parser.add_argument("--skip-init-schema", action="store_true")
    args = parser.parse_args()

    os.environ["CRAWLER_ENABLE_MYSQL"] = "1"
    if not args.skip_init_schema:
        init_schema()

    keywords = _collect_keywords(args.keyword or [], args.keyword_file, args.use_default_keywords)
    if not keywords:
        raise SystemExit("No keywords provided. Use --keyword, --keyword-file, or --use-default-keywords.")

    settings = get_project_settings()
    platform_code = normalize_task_platform(args.platform)
    _print_cache_status(settings, keywords, args.platform, "before")

    missing = _missing_keywords(settings, keywords, args.platform, args.min_count)
    if missing and not args.no_live:
        for keyword in missing:
            enqueue_tasks(settings, keyword, [platform_code])
            print(f"crawl task ready: keyword={keyword}, platform={platform_code}")
        _run_live_rounds(args)
        missing = _missing_keywords(settings, keywords, args.platform, args.min_count)

    if missing and not args.no_seed_fallback:
        imported = _import_fallback_records(settings, missing, args)
        print(f"seed fallback finished: keywords={len(missing)}, records={imported}")

    _print_cache_status(settings, keywords, args.platform, "after")


def _run_live_rounds(args) -> None:
    for round_no in range(1, max(1, args.rounds) + 1):
        command = [
            sys.executable,
            "-m",
            "jobs.run_crawl_tasks",
            "--limit",
            str(args.task_limit),
            "--platform",
            args.platform,
            "--pages",
            str(args.pages),
            "--item-limit",
            str(args.item_limit),
            "--timeout",
            str(args.timeout),
        ]
        if args.headless:
            command.append("--headless")
        print(f"running live crawl round: {round_no}/{max(1, args.rounds)}")
        completed = subprocess.run(command, text=True)
        if completed.returncode != 0:
            print(f"live crawl round failed: exit={completed.returncode}")
            break
        if round_no < max(1, args.rounds):
            time.sleep(2)


def _import_fallback_records(settings, keywords: list[str], args) -> int:
    seed_records = load_seed_records(args.seed_file)
    runner = PipelineRunner(settings)
    imported = 0
    for keyword in keywords:
        records = select_seed_records(seed_records, [keyword], args.platform, limit_per_keyword=args.min_count)
        if len(records) < args.min_count and not args.no_generate_missing:
            target_count = max(args.generated_count, args.min_count)
            records = records + build_generated_records(
                keyword,
                args.platform,
                max(0, target_count - len(records)),
            )
            print(f"generated local demo fallback: keyword={keyword}, records={len(records)}")
        for record in records:
            runner.process(record_to_raw_item(record, keyword=keyword))
            imported += 1
    return imported


def _missing_keywords(settings, keywords: list[str], platform: str, min_count: int) -> list[str]:
    missing = []
    for keyword in keywords:
        count = count_cached_products(settings, keyword, platform)
        if count < min_count:
            missing.append(keyword)
    return missing


def _print_cache_status(settings, keywords: list[str], platform: str, label: str) -> None:
    for keyword in keywords:
        count = count_cached_products(settings, keyword, platform)
        print(f"cache status {label}: keyword={keyword}, count={count}")


if __name__ == "__main__":
    main()
