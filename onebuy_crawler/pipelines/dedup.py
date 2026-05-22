from __future__ import annotations

from onebuy_crawler.item_adapter import ItemAdapter
from onebuy_crawler.services.sku import generate_product_id


class DedupPipeline:
    """Assign stable product IDs for source SKUs and cross-platform matches."""

    def __init__(self):
        self.source_to_product: dict[str, str] = {}
        self.fingerprint_to_product: dict[str, str] = {}

    def process_item(self, item):
        adapter = ItemAdapter(item)
        source_key = adapter.get("source_key")
        fingerprint = adapter.get("match_fingerprint")
        if not source_key or not fingerprint:
            return item

        product_id = adapter.get("product_id") or self.source_to_product.get(source_key) or self.fingerprint_to_product.get(fingerprint)
        if not product_id:
            product_id = generate_product_id(fingerprint)
        self.source_to_product[source_key] = product_id
        self.fingerprint_to_product[fingerprint] = product_id
        adapter["product_id"] = product_id
        return item
