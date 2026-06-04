from __future__ import annotations

import argparse
from pathlib import Path

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def detect_spider(url: str) -> str | None:
    if "jd.com" in url:
        return "jd_detail"
    if "taobao.com" in url or "tmall.com" in url:
        return "taobao_detail"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill product details from URL list.")
    parser.add_argument("--input", required=True, help="Text file containing one product URL per line")
    args = parser.parse_args()

    urls = [line.strip() for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    for url in urls:
        spider = detect_spider(url)
        if spider:
            process.crawl(spider, url=url)
    process.start()


if __name__ == "__main__":
    main()
