from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from urllib.parse import quote_plus

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.browser_extractors import (
    extract_from_dom,
    extract_from_response,
    failure_item,
)
from onebuy_crawler.services.pipeline_runner import PipelineRunner
from onebuy_crawler.services.proxy_pool import ProxyPool, load_proxies_from_settings, playwright_proxy_config


SEARCH_URLS = {
    "taobao": "https://s.taobao.com/search?q={keyword}&s={offset}",
    "jd": "https://search.jd.com/Search?keyword={keyword}&enc=utf-8&page={page}",
}

JD_SEARCH_INPUT_SELECTORS = (
    "input.jd_pc_search_bar_react_search_input",
    'input[aria-label="搜索"]',
    "#key",
    'input[type="search"]',
    'input[type="text"]',
)

JD_SEARCH_BUTTON_SELECTORS = (
    "button.jd_pc_search_bar_react_search_btn",
    "#search button",
    ".button",
    'button:has-text("搜索")',
    'input[type="button"]',
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture product search data through a real browser.")
    parser.add_argument("--platform", required=True, choices=["taobao", "jd"], help="Target platform")
    parser.add_argument("--keyword", required=True, help="Search keyword")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--limit", type=int, default=30, help="Stop after collecting this many products")
    parser.add_argument("--profile-dir", default="", help="Persistent browser profile directory")
    parser.add_argument("--proxy", default="", help="Proxy used by the browser context, for example http://host:port")
    parser.add_argument("--use-proxy-pool", action="store_true", help="Choose one proxy from the configured proxy pool")
    parser.add_argument(
        "--cdp-url",
        default="",
        help="Connect to an already running Chrome/Edge browser, for example http://127.0.0.1:9222",
    )
    parser.add_argument("--headless", action="store_true", help="Run browser without UI after login/profile is ready")
    parser.add_argument("--login-wait", action="store_true", help="Pause for manual login before capture")
    parser.add_argument(
        "--manual-search-wait",
        action="store_true",
        help="Pause for manual search and capture the current browser page instead of navigating automatically",
    )
    parser.add_argument("--timeout", type=int, default=25, help="Seconds to wait for network responses per page")
    args = parser.parse_args()

    settings = get_project_settings()
    runner = PipelineRunner(settings)
    profile_dir = Path(args.profile_dir or f"browser_profiles/{args.platform}").resolve()
    if not args.cdp_url:
        profile_dir.mkdir(parents=True, exist_ok=True)

    collected_keys: set[tuple[str, str]] = set()
    collected_count = 0
    final_failure_reason = ""
    browser_proxy = args.proxy
    if args.use_proxy_pool and not browser_proxy:
        browser_proxy = ProxyPool(
            load_proxies_from_settings(settings),
            max_fails=settings.getint("CRAWLER_PROXY_MAX_FAILS", 3),
            cooldown_seconds=settings.getint("CRAWLER_PROXY_COOLDOWN_SECONDS", 300),
        ).choose() or ""

    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Playwright is not installed. Run: .\\.venv\\Scripts\\pip install -r requirements.txt") from exc

    with sync_playwright() as p:
        browser = None
        created_page = True
        if args.cdp_url:
            if browser_proxy:
                print("warning: --proxy/--use-proxy-pool is ignored when --cdp-url is used; set proxy when launching the browser.")
            try:
                browser = p.chromium.connect_over_cdp(args.cdp_url)
            except PlaywrightError as exc:
                raise SystemExit(
                    f"Cannot connect to browser CDP endpoint: {args.cdp_url}\n"
                    "请先运行：.\\.venv\\Scripts\\python.exe -m jobs.launch_debug_browser --port 9222\n"
                    "并确认输出包含 debug browser launched and verified。"
                ) from exc
            context = browser.contexts[0] if browser.contexts else browser.new_context(locale="zh-CN")
            if args.manual_search_wait and context.pages:
                page = _select_context_page(context, args.platform)
                created_page = False
            else:
                page = context.new_page()
        else:
            context = _launch_context(p, profile_dir, args.headless, browser_proxy)
            page = context.new_page()
        page.set_default_timeout(args.timeout * 1000)

        if args.login_wait:
            page.goto(_home_url(args.platform), wait_until="domcontentloaded")
            input("请在打开的浏览器中完成登录/定位后回到终端按 Enter 继续...")

        def handle_response(response):
            nonlocal collected_count
            if collected_count >= args.limit:
                return
            url = response.url
            if not _looks_like_product_response(args.platform, url):
                return
            try:
                body = response.text()
            except BaseException:
                return
            result = extract_from_response(args.platform, url, body, args.keyword)
            for item in result.items:
                if collected_count >= args.limit:
                    break
                key = (item.get("platform_code"), item.get("source_sku_id"))
                if key in collected_keys:
                    continue
                collected_keys.add(key)
                runner.process(item)
                collected_count += 1

        page.on("response", handle_response)

        if args.manual_search_wait:
            input("请在浏览器中手动搜索关键词并确认商品列表可见；如果仍停在首页，也可以直接回到终端按 Enter 让程序自动搜索...")
            if not _current_page_looks_search_page(page, args.platform):
                _ensure_manual_search_page(page, args.platform, args.keyword, PlaywrightTimeoutError)

        for page_no in range(1, args.pages + 1):
            if collected_count >= args.limit:
                break
            if args.manual_search_wait and page_no == 1:
                deadline = time.time() + args.timeout
                while time.time() < deadline and collected_count < args.limit:
                    try:
                        page.wait_for_timeout(1000)
                        dom_rows = _extract_dom_rows(page, args.platform)
                    except PlaywrightError:
                        break
                    dom_items = extract_from_dom(args.platform, dom_rows, args.keyword)
                    for item in dom_items:
                        key = (item.get("platform_code"), item.get("source_sku_id"))
                        if key in collected_keys:
                            continue
                        collected_keys.add(key)
                        runner.process(item)
                        collected_count += 1
                        if collected_count >= args.limit:
                            break
                continue
            url = _search_url(args.platform, args.keyword, page_no)
            _open_search_page(page, args.platform, args.keyword, page_no, url, PlaywrightError, PlaywrightTimeoutError)
            if _page_has_failure_marker(page, args.platform):
                break
            _nudge_page(page)
            deadline = time.time() + args.timeout
            while time.time() < deadline and collected_count < args.limit:
                try:
                    page.wait_for_timeout(1000)
                    dom_rows = _extract_dom_rows(page, args.platform)
                except PlaywrightError:
                    break
                dom_items = extract_from_dom(args.platform, dom_rows, args.keyword)
                for item in dom_items:
                    key = (item.get("platform_code"), item.get("source_sku_id"))
                    if key in collected_keys:
                        continue
                    collected_keys.add(key)
                    runner.process(item)
                    collected_count += 1
                    if collected_count >= args.limit:
                        break

        if collected_count == 0:
            failure_reason = _detect_browser_failure_reason(page, args.platform)
            final_failure_reason = failure_reason
            runner.process(
                failure_item(
                    args.platform,
                    page.url,
                    args.keyword,
                    failure_reason,
                    {
                        "title": _safe_title(page),
                        "profile_dir": str(profile_dir),
                        "cdp_url": args.cdp_url,
                        "proxy": browser_proxy,
                    },
                )
            )

        try:
            page.remove_listener("response", handle_response)
        except Exception:
            pass
        if args.cdp_url:
            if created_page:
                page.close()
        else:
            context.close()

    message = f"browser_capture finished: platform={args.platform}, keyword={args.keyword}, items={collected_count}"
    if final_failure_reason:
        message += f", reason={final_failure_reason}"
    print(message)


def _launch_context(playwright, profile_dir: Path, headless: bool, proxy_url: str = ""):
    kwargs = {
        "user_data_dir": str(profile_dir),
        "headless": headless,
        "viewport": {"width": 1366, "height": 900},
        "locale": "zh-CN",
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
        ],
    }
    proxy_config = playwright_proxy_config(proxy_url)
    if proxy_config:
        kwargs["proxy"] = proxy_config
    for channel in ("msedge", "chrome", "chromium"):
        try:
            return playwright.chromium.launch_persistent_context(channel=channel, **kwargs)
        except Exception:
            continue
    return playwright.chromium.launch_persistent_context(**kwargs)


