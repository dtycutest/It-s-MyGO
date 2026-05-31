from __future__ import annotations

import unittest
from unittest.mock import patch

from jobs import rebuild_categories


class RebuildCategoriesTests(unittest.TestCase):
    def test_rebuild_categories_updates_generic_rows(self):
        cursor = FakeCursor(
            [
                ("SKU1", "Apple iPhone 15 128GB 手机", "未分类"),
                ("SKU2", "已有分类商品", "手机-智能手机"),
            ]
        )
        with patch("jobs.rebuild_categories.get_project_settings", return_value=None), patch(
            "jobs.rebuild_categories.mysql_connection", return_value=FakeConnection(cursor)
        ), patch("sys.argv", ["rebuild_categories", "--apply"]):
            rebuild_categories.main()
        update_calls = [call for call in cursor.calls if call[0].lstrip().upper().startswith("UPDATE")]
        self.assertEqual(len(update_calls), 1)
        self.assertEqual(update_calls[0][1], (100, "手机-智能手机", "SKU1"))

    def test_rebuild_categories_updates_new_stable_demo_rows(self):
        cursor = FakeCursor([("SKU1", "可口可乐 330ml 24罐 整箱", "未分类")])
        with patch("jobs.rebuild_categories.get_project_settings", return_value=None), patch(
            "jobs.rebuild_categories.mysql_connection", return_value=FakeConnection(cursor)
        ), patch("sys.argv", ["rebuild_categories", "--apply"]):
            rebuild_categories.main()
        update_calls = [call for call in cursor.calls if call[0].lstrip().upper().startswith("UPDATE")]
        self.assertEqual(update_calls[0][1], (700, "食品饮料-碳酸饮料", "SKU1"))

    def test_force_rebuild_ignores_existing_category(self):
        cursor = FakeCursor([("SKU1", "罗技 K380 蓝牙键盘", "旧分类")])
        with patch("jobs.rebuild_categories.get_project_settings", return_value=None), patch(
            "jobs.rebuild_categories.mysql_connection", return_value=FakeConnection(cursor)
        ), patch("sys.argv", ["rebuild_categories", "--apply", "--force"]):
            rebuild_categories.main()
        update_calls = [call for call in cursor.calls if call[0].lstrip().upper().startswith("UPDATE")]
        self.assertEqual(update_calls[0][1], (210, "电脑办公-键盘鼠标", "SKU1"))


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
