from __future__ import annotations

import unittest

from jobs.run_crawl_tasks import FINISH_RE
from onebuy_crawler.services.crawl_tasks import normalize_task_platform, task_platform_to_capture_platform
from onebuy_crawler.services.db import SCHEMA_SQL


class CrawlTaskTests(unittest.TestCase):
    def test_platform_aliases(self):
        self.assertEqual(normalize_task_platform("jd"), "jingdong")
        self.assertEqual(normalize_task_platform("jingdong"), "jingdong")
        self.assertEqual(normalize_task_platform("taobao"), "taobao")
        self.assertEqual(task_platform_to_capture_platform("jingdong"), "jd")

    def test_finish_line_parses_items_and_reason(self):
        output = "browser_capture finished: platform=jd, keyword=iPhone 15, items=0, reason=jd_access_too_frequent"
        match = FINISH_RE.search(output)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "0")
        self.assertEqual(match.group(2), "jd_access_too_frequent")

    def test_schema_contains_crawl_tasks(self):
        schema = "\n".join(SCHEMA_SQL)
        self.assertIn("CREATE TABLE IF NOT EXISTS crawl_tasks", schema)
        self.assertIn("uk_task_keyword_platform", schema)


if __name__ == "__main__":
    unittest.main()
