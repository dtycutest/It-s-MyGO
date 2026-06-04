from __future__ import annotations

import hashlib
from datetime import datetime, timezone


def generate_product_id(seed: str, now: datetime | None = None) -> str:
    """Generate OpenAPI-compatible SKUyyyyMMddNNN style IDs.

    The final three digits are deterministic for the same normalized seed on
    the same date. Database uniqueness is still enforced by `product_id`.
    """

    if now is None:
        now = datetime.now(timezone.utc)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    suffix = int(digest[:8], 16) % 1000
    return f"SKU{now.strftime('%Y%m%d')}{suffix:03d}"


def build_source_key(platform_code: str, source_sku_id: str) -> str:
    return f"{platform_code.strip()}:{source_sku_id.strip()}".lower()
