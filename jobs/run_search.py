from __future__ import annotations

import argparse

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run product search spiders.")
    parser.add_argument("--keyword", required=True, help="Search keyword, for example: iPhone 15")
    parser.add_argument("--platform", default="all", choices=["all", "jd", "taobao"], help="Target platform")
    parser.add_argument("--pages", default=1, type=int, help="Search pages per platform")
    args = parser.parse_args()

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    if args.platform in {"all", "jd"}:
        process.crawl("jd_search", keyword=args.keyword, pages=args.pages)
    if args.platform in {"all", "taobao"}:
        process.crawl("taobao_search", keyword=args.keyword, pages=args.pages)
    process.start()


if __name__ == "__main__":
    main()
