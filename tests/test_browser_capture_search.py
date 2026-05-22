from __future__ import annotations

import unittest

from jobs.browser_capture_search import _detect_browser_failure_reason


class FakeLocator:
    def __init__(self, text: str):
        self.text = text

    def inner_text(self, timeout: int = 3000) -> str:
        return self.text


class FakePage:
    def __init__(self, url: str, title: str, body: str):
        self.url = url
        self._title = title
        self._body = body

    def title(self) -> str:
        return self._title

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self._body)


class BrowserCaptureSearchTests(unittest.TestCase):
    def test_detect_access_too_frequent(self):
        page = FakePage("https://search.jd.com", "商品搜索", "抱歉由于访问频繁导致无法搜索")
        self.assertEqual(_detect_browser_failure_reason(page, "jd"), "jd_access_too_frequent")

    def test_detect_jd_page_abnormal_as_access_too_frequent(self):
        page = FakePage("https://www.jd.com", "京东", "内容太火爆了，请稍后再试 当前页面异常 请刷新或切换账户试试")
        self.assertEqual(_detect_browser_failure_reason(page, "jd"), "jd_access_too_frequent")

    def test_detect_jd_search_redirected_home(self):
        page = FakePage("https://www.jd.com/?from=pc_search_sd", "京东", "京东首页")
        self.assertEqual(_detect_browser_failure_reason(page, "jd"), "jd_search_redirected_to_home")

    def test_detect_captcha_or_login(self):
        captcha_page = FakePage("https://search.jd.com", "安全验证", "请完成验证码")
        login_page = FakePage("https://passport.jd.com/new/login.aspx", "登录", "京东登录")
        self.assertEqual(_detect_browser_failure_reason(captcha_page, "jd"), "jd_captcha_or_security_check")
        self.assertEqual(_detect_browser_failure_reason(login_page, "jd"), "jd_login_required")

    def test_detect_taobao_login_and_security(self):
        login_page = FakePage("https://login.taobao.com/member/login.jhtml", "淘宝登录", "亲，请登录")
        security_page = FakePage("https://sec.taobao.com/query.htm", "访问受限", "请完成滑块验证")
        self.assertEqual(_detect_browser_failure_reason(login_page, "taobao"), "taobao_login_required")
        self.assertEqual(_detect_browser_failure_reason(security_page, "taobao"), "taobao_captcha_or_security_check")


if __name__ == "__main__":
    unittest.main()
