from __future__ import annotations

import unittest

from scrapy import Selector
from scrapy.spiderloader import SpiderLoader
from scrapy.utils.project import get_project_settings

from onebuy_crawler.spiders.base import BaseProductSpider


class ScrapyProjectTests(unittest.TestCase):
    def test_expected_spiders_are_registered(self):
        settings = get_project_settings()
        loader = SpiderLoader.from_settings(settings)

        self.assertEqual(
            {"jd_detail", "jd_search", "taobao_detail", "taobao_search"},
            set(loader.list()),
        )

    def test_core_pipelines_are_enabled(self):
        settings = get_project_settings()
        pipelines = settings.getdict("ITEM_PIPELINES")

        self.assertIn("onebuy_crawler.pipelines.cleaning.CleaningPipeline", pipelines)
        self.assertIn("onebuy_crawler.pipelines.dedup.DedupPipeline", pipelines)
        self.assertIn("onebuy_crawler.pipelines.raw_log.RawLogPipeline", pipelines)

    def test_first_text_skips_empty_text_nodes(self):
        selector = Selector(text="<div class='sku-name'>\n <img/> 京东商品标题 </div><title>兜底标题</title>")

        self.assertEqual(BaseProductSpider.first_text(selector, ".sku-name::text", "title::text"), "京东商品标题")


if __name__ == "__main__":
    unittest.main()
