"""Import seed data from crawler JSON into MySQL.

Usage:
    cd backend
    python -m scripts.import_seed
"""

from __future__ import annotations

import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.models import ProductModel, PlatformOfferModel, PriceHistoryModel
from app.database import engine, SessionLocal, create_tables

SEED_FILE = Path(__file__).resolve().parent.parent.parent / "crawler" / "data" / "onebuy_seed_records_all.json"

PLATFORM_CODE_TO_ID = {
    "taobao": 1,
    "jingdong": 2,
    "pinduoduo": 3,
    "amazon": 4,
    "other": 5,
}

PLATFORM_CODE_TO_NAME = {
    "taobao": "淘宝",
    "jingdong": "京东",
    "pinduoduo": "拼多多",
    "amazon": "亚马逊",
    "other": "其他",
}


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


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def import_seed():
    if not SEED_FILE.exists():
        print(f"Seed file not found: {SEED_FILE}")
        return

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    records: list[dict] = data.get("records", [])
    print(f"Loaded {len(records)} records from seed file")

    create_tables()
    print("Tables created/verified")

    # Group by product_id
    groups: dict[str, list[dict]] = {}
    for rec in records:
        pid = rec["product_id"]
        groups.setdefault(pid, []).append(rec)

    db = SessionLocal()

    try:
        product_count = 0
        offer_count = 0
        history_count = 0

        for product_id, group in groups.items():
            first = group[0]
            title = first["title"]
            category_text = first.get("category_text", "未分类")

            # Find category_id from path
            category_id = hash(category_text) % 10000 + 1 if category_text != "未分类" else 0

            prices = []
            for rec in group:
                price = _parse_float(rec.get("price_text")) or 0.0
                if price > 0:
                    prices.append(price)

            min_price = min(prices) if prices else 0.0
            max_price = max(prices) if prices else 0.0
            price_diff = max_price - min_price

            best_platform = ""
            if group and prices:
                best_idx = prices.index(min_price)
                best_platform = group[best_idx].get("platform_name", "")

            # Check if product already exists
            existing = db.query(ProductModel).filter(ProductModel.product_id == product_id).first()
            if existing:
                # Update existing
                existing.title = title
                existing.category_id = category_id
                existing.category_name = category_text
                existing.image_url = first.get("image_url")
                existing.images = [first.get("image_url")] if first.get("image_url") else []
                existing.min_price = min_price
                existing.max_price = max_price
                existing.price_diff = price_diff
                existing.best_platform = best_platform
                existing.updated_at = datetime.now(timezone.utc)
            else:
                fingerprint = hashlib.sha256(title.encode()).hexdigest()[:64]
                db_product = ProductModel(
                    product_id=product_id,
                    match_fingerprint=fingerprint,
                    title=title,
                    category_id=category_id,
                    category_name=category_text,
                    image_url=first.get("image_url"),
                    images=[first.get("image_url")] if first.get("image_url") else [],
                    min_price=min_price,
                    max_price=max_price,
                    price_diff=price_diff,
                    best_platform=best_platform,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(db_product)
                product_count += 1

            # Insert platform offers
            for rec in group:
                platform_code = rec["platform_code"]
                platform_id = PLATFORM_CODE_TO_ID.get(platform_code, 5)
                platform_name = PLATFORM_CODE_TO_NAME.get(platform_code, "其他")
                source_sku_id = rec.get("source_sku_id", "")
                price = _parse_float(rec.get("price_text")) or 0.0
                original_price = _parse_float(rec.get("original_price_text"))
                sales_volume = _parse_int(rec.get("sales_text"))
                seller_rating = _parse_float(rec.get("seller_rating_text"))
                crawl_time = _parse_datetime(rec.get("crawl_time")) or datetime.now(timezone.utc)

                discount_rate = None
                if original_price and original_price > 0 and price > 0:
                    discount_rate = int(max(0, min(100, (1 - price / original_price) * 100)))

                # Check if offer already exists
                existing_offer = (
                    db.query(PlatformOfferModel)
                    .filter(
                        PlatformOfferModel.platform_code == platform_code,
                        PlatformOfferModel.source_sku_id == source_sku_id,
                    )
                    .first()
                )
                if existing_offer:
                    existing_offer.price = price
                    existing_offer.original_price = original_price
                    existing_offer.discount_rate = discount_rate
                    existing_offer.sales_volume = sales_volume
                    existing_offer.seller_rating = seller_rating
                    existing_offer.update_at = crawl_time
                else:
                    db_offer = PlatformOfferModel(
                        product_id=product_id,
                        platform_id=platform_id,
                        platform_name=platform_name,
                        platform_code=platform_code,
                        source_sku_id=source_sku_id,
                        price=price,
                        original_price=original_price,
                        discount_rate=discount_rate,
                        sales_volume=sales_volume,
                        seller_name=rec.get("seller_name") or None,
                        seller_rating=seller_rating,
                        seller_id=rec.get("seller_id") or rec.get("source_sku_id"),
                        product_url=rec.get("product_url"),
                        in_stock=rec.get("in_stock", True),
                        stock_quantity=rec.get("stock_quantity"),
                        update_at=crawl_time,
                    )
                    db.add(db_offer)
                    offer_count += 1

                # Insert price history
                if price > 0:
                    db_history = PriceHistoryModel(
                        product_id=product_id,
                        platform_code=platform_code,
                        price=price,
                        promo_info=rec.get("promo_info") or None,
                        crawl_time=crawl_time,
                    )
                    db.add(db_history)
                    history_count += 1

        db.commit()
        print(f"Imported: {product_count} new products, {offer_count} new offers, {history_count} price history records")

        # Verify
        total_products = db.query(ProductModel).count()
        total_offers = db.query(PlatformOfferModel).count()
        total_history = db.query(PriceHistoryModel).count()
        print(f"Database now has: {total_products} products, {total_offers} offers, {total_history} price records")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_seed()