from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

from onebuy_crawler.items import RawProductItem
from onebuy_crawler.services.normalizer import clean_text


JSONP_RE = re.compile(r"^[\w.$]+\((.*)\)\s*;?\s*$", re.S)


@dataclass(frozen=True)
class ExtractResult:
    items: list[RawProductItem]
    reason: str = ""


def parse_jsonish(text: str) -> Any | None:
    text = text.strip()
    if not text:
        return None
    match = JSONP_RE.match(text)
    if match:
        text = match.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_from_response(platform: str, url: str, body: str, keyword: str) -> ExtractResult:
    payload = parse_jsonish(body)
    if payload is None:
        return ExtractResult([])

    if platform == "taobao":
        items = _extract_taobao_payload(payload, keyword)
        return ExtractResult(items, "" if items else "taobao_response_without_product_items")
    if platform == "jd":
        items = _extract_jd_payload(payload, keyword)
        return ExtractResult(items, "" if items else "jd_response_without_product_items")
    return ExtractResult([])


def extract_jd_price_map(body_or_payload: Any) -> dict[str, dict[str, str]]:
    payload = parse_jsonish(body_or_payload) if isinstance(body_or_payload, str) else body_or_payload
    if payload is None:
        return {}

    prices: dict[str, dict[str, str]] = {}
    for mapping in _walk_dicts(payload):
        sku = _normalize_jd_sku(_first(mapping, "skuId", "sku_id", "sku", "wareId", "id"))
        price = _first(mapping, "price", "p", "jdPrice", "lowestPrice", "lowestCouponPrice")
        if not sku or not price:
            continue
        entry = {"price": clean_text(price)}
        original_price = _first(mapping, "originalPrice", "marketPrice", "m", "op", "wlPrice")
        if original_price:
            entry["original_price"] = clean_text(original_price)
        prices[sku] = entry
    return prices


def extract_from_dom(platform: str, rows: Iterable[dict[str, Any]], keyword: str) -> list[RawProductItem]:
    items = []
    for row in rows:
        if platform == "taobao":
            item = _taobao_item_from_mapping(row, keyword)
        elif platform == "jd":
            item = _jd_item_from_mapping(row, keyword)
        else:
            item = None
        if item:
            items.append(item)
    return items


def failure_item(platform: str, url: str, keyword: str, reason: str, payload: dict[str, Any] | None = None) -> RawProductItem:
    platform_name = {"taobao": "淘宝", "jd": "京东", "jingdong": "京东"}.get(platform, "其他")
    platform_code = "jingdong" if platform == "jd" else platform
    item = RawProductItem()
    item["platform_code"] = platform_code
    item["platform_name"] = platform_name
    item["keyword"] = keyword
    item["product_url"] = url
    item["parse_status"] = "failed"
    item["failure_reason"] = reason
    item["raw_payload"] = payload or {}
    item["crawl_time"] = datetime.now(timezone.utc).isoformat()
    return item


def _extract_taobao_payload(payload: Any, keyword: str) -> list[RawProductItem]:
    items: list[RawProductItem] = []
    for mapping in _walk_dicts(payload):
        item = _taobao_item_from_mapping(mapping, keyword)
        if item:
            items.append(item)
    return _dedupe(items)


def _extract_jd_payload(payload: Any, keyword: str) -> list[RawProductItem]:
    items: list[RawProductItem] = []
    for mapping in _walk_dicts(payload):
        item = _jd_item_from_mapping(mapping, keyword)
        if item:
            items.append(item)
    return _dedupe(items)


