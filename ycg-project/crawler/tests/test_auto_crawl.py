from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jobs.auto_crawl import DEFAULT_KEYWORDS, DEFAULT_PLATFORM, _collect_keywords, _platforms


class AutoCrawlTests(unittest.TestCase):
    def test_collect_keywords_from_args_file_and_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "keywords.txt"
            path.write_text("蓝牙耳机\n# comment\n机械键盘\n", encoding="utf-8")
            keywords = _collect_keywords(["iPhone 15", "蓝牙耳机"], str(path), use_default_keywords=False)
        self.assertEqual(keywords, ["iPhone 15", "蓝牙耳机", "机械键盘"])

    def test_collect_default_keywords_only_when_requested(self):
        self.assertEqual(_collect_keywords([], "", use_default_keywords=False), [])
        self.assertEqual(_collect_keywords([], "", use_default_keywords=True), DEFAULT_KEYWORDS)

    def test_platforms(self):
        self.assertEqual(_platforms("all"), ["jingdong", "taobao"])
        self.assertEqual(_platforms("jd"), ["jingdong"])
        self.assertEqual(_platforms("taobao"), ["taobao"])

    def test_default_platform_is_jd(self):
        self.assertEqual(DEFAULT_PLATFORM, "jd")
        self.assertEqual(_platforms(DEFAULT_PLATFORM), ["jingdong"])


if __name__ == "__main__":
    unittest.main()
