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

    def test_infer_stable_demo_categories(self):
        cases = [
            ("余华 活着 ISBN 9787530215593", 600, "图书文具-图书"),
            ("维达 V2239 抽纸 3层130抽24包", 400, "生活日用-纸品"),
            ("蓝月亮 深层洁净护理洗衣液 3kg", 410, "生活日用-衣物清洁"),
            ("云南白药 益优冰柠牙膏 145g", 500, "个护清洁-口腔护理"),
            ("海飞丝 怡神冰凉去屑洗发水 750ml", 510, "个护清洁-洗护沐浴"),
            ("多芬 深层营润沐浴露 720g", 510, "个护清洁-洗护沐浴"),
            ("南孚 5号电池 聚能环4代 40粒", 420, "生活日用-家用电池"),
            ("晨光 K35 中性笔 0.5mm 黑色 12支", 610, "图书文具-书写工具"),
            ("可口可乐 330ml 24罐 整箱", 700, "食品饮料-碳酸饮料"),
            ("雀巢咖啡 1+2 原味 15g 100条", 710, "食品饮料-咖啡冲饮"),
        ]
        for title, expected_id, expected_name in cases:
            with self.subTest(title=title):
                category = infer_category(title)
                self.assertEqual(category.category_id, expected_id)
                self.assertEqual(category.category_name, expected_name)

    def test_battery_use_case_words_do_not_override_battery_category(self):
        category = infer_category("南孚电池聚能环5代5号7号碱性干电池 玩具遥控器鼠标电池")
        self.assertEqual(category.category_id, 420)
        self.assertEqual(category.category_name, "生活日用-家用电池")

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

    def test_cleaning_pipeline_infers_taobao_lifestyle_category_when_generic(self):
        item = {
            "platform_code": "taobao",
            "source_sku_id": "tb10001",
            "title": "维达 V2239 抽纸 3层130抽24包",
            "price_text": "49.90",
            "category_text": "淘宝商品",
            "product_url": "https://item.taobao.com/item.htm?id=10001",
        }
        cleaned = CleaningPipeline().process_item(item)
        self.assertEqual(cleaned["category_name"], "生活日用-纸品")
        self.assertEqual(cleaned["category_id"], 400)


if __name__ == "__main__":
    unittest.main()
