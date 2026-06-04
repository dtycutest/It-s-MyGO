from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.crawl_tasks import enqueue_tasks

BATCH_SIZE = 5
BATCH_INTERVAL_SECONDS = 30


def main() -> None:
    parser = argparse.ArgumentParser(description="批量爬取：从关键词文件批量入队并执行")
    parser.add_argument("--keyword-file", required=True, help="UTF-8 关键词文件，每行一个")
    parser.add_argument("--platform", default="all", choices=["jd", "jingdong", "taobao", "all"])
    parser.add_argument("--force", action="store_true", help="强制重置已有任务")
    parser.add_argument("--pages", type=int, default=2, help="每个任务爬取页数")
    parser.add_argument("--item-limit", type=int, default=20, help="每个任务最大商品数")
    parser.add_argument("--rounds", type=int, default=1, help="爬取轮数")
    parser.add_argument("--task-limit", type=int, default=10, help="每轮最大任务数")
    parser.add_argument("--headless", action="store_true", help="无头模式运行浏览器")
    parser.add_argument("--dry-run", action="store_true", help="仅入队不执行爬取")
    args = parser.parse_args()

    keywords = _load_keywords(args.keyword_file)
    print(f"loaded {len(keywords)} keywords from {args.keyword_file}")
    platforms = ["jingdong", "taobao"] if args.platform == "all" else [_normalize_platform(args.platform)]

    total_tasks = len(keywords) * len(platforms)
    print(f"total tasks to enqueue: {total_tasks} ({len(keywords)} keywords × {len(platforms)} platforms)")

    settings = get_project_settings()
    for keyword in keywords:
        enqueue_tasks(settings, keyword, platforms, force=args.force)
        print(f"  enqueued: {keyword} -> {', '.join(platforms)}")

    if args.dry_run:
        print("dry-run mode, skipping crawl execution")
        return

    if not keywords:
        print("no keywords to process")
        return

    for round_no in range(1, max(1, args.rounds) + 1):
        print(f"\n=== crawl round {round_no}/{max(1, args.rounds)} ===")
        command = [
            sys.executable, "-m", "jobs.run_crawl_tasks",
            "--limit", str(args.task_limit),
            "--platform", args.platform,
            "--pages", str(args.pages),
            "--item-limit", str(args.item_limit),
            "--timeout", "30",
            "--max-retries", "2",
            "--failed-delay-minutes", "10",
            "--blocked-delay-minutes", "30",
        ]
        if args.headless:
            command.append("--headless")
        for keyword in keywords:
            command.extend(["--keyword", keyword])

        print(f"running: {' '.join(command)}")
        result = subprocess.run(command, text=True)
        if result.returncode != 0:
            print(f"round {round_no} exited with code {result.returncode}, continuing...")

        if round_no < max(1, args.rounds):
            print(f"waiting {BATCH_INTERVAL_SECONDS}s before next round...")
            time.sleep(BATCH_INTERVAL_SECONDS)

    print("\nbatch crawl completed")


def _load_keywords(path: str) -> list[str]:
    filepath = Path(path)
    if not filepath.exists():
        print(f"keyword file not found: {path}")
        return []
    keywords = []
    for line in filepath.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        keywords.append(stripped)
    return list(dict.fromkeys(keywords))


def _normalize_platform(platform: str) -> str:
    mapping = {"jd": "jingdong", "jingdong": "jingdong", "taobao": "taobao"}
    return mapping.get(platform, platform)


if __name__ == "__main__":
    main()