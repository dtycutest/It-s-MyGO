from __future__ import annotations

import argparse

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.crawl_tasks import enqueue_tasks, normalize_task_platform


def main() -> None:
    parser = argparse.ArgumentParser(description="Create background crawl tasks for missing search keywords.")
    parser.add_argument("--keyword", action="append", required=True, help="Keyword to enqueue. Can be used multiple times.")
    parser.add_argument(
        "--platform",
        default="all",
        choices=["all", "jd", "jingdong", "taobao"],
        help="Target platform. Use all to enqueue both JD and Taobao.",
    )
    parser.add_argument("--force", action="store_true", help="Reset existing tasks to pending.")
    args = parser.parse_args()

    platforms = ["jingdong", "taobao"] if args.platform == "all" else [normalize_task_platform(args.platform)]
    settings = get_project_settings()
    for keyword in args.keyword:
        enqueue_tasks(settings, keyword, platforms, force=args.force)
        print(f"crawl task enqueued: keyword={keyword}, platforms={','.join(platforms)}")


if __name__ == "__main__":
    main()
