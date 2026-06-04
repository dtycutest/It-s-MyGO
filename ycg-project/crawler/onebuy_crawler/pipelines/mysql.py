from __future__ import annotations

import json
from datetime import datetime

from onebuy_crawler.item_adapter import ItemAdapter
from onebuy_crawler.services.db import mysql_connection


class MySqlPipeline:
    """Persist cleaned items into products, platform_offers, and price_history."""

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.settings = settings

    def process_item(self, item):
        adapter = ItemAdapter(item)
        if adapter.get("parse_status") and adapter.get("parse_status") != "ok":
            self._insert_raw(adapter)
            return item

        if not adapter.get("product_id") or adapter.get("price") is None:
            return item

        with mysql_connection(self.settings) as conn:
            with conn.cursor() as cursor:
                self._upsert_product(cursor, adapter)
                self._upsert_offer(cursor, adapter)
                self._insert_price_history(cursor, adapter)
                self._refresh_product_price_summary(cursor, adapter["product_id"])
        return item

    def _insert_raw(self, adapter: ItemAdapter) -> None:
        with mysql_connection(self.settings) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO raw_crawl_records
                        (platform_code, source_sku_id, url, keyword_value, parse_status,
                         failure_reason, raw_payload, crawl_time)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        adapter.get("platform_code"),
                        adapter.get("source_sku_id"),
                        adapter.get("product_url"),
                        adapter.get("keyword"),
                        adapter.get("parse_status", "failed"),
                        adapter.get("failure_reason"),
                        json.dumps(adapter.get("raw_payload") or {}, ensure_ascii=False),
                        self._mysql_time(adapter.get("crawl_time")),
                    ),
                )

    def _upsert_product(self, cursor, adapter: ItemAdapter) -> None:
        cursor.execute(
            """
            INSERT INTO products
                (product_id, match_fingerprint, title, category_id, category_name, image_url,
                 images, description, specs, min_price, max_price, price_diff, best_platform)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s)
            ON DUPLICATE KEY UPDATE
                title=VALUES(title),
                category_id=VALUES(category_id),
                category_name=VALUES(category_name),
                image_url=COALESCE(VALUES(image_url), image_url),
                images=COALESCE(VALUES(images), images),
                description=COALESCE(VALUES(description), description),
                specs=COALESCE(VALUES(specs), specs),
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                adapter["product_id"],
                adapter["match_fingerprint"],
                adapter["title"],
                adapter.get("category_id", 0),
                adapter.get("category_name", "未分类"),
                adapter.get("image_url"),
                json.dumps(adapter.get("images") or [], ensure_ascii=False),
                adapter.get("description"),
                json.dumps(adapter.get("specs") or {}, ensure_ascii=False),
                adapter["price"],
                adapter["price"],
                adapter.get("platform_name"),
            ),
        )

    def _upsert_offer(self, cursor, adapter: ItemAdapter) -> None:
        cursor.execute(
            """
            INSERT INTO platform_offers
                (product_id, platform_id, platform_name, platform_code, source_sku_id,
                 price, original_price, discount_rate, sales_volume, seller_name,
                 seller_rating, seller_id, product_url, in_stock, stock_quantity, update_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                product_id=VALUES(product_id),
                price=VALUES(price),
                original_price=VALUES(original_price),
                discount_rate=VALUES(discount_rate),
                sales_volume=VALUES(sales_volume),
                seller_name=VALUES(seller_name),
                seller_rating=VALUES(seller_rating),
                seller_id=VALUES(seller_id),
                product_url=VALUES(product_url),
                in_stock=VALUES(in_stock),
                stock_quantity=VALUES(stock_quantity),
                update_at=VALUES(update_at)
            """,
            (
                adapter["product_id"],
                adapter["platform_id"],
                adapter["platform_name"],
                adapter["platform_code"],
                adapter["source_sku_id"],
                adapter["price"],
                adapter.get("original_price"),
                adapter.get("discount_rate"),
                adapter.get("sales_volume"),
                adapter.get("seller_name"),
                adapter.get("seller_rating"),
                adapter.get("seller_id"),
                adapter.get("product_url"),
                1 if adapter.get("in_stock", True) else 0,
                adapter.get("stock_quantity"),
                self._mysql_time(adapter.get("crawl_time")),
            ),
        )

    def _insert_price_history(self, cursor, adapter: ItemAdapter) -> None:
        cursor.execute(
            """
            INSERT INTO price_history (product_id, platform_code, price, promo_info, crawl_time)
            VALUES (%s,%s,%s,%s,%s)
            """,
            (
                adapter["product_id"],
                adapter["platform_code"],
                adapter["price"],
                adapter.get("promo_info"),
                self._mysql_time(adapter.get("crawl_time")),
            ),
        )

    def _refresh_product_price_summary(self, cursor, product_id: str) -> None:
        cursor.execute(
            """
            UPDATE products p
            JOIN (
                SELECT
                    product_id,
                    MIN(price) AS min_price,
                    MAX(price) AS max_price,
                    SUBSTRING_INDEX(
                        GROUP_CONCAT(platform_name ORDER BY price ASC, update_at DESC),
                        ',', 1
                    ) AS best_platform
                FROM platform_offers
                WHERE product_id = %s
                GROUP BY product_id
            ) s ON p.product_id = s.product_id
            SET p.min_price = s.min_price,
                p.max_price = s.max_price,
                p.price_diff = s.max_price - s.min_price,
                p.best_platform = s.best_platform,
                p.updated_at = CURRENT_TIMESTAMP
            """,
            (product_id,),
        )

    @staticmethod
    def _mysql_time(value):
        if not value:
            return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value).replace("T", " ").replace("Z", "").split("+")[0]
