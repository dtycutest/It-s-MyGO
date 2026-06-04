from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote_plus

from onebuy_crawler.items import RawProductItem
from onebuy_crawler.services.normalizer import clean_text


DEFAULT_SEED_FILE = Path(__file__).resolve().parents[2] / "data" / "jd_seed_products.json"

PLATFORM_ALIASES = {
    "jd": "jingdong",
    "jingdong": "jingdong",
    "taobao": "taobao",
}


def load_seed_records(path: str | Path | None = None) -> list[dict[str, Any]]:
    seed_path = Path(path) if path else DEFAULT_SEED_FILE
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        records = payload.get("records", [])
    else:
        records = payload
    if not isinstance(records, list):
        raise ValueError(f"Seed file records must be a list: {seed_path}")
    return [record for record in records if isinstance(record, dict)]


def select_seed_records(
    records: Iterable[dict[str, Any]],
    keywords: Iterable[str] | None = None,
    platform: str = "jd",
    limit_per_keyword: int = 0,
) -> list[dict[str, Any]]:
    platform_code = normalize_seed_platform(platform)
    keyword_list = [clean_text(keyword) for keyword in (keywords or []) if clean_text(keyword)]
    candidates = [record for record in records if normalize_seed_platform(record.get("platform_code", "jd")) == platform_code]

    if not keyword_list:
        return candidates

    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for keyword in keyword_list:
        matches = [record for record in candidates if record_matches_keyword(record, keyword)]
        if limit_per_keyword > 0:
            matches = matches[:limit_per_keyword]
        for record in matches:
            key = (
                normalize_seed_platform(record.get("platform_code", "jd")),
                clean_text(record.get("source_sku_id") or record.get("product_id") or record.get("title")),
            )
            if key in seen:
                continue
            seen.add(key)
            selected.append(record)
    return selected


def record_matches_keyword(record: dict[str, Any], keyword: str) -> bool:
    keyword_text = clean_text(keyword).lower()
    if not keyword_text:
        return True

    explicit_keywords = record.get("keywords") or record.get("keyword") or []
    if isinstance(explicit_keywords, str):
        explicit_keywords = [explicit_keywords]
    for value in explicit_keywords:
        if clean_text(value).lower() == keyword_text:
            return True

    title = clean_text(record.get("title")).lower()
    tokens = [token for token in re.split(r"\s+", keyword_text) if token]
    return all(token in title for token in tokens)


def build_generated_records(keyword: str, platform: str = "jd", count: int = 5) -> list[dict[str, Any]]:
    keyword = clean_text(keyword)
    platform_code = normalize_seed_platform(platform)
    if platform_code != "jingdong":
        raise ValueError("Generated fallback records currently support JD only.")
    if not keyword:
        return []

    digest = hashlib.sha1(keyword.encode("utf-8")).hexdigest()
    categories = ["数码配件", "智能硬件", "日用百货", "电脑办公", "家用电器"]
    records: list[dict[str, Any]] = []
    for index in range(1, max(0, count) + 1):
        price_seed = int(digest[index : index + 6], 16)
        price = 99 + (price_seed % 4900) + index * 7
        source_sku_id = f"seed-generated-{digest[:10]}-{index:03d}"
        title = f"{keyword} 京东课程演示商品 {index}"
        records.append(
            {
                "product_id": f"SKUDEMO{digest[:10].upper()}{index:03d}",
                "platform_code": "jingdong",
                "platform_name": "京东",
                "source_sku_id": source_sku_id,
                "keyword": keyword,
                "keywords": [keyword],
                "title": title,
                "price_text": f"{price:.2f}",
                "original_price_text": f"{price + 100:.2f}",
                "sales_text": f"{1000 + index * 137}+",
                "seller_name": "课程演示数据",
                "image_url": "",
                "product_url": f"https://search.jd.com/Search?keyword={quote_plus(keyword)}",
                "category_text": categories[(index - 1) % len(categories)],
                "promo_info": "本地兜底数据，用于联调演示，不代表实时京东价格",
                "raw_payload": {"source": "generated_seed_fallback"},
            }
        )
    return records


def record_to_raw_item(record: dict[str, Any], keyword: str = "") -> RawProductItem:
    platform_code = normalize_seed_platform(record.get("platform_code", "jd"))
    platform_name = clean_text(record.get("platform_name")) or ("京东" if platform_code == "jingdong" else "淘宝")
    crawl_time = record.get("crawl_time") or datetime.now(timezone.utc).isoformat()
    raw_payload = record.get("raw_payload") or {"source": "seed_cache"}

    item = RawProductItem()
    item["product_id"] = clean_text(record.get("product_id"))
    item["platform_code"] = platform_code
    item["platform_name"] = platform_name
    item["source_sku_id"] = clean_text(record.get("source_sku_id"))
    item["keyword"] = clean_text(keyword or record.get("keyword"))
    item["title"] = clean_text(record.get("title"))
    item["price_text"] = clean_text(record.get("price_text") or record.get("price"))
    item["original_price_text"] = clean_text(record.get("original_price_text") or record.get("original_price"))
    item["sales_text"] = clean_text(record.get("sales_text") or record.get("sales_volume"))
    item["seller_name"] = clean_text(record.get("seller_name"))
    item["seller_rating_text"] = clean_text(record.get("seller_rating_text") or record.get("seller_rating"))
    item["seller_id"] = clean_text(record.get("seller_id"))
    item["image_url"] = clean_text(record.get("image_url"))
    item["product_url"] = clean_text(record.get("product_url"))
    item["category_text"] = clean_text(record.get("category_text") or record.get("category_name"))
    item["promo_info"] = clean_text(record.get("promo_info"))
    item["specs"] = record.get("specs") or {}
    item["in_stock"] = record.get("in_stock", True)
    item["stock_quantity"] = record.get("stock_quantity")
    item["raw_payload"] = raw_payload
    item["crawl_time"] = crawl_time
    item["parse_status"] = "ok"
    return item


def normalize_seed_platform(platform: Any) -> str:
    platform_code = PLATFORM_ALIASES.get(clean_text(platform).lower())
    if not platform_code:
        raise ValueError(f"Unsupported platform: {platform}")
    return platform_code
