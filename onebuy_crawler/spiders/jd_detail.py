from __future__ import annotations

import json

from onebuy_crawler.compat import scrapy
from onebuy_crawler.spiders.base import BaseProductSpider


class JdDetailSpider(BaseProductSpider):
    name = "jd_detail"
    platform_code = "jingdong"
    platform_name = "京东"
    allowed_domains = ["item.jd.com", "search.jd.com", "p.3.cn"]
    referer = "https://www.jd.com/"

    def __init__(self, url: str = "", source_sku_id: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.source_sku_id = source_sku_id

    async def start(self):
        if self.url:
            yield scrapy.Request(
                self.url,
                callback=self.parse,
                meta={"source_sku_id": self.source_sku_id, "platform_code": self.platform_code},
                headers={"Referer": self.referer},
            )

    def parse(self, response):
        if self.is_blocked(response):
            yield self.blocked_item(response)
            return

        sku = response.meta.get("source_sku_id") or response.css("div.itemInfo-wrap::attr(data-sku)").get()
        title = self.first_text(response, ".sku-name::text", "title::text")
        image_url = self.first_attr(response, "#spec-img::attr(data-origin)", response.url) or self.first_attr(
            response, "#spec-img::attr(src)", response.url
        )
        seller_name = self.first_text(response, ".name a::text", "#popbox .mt h3 a::text")
        category = "京东商品"
        if not sku:
            sku = response.url.rstrip("/").split("/")[-1].replace(".html", "")

        if not title:
            yield self.blocked_item(response, "empty_or_structure_changed")
            return

        price = self.first_text(response, ".summary-price .price::text", ".p-price .price::text")
        base_item = self.raw_item(
            source_sku_id=sku,
            title=title,
            price_text=price,
            image_url=image_url,
            product_url=response.url,
            seller_name=seller_name,
            category_text=category,
            in_stock=True,
            raw_payload={"source": "detail"},
        )

        if price:
            yield base_item
            return

        yield scrapy.Request(
            f"https://p.3.cn/prices/mgets?skuIds=J_{sku}",
            callback=self.parse_price_api,
            meta={"base_item": dict(base_item), "platform_code": self.platform_code},
            dont_filter=True,
        )

    def parse_price_api(self, response):
        base_item = response.meta["base_item"]
        try:
            payload = json.loads(response.text)
            if payload:
                base_item["price_text"] = payload[0].get("p") or payload[0].get("op")
                base_item["original_price_text"] = payload[0].get("m")
        except (json.JSONDecodeError, KeyError, TypeError):
            base_item["parse_status"] = "failed"
            base_item["failure_reason"] = "price_api_parse_failed"
        yield base_item
