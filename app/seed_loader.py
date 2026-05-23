"""Load crawled seed.json data and transform into backend schema objects."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .schemas import Category, Platform, Product

SEED_PATH = Path(__file__).parent / "seed.json"

PLATFORM_CODE_TO_ID: Dict[str, int] = {
    "taobao": 1,
    "jingdong": 2,
    "pinduoduo": 3,
    "amazon": 4,
    "other": 5,
}

# Build category tree from dotted paths like "手机-智能手机"
def _build_categories(records: List[dict]) -> List[Category]:
    cat_map: Dict[str, int] = {}
    cat_list: List[Category] = []
    cat_id = 1

    for rec in records:
        path = rec.get("category_text", "")
        if not path:
            continue
        parts = path.split("-")
        for i, part in enumerate(parts):
            key = "-".join(parts[: i + 1])
            if key not in cat_map:
                parent_key = "-".join(parts[:i]) if i > 0 else ""
                parent_id = cat_map.get(parent_key, 0)
                cat_map[key] = cat_id
                cat_list.append(Category(category_id=cat_id, name=part, parent_id=parent_id))
                cat_id += 1
    return cat_list


def _parse_float(value: str | None) -> float | None:
    if not value or not str(value).strip():
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_int(value: str | None) -> int | None:
    if not value or not str(value).strip():
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _map_platform_name(code: str) -> str:
    mapping = {
        "taobao": "淘宝",
        "jingdong": "京东",
        "pinduoduo": "拼多多",
        "amazon": "亚马逊",
        "other": "其他",
    }
    return mapping.get(code, "其他")


def load_seed() -> tuple[List[Product], List[Category], List[dict]]:
    """Load seed.json and return (products, categories, raw_records)."""
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    records: List[dict] = data.get("records", [])

    # Build category tree
    categories = _build_categories(records)
    cat_path_to_id: Dict[str, int] = {}
    for cat in categories:
        # Reconstruct full path by parent chain
        cat_path_to_id[cat.name] = cat.category_id

    # Actually, build proper path-to-id mapping
    cat_path_to_id = {}
    for rec in records:
        path = rec.get("category_text", "")
        if path and path not in cat_path_to_id:
            for cat in categories:
                # Walk parent chain to reconstruct path
                parts = [cat.name]
                parent_id = cat.parent_id
                while parent_id:
                    parent = next((c for c in categories if c.category_id == parent_id), None)
                    if parent:
                        parts.insert(0, parent.name)
                        parent_id = parent.parent_id
                    else:
                        break
                full = "-".join(parts)
                if full == path:
                    cat_path_to_id[path] = cat.category_id
                    break

    # Group records by product_id
    groups: Dict[str, List[dict]] = {}
    for rec in records:
        pid = rec["product_id"]
        if pid not in groups:
            groups[pid] = []
        groups[pid].append(rec)

    # Build Product objects
    products: List[Product] = []
    for product_id, group in groups.items():
        first = group[0]
        title = first["title"]
        category_text = first.get("category_text", "")
        category_id = cat_path_to_id.get(category_text, 0)

        # Build category name from path
        cat_name = category_text

        # Build platforms
        platforms: List[Platform] = []
        prices: List[float] = []

        for rec in group:
            platform_code = rec["platform_code"]
            platform_id = PLATFORM_CODE_TO_ID.get(platform_code, 5)
            platform_name = _map_platform_name(platform_code)
            price = _parse_float(rec.get("price_text")) or 0.0
            original_price = _parse_float(rec.get("original_price_text"))
            sales_volume = _parse_int(rec.get("sales_text"))

            if price > 0:
                prices.append(price)

            discount_rate = None
            if original_price and original_price > 0 and price > 0:
                discount_rate = int(max(0, min(100, (1 - price / original_price) * 100)))

            crawl_time = rec.get("crawl_time")
            update_at = None
            if crawl_time:
                try:
                    update_at = datetime.strptime(crawl_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass

            platform = Platform(
                platform_id=platform_id,
                platform_name=platform_name,
                platform_code=platform_code,
                price=price,
                original_price=original_price,
                discount_rate=discount_rate,
                in_stock=rec.get("in_stock", True),
                product_url=rec.get("product_url"),
                seller_id=rec.get("seller_id") or rec.get("source_sku_id"),
                seller_name=rec.get("seller_name") or None,
                seller_rating=_parse_float(rec.get("seller_rating_text")),
                sales_volume=sales_volume,
                stock_quantity=rec.get("stock_quantity"),
                update_at=update_at,
            )
            platforms.append(platform)

        min_price = min(prices) if prices else 0.0
        max_price = max(prices) if prices else 0.0
        price_diff = max_price - min_price

        best_platform = ""
        if platforms and prices:
            best_idx = prices.index(min_price)
            best_platform = platforms[best_idx].platform_name

        now = datetime.now(timezone.utc)

        product = Product(
            product_id=product_id,
            title=title,
            category_id=category_id,
            category_name=cat_name,
            description="",
            image_url=first.get("image_url"),
            images=[first.get("image_url")] if first.get("image_url") else [],
            min_price=min_price,
            max_price=max_price,
            best_platform=best_platform,
            price_diff=price_diff,
            specs=first.get("specs") or {},
            platforms=platforms,
            created_at=now,
            updated_at=now,
        )
        products.append(product)

    return products, categories, records
