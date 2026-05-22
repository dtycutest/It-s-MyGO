from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jobs.crawl_product_urls import collect_urls, detect_platform, extract_source_sku_id


class CrawlProductUrlsTests(unittest.TestCase):
    def test_detect_platform(self):
        self.assertEqual(detect_platform("https://item.jd.com/100144527620.html"), "jd")
        self.assertEqual(detect_platform("https://item.taobao.com/item.htm?id=123"), "taobao")
        self.assertEqual(detect_platform("https://detail.tmall.com/item.htm?id=456"), "taobao")

    def test_extract_source_sku_id(self):
        self.assertEqual(extract_source_sku_id("https://item.jd.com/100144527620.html", "jd"), "100144527620")
        self.assertEqual(extract_source_sku_id("https://item.taobao.com/item.htm?id=123&spm=a", "taobao"), "123")

    def test_collect_urls_from_args_and_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "urls.txt"
            path.write_text("https://item.jd.com/1.html\n# comment\nhttps://item.jd.com/2.html\n", encoding="utf-8")
            urls = collect_urls(["https://item.jd.com/1.html"], str(path))
        self.assertEqual(urls, ["https://item.jd.com/1.html", "https://item.jd.com/2.html"])

    def test_missing_url_file_creates_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "urls.txt"
            with self.assertRaises(SystemExit):
                collect_urls([], str(path))
            self.assertTrue(path.exists())
            self.assertIn("https://item.jd.com", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
