from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, unquote, urlparse


JD_ITEM_URL_RE = re.compile(
    r"(?:(?:https?:)?//)?(?:item|item\.m)\.jd\.com/(?:product/)?(\d+)\.html",
    re.I,
)
JD_SKU_RE = re.compile(r"""(?:data-sku|skuId|sku_id|sku)["'\s:=]+(\d{5,})""", re.I)
TAOBAO_ITEM_URL_RE = re.compile(
    r"(?:(?:https?:)?//)?(?:item\.taobao|detail\.tmall)\.com/item\.htm\?[^\"'<>\\\s]+",
    re.I,
)


def extract_product_urls(text: str, platform: str = "auto") -> list[str]:
    """Extract canonical product detail URLs from plain text, copied links, or HTML."""
    normalized = html.unescape(unquote(str(text or "")))
    urls: list[str] = []
    if platform in {"auto", "jd", "jingdong"}:
        urls.extend(f"https://item.jd.com/{match.group(1)}.html" for match in JD_ITEM_URL_RE.finditer(normalized))
        urls.extend(f"https://item.jd.com/{match.group(1)}.html" for match in JD_SKU_RE.finditer(normalized))
    if platform in {"auto", "taobao"}:
        for match in TAOBAO_ITEM_URL_RE.finditer(normalized):
            url = _with_scheme(match.group(0))
            item_id = parse_qs(urlparse(url).query).get("id", [""])[0]
            if item_id:
                host = urlparse(url).netloc.lower()
                domain = "detail.tmall.com" if "tmall.com" in host else "item.taobao.com"
                urls.append(f"https://{domain}/item.htm?id={item_id}")
    return list(dict.fromkeys(urls))


def extract_jd_sku(url: str) -> str:
    match = JD_ITEM_URL_RE.search(html.unescape(unquote(str(url or ""))))
    return match.group(1) if match else ""


def _with_scheme(url: str) -> str:
    return "https:" + url if url.startswith("//") else url
