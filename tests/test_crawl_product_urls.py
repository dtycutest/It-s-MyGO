from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jobs.crawl_product_urls import collect_urls, detect_platform, extract_source_sku_id
from onebuy_crawler.services.product_urls import extract_product_urls


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
            path.write_text("https://item.jd.com/100001.html\n# comment\nhttps://item.jd.com/100002.html\n", encoding="utf-8")
            urls = collect_urls(["https://item.jd.com/100001.html"], str(path))
        self.assertEqual(urls, ["https://item.jd.com/100001.html", "https://item.jd.com/100002.html"])

    def test_extract_urls_from_copied_jd_html(self):
        text = '<a href="//item.jd.com/100144527620.html">iPhone</a> <a href="https://item.m.jd.com/product/100012043978.html?x=1">mobile</a>'
        self.assertEqual(
            extract_product_urls(text, platform="jd"),
            ["https://item.jd.com/100144527620.html", "https://item.jd.com/100012043978.html"],
        )

    def test_collect_urls_extracts_from_pasted_html_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "urls.txt"
            path.write_text('<a href="//item.jd.com/100144527620.html">iPhone</a>', encoding="utf-8")
            urls = collect_urls([], str(path))
        self.assertEqual(urls, ["https://item.jd.com/100144527620.html"])

    def test_extract_urls_from_jd_sku_attributes(self):
        text = '<li class="gl-item" data-sku="100144527620"></li>{"skuId":"100012043978"}'
        self.assertEqual(
            extract_product_urls(text, platform="jd"),
            ["https://item.jd.com/100144527620.html", "https://item.jd.com/100012043978.html"],
        )

    def test_missing_url_file_creates_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "urls.txt"
            with self.assertRaises(SystemExit):
                collect_urls([], str(path))
            self.assertTrue(path.exists())
            self.assertIn("https://item.jd.com", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