def _taobao_item_from_mapping(data: dict[str, Any], keyword: str) -> RawProductItem | None:
    sku = _first(data, "item_id", "itemId", "nid", "id", "auctionId", "itemIdStr")
    title = _first(data, "title", "raw_title", "rawTitle", "name", "item_title")
    price = _first(data, "view_price", "price", "salePrice", "realPrice", "promotionPrice")
    if not sku or not title or not price:
        return None
    if not _matches_keyword(title, keyword):
        return None
    url = _first(data, "detail_url", "detailUrl", "auctionURL", "item_url", "url")
    image = _first(data, "pic_url", "picUrl", "pict_url", "image", "img")
    return _raw_item(
        platform_code="taobao",
        platform_name="淘宝",
        keyword=keyword,
        source_sku_id=str(sku),
        title=title,
        price_text=price,
        sales_text=_first(data, "view_sales", "sales", "sold", "monthSales", "realSales"),
        seller_name=_first(data, "nick", "shopName", "sellerName", "storeName"),
        image_url=_url(image, "https:"),
        product_url=_url(url, "https://item.taobao.com/"),
        promo_info=_first(data, "promotion", "coupon", "icon", "subTitle"),
        raw_payload={"source": "browser_response"},
    )


def _jd_item_from_mapping(data: dict[str, Any], keyword: str) -> RawProductItem | None:
    sku = _normalize_jd_sku(_first(data, "skuId", "sku_id", "sku", "wareId", "ware_id", "spuId", "id"))
    title = _first(data, "skuName", "productName", "wareName", "name", "title")
    price = _first(data, "price", "p", "lowestPrice", "lowestCouponPrice", "wlPrice", "jdPrice")
    if not sku or not title or not price:
        return None
    if not _matches_keyword(title, keyword):
        return None
    image = _first(data, "imageUrl", "image", "imgUrl", "pictureUrl", "skuPicUrl")
    url = _first(data, "materialUrl", "itemUrl", "url", "link")
    return _raw_item(
        platform_code="jingdong",
        platform_name="京东",
        keyword=keyword,
        source_sku_id=sku,
        title=title,
        price_text=price,
        original_price_text=_first(data, "originalPrice", "marketPrice", "m", "op", "wlPrice"),
        sales_text=_first(data, "comments", "commentCount", "sales", "inOrderCount30Days"),
        seller_name=_first(data, "shopName", "sellerName", "owner"),
        image_url=_url(image, "https://img10.360buyimg.com/"),
        product_url=_url(url, f"https://item.jd.com/{sku}.html"),
        promo_info=_first(data, "couponInfo", "discount", "promotionLabel"),
        raw_payload={"source": "browser_response"},
    )


def _raw_item(**values: Any) -> RawProductItem:
    item = RawProductItem()
    item["crawl_time"] = datetime.now(timezone.utc).isoformat()
    item["parse_status"] = "ok"
    item["in_stock"] = True
    for key, value in values.items():
        item[key] = clean_text(value) if isinstance(value, str) else value
    return item


def _walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _first(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, "", [], {}):
            if isinstance(value, dict):
                nested = _first(value, "price", "value", "text", "title", "url")
                if nested not in (None, ""):
                    return nested
            else:
                return value
    return ""


def _url(value: Any, default_or_base: str) -> str:
    text = clean_text(value)
    if not text:
        return default_or_base
    if text.startswith("//"):
        return "https:" + text
    if text.startswith("http"):
        return text
    if default_or_base.startswith("http") and default_or_base.endswith("/"):
        return urljoin(default_or_base, text)
    return text


def _normalize_jd_sku(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    match = re.search(r"(\d{5,})", text)
    return match.group(1) if match else text


def _dedupe(items: list[RawProductItem]) -> list[RawProductItem]:
    seen = set()
    result = []
    for item in items:
        key = (item.get("platform_code"), item.get("source_sku_id"))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _matches_keyword(title: Any, keyword: str) -> bool:
    title_text = clean_text(title).lower()
    keyword_text = clean_text(keyword).lower()
    if not keyword_text:
        return True
    tokens = [token for token in re.split(r"\s+", keyword_text) if len(token) >= 2]
    if not tokens:
        return keyword_text in title_text
    return all(token in title_text for token in tokens)
