from __future__ import annotations

import unittest

from scrapy.spiderloader import SpiderLoader
from scrapy.utils.project import get_project_settings


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


if __name__ == "__main__":
    unittest.main()
