from __future__ import annotations

import unittest

from jobs.query_products import _pagination


class QueryProductsTests(unittest.TestCase):
    def test_pagination_uses_limit_by_default(self):
        self.assertEqual(_pagination(limit=20, page=3), (20, 40))

    def test_page_size_overrides_limit(self):
        self.assertEqual(_pagination(limit=20, page=2, page_size=5), (5, 5))

    def test_pagination_clamps_invalid_values(self):
        self.assertEqual(_pagination(limit=0, page=0), (1, 0))


if __name__ == "__main__":
    unittest.main()
