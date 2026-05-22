from __future__ import annotations

import json
import unittest

from jobs.browser_capture_search import _merge_jd_prices
from onebuy_crawler.services.browser_extractors import extract_from_dom, extract_from_response, extract_jd_price_map


class BrowserExtractorTests(unittest.TestCase):
    def test_extract_taobao_jsonp(self):
        body = "mtopjsonp1(" + json.dumps(
            {
                "data": {
                    "auctions": [
                        {
                            "item_id": "123",
                            "title": "Apple iPhone 15",
                            "view_price": "4999.00",
                            "pic_url": "//img.alicdn.com/a.jpg",
                            "detail_url": "//item.taobao.com/item.htm?id=123",
                            "nick": "旗舰店",
                        }
                    ]
                }
            },
            ensure_ascii=False,
        ) + ")"
        result = extract_from_response("taobao", "https://h5api.m.taobao.com", body, "iPhone")
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["source_sku_id"], "123")
        self.assertEqual(result.items[0]["platform_code"], "taobao")

    def test_extract_jd_json(self):
        body = json.dumps(
            {
                "data": {
                    "goodsList": [
                        {
                            "skuId": 456,
                            "skuName": "Apple iPhone 15",
                            "price": "5099.00",
                            "shopName": "京东自营",
                        }
                    ]
                }
            },
            ensure_ascii=False,
        )
        result = extract_from_response("jd", "https://api.m.jd.com", body, "iPhone")
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["source_sku_id"], "456")
        self.assertEqual(result.items[0]["platform_code"], "jingdong")

    def test_extract_jd_price_map(self):
        body = json.dumps([{"id": "J_100012043978", "p": "4599.00", "m": "4999.00"}])
        prices = extract_jd_price_map(body)
        self.assertEqual(prices["100012043978"]["price"], "4599.00")
        self.assertEqual(prices["100012043978"]["original_price"], "4999.00")

    def test_merge_jd_dom_rows_with_async_price(self):
        rows = [{"skuId": "100012043978", "skuName": "Apple iPhone 15", "price": ""}]
        merged = _merge_jd_prices(rows, {"100012043978": {"price": "4599.00"}})
        items = extract_from_dom("jd", merged, "iPhone")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["price_text"], "4599.00")

    def test_extract_dom_rows(self):
        rows = [{"item_id": "789", "title": "iPhone 15", "price": "￥4888", "detail_url": "https://item.taobao.com/item.htm?id=789"}]
        items = extract_from_dom("taobao", rows, "iPhone")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["price_text"], "￥4888")


if __name__ == "__main__":
    unittest.main()
