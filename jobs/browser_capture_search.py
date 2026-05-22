from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.browser_extractors import (
    extract_from_dom,
    extract_jd_price_map,
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

TAOBAO_SEARCH_INPUT_SELECTORS = (
    "#q",
    'input[name="q"]',
    'input[aria-label*="搜索"]',
    'input[placeholder*="搜索"]',
    'input[type="search"]',
    'input[type="text"]',
)

TAOBAO_SEARCH_BUTTON_SELECTORS = (
    'button[type="submit"]',
    'button:has-text("搜索")',
    '.btn-search',
    '.search-button',
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
    parser.add_argument(
        "--manual-search-only",
        action="store_true",
        help="With --manual-search-wait, never auto-submit search; only capture after the current page is a search result page.",
    )
    parser.add_argument("--timeout", type=int, default=25, help="Seconds to wait for network responses per page")
    parser.add_argument(
        "--open-strategy",
        default="direct-first",
        choices=["direct-first", "home-first"],
        help="Search navigation strategy for page 1. Direct search is more reliable for JD in the current profile.",
    )
    parser.add_argument("--typing-delay-ms", type=int, default=120, help="Delay between search keyword characters.")
    parser.add_argument("--pre-search-delay-ms", type=int, default=800, help="Delay before typing on the home page.")
    parser.add_argument("--post-search-delay-ms", type=int, default=1500, help="Delay after submitting a search.")
    parser.add_argument(
        "--no-jd-price-fetch",
        action="store_true",
        help="Disable supplemental JD price fetch for SKUs found in the DOM.",
    )
    parser.add_argument("--debug-dir", default="output/browser_debug", help="Directory for zero-item debug snapshots.")
    parser.add_argument("--no-debug-dump", action="store_true", help="Do not save HTML/screenshot when no items are captured.")
    parser.add_argument("--summary-file", default="", help="Optional JSON file for machine-readable capture summary.")
    parser.add_argument(
        "--manual-verify-on-failure",
        action="store_true",
        help="Keep the browser open on login/security failure, wait for manual verification, then retry once.",
    )
    parser.add_argument(
        "--keep-open-on-failure",
        action="store_true",
        help="Keep the browser open after a failed capture until Enter is pressed.",
    )
    args = parser.parse_args()
    if args.manual_search_only:
        args.manual_search_wait = True

    settings = get_project_settings()
    runner = PipelineRunner(settings)
    profile_dir = Path(args.profile_dir or f"browser_profiles/{args.platform}").resolve()
    if not args.cdp_url:
        profile_dir.mkdir(parents=True, exist_ok=True)

    collected_keys: set[tuple[str, str]] = set()
    collected_count = 0
    final_failure_reason = ""
    last_dom_row_count = 0
    debug_snapshot = ""
    jd_price_cache: dict[str, dict[str, str]] = {}
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
            if args.platform == "jd":
                jd_price_cache.update(extract_jd_price_map(body))
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

        def collect_dom_items_until(timeout_seconds: int) -> None:
            nonlocal collected_count, last_dom_row_count, jd_price_cache
            deadline = time.time() + timeout_seconds
            while time.time() < deadline and collected_count < args.limit:
                try:
                    page.wait_for_timeout(1000)
                    dom_rows = _extract_dom_rows(page, args.platform)
                    dom_rows.extend(_extract_state_rows(page, args.platform))
                    dom_rows = _dedupe_dom_rows(dom_rows, args.platform)
                    last_dom_row_count = len(dom_rows)
                    if args.platform == "jd":
                        if not args.no_jd_price_fetch:
                            jd_price_cache.update(_fetch_jd_prices_for_rows(page, dom_rows, jd_price_cache))
                        dom_rows = _merge_jd_prices(dom_rows, jd_price_cache)
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

        if args.manual_search_wait:
            if getattr(page, "url", "").lower().startswith("about:"):
                page.goto(_home_url(args.platform), wait_until="domcontentloaded")
            _wait_for_manual_search_page(
                page,
                args.platform,
                args.keyword,
                PlaywrightTimeoutError,
                allow_auto_search=not args.manual_search_only,
            )

        for page_no in range(1, args.pages + 1):
            if collected_count >= args.limit:
                break
            if args.manual_search_wait and page_no == 1:
                collect_dom_items_until(args.timeout)
                continue
            url = _search_url(args.platform, args.keyword, page_no)
            _open_search_page(
                page,
                args.platform,
                args.keyword,
                page_no,
                url,
                PlaywrightError,
                PlaywrightTimeoutError,
                args.open_strategy,
                args.typing_delay_ms,
                args.pre_search_delay_ms,
                args.post_search_delay_ms,
            )
            if _page_has_failure_marker(page, args.platform):
                break
            _wait_for_product_signals(page, args.platform, PlaywrightTimeoutError, timeout_ms=min(12000, args.timeout * 1000))
            _nudge_page(page)
            collect_dom_items_until(args.timeout)

        if collected_count == 0:
            failure_reason = _detect_browser_failure_reason(page, args.platform)
            if args.manual_verify_on_failure and _is_hard_failure_reason(failure_reason):
                print(
                    f"manual verification needed: platform={args.platform}, reason={failure_reason}\n"
                    "请在打开的浏览器中完成登录/安全验证，并确认商品列表可见；完成后回到终端按 Enter 继续...",
                    flush=True,
                )
                input()
                if not _current_page_looks_search_page(page, args.platform):
                    if args.manual_search_only:
                        _wait_for_manual_search_page(
                            page,
                            args.platform,
                            args.keyword,
                            PlaywrightTimeoutError,
                            allow_auto_search=False,
                        )
                    else:
                        _ensure_manual_search_page(page, args.platform, args.keyword, PlaywrightTimeoutError)
                _wait_for_product_signals(page, args.platform, PlaywrightTimeoutError, timeout_ms=min(15000, args.timeout * 1000))
                _nudge_page(page)
                collect_dom_items_until(args.timeout)

            if collected_count == 0:
                failure_reason = _detect_browser_failure_reason(page, args.platform)
                final_failure_reason = failure_reason
                if not args.no_debug_dump:
                    debug_snapshot = _save_debug_snapshot(page, args.platform, args.keyword, Path(args.debug_dir))
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
                            "dom_rows": last_dom_row_count,
                            "jd_price_cache": len(jd_price_cache),
                            "debug_snapshot": debug_snapshot,
                        },
                    )
                )

        if collected_count == 0 and args.keep_open_on_failure and not args.cdp_url:
            input("采集仍未成功，浏览器已保持打开。检查页面后按 Enter 关闭浏览器...")

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
    if last_dom_row_count:
        message += f", dom_rows={last_dom_row_count}"
    if jd_price_cache:
        message += f", jd_prices={len(jd_price_cache)}"
    if debug_snapshot:
        message += f", debug={debug_snapshot}"
    print(message)
    if args.summary_file:
        _write_summary(
            args.summary_file,
            {
                "platform": args.platform,
                "keyword": args.keyword,
                "items": collected_count,
                "reason": final_failure_reason,
                "dom_rows": last_dom_row_count,
                "jd_prices": len(jd_price_cache),
                "debug": debug_snapshot,
            },
        )


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


