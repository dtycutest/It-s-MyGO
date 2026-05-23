from __future__ import annotations

import unittest

from onebuy_crawler.pipelines.cleaning import CleaningPipeline
from onebuy_crawler.services.categories import infer_category


class CategoryTests(unittest.TestCase):
    def test_infer_phone_accessory_before_phone(self):
        category = infer_category("适用 Apple iPhone 15 蓝色 液态硅胶手机壳")
        self.assertEqual(category.category_name, "手机-配件")

    def test_infer_common_categories(self):
        self.assertEqual(infer_category("Apple iPhone 15 128GB 手机").category_name, "手机-智能手机")
        self.assertEqual(infer_category("Sony 蓝牙耳机 真无线降噪").category_name, "数码配件-耳机音频")
        self.assertEqual(infer_category("罗技 K380 蓝牙键盘").category_name, "电脑办公-键盘鼠标")
        self.assertEqual(infer_category("20000毫安 充电宝").category_name, "数码配件-移动电源")

    def test_title_category_beats_noisy_search_keyword(self):
        category = infer_category("Apple iPhone 15 128GB 蓝色 6.1英寸 手机", keyword="显示器")
        self.assertEqual(category.category_name, "手机-智能手机")

    def test_cleaning_pipeline_infers_category_when_generic(self):
        item = {
            "platform_code": "jingdong",
            "source_sku_id": "10001",
            "title": "Apple iPhone 15 128GB 蓝色 手机",
            "price_text": "4999",
            "category_text": "京东商品",
            "product_url": "https://item.jd.com/10001.html",
        }
        cleaned = CleaningPipeline().process_item(item)
        self.assertEqual(cleaned["category_name"], "手机-智能手机")
        self.assertEqual(cleaned["category_id"], 100)


if __name__ == "__main__":
    unittest.main()
