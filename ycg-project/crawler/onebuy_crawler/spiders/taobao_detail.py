from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from onebuy_crawler.compat import scrapy
from onebuy_crawler.spiders.base import BaseProductSpider


class TaobaoDetailSpider(BaseProductSpider):
    name = "taobao_detail"
    platform_code = "taobao"
    platform_name = "淘宝"
    allowed_domains = ["item.taobao.com", "detail.tmall.com"]
    referer = "https://www.taobao.com/"

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

        parsed = urlparse(response.url)
        sku = response.meta.get("source_sku_id") or parse_qs(parsed.query).get("id", [""])[0]
        title = self.first_text(response, "h1::text", "title::text")
        price = self.first_text(
            response,
            ".tb-rmb-num::text",
            ".tm-price::text",
            "#J_StrPrice .tb-rmb-num::text",
            "#J_PromoPrice .tb-rmb-num::text",
        )
        image_url = self.first_attr(response, "img#J_ImgBooth::attr(src)", response.url)
        seller_name = self.first_text(response, ".shop-name-link::text", ".tb-shop-name a::text")
        if not sku or not title:
            yield self.blocked_item(response, "empty_or_structure_changed")
            return

        yield self.raw_item(
            source_sku_id=sku,
            title=title,
            price_text=price,
            image_url=image_url,
            product_url=response.url,
            seller_name=seller_name,
            category_text="淘宝商品",
            in_stock=True,
            raw_payload={"source": "detail"},
        )
