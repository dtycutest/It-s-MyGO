from __future__ import annotations

import unittest

from onebuy_crawler.pipelines.mysql import MySqlPipeline


class FakeCursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


class MysqlPipelineSqlTests(unittest.TestCase):
    def test_refresh_product_summary_sql_targets_product_id(self):
        pipeline = MySqlPipeline(settings=None)
        cursor = FakeCursor()
        pipeline._refresh_product_price_summary(cursor, "SKU20260517001")
        self.assertEqual(cursor.calls[0][1], ("SKU20260517001",))
        self.assertIn("MIN(price)", cursor.calls[0][0])
        self.assertIn("best_platform", cursor.calls[0][0])


if __name__ == "__main__":
    unittest.main()