def _open_search_page(
    page,
    platform: str,
    keyword: str,
    page_no: int,
    direct_url: str,
    playwright_error,
    timeout_error,
    open_strategy: str = "direct-first",
    typing_delay_ms: int = 120,
    pre_search_delay_ms: int = 800,
    post_search_delay_ms: int = 1500,
) -> None:
    if page_no != 1 or platform not in {"jd", "taobao"}:
        _goto_search_url(page, direct_url, playwright_error, timeout_error)
        return

    if platform == "jd":
        strategies = [_open_jd_direct_search, _open_jd_home_search]
    else:
        strategies = [_open_taobao_direct_search, _open_taobao_home_search]
    if open_strategy == "home-first":
        strategies.reverse()

    for strategy in strategies:
        try:
            if strategy(
                page,
                keyword,
                direct_url,
                playwright_error,
                timeout_error,
                typing_delay_ms,
                pre_search_delay_ms,
                post_search_delay_ms,
            ):
                return
        except playwright_error:
            continue
        reason = _detect_browser_failure_reason(page, platform)
        if _is_hard_failure_reason(reason):
            return


def _open_jd_direct_search(
    page,
    keyword: str,
    direct_url: str,
    playwright_error,
    timeout_error,
    typing_delay_ms: int = 120,
    pre_search_delay_ms: int = 800,
    post_search_delay_ms: int = 1500,
) -> bool:
    _goto_search_url(page, direct_url, playwright_error, timeout_error)
    return "search.jd.com" in getattr(page, "url", "").lower()


