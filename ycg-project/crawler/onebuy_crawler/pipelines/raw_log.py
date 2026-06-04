from __future__ import annotations

import json
import logging

from onebuy_crawler.item_adapter import ItemAdapter
logger = logging.getLogger(__name__)


class RawLogPipeline:
    """Emit failed parse records to the crawler log for later triage."""

    def process_item(self, item):
        adapter = ItemAdapter(item)
        status = adapter.get("parse_status")
        if status and status != "ok":
            logger.warning(
                "crawl_record_failed platform=%s status=%s reason=%s payload=%s",
                adapter.get("platform_code"),
                status,
                adapter.get("failure_reason"),
                json.dumps(dict(adapter), ensure_ascii=False, default=str)[:500],
            )
        return item
