from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scrapy.http import Request, TextResponse
from scrapy.settings import Settings

from onebuy_crawler.middlewares.proxy import ProxyMiddleware
from onebuy_crawler.services.proxy_pool import ProxyPool, load_proxies_from_settings, playwright_proxy_config


class ProxyPoolTests(unittest.TestCase):
    def test_loads_proxy_list_and_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            proxy_file = Path(tmp) / "proxies.txt"
            proxy_file.write_text("# comment\n2.2.2.2:8000\nhttp://3.3.3.3:9000\n", encoding="utf-8")
            settings = Settings(
                {
                    "CRAWLER_PROXY_LIST": "1.1.1.1:7000,http://2.2.2.2:8000",
                    "CRAWLER_PROXY_FILE": str(proxy_file),
                }
            )
            self.assertEqual(
                load_proxies_from_settings(settings),
                ["http://1.1.1.1:7000", "http://2.2.2.2:8000", "http://3.3.3.3:9000"],
            )

    def test_marks_proxy_as_cooling_after_failures(self):
        pool = ProxyPool(["1.1.1.1:7000"], max_fails=2, cooldown_seconds=60)
        proxy = pool.choose()
        self.assertEqual(proxy, "http://1.1.1.1:7000")
        pool.report_failure(proxy)
        self.assertEqual(pool.choose(), "http://1.1.1.1:7000")
        pool.report_failure(proxy)
        self.assertIsNone(pool.choose())

    def test_playwright_proxy_config(self):
        self.assertEqual(
            playwright_proxy_config("http://user:pass@127.0.0.1:8888"),
            {"server": "http://127.0.0.1:8888", "username": "user", "password": "pass"},
        )

    def test_middleware_assigns_and_scores_proxy(self):
        middleware = ProxyMiddleware(["1.1.1.1:7000"], max_fails=1, cooldown_seconds=60)
        request = Request("https://example.com")
        middleware.process_request(request)
        self.assertEqual(request.meta["proxy"], "http://1.1.1.1:7000")

        response = TextResponse("https://example.com", status=429, request=request)
        middleware.process_response(request, response)

        next_request = Request("https://example.com/next")
        middleware.process_request(next_request)
        self.assertNotIn("proxy", next_request.meta)


if __name__ == "__main__":
    unittest.main()
