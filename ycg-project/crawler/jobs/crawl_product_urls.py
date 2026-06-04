from __future__ import annotations

import argparse
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.normalizer import normalize_url
from onebuy_crawler.services.product_urls import extract_jd_sku, extract_product_urls


def main() -> None:
    os.environ.setdefault("CRAWLER_ENABLE_MYSQL", "1")

    parser = argparse.ArgumentParser(description="Crawl product detail URLs when search pages are blocked.")
    parser.add_argument("--url", action="append", help="Product detail URL. Can be used multiple times.")
    parser.add_argument("--url-file", default="", help="UTF-8 text file, one product detail URL per line.")
    parser.add_argument("--platform", default="auto", choices=["auto", "jd", "jingdong", "taobao"])
    args = parser.parse_args()

    urls = collect_urls(args.url or [], args.url_file)
    if not urls:
        raise SystemExit("No product URLs provided. Use --url or --url-file.")

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    queued = 0
    for url in urls:
        platform = detect_platform(url) if args.platform == "auto" else normalize_platform(args.platform)
        source_sku_id = extract_source_sku_id(url, platform)
        if not platform or not source_sku_id:
            print(f"skip unsupported url: {url}")
            continue
        spider = "jd_detail" if platform == "jd" else "taobao_detail"
        process.crawl(spider, url=normalize_url(url), source_sku_id=source_sku_id)
        queued += 1

    if queued == 0:
        raise SystemExit("No supported product URLs queued.")
    print(f"detail crawl queued: {queued}")
    process.start()


def collect_urls(url_args: list[str], url_file: str) -> list[str]:
    urls = []
    for value in url_args:
        extracted = extract_product_urls(value)
        urls.extend(extracted or [value])
    if url_file:
        path = Path(url_file)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# Add one product detail URL per line, or paste copied search-result HTML/text.\n"
                "# https://item.jd.com/100144527620.html\n"
                "# https://item.taobao.com/item.htm?id=123456789\n",
                encoding="utf-8",
            )
            raise SystemExit(f"URL file not found, so a template was created: {path}")
        text = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#"))
        extracted = extract_product_urls(text)
        if extracted:
            urls.extend(extracted)
        else:
            urls.extend(line.strip() for line in text.splitlines() if line.strip())
    return list(dict.fromkeys(urls))


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "jd.com" in host:
        return "jd"
    if "taobao.com" in host or "tmall.com" in host:
        return "taobao"
    return ""


def normalize_platform(platform: str) -> str:
    return "jd" if platform in {"jd", "jingdong"} else platform


def extract_source_sku_id(url: str, platform: str) -> str:
    parsed = urlparse(url)
    if platform == "jd":
        return extract_jd_sku(url)
    if platform == "taobao":
        return parse_qs(parsed.query).get("id", [""])[0]
    return ""


if __name__ == "__main__":
    main()