def _open_jd_home_search(
    page,
    keyword: str,
    direct_url: str,
    playwright_error,
    timeout_error,
    typing_delay_ms: int = 120,
    pre_search_delay_ms: int = 800,
    post_search_delay_ms: int = 1500,
) -> bool:
    page.goto("https://www.jd.com/?country=CN", wait_until="domcontentloaded")
    return _submit_jd_home_search(page, keyword, timeout_error, typing_delay_ms, pre_search_delay_ms, post_search_delay_ms)


def _open_taobao_direct_search(
    page,
    keyword: str,
    direct_url: str,
    playwright_error,
    timeout_error,
    typing_delay_ms: int = 120,
    pre_search_delay_ms: int = 800,
    post_search_delay_ms: int = 1500,
) -> bool:
    _goto_search_url(page, direct_url, playwright_error, timeout_error)
    return _current_page_looks_search_page(page, "taobao")


def _open_taobao_home_search(
    page,
    keyword: str,
    direct_url: str,
    playwright_error,
    timeout_error,
    typing_delay_ms: int = 120,
    pre_search_delay_ms: int = 800,
    post_search_delay_ms: int = 1500,
) -> bool:
    page.goto("https://www.taobao.com/", wait_until="domcontentloaded")
    return _submit_taobao_home_search(page, keyword, timeout_error, typing_delay_ms, pre_search_delay_ms, post_search_delay_ms)


def _goto_search_url(page, direct_url: str, playwright_error, timeout_error) -> None:
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
    if platform == "taobao":
        lowered = getattr(page, "url", "").lower()
        if "taobao.com" in lowered or "tmall.com" in lowered:
            if _submit_taobao_home_search(page, keyword, timeout_error):
                return
            if _page_has_failure_marker(page, platform):
                return
    page.goto(_search_url(platform, keyword, 1), wait_until="domcontentloaded")
    _wait_for_navigation_settle(page, timeout_error)


def _wait_for_manual_search_page(page, platform: str, keyword: str, timeout_error, allow_auto_search: bool) -> None:
    while True:
        input(
            "Manual search mode: finish the search in the browser and make sure the product list is visible, "
            "then press Enter here to capture the current page..."
        )
        if _current_page_looks_search_page(page, platform) or _page_has_failure_marker(page, platform):
            return
        if allow_auto_search:
            _ensure_manual_search_page(page, platform, keyword, timeout_error)
            return
        print("The current page is not a search result page yet. I will not auto-search; please search manually and press Enter again.")


def _submit_jd_home_search(
    page,
    keyword: str,
    timeout_error,
    typing_delay_ms: int = 120,
    pre_search_delay_ms: int = 800,
    post_search_delay_ms: int = 1500,
) -> bool:
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
    _human_pause(page, pre_search_delay_ms, pre_search_delay_ms + 600)
    _human_type_keyword(search_input, keyword, typing_delay_ms)
    _human_pause(page, 300, 900)
    for selector in JD_SEARCH_BUTTON_SELECTORS:
        button = page.locator(selector).first
        try:
            if button.count() and button.is_visible(timeout=1000):
                _human_pause(page, 200, 700)
                button.click(timeout=3000)
                break
        except Exception:
            continue
    else:
        _human_pause(page, 200, 700)
        search_input.press("Enter")

    _human_pause(page, post_search_delay_ms, post_search_delay_ms + 1000)
    _wait_for_navigation_settle(page, timeout_error)
    return "search.jd.com" in page.url.lower()


