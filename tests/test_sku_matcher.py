from __future__ import annotations

import unittest
from datetime import datetime, timezone

from onebuy_crawler.services.matcher import build_match_fingerprint, extract_match_tokens, likely_same_product
from onebuy_crawler.services.sku import build_source_key, generate_product_id


class SkuMatcherTests(unittest.TestCase):
    def test_product_id_shape_is_stable(self):
        now = datetime(2026, 5, 17, tzinfo=timezone.utc)
        left = generate_product_id("match:iphone15-256", now)
        right = generate_product_id("match:iphone15-256", now)
        self.assertEqual(left, right)
        self.assertRegex(left, r"^SKU20260517\d{3}$")

    def test_source_key(self):
        self.assertEqual(build_source_key("JingDong", " 123 "), "jingdong:123")

    def test_match_fingerprint(self):
        jd = {"title": "Apple iPhone 15 Pro Max 256GB 深空黑 官方旗舰店"}
        tb = {"title": "苹果 Apple iPhone 15 Pro Max 256GB 深空黑 正品包邮"}
        self.assertTrue(likely_same_product(jd, tb))
        self.assertEqual(build_match_fingerprint(jd["title"]), build_match_fingerprint(tb["title"]))

    def test_generic_tokens_do_not_merge_unrelated_products(self):
        humidifier = {"title": "小熊（Bear）加湿器 卧室轻音大容量 空调伴侣JSQ-C45U1 4.5L"}
        stationery = {"title": "得力桌面文件收纳盒 办公用品 加厚资料架"}
        self.assertFalse(likely_same_product(humidifier, stationery))

    def test_phone_capacity_and_color_stay_in_fingerprint(self):
        black = build_match_fingerprint("Apple iPhone 15 128GB 黑色 5G 手机")
        blue = build_match_fingerprint("Apple iPhone 15 128GB 蓝色 5G 手机")
        self.assertNotEqual(black, blue)
        self.assertNotIn("5g", extract_match_tokens("Apple iPhone 15 128GB 黑色 5G 手机"))


if __name__ == "__main__":
    unittest.main()