def _select_context_page(context, platform: str):
    pages = [page for page in context.pages if not page.is_closed()]
    if not pages:
        return context.new_page()

    platform_tokens = {
        "jd": ("jd.com", "京东"),
        "taobao": ("taobao.com", "tmall.com", "淘宝", "天猫"),
    }.get(platform, ())
    for page in reversed(pages):
        url = getattr(page, "url", "")
        title = _safe_title(page)
        if any(token in url or token in title for token in platform_tokens):
            try:
                page.bring_to_front()
            except Exception:
                pass
            return page
    return pages[-1]


def _search_url(platform: str, keyword: str, page_no: int) -> str:
    encoded = quote_plus(keyword)
    if platform == "taobao":
        return SEARCH_URLS[platform].format(keyword=encoded, offset=(page_no - 1) * 44)
    return SEARCH_URLS[platform].format(keyword=encoded, page=page_no * 2 - 1)


def _open_search_page(page, platform: str, keyword: str, page_no: int, direct_url: str, playwright_error, timeout_error) -> None:
    if platform == "jd" and page_no == 1:
        try:
            page.goto("https://www.jd.com/?country=CN", wait_until="domcontentloaded")
            if _submit_jd_home_search(page, keyword, timeout_error):
                return
            if _page_has_failure_marker(page, platform):
                return
        except playwright_error:
            pass

    try:
        page.goto(direct_url, wait_until="domcontentloaded")
    except playwright_error as exc:
        message = str(exc)
        if "interrupted by another navigation" not in message:
            raise
        _wait_for_navigation_settle(page, timeout_error)


