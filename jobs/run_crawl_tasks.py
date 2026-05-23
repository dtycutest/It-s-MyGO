from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.crawl_tasks import (
    BLOCKED_FAILURE_REASONS,
    CrawlTask,
    load_due_tasks,
    mark_failed,
    mark_running,
    mark_success,
    reset_stale_running_tasks,
    task_platform_to_capture_platform,
)


FINISH_RE = re.compile(r"browser_capture finished: .*?items=(\d+)(?:,\s*reason=([^,\r\n]+))?")
JD_SESSION_BLOCK_REASONS = {
    "jd_access_too_frequent",
    "jd_captcha_or_security_check",
    "jd_login_required",
    "jd_risk_handler",
    "jd_search_redirected_to_home",
}


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
    parser.add_argument("--manual-search-only", action="store_true", help="Never auto-submit search during manual search mode.")
    parser.add_argument(
        "--manual-open-search-url",
        action="store_true",
        help="Open the direct search URL before manual confirmation.",
    )
    parser.add_argument(
        "--open-strategy",
        default="direct-first",
        choices=["direct-first", "home-first"],
        help="Search navigation strategy for page 1.",
    )
    parser.add_argument("--typing-delay-ms", type=int, default=120, help="Delay between search keyword characters.")
    parser.add_argument("--pre-search-delay-ms", type=int, default=800, help="Delay before typing on the home page.")
    parser.add_argument("--post-search-delay-ms", type=int, default=1500, help="Delay after submitting a search.")
    parser.add_argument("--login-wait", action="store_true", help="Pause for manual login before each task.")
    parser.add_argument(
        "--manual-verify-on-failure",
        action="store_true",
        help="Keep browser open on login/security failure, wait for manual verification, then retry once.",
    )
    parser.add_argument("--keep-open-on-failure", action="store_true", help="Keep browser open after failed capture.")
    parser.add_argument("--headless", action="store_true", help="Run browser capture in headless mode when CDP is not used.")
    parser.add_argument("--keyword", action="append", help="Only run due tasks for this exact keyword. Can repeat.")
    parser.add_argument(
        "--stale-running-minutes",
        type=int,
        default=30,
        help="Reset tasks left in running state longer than this many minutes.",
    )
    args = parser.parse_args()

    settings = get_project_settings()
    platform = "" if args.platform == "all" else args.platform
    reset_count = reset_stale_running_tasks(
        settings,
        stale_minutes=args.stale_running_minutes,
        platform=platform,
        keywords=args.keyword,
    )
    if reset_count:
        print(f"reset stale running crawl tasks: {reset_count}")
    tasks = load_due_tasks(settings, args.limit, platform=platform, max_retries=args.max_retries, keywords=args.keyword)
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
            if _should_stop_platform_batch(task, reason):
                _safe_print(
                    "JD capture appears blocked for the current browser profile/IP; "
                    "stopping this run to avoid burning the remaining queued tasks."
                )
                break


def _run_capture(task: CrawlTask, args) -> tuple[int, str, str]:
    platform = task_platform_to_capture_platform(task.platform_code)
    summary_path = _new_summary_path()
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
        "--open-strategy",
        args.open_strategy,
        "--typing-delay-ms",
        str(args.typing_delay_ms),
        "--pre-search-delay-ms",
        str(args.pre_search_delay_ms),
        "--post-search-delay-ms",
        str(args.post_search_delay_ms),
        "--summary-file",
        str(summary_path),
    ]
    cdp_url = args.jd_cdp_url if platform == "jd" else args.taobao_cdp_url
    if cdp_url:
        command.extend(["--cdp-url", cdp_url])
    elif args.headless:
        command.append("--headless")
    if args.login_wait:
        command.append("--login-wait")
    if args.manual_search_wait or args.manual_search_only:
        command.append("--manual-search-wait")
    if args.manual_search_only:
        command.append("--manual-search-only")
    if args.manual_open_search_url:
        command.append("--manual-open-search-url")
    if args.manual_verify_on_failure:
        command.append("--manual-verify-on-failure")
    if args.keep_open_on_failure:
        command.append("--keep-open-on-failure")

    env = os.environ.copy()
    env.setdefault("CRAWLER_ENABLE_MYSQL", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    interactive = (
        args.login_wait
        or args.manual_search_wait
        or args.manual_open_search_url
        or args.manual_verify_on_failure
        or args.keep_open_on_failure
    )
    try:
        if interactive:
            completed = subprocess.run(command, text=True, env=env)
            summary = _read_summary(summary_path)
            if summary:
                return int(summary.get("items", 0)), str(summary.get("reason") or ""), ""
            return 0, f"capture_process_failed_exit_{completed.returncode}", ""

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
        summary = _read_summary(summary_path)
        if summary:
            return int(summary.get("items", 0)), str(summary.get("reason") or ""), output
        match = FINISH_RE.search(output)
        if not match:
            return 0, f"capture_process_failed_exit_{completed.returncode}", output
        items = int(match.group(1))
        reason = (match.group(2) or "").strip()
        return items, reason, output
    finally:
        try:
            summary_path.unlink(missing_ok=True)
        except Exception:
            pass


def _should_stop_platform_batch(task: CrawlTask, reason: str) -> bool:
    if task.platform_code != "jingdong":
        return False
    normalized_reason = (reason or "").strip()
    if normalized_reason in JD_SESSION_BLOCK_REASONS:
        return True
    return normalized_reason in BLOCKED_FAILURE_REASONS and normalized_reason.startswith("jd_")


def _new_summary_path() -> Path:
    handle = tempfile.NamedTemporaryFile(prefix="onebuy_capture_", suffix=".json", delete=False)
    handle.close()
    return Path(handle.name)


def _read_summary(path: Path) -> dict:
    try:
        if not path.exists() or path.stat().st_size == 0:
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _safe_print(value: str) -> None:
    try:
        print(value)
    except UnicodeEncodeError:
        encoded = value.encode(sys.stdout.encoding or "utf-8", errors="replace")
        print(encoded.decode(sys.stdout.encoding or "utf-8", errors="replace"))


if __name__ == "__main__":
    main()
