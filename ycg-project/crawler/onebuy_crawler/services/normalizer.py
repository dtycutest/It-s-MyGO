from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse, urlunparse


SPACE_RE = re.compile(r"\s+")
PRICE_RE = re.compile(r"(\d+(?:\.\d+)?)")
SALES_RE = re.compile(r"(\d+(?:\.\d+)?)(万|千|k|K)?")
TAG_RE = re.compile(r"<[^>]+>")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = TAG_RE.sub("", str(value))
    return SPACE_RE.sub(" ", text).strip()


def normalize_title(value: Any) -> str:
    title = unicodedata.normalize("NFKC", clean_text(value))
    title = re.sub(r"[\u200b\xa0]+", " ", title)
    return SPACE_RE.sub(" ", title).strip()


def parse_price(value: Any) -> Decimal | None:
    text = clean_text(value).replace(",", "")
    match = PRICE_RE.search(text)
    if not match:
        return None
    try:
        return Decimal(match.group(1)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def parse_sales(value: Any) -> int | None:
    text = clean_text(value).replace("+", "").replace(",", "")
    match = SALES_RE.search(text)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "万":
        number *= 10000
    elif unit in {"千", "k", "K"}:
        number *= 1000
    return int(number)


def parse_rating(value: Any) -> float | None:
    text = clean_text(value)
    match = PRICE_RE.search(text)
    if not match:
        return None
    rating = float(match.group(1))
    return max(0.0, min(5.0, rating))


def normalize_url(value: Any, base_url: str = "") -> str:
    text = clean_text(value)
    if not text:
        return ""
    if text.startswith("//"):
        text = "https:" + text
    if base_url:
        text = urljoin(base_url, text)
    return canonicalize_product_url(text)


def canonicalize_product_url(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    parsed = urlparse(text)
    host = parsed.netloc.lower()
    query = parse_qs(parsed.query)

    if "taobao.com" in host or "tmall.com" in host:
        item_id = _first_query_value(query, "id", "item_id", "itemId", "itemIdStr", "nid")
        if not item_id and "url" in query:
            nested = canonicalize_product_url(unquote(query["url"][0]))
            if nested:
                return nested
        if item_id:
            if "tmall.com" in host:
                return f"https://detail.tmall.com/item.htm?id={item_id}"
            return f"https://item.taobao.com/item.htm?id={item_id}"

    if "jd.com" in host:
        match = re.search(r"/(\d{5,})\.html", parsed.path)
        if match:
            return f"https://item.jd.com/{match.group(1)}.html"

    if parsed.query:
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return text


def _first_query_value(query: dict[str, list[str]], *keys: str) -> str:
    for key in keys:
        values = query.get(key)
        if values and values[0]:
            return clean_text(values[0])
    return ""


def normalize_image_url(value: Any, base_url: str = "") -> str:
    url = normalize_url(value, base_url)
    return url.split(".webp")[0] + ".webp" if ".webp" in url else url


def calculate_discount_rate(price: Decimal | None, original_price: Decimal | None) -> int | None:
    if not price or not original_price or original_price <= 0:
        return None
    rate = int((Decimal("1") - price / original_price) * 100)
    return max(0, min(100, rate))


def decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def compact_fingerprint_text(value: Any) -> str:
    text = normalize_title(value).lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    noise_words = (
        "官方",
        "旗舰店",
        "官方旗舰",
        "自营",
        "京东",
        "淘宝",
        "天猫",
        "正品",
        "包邮",
        "现货",
        "新品",
        "全新",
        "国行",
        "原装",
        "授权",
        "旗舰",
        "百亿补贴",
        "限时",
        "秒杀",
        "套餐",
        "赠品",
        "到手价",
        "全国联保",
    )
    for word in noise_words:
        text = text.replace(word, "")
    return text
