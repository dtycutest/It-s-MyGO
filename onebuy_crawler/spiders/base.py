from __future__ import annotations

from datetime import datetime, timezone

from onebuy_crawler.compat import scrapy
from onebuy_crawler.constants import ANTI_BOT_MARKERS
from onebuy_crawler.items import RawProductItem
from onebuy_crawler.services.normalizer import clean_text, normalize_url


class BaseProductSpider(scrapy.Spider):
    platform_code = "other"
    platform_name = "其他"
    allowed_domains: list[str] = []
    referer = "https://www.baidu.com/"

    def blocked_item(self, response, reason: str = "anti_bot_or_blocked"):
        item = RawProductItem()
        item["platform_code"] = self.platform_code
        item["platform_name"] = self.platform_name
        item["product_url"] = getattr(response, "url", "")
        item["parse_status"] = "failed"
        item["failure_reason"] = reason
        item["raw_payload"] = {"status": getattr(response, "status", None)}
        item["crawl_time"] = datetime.now(timezone.utc).isoformat()
        return item

    def is_blocked(self, response) -> bool:
        if getattr(response, "status", 200) in (401, 403, 429):
            return True
        text = getattr(response, "text", "")[:2000]
        return any(marker.lower() in text.lower() for marker in ANTI_BOT_MARKERS)

    def raw_item(self, **kwargs):
        item = RawProductItem()
        item["platform_code"] = self.platform_code
        item["platform_name"] = self.platform_name
        item["crawl_time"] = datetime.now(timezone.utc).isoformat()
        item["parse_status"] = "ok"
        for key, value in kwargs.items():
            item[key] = value
        return item

    @staticmethod
    def first_text(selector, *queries: str) -> str:
        for query in queries:
            for value in selector.css(query).getall():
                text = clean_text(value)
                if text:
                    return text
        return ""

    @staticmethod
    def first_attr(selector, query: str, base_url: str = "") -> str:
        value = selector.css(query).get()
        return normalize_url(value, base_url)
