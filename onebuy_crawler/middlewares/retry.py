from __future__ import annotations

import logging

try:
    from scrapy.downloadermiddlewares.retry import RetryMiddleware
    from scrapy.utils.response import response_status_message
except Exception:  # pragma: no cover
    RetryMiddleware = object

    def response_status_message(status):
        return f"HTTP {status}"

from onebuy_crawler.constants import ANTI_BOT_MARKERS

logger = logging.getLogger(__name__)


class PoliteRetryMiddleware(RetryMiddleware):
    """Retry network failures, but let spiders record anti-bot blocks explicitly."""

    def process_response(self, request, response):
        body_text = ""
        try:
            body_text = response.text[:2000].lower()
        except Exception:
            pass

        if any(marker.lower() in body_text for marker in ANTI_BOT_MARKERS):
            logger.warning("anti_bot_detected url=%s", response.url)
            request.meta["failure_reason"] = "anti_bot_detected"
            return response
        return response
