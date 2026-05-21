from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.crawl_tasks import (
    CrawlTask,
    load_due_tasks,
    mark_failed,
    mark_running,
    mark_success,
    task_platform_to_capture_platform,
)


FINISH_RE = re.compile(r"browser_capture finished: .*?items=(\d+)(?:,\s*reason=([^\r\n]+))?")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run due background crawl tasks from MySQL.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum task count to process in this run.")
    parser.add_argument("--platform", default="jd", choices=["all", "jd", "jingdong", "taobao"])
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--item-limit", type=int, default=20, help="Maximum products captured per task.")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--failed-delay-minutes", type=int, default=15)
    parser.add_argument("--blocked-delay-minutes", type=int, default=60)
    parser.add_argument("--jd-cdp-url", default="", help="Optional CDP URL for JD, for example http://127.0.0.1:9222")
    parser.add_argument("--taobao-cdp-url", default="", help="Optional CDP URL for Taobao.")
    parser.add_argument("--manual-search-wait", action="store_true", help="Pause for manual search before each task.")
    parser.add_argument("--headless", action="store_true", help="Run browser capture in headless mode when CDP is not used.")
    args = parser.parse_args()

    settings = get_project_settings()
    platform = "" if args.platform == "all" else args.platform
    tasks = load_due_tasks(settings, args.limit, platform=platform, max_retries=args.max_retries)
    if not tasks:
        print("no due crawl tasks")
        return

    for task in tasks:
        _safe_print(f"running crawl task: id={task.id}, platform={task.platform_code}, keyword={task.keyword}")
        mark_running(settings, task.id)
        items, reason, output = _run_capture(task, args)
        if output.strip():
            _safe_print(output.rstrip())
        if items > 0:
            mark_success(settings, task.id)
            _safe_print(f"crawl task success: id={task.id}, items={items}")
        else:
            next_retry_count = task.retry_count + 1
            mark_failed(
                settings,
                task.id,
                reason or "capture_no_items",
                retry_count=next_retry_count,
                failed_delay_minutes=args.failed_delay_minutes,
                blocked_delay_minutes=args.blocked_delay_minutes,
            )
            _safe_print(f"crawl task deferred: id={task.id}, retry_count={next_retry_count}, reason={reason or 'capture_no_items'}")


def _run_capture(task: CrawlTask, args) -> tuple[int, str, str]:
    platform = task_platform_to_capture_platform(task.platform_code)
    command = [
        sys.executable,
        "-m",
        "jobs.browser_capture_search",
        "--platform",
        platform,
        "--keyword",
        task.keyword,
        "--pages",
        str(args.pages),
        "--limit",
        str(args.item_limit),
        "--timeout",
        str(args.timeout),
    ]
    cdp_url = args.jd_cdp_url if platform == "jd" else args.taobao_cdp_url
    if cdp_url:
        command.extend(["--cdp-url", cdp_url])
    elif args.headless:
        command.append("--headless")
    if args.manual_search_wait:
        command.append("--manual-search-wait")

    env = os.environ.copy()
    env.setdefault("CRAWLER_ENABLE_MYSQL", "1")
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    match = FINISH_RE.search(output)
    if not match:
        return 0, f"capture_process_failed_exit_{completed.returncode}", output
    items = int(match.group(1))
    reason = (match.group(2) or "").strip()
    return items, reason, output


def _safe_print(value: str) -> None:
    try:
        print(value)
    except UnicodeEncodeError:
        encoded = value.encode(sys.stdout.encoding or "utf-8", errors="replace")
        print(encoded.decode(sys.stdout.encoding or "utf-8", errors="replace"))


if __name__ == "__main__":
    main()