def _submit_taobao_home_search(
    page,
    keyword: str,
    timeout_error,
    typing_delay_ms: int = 120,
    pre_search_delay_ms: int = 800,
    post_search_delay_ms: int = 1500,
) -> bool:
    search_input = None
    for selector in TAOBAO_SEARCH_INPUT_SELECTORS:
        locator = page.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=2500)
            search_input = locator
            break
        except Exception:
            continue
    if search_input is None:
        return False

    _human_pause(page, pre_search_delay_ms, pre_search_delay_ms + 600)
    _human_type_keyword(search_input, keyword, typing_delay_ms)
    _human_pause(page, 300, 900)
    for selector in TAOBAO_SEARCH_BUTTON_SELECTORS:
        button = page.locator(selector).first
        try:
            if button.count() and button.is_visible(timeout=1000):
                _human_pause(page, 200, 700)
                button.click(timeout=3000)
                break
        except Exception:
            continue
    else:
        _human_pause(page, 200, 700)
        search_input.press("Enter")

    _human_pause(page, post_search_delay_ms, post_search_delay_ms + 1000)
    _wait_for_navigation_settle(page, timeout_error)
    return _current_page_looks_search_page(page, "taobao")


def _human_type_keyword(locator, keyword: str, delay_ms: int = 120) -> None:
    delay_ms = max(0, delay_ms)
    try:
        locator.click(timeout=5000)
    except Exception:
        pass
    try:
        locator.press("Control+A", timeout=3000)
        locator.press("Backspace", timeout=3000)
    except Exception:
        try:
            locator.fill("", timeout=3000)
        except Exception:
            pass
    try:
        locator.press_sequentially(keyword, delay=delay_ms, timeout=max(8000, len(keyword) * max(delay_ms, 1) + 5000))
    except Exception:
        locator.fill(keyword, timeout=5000)


def _human_pause(page, min_ms: int, max_ms: int | None = None) -> None:
    if max_ms is None:
        max_ms = min_ms
    low = max(0, min(min_ms, max_ms))
    high = max(0, max(min_ms, max_ms))
    page.wait_for_timeout(random.randint(low, high))


def _wait_for_navigation_settle(page, timeout_error) -> None:
    try:
        page.wait_for_load_state("domcontentloaded", timeout=8000)
    except timeout_error:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except timeout_error:
        pass


def _wait_for_product_signals(page, platform: str, timeout_error, timeout_ms: int = 10000) -> None:
    selectors = {
        "jd": 'li.gl-item, [data-sku], a[href*="item.jd.com"]',
        "taobao": '[data-nid], [data-item-id], [data-auction-id], a[href*="item.taobao"], a[href*="detail.tmall"], a[href*="item.htm?id="]',
    }
    selector = selectors.get(platform)
    if not selector:
        return
    try:
        page.locator(selector).first.wait_for(state="attached", timeout=timeout_ms)
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
        return (
            "s.taobao.com" in lowered
            or "list.taobao.com" in lowered
            or "item.taobao.com" in lowered
            or "detail.tmall.com" in lowered
        )
    return False


