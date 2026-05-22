from __future__ import annotations

import unittest
from types import SimpleNamespace

from onebuy_crawler.pipelines.dedup import DedupPipeline
from onebuy_crawler.pipelines.cleaning import CleaningPipeline
from jobs.import_seed_data import _records_to_import
from onebuy_crawler.services.search_query import title_keyword_clause
from onebuy_crawler.services.seed_data import (
    build_generated_records,
    load_seed_records,
    record_to_raw_item,
    select_seed_records,
)


class SeedDataTests(unittest.TestCase):
    def test_default_seed_contains_jd_default_keywords(self):
        records = load_seed_records()
        selected = select_seed_records(records, ["iPhone 15", "显示器"], "jd", limit_per_keyword=2)
        self.assertGreaterEqual(len(selected), 4)
        self.assertTrue(all(record["platform_code"] == "jingdong" for record in selected))

    def test_generated_records_are_marked_as_demo_data(self):
        records = build_generated_records("洗衣机", count=2)
        self.assertEqual(len(records), 2)
        self.assertIn("洗衣机", records[0]["title"])
        self.assertIn("本地兜底数据", records[0]["promo_info"])

    def test_record_to_raw_item_preserves_seed_product_id(self):
        item = record_to_raw_item(
            {
                "product_id": "SKUDEMO001",
                "platform_code": "jd",
                "source_sku_id": "seed-1",
                "title": "iPhone 15",
                "price_text": "4999",
            }
        )
        cleaned = CleaningPipeline().process_item(item)
        processed = DedupPipeline().process_item(cleaned)
        self.assertEqual(processed["product_id"], "SKUDEMO001")

    def test_title_keyword_clause_splits_space_keywords(self):
        clause, params = title_keyword_clause("华为 手机")
        self.assertEqual(clause, "p.title LIKE %s AND p.title LIKE %s")
        self.assertEqual(params, ["%华为%", "%手机%"])

    def test_import_all_platforms_selects_both_platforms_without_keywords(self):
        records = [
            {"platform_code": "jingdong", "source_sku_id": "jd1", "title": "iPhone 15", "price_text": "1"},
            {"platform_code": "taobao", "source_sku_id": "tb1", "title": "iPhone 15", "price_text": "1"},
        ]
        args = SimpleNamespace(platform="all", limit_per_keyword=10)
        selected = _records_to_import(None, records, [], args)
        self.assertEqual({record["platform_code"] for record in selected}, {"jingdong", "taobao"})


if __name__ == "__main__":
    unittest.main()
