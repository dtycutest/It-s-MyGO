from __future__ import annotations

import unittest
from unittest.mock import patch

from jobs.query_products import _pagination, query_products
from onebuy_crawler.services.search_query import title_keyword_clause


class QueryProductsTests(unittest.TestCase):
    def test_pagination_uses_limit_by_default(self):
        self.assertEqual(_pagination(limit=20, page=3), (20, 40))

    def test_page_size_overrides_limit(self):
        self.assertEqual(_pagination(limit=20, page=2, page_size=5), (5, 5))

    def test_pagination_clamps_invalid_values(self):
        self.assertEqual(_pagination(limit=0, page=0), (1, 0))

    def test_query_products_can_filter_platform(self):
        fake_cursor = FakeCursor([])
        with patch("jobs.query_products.mysql_connection", return_value=FakeConnection(fake_cursor)):
            query_products(None, "iPhone 15", 10, platform="jd")
        sql, params = fake_cursor.calls[0]
        self.assertIn("o.platform_code = %s", sql)
        self.assertIn("jingdong", params)
        self.assertIn("p.category_name = %s", sql)
        self.assertIn("手机-智能手机", params)

    def test_title_keyword_clause_expands_capacity_units(self):
        sql, params = title_keyword_clause("iPhone 15 128GB")
        self.assertIn("OR", sql)
        self.assertIn("%128GB%", params)
        self.assertIn("%128G%", params)

    def test_title_keyword_clause_expands_brand_aliases(self):
        sql, params = title_keyword_clause("Logitech K380 蓝牙键盘")
        self.assertIn("OR", sql)
        self.assertIn("%Logitech%", params)
        self.assertIn("%罗技%", params)


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

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
