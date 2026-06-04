from __future__ import annotations

import json
import re
from urllib.parse import urlencode

from onebuy_crawler.compat import scrapy
from onebuy_crawler.spiders.base import BaseProductSpider


class TaobaoSearchSpider(BaseProductSpider):
    name = "taobao_search"
    platform_code = "taobao"
    platform_name = "淘宝"
    allowed_domains = ["s.taobao.com", "item.taobao.com"]
    referer = "https://www.taobao.com/"

    def __init__(self, keyword: str = "", pages: int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword = keyword
        self.pages = int(pages)

    async def start(self):
        for page in range(self.pages):
            params = {"q": self.keyword, "s": page * 44}
            yield scrapy.Request(
                f"https://s.taobao.com/search?{urlencode(params)}",
                callback=self.parse,
                meta={"keyword": self.keyword, "page": page + 1, "platform_code": self.platform_code},
                headers={"Referer": self.referer},
            )

    def parse(self, response):
        if self.is_blocked(response):
            yield self.blocked_item(response)
            return

        yielded = False
        for payload in self._extract_embedded_items(getattr(response, "text", "")):
            yielded = True
            yield self.raw_item(
                keyword=response.meta.get("keyword"),
                source_sku_id=str(payload.get("item_id") or payload.get("nid") or payload.get("id") or ""),
                title=payload.get("title") or payload.get("raw_title"),
                price_text=payload.get("view_price") or payload.get("price"),
                sales_text=payload.get("view_sales") or payload.get("sold"),
                seller_name=payload.get("nick") or payload.get("shopName"),
                image_url=payload.get("pic_url") or payload.get("picUrl"),
                product_url=payload.get("detail_url") or payload.get("auctionURL"),
                promo_info=payload.get("icon") or payload.get("promotion"),
                in_stock=True,
                raw_payload={"page": response.meta.get("page")},
            )

        if yielded:
            return

        text = getattr(response, "text", "")
        if '"documentOnly":true' in text or "请不要禁用JS" in text:
            yield self.blocked_item(response, "taobao_client_rendered_without_embedded_items")
            return

        if getattr(response, "selector", None) is not None and getattr(response.selector, "type", "") == "json":
            yield self.blocked_item(response, "taobao_json_without_items")
            return

        cards = response.css("[data-category='auctions'] .item, .items .item")
        if not cards:
            yield self.blocked_item(response, "empty_or_structure_changed")
            return
        for card in cards:
            sku = card.css("::attr(data-nid)").get()
            title = self.first_text(card, ".title::text", ".row-2.title a::text")
            price = self.first_text(card, ".price strong::text", ".price::text")
            if not sku or not title:
                continue
            yield self.raw_item(
                keyword=response.meta.get("keyword"),
                source_sku_id=sku,
                title=title,
                price_text=price,
                sales_text=self.first_text(card, ".deal-cnt::text"),
                seller_name=self.first_text(card, ".shopname::text"),
                image_url=self.first_attr(card, "img::attr(data-src)", response.url),
                product_url=self.first_attr(card, ".title a::attr(href)", response.url),
                in_stock=True,
                raw_payload={"page": response.meta.get("page")},
            )

    @staticmethod
    def _extract_embedded_items(text: str) -> list[dict]:
        candidates = []
        for match in re.finditer(r"g_page_config\s*=\s*(\{.*?\});", text, flags=re.S):
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            auctions = (
                data.get("mods", {})
                .get("itemlist", {})
                .get("data", {})
                .get("auctions", [])
            )
            candidates.extend([item for item in auctions if isinstance(item, dict)])
        return candidates
