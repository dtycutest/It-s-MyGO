from __future__ import annotations

import unittest
from decimal import Decimal

from onebuy_crawler.services.normalizer import (
    calculate_discount_rate,
    normalize_title,
    normalize_url,
    parse_price,
    parse_rating,
    parse_sales,
)


class NormalizerTests(unittest.TestCase):
    def test_parse_price(self):
        self.assertEqual(parse_price("￥6,699.00"), Decimal("6699.00"))
        self.assertIsNone(parse_price("暂无报价"))

    def test_parse_sales(self):
        self.assertEqual(parse_sales("2.5万+人付款"), 25000)
        self.assertEqual(parse_sales("900+评价"), 900)

    def test_rating_is_clamped(self):
        self.assertEqual(parse_rating("4.8分"), 4.8)
        self.assertEqual(parse_rating("9.9"), 5.0)

    def test_title_and_url(self):
        self.assertEqual(normalize_title(" Apple\u200b   iPhone 15 "), "Apple iPhone 15")
        self.assertEqual(normalize_url("//item.jd.com/1.html"), "https://item.jd.com/1.html")

    def test_discount(self):
        self.assertEqual(calculate_discount_rate(Decimal("75"), Decimal("100")), 25)


if __name__ == "__main__":
    unittest.main()
