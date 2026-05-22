from __future__ import annotations

import unittest
from datetime import datetime, timezone

from onebuy_crawler.services.matcher import (
    build_match_fingerprint,
    extract_match_tokens,
    extract_product_signature,
    likely_same_product,
)
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

    def test_cross_platform_aliases_match(self):
        jd = {"title": "HUAWEI 华为 FreeBuds Pro 3 蓝牙耳机 星河蓝 官方旗舰店"}
        tb = {"title": "华为FreeBuds Pro3 真无线降噪蓝牙耳机 星河蓝"}
        self.assertTrue(likely_same_product(jd, tb))

    def test_accessory_does_not_merge_with_phone(self):
        phone = {"title": "Apple iPhone 15 128GB 蓝色 5G 手机"}
        case = {"title": "适用 Apple iPhone 15 蓝色 液态硅胶手机壳"}
        self.assertFalse(likely_same_product(phone, case))

    def test_edition_does_not_merge(self):
        standard = {"title": "REDMI K80 红米k80 手机 官方旗舰店"}
        extreme = {"title": "REDMI K80 至尊版 手机 红米k80至尊 游戏手机"}
        self.assertFalse(likely_same_product(standard, extreme))

    def test_phone_without_capacity_is_conservative(self):
        official = {"title": "Apple/苹果 iPhone 15 Plus 原封全新正品手机"}
        live = {"title": "Apple/苹果 iPhone 15 Plus 苹果15 plus 直播间专享手机"}
        self.assertFalse(likely_same_product(official, live))

    def test_keyboard_variant_tokens(self):
        title = "罗技 Logitech K380 蓝牙键盘 女生办公 便携无线键盘"
        signature = extract_product_signature(title)
        self.assertEqual(signature["brand"], "logitech")
        self.assertIn("k380", signature["model_tokens"])
        self.assertEqual(signature["product_type"], "keyboard")

    def test_generic_tokens_do_not_merge_unrelated_products(self):
        humidifier = {"title": "小熊（Bear）加湿器 卧室轻音大容量 空调伴侣JSQ-C45U1 4.5L"}
        stationery = {"title": "得力桌面文件收纳盒 办公用品 加厚资料架"}
        self.assertFalse(likely_same_product(humidifier, stationery))

    def test_phone_capacity_and_color_stay_in_fingerprint(self):
        black = build_match_fingerprint("Apple iPhone 15 128GB 黑色 5G 手机")
        blue = build_match_fingerprint("Apple iPhone 15 128GB 蓝色 5G 手机")
        self.assertNotEqual(black, blue)
        self.assertNotIn("5g", extract_match_tokens("Apple iPhone 15 128GB 黑色 5G 手机"))
        self.assertIn("spec:128gb", extract_match_tokens("Apple iPhone 15 128GB 黑色 5G 手机"))

    def test_used_and_new_conditions_do_not_merge(self):
        used = {"title": "Apple iPhone 15 Pro 256GB 原色钛金属 99新 二手机"}
        new = {"title": "苹果 Apple iPhone 15 Pro 256GB 原色钛金属 全新未激活"}
        self.assertFalse(likely_same_product(used, new))
        self.assertIn("condition:used", extract_match_tokens(used["title"]))
        self.assertIn("condition:new", extract_match_tokens(new["title"]))


if __name__ == "__main__":
    unittest.main()
