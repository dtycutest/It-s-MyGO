from __future__ import annotations

import unittest

from onebuy_crawler.services.copied_search_html import extract_jd_rows_from_copied_html


class CopiedSearchHtmlTests(unittest.TestCase):
    def test_extract_jd_card_rows(self):
        html = '''
        <div class="plugin_goodsCardWrapper" data-sku="10078322255876">
          <div title="罗技（Logitech）K380多设备蓝牙键盘 K380多设备蓝牙键盘(红色)">
            <img data-src="//img11.360buyimg.com/n2/demo.jpg.avif">
          </div>
          <span class="_price"><i>¥</i><span>109</span></span>
          <span title="已售3000+">已售3000+</span>
          <span class="_limit">罗技高端外设旗舰店</span>
        </div>
        '''
        rows = extract_jd_rows_from_copied_html(html)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["skuId"], "10078322255876")
        self.assertIn("K380", rows[0]["skuName"])
        self.assertEqual(rows[0]["price"], "109")
        self.assertIn("360buyimg", rows[0]["imageUrl"])


if __name__ == "__main__":
    unittest.main()
