from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import unquote


JD_CARD_RE = re.compile(r'data-sku=["\'](\d{5,})["\']', re.I)
TAG_RE = re.compile(r"<[^>]+>")


def extract_jd_rows_from_copied_html(text: str, max_rows: int = 0) -> list[dict[str, Any]]:
    """Extract JD product rows from copied search-result HTML."""
    source = html.unescape(unquote(str(text or "")))
    matches = list(JD_CARD_RE.finditer(source))
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, match in enumerate(matches):
        sku = match.group(1)
        if sku in seen:
            continue
        seen.add(sku)
        end = matches[index + 1].start() if index + 1 < len(matches) else min(len(source), match.start() + 12000)
        segment = source[match.start() : end]
        row = {
            "skuId": sku,
            "skuName": _first_title(segment),
            "price": _first_price(segment),
            "imageUrl": _first_image(segment),
            "itemUrl": f"https://item.jd.com/{sku}.html",
            "shopName": _first_shop(segment),
            "commentCount": _first_sales(segment),
        }
        if row["skuName"] and row["price"]:
            rows.append(row)
            if max_rows and len(rows) >= max_rows:
                break
    return rows


def _first_title(segment: str) -> str:
    titles = re.findall(r'title=["\']([^"\']{4,300})["\']', segment, flags=re.I)
    for title in titles:
        cleaned = _clean(title)
        if _looks_like_product_title(cleaned):
            return cleaned
    text_matches = re.findall(r'class=["\'][^"\']*(?:text|title)[^"\']*["\'][^>]*>(.*?)</span>', segment, flags=re.I | re.S)
    for value in text_matches:
        cleaned = _clean(value)
        if _looks_like_product_title(cleaned):
            return cleaned
    return ""


def _first_price(segment: str) -> str:
    for pattern in (
        r">¥</i>\s*<span[^>]*>\s*(\d+(?:\.\d+)?)\s*</span>",
        r"[¥￥]\s*(\d+(?:\.\d+)?)",
        r'"(?:price|jdPrice|p)"\s*:\s*"?(\d+(?:\.\d+)?)"?',
    ):
        match = re.search(pattern, segment, flags=re.I | re.S)
        if match:
            return match.group(1)
    return ""


def _first_image(segment: str) -> str:
    for pattern in (
        r'(?:data-src|src)=["\']([^"\']*(?:360buyimg|jdimg)[^"\']+)["\']',
        r'"(?:imageUrl|imgUrl|image)"\s*:\s*"([^"]+)"',
    ):
        match = re.search(pattern, segment, flags=re.I)
        if match:
            return _clean(match.group(1))
    return ""


def _first_shop(segment: str) -> str:
    for pattern in (
        r'class=["\'][^"\']*(?:limit|shop|name)[^"\']*["\'][^>]*>([^<>]{2,80})</span>',
        r'"(?:shopName|sellerName)"\s*:\s*"([^"]+)"',
    ):
        match = re.search(pattern, segment, flags=re.I | re.S)
        if match:
            cleaned = _clean(match.group(1))
            if cleaned and not _looks_like_product_title(cleaned):
                return cleaned
    return ""


def _first_sales(segment: str) -> str:
    match = re.search(r'(已售\s*\d+[\d.,万千kK+]*|评论\s*\d+[\d.,万千kK+]*|\d+[\d.,万千kK+]*\s*条评价)', segment)
    return _clean(match.group(1)) if match else ""


def _looks_like_product_title(value: str) -> bool:
    if len(value) < 4:
        return False
    bad_tokens = ("http", "javascript", "客服", "购物车", "反馈", "显示更多", "展开筛选")
    return not any(token in value for token in bad_tokens)


def _clean(value: Any) -> str:
    text = html.unescape(unquote(str(value or "")))
    text = TAG_RE.sub("", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
