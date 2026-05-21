from __future__ import annotations

import json
import unittest

from onebuy_crawler.services.browser_extractors import extract_from_dom, extract_from_response


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

    def test_extract_dom_rows(self):
        rows = [{"item_id": "789", "title": "iPhone 15", "price": "￥4888", "detail_url": "https://item.taobao.com/item.htm?id=789"}]
        items = extract_from_dom("taobao", rows, "iPhone")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["price_text"], "￥4888")


if __name__ == "__main__":
    unittest.main()
