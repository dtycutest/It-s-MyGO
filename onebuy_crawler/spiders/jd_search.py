from __future__ import annotations

from urllib.parse import urlencode

from onebuy_crawler.compat import scrapy
from onebuy_crawler.spiders.base import BaseProductSpider


class JdSearchSpider(BaseProductSpider):
    name = "jd_search"
    platform_code = "jingdong"
    platform_name = "京东"
    allowed_domains = ["search.jd.com", "item.jd.com", "cfe.m.jd.com", "www.jd.com"]
    referer = "https://www.jd.com/"

    def __init__(self, keyword: str = "", pages: int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword = keyword
        self.pages = int(pages)

    async def start(self):
        for page in range(1, self.pages + 1):
            params = {"keyword": self.keyword, "enc": "utf-8", "page": page * 2 - 1}
            yield scrapy.Request(
                f"https://search.jd.com/Search?{urlencode(params)}",
                callback=self.parse,
                meta={"keyword": self.keyword, "page": page, "platform_code": self.platform_code},
                headers={"Referer": self.referer},
            )

    def parse(self, response):
        if "risk_handler" in response.url:
            yield self.blocked_item(response, "jd_risk_handler_without_cookie")
            return

        if self.is_blocked(response):
            yield self.blocked_item(response)
            return

        cards = response.css("li.gl-item")
        if not cards:
            yield self.blocked_item(response, "empty_or_structure_changed")
            return

        for card in cards:
            sku = card.attrib.get("data-sku") or self.first_text(card, "::attr(data-sku)")
            title = self.first_text(card, ".p-name em::text", ".p-name a::attr(title)")
            price = self.first_text(card, ".p-price i::text")
            detail_url = self.first_attr(card, ".p-name a::attr(href)", response.url)
            image_url = self.first_attr(card, ".p-img img::attr(data-lazy-img)", response.url) or self.first_attr(
                card, ".p-img img::attr(src)", response.url
            )
            seller_name = self.first_text(card, ".p-shop a::text", ".p-shop span::text")
            sales = self.first_text(card, ".p-commit strong a::text", ".p-commit strong::text")

            if not sku or not title:
                continue

            yield self.raw_item(
                keyword=response.meta.get("keyword"),
                source_sku_id=sku,
                title=title,
                price_text=price,
                sales_text=sales,
                seller_name=seller_name,
                image_url=image_url,
                product_url=detail_url,
                in_stock=True,
                raw_payload={"page": response.meta.get("page")},
            )
