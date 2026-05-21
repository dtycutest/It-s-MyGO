from __future__ import annotations

import unittest

from onebuy_crawler.middlewares.cookies import ManualCookieMiddleware


class ManualCookieMiddlewareTests(unittest.TestCase):
    def test_plain_cookie(self):
        cookie = ManualCookieMiddleware._normalize_cookie_value("jingdong", ["a=1; b=2"])
        self.assertEqual(cookie, "a=1; b=2")

    def test_json_object_cookie(self):
        cookie = ManualCookieMiddleware._normalize_cookie_value("jingdong", ['{"pt_key":"k","pt_pin":"p"}'])
        self.assertEqual(cookie, "pt_key=k; pt_pin=p")

    def test_json_list_cookie(self):
        cookie = ManualCookieMiddleware._normalize_cookie_value(
            "taobao",
            ['[{"name":"_m_h5_tk","value":"abc"},{"name":"cookie2","value":"xyz"}]'],
        )
        self.assertEqual(cookie, "_m_h5_tk=abc; cookie2=xyz")

    def test_platform_map_cookie(self):
        cookie = ManualCookieMiddleware._normalize_cookie_value(
            "taobao",
            ['{"jingdong":"jd=1","taobao":"tb=2"}'],
        )
        self.assertEqual(cookie, "tb=2")


if __name__ == "__main__":
    unittest.main()