def _ensure_manual_search_page(page, platform: str, keyword: str, timeout_error) -> None:
    if platform == "jd":
        lowered = getattr(page, "url", "").lower()
        if "jd.com" not in lowered:
            page.goto("https://www.jd.com/?country=CN", wait_until="domcontentloaded")
        if _submit_jd_home_search(page, keyword, timeout_error):
            return
        if _page_has_failure_marker(page, platform):
            return
    page.goto(_search_url(platform, keyword, 1), wait_until="domcontentloaded")
    _wait_for_navigation_settle(page, timeout_error)


def _submit_jd_home_search(page, keyword: str, timeout_error) -> bool:
    search_input = None
    for selector in JD_SEARCH_INPUT_SELECTORS:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=2000)
            search_input = locator
            break
        except Exception:
            continue
    if search_input is None:
        return False

    try:
        page.evaluate("() => { if (window.search) window.search.isSubmitted = 0; }")
    except Exception:
        pass
    search_input.fill(keyword, timeout=5000)
    for selector in JD_SEARCH_BUTTON_SELECTORS:
        button = page.locator(selector).first
        try:
            if button.count() and button.is_visible(timeout=1000):
                button.click(timeout=3000)
                break
        except Exception:
            continue
    else:
        search_input.press("Enter")

    _wait_for_navigation_settle(page, timeout_error)
    return "search.jd.com" in page.url.lower()


def _wait_for_navigation_settle(page, timeout_error) -> None:
    try:
        page.wait_for_load_state("domcontentloaded", timeout=8000)
    except timeout_error:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except timeout_error:
        pass


def _home_url(platform: str) -> str:
    return "https://www.taobao.com/" if platform == "taobao" else "https://www.jd.com/"


def _current_page_looks_search_page(page, platform: str) -> bool:
    lowered = getattr(page, "url", "").lower()
    if platform == "jd":
        return "search.jd.com" in lowered or "item.jd.com" in lowered
    if platform == "taobao":
        return "s.taobao.com" in lowered or "item.taobao.com" in lowered or "detail.tmall.com" in lowered
    return False


def _looks_like_product_response(platform: str, url: str) -> bool:
    lowered = url.lower()
    if platform == "taobao":
        return any(token in lowered for token in ("mtop", "search", "h5api", "item"))
    if platform == "jd":
        return any(token in lowered for token in ("search", "prices", "goods", "ware", "sku", "item"))
    return False