def _looks_like_product_response(platform: str, url: str) -> bool:
    lowered = url.lower()
    if platform == "taobao":
        return any(
            token in lowered
            for token in (
                "mtop",
                "h5api",
                "search",
                "pcsearch",
                "auction",
                "item",
                "taobao.com",
                "tmall.com",
            )
        )
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
            () => {
              const cards = Array.from(document.querySelectorAll('[data-nid], [data-item-id], [data-auction-id], a[href*="item.taobao"], a[href*="detail.tmall"], a[href*="item.htm?id="]'));
              const seen = new Set();
              const rows = [];
              for (const el of cards) {
                const card = el.closest('[data-nid], [data-item-id], [data-auction-id], [class*="item"], [class*="Item"], [class*="Card"], [class*="card"], li, div') || el;
                const hrefEl = card.querySelector('a[href*="item.taobao"], a[href*="detail.tmall"], a[href*="item.htm?id="]') || el;
                if (!hrefEl || !hrefEl.href) continue;
                let itemId = card.getAttribute('data-nid') || card.getAttribute('data-item-id') || card.getAttribute('data-auction-id') || '';
                try { itemId = itemId || new URL(hrefEl.href).searchParams.get('id') || ''; } catch (e) {}
                itemId = itemId || hrefEl.href;
                if (seen.has(itemId)) continue;
                seen.add(itemId);
                const img = card.querySelector('img');
                const text = card.innerText || '';
                const priceEl = card.querySelector('[class*="price"], [class*="Price"], [class*="PRICE"]');
                const price = (priceEl && priceEl.innerText) || (text.match(/¥\\s*\\d+(?:\\.\\d+)?|￥\\s*\\d+(?:\\.\\d+)?|\\d+(?:\\.\\d+)?\\s*元/) || [''])[0];
                const lines = text.split('\\n').map((line) => line.trim()).filter(Boolean);
                const titleFromLines = lines.find((line) => !/[¥￥]\\s*\\d|销量|付款|评价|包邮|进店|相似/.test(line) && line.length >= 4) || '';
                rows.push({
                  item_id: itemId,
                  title: hrefEl.getAttribute('title') || hrefEl.getAttribute('aria-label') || (card.querySelector('[title]') || {}).title || (img && img.alt) || titleFromLines,
                  price: price,
                  pic_url: img ? (img.currentSrc || img.src || img.getAttribute('data-src')) : '',
                  detail_url: hrefEl.href,
                  shopName: ((card.querySelector('[class*="shop"], [class*="Shop"], [class*="seller"], [class*="Seller"]') || {}).innerText || '').split('\\n')[0],
                  view_sales: text
                });
              }
              return rows;
            }
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
            const priceEl = card.querySelector('.p-price i, .p-price strong, [class*="price"] i, [class*="Price"]');
            const price = (priceEl && priceEl.innerText) || (text.match(/¥\\s*\\d+(?:\\.\\d+)?|￥\\s*\\d+(?:\\.\\d+)?/) || [''])[0];
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


def _extract_state_rows(page, platform: str) -> list[dict]:
    if platform != "taobao":
        return []
    try:
        return page.evaluate(
            """
            () => {
              const rows = [];
              const seen = new Set();
              const visited = new WeakSet();
              const idKeys = ['item_id', 'itemId', 'nid', 'id', 'auctionId', 'itemIdStr', 'auction_id', 'item_id_str'];
              const titleKeys = ['title', 'raw_title', 'rawTitle', 'name', 'item_title', 'itemTitle', 'shortTitle'];
              const priceKeys = ['view_price', 'price', 'salePrice', 'realPrice', 'promotionPrice', 'priceShow', 'priceWithRate', 'proPrice'];
              const urlKeys = ['detail_url', 'detailUrl', 'auctionURL', 'item_url', 'url', 'clickUrl'];
              const imageKeys = ['pic_url', 'picUrl', 'pict_url', 'image', 'img', 'imgUrl', 'itemPic'];
              const shopKeys = ['nick', 'shopName', 'sellerName', 'storeName', 'sellerNick'];
              const salesKeys = ['view_sales', 'sales', 'sold', 'monthSales', 'realSales', 'tradeCount'];

              const clean = (value) => {
                if (value === undefined || value === null) return '';
                if (typeof value === 'object') {
                  for (const key of ['price', 'value', 'text', 'title', 'url', 'priceText', 'display']) {
                    if (value[key] !== undefined && value[key] !== null && value[key] !== '') return clean(value[key]);
                  }
                  return '';
                }
                return String(value).replace(/<[^>]+>/g, '').replace(/\\s+/g, ' ').trim();
              };
              const first = (obj, keys) => {
                for (const key of keys) {
                  const text = clean(obj && obj[key]);
                  if (text) return text;
                }
                return '';
              };
              const add = (obj) => {
                if (!obj || typeof obj !== 'object') return;
                const itemId = first(obj, idKeys);
                const title = first(obj, titleKeys);
                const price = first(obj, priceKeys);
                if (!itemId || !title || !price || seen.has(itemId)) return;
                seen.add(itemId);
                rows.push({
                  item_id: itemId,
                  title: title,
                  price: price,
                  detail_url: first(obj, urlKeys),
                  pic_url: first(obj, imageKeys),
                  shopName: first(obj, shopKeys),
                  view_sales: first(obj, salesKeys)
                });
              };
              const walk = (value, depth = 0) => {
                if (!value || depth > 8) return;
                if (typeof value === 'string') {
                  const text = value.trim();
                  if (text.length > 2 && text.length < 2000000 && (text[0] === '{' || text[0] === '[')) {
                    try { walk(JSON.parse(text), depth + 1); } catch (e) {}
                  }
                  return;
                }
                if (typeof value !== 'object') return;
                if (visited.has(value)) return;
                visited.add(value);
                add(value);
                if (Array.isArray(value)) {
                  for (const child of value) walk(child, depth + 1);
                  return;
                }
                for (const child of Object.values(value)) walk(child, depth + 1);
              };

              for (const name of ['__INIT_DATA__', '__SEARCH_DATA__', '__PAGE_DATA__', '__GLOBAL_INIT_DATA__', '__APOLLO_STATE__', 'g_config']) {
                try { walk(window[name]); } catch (e) {}
              }
              return rows;
            }
            """
        )
    except Exception:
        return []


