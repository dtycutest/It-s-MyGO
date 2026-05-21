from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urljoin


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
    title = clean_text(value)
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
        return "https:" + text
    if base_url:
        return urljoin(base_url, text)
    return text


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
    noise_words = ("官方", "旗舰店", "自营", "正品", "包邮", "现货", "新品")
    for word in noise_words:
        text = text.replace(word, "")
    return text