def _nudge_page(page) -> None:
    for _ in range(4):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(600)


def _extract_dom_rows(page, platform: str) -> list[dict]:
    if platform == "taobao":
        return page.evaluate(
            """
            () => Array.from(document.querySelectorAll('[data-nid], [data-item-id], a[href*="item.taobao"], a[href*="detail.tmall"]'))
              .map((el) => {
                const card = el.closest('[data-nid], [data-item-id], .item, [class*="Card"], [class*="card"]') || el;
                const hrefEl = card.querySelector('a[href*="item.taobao"], a[href*="detail.tmall"]') || el;
                const img = card.querySelector('img');
                const text = card.innerText || '';
                const price = (text.match(/¥\\s*\\d+(?:\\.\\d+)?|￥\\s*\\d+(?:\\.\\d+)?/) || [''])[0];
                return {
                  item_id: card.getAttribute('data-nid') || card.getAttribute('data-item-id') || new URL(hrefEl.href).searchParams.get('id') || hrefEl.href,
                  title: hrefEl.getAttribute('title') || (card.querySelector('[title]') || {}).title || text.split('\\n')[0],
                  price: price,
                  pic_url: img ? (img.currentSrc || img.src) : '',
                  detail_url: hrefEl.href,
                  shopName: '',
                  view_sales: text
                };
              })
            """
        )
    return page.evaluate(
        """
        () => Array.from(document.querySelectorAll('li.gl-item, [data-sku], a[href*="item.jd.com"]'))
          .map((el) => {
            const card = el.closest('li.gl-item, [data-sku], .goods-item') || el;
            const hrefEl = card.querySelector('a[href*="item.jd.com"]') || el;
            const img = card.querySelector('img');
            const text = card.innerText || '';
            const sku = card.getAttribute('data-sku') || (hrefEl.href.match(/item\\.jd\\.com\\/(\\d+)\\.html/) || [,''])[1] || hrefEl.href;
            const price = (text.match(/¥\\s*\\d+(?:\\.\\d+)?|￥\\s*\\d+(?:\\.\\d+)?/) || [''])[0];
            return {
              skuId: sku,
              skuName: (card.querySelector('.p-name em, .p-name a, [title]') || {}).innerText || hrefEl.getAttribute('title') || text.split('\\n')[0],
              price: price,
              imageUrl: img ? (img.currentSrc || img.src || img.getAttribute('data-lazy-img')) : '',
              itemUrl: hrefEl.href,
              shopName: (card.querySelector('.p-shop a, .p-shop span') || {}).innerText || '',
              commentCount: text
            };
          })
        """
    )


def _safe_title(page) -> str:
    try:
        return page.title()
    except Exception:
        return ""


def _page_has_failure_marker(page, platform: str) -> bool:
    return _detect_browser_failure_reason(page, platform) != f"{platform}_browser_capture_no_items"


def _detect_browser_failure_reason(page, platform: str) -> str:
    url = getattr(page, "url", "")
    title = _safe_title(page)
    try:
        body_text = page.locator("body").inner_text(timeout=3000)[:3000]
    except Exception:
        body_text = ""

    combined = f"{url}\n{title}\n{body_text}".lower()
    if "risk_handler" in combined:
        return f"{platform}_risk_handler"
    if platform == "jd" and "www.jd.com" in combined and "from=pc_search_sd" in combined:
        return "jd_search_redirected_to_home"
    if (
        "访问频繁" in combined
        or "无法搜索" in combined
        or "too frequent" in combined
        or "内容太火爆" in combined
        or "当前页面异常" in combined
        or "请刷新或切换账户" in combined
    ):
        return f"{platform}_access_too_frequent"
    if "验证码" in combined or "captcha" in combined or "安全验证" in combined:
        return f"{platform}_captcha_or_security_check"
    if "登录" in combined and ("passport" in combined or "login" in combined):
        return f"{platform}_login_required"
    return f"{platform}_browser_capture_no_items"


if __name__ == "__main__":
    main()