def _dedupe_dom_rows(rows: list[dict], platform: str) -> list[dict]:
    key_names = ("skuId", "sku_id", "wareId") if platform == "jd" else ("item_id", "itemId", "nid", "auctionId")
    seen = set()
    result = []
    for row in rows:
        key = ""
        for name in key_names:
            if row.get(name):
                key = str(row.get(name))
                break
        if not key:
            key = str(row.get("detail_url") or row.get("itemUrl") or row.get("url") or row)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _merge_jd_prices(rows: list[dict], price_cache: dict[str, dict[str, str]]) -> list[dict]:
    merged = []
    for row in rows:
        sku = _normalize_sku(row.get("skuId"))
        price_info = price_cache.get(sku, {})
        if price_info:
            row = dict(row)
            row["skuId"] = sku
            row["price"] = row.get("price") or price_info.get("price", "")
            row["originalPrice"] = row.get("originalPrice") or price_info.get("original_price", "")
        merged.append(row)
    return merged


def _fetch_jd_prices_for_rows(page, rows: list[dict], price_cache: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    missing = []
    for row in rows:
        sku = _normalize_sku(row.get("skuId"))
        if sku and sku not in price_cache:
            missing.append(sku)
    missing = list(dict.fromkeys(missing))[:50]
    if not missing:
        return {}

    sku_ids = ",".join(f"J_{sku}" for sku in missing)
    url = f"https://p.3.cn/prices/mgets?type=1&skuIds={quote_plus(sku_ids)}"
    try:
        response = page.context.request.get(
            url,
            timeout=8000,
            headers={
                "Referer": getattr(page, "url", "https://search.jd.com/"),
                "Accept": "application/json,text/javascript,*/*;q=0.01",
            },
        )
        if not response.ok:
            return {}
        return extract_jd_price_map(response.text())
    except Exception:
        return {}


def _normalize_sku(value) -> str:
    text = str(value or "").strip()
    match = re.search(r"(\d{5,})", text)
    return match.group(1) if match else text


def _save_debug_snapshot(page, platform: str, keyword: str, debug_dir: Path) -> str:
    debug_dir.mkdir(parents=True, exist_ok=True)
    safe_keyword = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", keyword).strip("_")[:40] or "keyword"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    base = debug_dir / f"{platform}_{safe_keyword}_{stamp}"
    html_path = base.with_suffix(".html")
    png_path = base.with_suffix(".png")
    try:
        html_path.write_text(page.content(), encoding="utf-8")
    except Exception:
        pass
    try:
        page.screenshot(path=str(png_path), full_page=True)
    except Exception:
        pass
    return str(base)


def _write_summary(path: str, payload: dict) -> None:
    summary_path = Path(path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


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
    if platform == "taobao" and (
        "login.taobao.com" in combined
        or "login.tmall.com" in combined
        or "请登录" in combined
        or "親，請登錄" in combined
    ):
        return "taobao_login_required"
    if platform == "taobao" and (
        "sec.taobao.com" in combined
        or "baxia" in combined
        or "punish" in combined
        or "访问受限" in combined
        or "访问被拒绝" in combined
        or "滑块" in combined
    ):
        return "taobao_captcha_or_security_check"
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


def _is_hard_failure_reason(reason: str) -> bool:
    return any(token in reason for token in ("access_too_frequent", "captcha", "risk_handler", "login_required"))


if __name__ == "__main__":
    main()
