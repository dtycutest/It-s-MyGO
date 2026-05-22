from __future__ import annotations

from datetime import datetime, timezone
from onebuy_crawler.constants import DEFAULT_CATEGORY_ID, DEFAULT_CATEGORY_NAME, PLATFORMS
from onebuy_crawler.item_adapter import ItemAdapter
from onebuy_crawler.items import CleanProductItem
from onebuy_crawler.services.matcher import build_match_fingerprint
from onebuy_crawler.services.normalizer import (
    calculate_discount_rate,
    clean_text,
    decimal_to_float,
    normalize_image_url,
    normalize_title,
    normalize_url,
    parse_price,
    parse_rating,
    parse_sales,
)
from onebuy_crawler.services.sku import build_source_key


class CleaningPipeline:
    """Convert platform-specific raw fields into the shared OpenAPI contract."""

    def process_item(self, item):
        adapter = ItemAdapter(item)
        if adapter.get("parse_status") and adapter.get("parse_status") != "ok":
            return item

        platform_code = adapter.get("platform_code") or "other"
        platform = PLATFORMS.get(platform_code, PLATFORMS["other"])
        source_sku_id = clean_text(adapter.get("source_sku_id"))
        title = normalize_title(adapter.get("title"))
        price = parse_price(adapter.get("price_text") or adapter.get("price"))
        original_price = parse_price(adapter.get("original_price_text") or adapter.get("original_price"))
        specs = adapter.get("specs") or {}

        clean = CleanProductItem()
        if adapter.get("product_id"):
            clean["product_id"] = clean_text(adapter.get("product_id"))
        clean["source_key"] = build_source_key(platform_code, source_sku_id)
        clean["match_fingerprint"] = build_match_fingerprint(title, specs)
        clean["platform_code"] = platform_code
        clean["platform_id"] = platform["platform_id"]
        clean["platform_name"] = platform["platform_name"]
        clean["source_sku_id"] = source_sku_id
        clean["title"] = title
        clean["category_id"] = adapter.get("category_id") or DEFAULT_CATEGORY_ID
        clean["category_name"] = clean_text(adapter.get("category_text")) or DEFAULT_CATEGORY_NAME
        clean["image_url"] = normalize_image_url(adapter.get("image_url"), adapter.get("product_url") or "")
        clean["images"] = [clean["image_url"]] if clean["image_url"] else []
        clean["description"] = clean_text(adapter.get("description") or adapter.get("promo_info"))
        clean["specs"] = specs
        clean["price"] = decimal_to_float(price)
        clean["original_price"] = decimal_to_float(original_price)
        clean["discount_rate"] = calculate_discount_rate(price, original_price)
        clean["sales_volume"] = parse_sales(adapter.get("sales_text") or adapter.get("sales_volume"))
        clean["seller_name"] = clean_text(adapter.get("seller_name"))
        clean["seller_rating"] = parse_rating(adapter.get("seller_rating_text") or adapter.get("seller_rating"))
        clean["seller_id"] = clean_text(adapter.get("seller_id"))
        clean["product_url"] = normalize_url(adapter.get("product_url"))
        clean["in_stock"] = adapter.get("in_stock", True)
        clean["stock_quantity"] = adapter.get("stock_quantity")
        clean["promo_info"] = clean_text(adapter.get("promo_info"))
        clean["crawl_time"] = adapter.get("crawl_time") or datetime.now(timezone.utc).isoformat()
        return clean
