from __future__ import annotations

import logging

try:
    from scrapy.exceptions import IgnoreRequest
except Exception:  # pragma: no cover
    IgnoreRequest = Exception

from onebuy_crawler.constants import ANTI_BOT_MARKERS
from onebuy_crawler.services.proxy_pool import ProxyPool, load_proxies_from_settings


logger = logging.getLogger(__name__)
BAD_PROXY_STATUS = {403, 407, 408, 429, 500, 502, 503, 504, 522, 524}


class ProxyMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            load_proxies_from_settings(crawler.settings),
            max_fails=crawler.settings.getint("CRAWLER_PROXY_MAX_FAILS", 3),
            cooldown_seconds=crawler.settings.getint("CRAWLER_PROXY_COOLDOWN_SECONDS", 300),
            proxy_required=crawler.settings.getbool("CRAWLER_PROXY_REQUIRED", False),
        )

    def __init__(
        self,
        proxies: list[str],
        max_fails: int = 3,
        cooldown_seconds: int = 300,
        proxy_required: bool = False,
    ):
        self.pool = ProxyPool(proxies, max_fails=max_fails, cooldown_seconds=cooldown_seconds)
        self.proxy_required = proxy_required

    def process_request(self, request):
        if self.pool.enabled and "proxy" not in request.meta:
            proxy = self.pool.choose()
            if proxy:
                request.meta["proxy"] = proxy
                request.meta["_proxy_url"] = proxy
                logger.debug("proxy_assigned proxy=%s url=%s", proxy, request.url)
            elif self.proxy_required:
                raise IgnoreRequest("proxy_pool_exhausted")
        return None

    def process_response(self, request, response):
        proxy = request.meta.get("_proxy_url") or request.meta.get("proxy")
        if proxy and self._is_bad_response(response):
            self.pool.report_failure(proxy)
            logger.warning("proxy_response_failed proxy=%s status=%s url=%s", proxy, response.status, response.url)
        elif proxy:
            self.pool.report_success(proxy)
        return response

    def process_exception(self, request, exception, spider):
        proxy = request.meta.get("_proxy_url") or request.meta.get("proxy")
        if proxy:
            self.pool.report_failure(proxy)
            logger.warning("proxy_exception proxy=%s error=%s url=%s", proxy, exception, request.url)
        return None

    @staticmethod
    def _is_bad_response(response) -> bool:
        if getattr(response, "status", 200) in BAD_PROXY_STATUS:
            return True
        try:
            body_text = response.text[:2000].lower()
        except Exception:
            return False
        return any(marker.lower() in body_text for marker in ANTI_BOT_MARKERS)
