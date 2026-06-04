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

    def test_extract_taobao_modern_nested_json_string(self):
        body = json.dumps(
            {
                "data": {
                    "payload": json.dumps(
                        {
                            "auctions": [
                                {
                                    "auctionId": "456",
                                    "rawTitle": "Sony 蓝牙耳机 真无线降噪",
                                    "priceShow": {"price": "399.00"},
                                    "clickUrl": "//item.taobao.com/item.htm?id=456",
                                    "sellerNick": "数码旗舰店",
                                }
                            ]
                        },
                        ensure_ascii=False,
                    )
                }
            },
            ensure_ascii=False,
        )
        result = extract_from_response("taobao", "https://h5api.m.taobao.com", body, "蓝牙耳机")
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["source_sku_id"], "456")
        self.assertEqual(result.items[0]["price_text"], "399.00")

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

    def test_extract_jd_image_url(self):
        body = json.dumps(
            {
                "data": {
                    "goodsList": [
                        {
                            "skuId": 456,
                            "skuName": "Apple iPhone 15 128GB",
                            "price": "5099.00",
                            "imageUrl": "jfs/t1/1/2/3/demo.jpg",
                        }
                    ]
                }
            },
            ensure_ascii=False,
        )
        result = extract_from_response("jd", "https://api.m.jd.com", body, "iPhone 15 128GB")
        self.assertEqual(result.items[0]["image_url"], "https://img10.360buyimg.com/n7/jfs/t1/1/2/3/demo.jpg")

    def test_specific_jd_keyword_filters_capacity(self):
        rows = [
            {"skuId": "1", "skuName": "Apple iPhone 15 128G 蓝色", "price": "4999"},
            {"skuId": "2", "skuName": "Apple iPhone 15 256GB 蓝色", "price": "5999"},
        ]
        items = extract_from_dom("jd", rows, "iPhone 15 128GB")
        self.assertEqual([item["source_sku_id"] for item in items], ["1"])

    def test_jd_keyword_filters_category_mismatch(self):
        rows = [
            {"skuId": "1", "skuName": "Apple iPhone 15 128G 蓝色 手机", "price": "4999"},
            {"skuId": "2", "skuName": "适用苹果iPhone15-17的充电宝 10000毫安", "price": "149"},
        ]
        items = extract_from_dom("jd", rows, "iPhone 15")
        self.assertEqual([item["source_sku_id"] for item in items], ["1"])

    def test_extract_jd_price_map(self):
        body = json.dumps([{"id": "J_100012043978", "p": "4599.00", "m": "4999.00"}])
        prices = extract_jd_price_map(body)
        self.assertEqual(prices["100012043978"]["price"], "4599.00")
        self.assertEqual(prices["100012043978"]["original_price"], "4999.00")

    def test_extract_jd_mobile_recommend_payload(self):
        body = json.dumps(
            {
                "data": {
                    "feeds": {
                        "content": [
                            {
                                "id": "100257997038",
                                "name": "唯怡 坚果奶饮料",
                                "price": "5.90",
                                "link": "https://item.m.jd.com/product/100257997038.html?cover=jfs/t1/demo.jpg",
                            }
                        ]
                    }
                }
            },
            ensure_ascii=False,
        )
        result = extract_from_response("jd", "https://api.m.jd.com/api?functionId=recommend_like_m", body, "")
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0]["source_sku_id"], "100257997038")
        self.assertEqual(result.items[0]["image_url"], "https://img10.360buyimg.com/n7/jfs/t1/demo.jpg")

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

    def test_taobao_keyword_matches_chinese_apple_title(self):
        rows = [
            {
                "item_id": "890",
                "title": "苹果 iPhone15 128G 国行正品手机",
                "price": "￥4699",
                "detail_url": "https://item.taobao.com/item.htm?id=890",
            }
        ]
        items = extract_from_dom("taobao", rows, "Apple iPhone 15 128GB")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["source_sku_id"], "890")

    def test_jd_keyword_matches_common_brand_aliases(self):
        rows = [
            {"skuId": "1", "skuName": "罗技 K380 多设备蓝牙键盘", "price": "109"},
            {"skuId": "2", "skuName": "华为 FreeBuds Pro 3 蓝牙耳机", "price": "699"},
            {"skuId": "3", "skuName": "小米 自带线充电宝 10000mAh 22.5W", "price": "99"},
        ]
        self.assertEqual(len(extract_from_dom("jd", rows[:1], "Logitech K380 蓝牙键盘")), 1)
        self.assertEqual(len(extract_from_dom("jd", rows[1:2], "HUAWEI FreeBuds Pro 3")), 1)
        self.assertEqual(len(extract_from_dom("jd", rows[2:], "Xiaomi 自带线充电宝 10000mAh 22.5W")), 1)

    def test_jd_keyword_matches_power_bank_title_variants(self):
        rows = [
            {
                "skuId": "1",
                "skuName": "小米（MI）小米充电宝移动电源 10000 自带线双向快充口袋版 浅咖色",
                "price": "88",
            },
            {
                "skuId": "2",
                "skuName": "小米自带线充电宝10000mAh 口袋版 Type-C双向快充 22.5W大功率",
                "price": "78",
            },
            {
                "skuId": "3",
                "skuName": "小米（MI）自带线充电宝 灰蓝色 10000毫安 22.5w",
                "price": "70",
            },
        ]
        items = extract_from_dom("jd", rows, "小米自带线充电宝 10000mAh 22.5W")
        self.assertEqual([item["source_sku_id"] for item in items], ["2", "3"])


if __name__ == "__main__":
    unittest.main()
