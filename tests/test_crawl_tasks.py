from __future__ import annotations

import unittest
from unittest.mock import patch

from jobs.run_crawl_tasks import FINISH_RE, _should_stop_platform_batch
from onebuy_crawler.services.crawl_tasks import (
    CrawlTask,
    load_due_tasks,
    normalize_task_platform,
    reset_stale_running_tasks,
    task_platform_to_capture_platform,
)
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

    def test_finish_line_reason_stops_before_extra_fields(self):
        output = (
            "browser_capture finished: platform=jd, keyword=iPhone 15, items=0, "
            "reason=jd_browser_capture_no_items, dom_rows=12, jd_prices=12"
        )
        match = FINISH_RE.search(output)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), "jd_browser_capture_no_items")

    def test_schema_contains_crawl_tasks(self):
        schema = "\n".join(SCHEMA_SQL)
        self.assertIn("CREATE TABLE IF NOT EXISTS crawl_tasks", schema)
        self.assertIn("uk_task_keyword_platform", schema)
        self.assertIn("product_url TEXT", schema)
        self.assertIn("url TEXT", schema)

    def test_load_due_tasks_can_filter_keywords(self):
        fake_cursor = FakeCursor([])
        with patch("onebuy_crawler.services.crawl_tasks.mysql_connection", return_value=FakeConnection(fake_cursor)):
            load_due_tasks(None, 1, platform="jd", keywords=["华为 手机"])
        sql, params = fake_cursor.calls[0]
        self.assertIn("keyword IN (%s)", sql)
        self.assertIn("华为 手机", params)

    def test_reset_stale_running_tasks_filters_scope(self):
        fake_cursor = FakeCursor([], rowcount=2)
        with patch("onebuy_crawler.services.crawl_tasks.mysql_connection", return_value=FakeConnection(fake_cursor)):
            count = reset_stale_running_tasks(None, stale_minutes=10, platform="taobao", keywords=["蓝牙耳机"])
        sql, params = fake_cursor.calls[0]
        self.assertEqual(count, 2)
        self.assertIn("status = 'running'", sql)
        self.assertIn("stale_running_task", sql)
        self.assertIn("platform_code = %s", sql)
        self.assertIn("keyword IN (%s)", sql)
        self.assertEqual(params, [10, "taobao", "蓝牙耳机"])

    def test_jd_blocked_reason_stops_current_batch(self):
        task = CrawlTask(id=1, keyword="iPhone 15", platform_code="jingdong", status="running", retry_count=0)
        self.assertTrue(_should_stop_platform_batch(task, "jd_search_redirected_to_home"))
        self.assertTrue(_should_stop_platform_batch(task, "jd_access_too_frequent"))
        self.assertFalse(_should_stop_platform_batch(task, "capture_no_items"))

    def test_taobao_blocked_reason_does_not_stop_jd_batch(self):
        task = CrawlTask(id=2, keyword="蓝牙耳机", platform_code="taobao", status="running", retry_count=0)
        self.assertFalse(_should_stop_platform_batch(task, "taobao_captcha_or_security_check"))


class FakeCursor:
    def __init__(self, rows, rowcount=0):
        self.rows = rows
        self.calls = []
        self.rowcount = rowcount

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self._cursor


if __name__ == "__main__":
    unittest.main()
