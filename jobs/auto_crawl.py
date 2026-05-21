from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.crawl_tasks import enqueue_tasks, normalize_task_platform


DEFAULT_KEYWORDS = [
    "iPhone 15",
    "华为 手机",
    "小米 手机",
    "蓝牙耳机",
    "机械键盘",
    "显示器",
    "充电宝",
]
DEFAULT_PLATFORM = "jd"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fully automated cache-first crawl workflow.")
    parser.add_argument("--keyword", action="append", help="Keyword to crawl. Can be used multiple times.")
    parser.add_argument("--keyword-file", default="", help="UTF-8 text file, one keyword per line.")
    parser.add_argument(
        "--use-default-keywords",
        action="store_true",
        help="Use a small demo keyword set when --keyword/--keyword-file is not provided.",
    )
    parser.add_argument(
        "--platform",
        default=DEFAULT_PLATFORM,
        choices=["jd", "jingdong", "taobao", "all"],
        help="Target platform. Defaults to JD because Taobao automation is not the current focus.",
    )
    parser.add_argument("--force", action="store_true", help="Reset existing tasks to pending.")
    parser.add_argument("--rounds", type=int, default=1, help="How many task-processing rounds to run.")
    parser.add_argument("--interval-seconds", type=int, default=0, help="Sleep seconds between rounds.")
    parser.add_argument("--task-limit", type=int, default=5, help="Maximum due tasks per round.")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--item-limit", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--failed-delay-minutes", type=int, default=15)
    parser.add_argument("--blocked-delay-minutes", type=int, default=60)
    parser.add_argument("--headless", action="store_true", help="Run browser capture headlessly.")
    parser.add_argument("--skip-init-schema", action="store_true", help="Do not initialize MySQL schema first.")
    parser.add_argument("--refresh-prices", action="store_true", help="Refresh existing offer prices after task processing.")
    parser.add_argument("--refresh-limit", type=int, default=50)
    args = parser.parse_args()

    if not args.skip_init_schema:
        _run_command([sys.executable, "-m", "jobs.init_schema"])

    keywords = _collect_keywords(args.keyword or [], args.keyword_file, args.use_default_keywords)
    platforms = _platforms(args.platform)
    if keywords:
        settings = get_project_settings()
        for keyword in keywords:
            enqueue_tasks(settings, keyword, platforms, force=args.force)
            print(f"crawl tasks ready: keyword={keyword}, platforms={','.join(platforms)}")
    else:
        print("no keywords provided; only existing due tasks will be processed")

    for round_no in range(1, max(1, args.rounds) + 1):
        print(f"processing crawl tasks: round={round_no}/{max(1, args.rounds)}")
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
            "--max-retries",
            str(args.max_retries),
            "--failed-delay-minutes",
            str(args.failed_delay_minutes),
            "--blocked-delay-minutes",
            str(args.blocked_delay_minutes),
        ]
        if args.headless:
            command.append("--headless")
        _run_command(command)
        if round_no < max(1, args.rounds) and args.interval_seconds > 0:
            time.sleep(args.interval_seconds)

    if args.refresh_prices:
        _run_command([sys.executable, "-m", "jobs.refresh_prices", "--limit", str(args.refresh_limit)])


def _collect_keywords(keyword_args: list[str], keyword_file: str, use_default_keywords: bool) -> list[str]:
    keywords = list(keyword_args)
    if keyword_file:
        path = Path(keyword_file)
        keywords.extend(
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    if not keywords and use_default_keywords:
        keywords.extend(DEFAULT_KEYWORDS)
    return list(dict.fromkeys(keywords))


def _platforms(platform: str) -> list[str]:
    if platform == "all":
        return ["jingdong", "taobao"]
    return [normalize_task_platform(platform)]


def _run_command(command: list[str]) -> None:
    print("running:", " ".join(command))
    completed = subprocess.run(command, text=True)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
