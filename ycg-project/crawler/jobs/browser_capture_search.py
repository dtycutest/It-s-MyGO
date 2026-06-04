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

from onebuy_crawler.item_adapter import ItemAdapter
from onebuy_crawler.services.browser_extractors import (
    extract_from_dom,
    extract_jd_price_map,
    extract_from_response,
    failure_item,
    matches_keyword,
)
from onebuy_crawler.services.pipeline_runner import PipelineRunner
from onebuy_crawler.services.product_urls import extract_product_urls
from onebuy_crawler.services.proxy_pool import ProxyPool, load_proxies_from_settings, playwright_proxy_config


SEARCH_URLS = {
    "taobao": "https://s.taobao.com/search?q={keyword}&s={offset}",
    "jd": "https://search.jd.com/Search?keyword={keyword}&enc=utf-8&page={page}",
}

JD_DETAIL_URL_RE = re.compile(r"https?://(?:item|item\.m)\.jd\.com/(?:product/)?(\d+)\.html")

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
    parser.add_argument(
        "--manual-open-search-url",
        action="store_true",
        help="Open the direct search URL in the connected browser before waiting for manual confirmation.",
    )
    parser.add_argument(
        "--search-url",
        default="",
        help="Open this already working search result URL for page 1 instead of building a normal search URL.",
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
    parser.add_argument(
        "--no-jd-mobile-fallback",
        action="store_true",
        help="Do not open m.jd.com as a fallback when the JD PC search page renders no products.",
    )
    parser.add_argument(
        "--allow-jd-recommend-fallback",
        action="store_true",
        help="Allow JD m.jd.com recommendation feeds when exact keyword search is unavailable. Off by default.",
    )
    parser.add_argument(
        "--allow-jd-home-fallback",
        action="store_true",
        help="Allow collecting visible JD home-page products when search is redirected to home. Off by default.",
    )
    parser.add_argument(
        "--jd-url",
        action="append",
        default=[],
        help="JD product detail URL to capture exactly. Can be used multiple times.",
    )
    parser.add_argument("--jd-url-file", default="", help="UTF-8 text file with one JD product detail URL per line.")
    parser.add_argument("--debug-dir", default="output/browser_debug", help="Directory for zero-item debug snapshots.")
    parser.add_argument("--no-debug-dump", action="store_true", help="Do not save HTML/screenshot when no items are captured.")
    parser.add_argument("--summary-file", default="", help="Optional JSON file for machine-readable capture summary.")
    parser.add_argument(
        "--output-file",
        default="",
        help="Optional JSONL export file. Defaults to output/browser_capture/*.jsonl when MySQL is disabled.",
    )
    parser.add_argument(
        "--no-visible-fallback",
        action="store_true",
        help="Do not collect visible JD page products when keyword search is redirected to the home page.",
    )
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
    args.jd_url = _collect_jd_urls(args.jd_url, args.jd_url_file)

    settings = get_project_settings()
    runner = PipelineRunner(settings)
    export_path = _resolve_output_file(args.output_file, args.platform, args.keyword)
    profile_dir = Path(args.profile_dir or f"browser_profiles/{args.platform}").resolve()
    if not args.cdp_url:
        profile_dir.mkdir(parents=True, exist_ok=True)

    collected_keys: set[tuple[str, str]] = set()
    collected_count = 0
    final_failure_reason = ""
    last_dom_row_count = 0
    debug_snapshot = ""
    jd_price_cache: dict[str, dict[str, str]] = {}
    network_keyword_override: str | None = None
    network_fallback_reason = ""
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
            if not _looks_like_product_response(args.platform, url, args.allow_jd_recommend_fallback):
                return
            try:
                body = response.text()
            except BaseException:
                return
            if args.platform == "jd":
                jd_price_cache.update(extract_jd_price_map(body))
            response_keyword = args.keyword if network_keyword_override is None else network_keyword_override
            result = extract_from_response(args.platform, url, body, response_keyword)
            for item in result.items:
                if collected_count >= args.limit:
                    break
                key = (item.get("platform_code"), item.get("source_sku_id"))
                if key in collected_keys:
                    continue
                collected_keys.add(key)
                if network_fallback_reason:
                    _mark_visible_fallback_item(item, args.keyword, network_fallback_reason)
                _process_and_export(runner, item, export_path)
                collected_count += 1

        page.on("response", handle_response)

        if args.platform == "jd" and args.jd_url:
            for detail_url in args.jd_url:
                if collected_count >= args.limit:
                    break
                try:
                    _goto_search_url(page, detail_url, PlaywrightError, PlaywrightTimeoutError)
                    _wait_for_navigation_settle(page, PlaywrightTimeoutError)
                    page.wait_for_timeout(2000)
                    for row in _extract_jd_detail_rows(page):
                        if collected_count >= args.limit:
                            break
                        for item in extract_from_dom(args.platform, [row], ""):
                            key = (item.get("platform_code"), item.get("source_sku_id"))
                            if key in collected_keys:
                                continue
                            collected_keys.add(key)
                            _mark_exact_url_item(item, args.keyword or row.get("skuId", ""))
                            _process_and_export(runner, item, export_path)
                            collected_count += 1
                except PlaywrightError:
                    continue

        def collect_dom_items_until(timeout_seconds: int, keyword_override: str | None = None, fallback_reason: str = "") -> None:
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
                dom_items = extract_from_dom(args.platform, dom_rows, args.keyword if keyword_override is None else keyword_override)
                for item in dom_items:
                    key = (item.get("platform_code"), item.get("source_sku_id"))
                    if key in collected_keys:
                        continue
                    collected_keys.add(key)
                    if keyword_override == "" and args.platform == "taobao":
                        _mark_relaxed_manual_item(item, args.keyword)
                    if fallback_reason:
                        _mark_visible_fallback_item(item, args.keyword, fallback_reason)
                    _process_and_export(runner, item, export_path)
                    collected_count += 1
                    if collected_count >= args.limit:
                        break

        if args.jd_url:
            pass
        elif args.manual_search_wait:
            if args.manual_open_search_url:
                _goto_search_url(
                    page,
                    args.search_url or _search_url(args.platform, args.keyword, 1),
                    PlaywrightError,
                    PlaywrightTimeoutError,
                )
                _wait_for_navigation_settle(page, PlaywrightTimeoutError)
            elif getattr(page, "url", "").lower().startswith("about:"):
                page.goto(_home_url(args.platform), wait_until="domcontentloaded")
            _wait_for_manual_search_page(
                page,
                args.platform,
                args.keyword,
                PlaywrightTimeoutError,
                custom_search_url=args.search_url,
                allow_auto_search=not args.manual_search_only,
            )
            if args.cdp_url:
                selected_page = _select_context_page(context, args.platform)
                if selected_page != page:
                    try:
                        page.remove_listener("response", handle_response)
                    except Exception:
                        pass
                    page = selected_page
                    page.set_default_timeout(args.timeout * 1000)
                    page.on("response", handle_response)

        for page_no in range(1, args.pages + 1):
            if collected_count >= args.limit:
                break
            if args.jd_url:
                break
            if args.manual_search_wait and page_no == 1:
                keyword_override = "" if args.platform == "taobao" else None
                collect_dom_items_until(args.timeout, keyword_override=keyword_override)
                continue
            url = args.search_url if page_no == 1 and args.search_url else _search_url(args.platform, args.keyword, page_no)
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
            opening_failure_reason = _detect_browser_failure_reason(page, args.platform)
            if _is_hard_failure_reason(opening_failure_reason):
                break
            _wait_for_product_signals(page, args.platform, PlaywrightTimeoutError, timeout_ms=min(12000, args.timeout * 1000))
            _nudge_page(page)
            collect_dom_items_until(args.timeout)

        if (
            collected_count == 0
            and not args.no_visible_fallback
            and args.platform == "jd"
            and args.allow_jd_home_fallback
            and last_dom_row_count > 0
            and not _is_hard_failure_reason(_detect_browser_failure_reason(page, args.platform))
        ):
            collect_dom_items_until(
                min(8, args.timeout),
                keyword_override="",
                fallback_reason=_detect_browser_failure_reason(page, args.platform),
            )

        if (
            collected_count == 0
            and args.platform == "jd"
            and not args.no_jd_mobile_fallback
            and args.allow_jd_recommend_fallback
        ):
            mobile_fallback_reason = _detect_browser_failure_reason(page, args.platform)
            try:
                network_keyword_override = ""
                network_fallback_reason = f"{mobile_fallback_reason}_mobile_visible_fallback"
                page.set_viewport_size({"width": 390, "height": 844})
                _goto_search_url(
                    page,
                    _mobile_search_url(args.keyword),
                    PlaywrightError,
                    PlaywrightTimeoutError,
                )
                _wait_for_navigation_settle(page, PlaywrightTimeoutError)
                _nudge_page(page)
                collect_dom_items_until(min(12, args.timeout), keyword_override="", fallback_reason=network_fallback_reason)
            except PlaywrightError:
                pass
            finally:
                network_keyword_override = None
                network_fallback_reason = ""

        if (
            collected_count == 0
            and not args.no_visible_fallback
            and args.platform == "jd"
            and args.allow_jd_home_fallback
        ):
            home_fallback_reason = _detect_browser_failure_reason(page, args.platform)
            try:
                page.goto(_home_url(args.platform), wait_until="domcontentloaded")
                _wait_for_navigation_settle(page, PlaywrightTimeoutError)
                _wait_for_product_signals(
                    page,
                    args.platform,
                    PlaywrightTimeoutError,
                    timeout_ms=min(12000, args.timeout * 1000),
                )
                _nudge_page(page)
                collect_dom_items_until(
                    min(12, args.timeout),
                    keyword_override="",
                    fallback_reason=f"{home_fallback_reason}_home_visible_fallback",
                )
            except PlaywrightError:
                pass

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
                            custom_search_url=args.search_url,
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
    if export_path:
        message += f", output={export_path}"
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
                "output": str(export_path) if export_path else "",
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

    search_url_tokens = {
        "jd": ("search.jd.com", "re.jd.com/search"),
        "taobao": ("s.taobao.com", "list.taobao.com"),
    }.get(platform, ())
    detail_url_tokens = {
        "jd": ("item.jd.com",),
        "taobao": ("item.taobao.com", "detail.tmall.com"),
    }.get(platform, ())
    site_tokens = {
        "jd": ("jd.com", "京东"),
        "taobao": ("taobao.com", "tmall.com", "淘宝", "天猫"),
    }.get(platform, ())

    for token_group in (search_url_tokens, detail_url_tokens, site_tokens):
        selected = _find_latest_context_page(pages, token_group)
        if selected:
            return selected
    return pages[-1]


def _find_latest_context_page(pages: list, tokens: tuple[str, ...]):
    if not tokens:
        return None
    for page in reversed(pages):
        url = getattr(page, "url", "")
        title = _safe_title(page)
        if any(token in url or token in title for token in tokens):
            try:
                page.bring_to_front()
            except Exception:
                pass
            return page
    return None


def _search_url(platform: str, keyword: str, page_no: int) -> str:
    encoded = quote_plus(keyword)
    if platform == "taobao":
        return SEARCH_URLS[platform].format(keyword=encoded, offset=(page_no - 1) * 44)
    return SEARCH_URLS[platform].format(keyword=encoded, page=page_no * 2 - 1)


def _mobile_search_url(keyword: str) -> str:
    return f"https://m.jd.com/search?keyword={quote_plus(keyword)}"


def _collect_jd_urls(url_args: list[str], url_file: str) -> list[str]:
    urls = []
    for value in url_args or []:
        extracted = extract_product_urls(value, platform="jd")
        urls.extend(extracted or [value])
    if url_file:
        path = Path(url_file)
        if path.exists():
            text = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#"))
            extracted = extract_product_urls(text, platform="jd")
            if extracted:
                urls.extend(extracted)
            else:
                urls.extend(line.strip() for line in text.splitlines() if line.strip())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# One JD product detail URL per line, or paste copied search-result HTML/text.\n"
                "# https://item.jd.com/100278221862.html\n",
                encoding="utf-8",
            )
            raise SystemExit(f"JD URL file not found, so a template was created: {path}")
    return list(dict.fromkeys(urls))


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
    return _current_page_looks_search_page(page, "jd")


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


def _wait_for_manual_search_page(
    page,
    platform: str,
    keyword: str,
    timeout_error,
    allow_auto_search: bool,
    custom_search_url: str = "",
) -> None:
    while True:
        search_url = custom_search_url or _search_url(platform, keyword, 1)
        input(
            f"Manual search mode: open this direct search URL in the browser if the page is still home:\n{search_url}\n"
            "Make sure the product list is visible, then press Enter here to capture the current page..."
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
        return "search.jd.com" in lowered or "re.jd.com/search" in lowered or "item.jd.com" in lowered
    if platform == "taobao":
        return (
            "s.taobao.com" in lowered
            or "list.taobao.com" in lowered
            or "item.taobao.com" in lowered
            or "detail.tmall.com" in lowered
        )
    return False


def _looks_like_product_response(platform: str, url: str, allow_jd_recommend_fallback: bool = False) -> bool:
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
        search_tokens = (
            "search",
            "prices",
            "goods",
            "ware",
            "sku",
            "item",
            "pctradesoa_mixer",
            "pc_search_searchware",
            "pc_search_getshopandware",
            "pc_search_adv_search",
        )
        if any(token in lowered for token in search_tokens):
            return True
        return allow_jd_recommend_fallback and "recommend_like_m" in lowered
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
              const looksPriced = (node) => {
                const text = (node && node.innerText) || '';
                return /[¥￥]\\s*\\d+(?:\\.\\d+)?|\\d+(?:\\.\\d+)?\\s*元/.test(text) || !!(node && node.querySelector && node.querySelector('[class*="price"], [class*="Price"], [class*="PRICE"]'));
              };
              const findCard = (node) => {
                let current = node;
                for (let depth = 0; current && depth < 8; depth += 1, current = current.parentElement) {
                  const text = current.innerText || '';
                  if (looksPriced(current) && text.length >= 20) return current;
                }
                return node.closest('[data-nid], [data-item-id], [data-auction-id], [class*="item"], [class*="Item"], [class*="Card"], [class*="card"], li, div') || node;
              };
              for (const el of cards) {
                const card = findCard(el);
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
                const titleEl = card.querySelector('[class*="title"], [class*="Title"], [class*="name"], [class*="Name"]');
                rows.push({
                  item_id: itemId,
                  title: hrefEl.getAttribute('title') || hrefEl.getAttribute('aria-label') || (card.querySelector('[title]') || {}).title || (titleEl && titleEl.innerText) || (img && img.alt) || titleFromLines,
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
            const card = el.closest('li.gl-item, [data-sku], .goods-item, .more2_item, .more2_lk') || el;
            const hrefEl = card.querySelector('a[href*="item.jd.com"]') || el;
            const img = card.querySelector('img');
            const text = card.innerText || '';
            const sku = card.getAttribute('data-sku') || (hrefEl.href.match(/item\\.jd\\.com\\/(\\d+)\\.html/) || [,''])[1] || hrefEl.href;
            const imageAttr = (image) => {
              if (!image) return '';
              for (const name of ['data-lazy-img', 'source-data-lazy-img', 'data-src', 'data-original', 'src']) {
                const value = image.getAttribute(name);
                if (value && !value.startsWith('data:')) return value;
              }
              if (image.currentSrc && !image.currentSrc.startsWith('data:')) return image.currentSrc;
              return '';
            };
            const priceText = (node) => {
              const value = (node && node.innerText) || '';
              const match = value.match(/[¥￥]\\s*\\d+(?:\\.\\d+)?/);
              return match ? match[0] : '';
            };
            const priceEl = card.querySelector('.p-price, .more2_info_price, [class*="price"], [class*="Price"]');
            const price = priceText(priceEl) || (text.match(/[¥￥]\\s*\\d+(?:\\.\\d+)?/) || [''])[0];
            const salesText = /评论|销量/.test(text) ? text : '';
            return {
              skuId: sku,
              skuName: hrefEl.getAttribute('title') || hrefEl.getAttribute('aria-label') || (card.querySelector('.p-name em, .p-name a, .more2_info_name, [title]') || {}).innerText || text.split('\\n')[0],
              price: price,
              imageUrl: imageAttr(img),
              itemUrl: hrefEl.href,
              shopName: (card.querySelector('.p-shop a, .p-shop span') || {}).innerText || '',
              commentCount: salesText
            };
          })
        """
    )


def _extract_jd_detail_rows(page) -> list[dict]:
    return page.evaluate(
        """
        () => {
          const url = location.href;
          const skuMatch = url.match(/(?:item|item\\.m)\\.jd\\.com\\/(?:product\\/)?(\\d+)\\.html/);
          const sku = skuMatch ? skuMatch[1] : '';
          const titleEl = document.querySelector('.sku-name, .itemInfo-wrap .sku-name, [class*="goods_name"], h1, title');
          const img = document.querySelector('#spec-img, .preview img, .goods_img img, img[src*="360buyimg"], img[data-origin]');
          const priceEl = document.querySelector('.summary-price .price, .p-price .price, .price, [class*="price"]');
          const bodyText = document.body ? document.body.innerText : '';
          const priceMatch = bodyText.match(/[¥￥]\\s*\\d+(?:\\.\\d+)?/);
          const imageAttr = (image) => {
            if (!image) return '';
            for (const name of ['data-origin', 'data-lazy-img', 'source-data-lazy-img', 'data-src', 'data-original', 'src']) {
              const value = image.getAttribute(name);
              if (value && !value.startsWith('data:')) return value;
            }
            if (image.currentSrc && !image.currentSrc.startsWith('data:')) return image.currentSrc;
            return '';
          };
          return [{
            skuId: sku,
            skuName: (titleEl && titleEl.innerText) || document.title.replace(/【行情 报价 价格 评测】-京东$/, ''),
            price: (priceEl && priceEl.innerText) || (priceMatch ? priceMatch[0] : ''),
            imageUrl: imageAttr(img),
            itemUrl: sku ? `https://item.jd.com/${sku}.html` : url,
            shopName: ((document.querySelector('.name a, #popbox .mt h3 a, [class*="shop"]') || {}).innerText || ''),
            commentCount: bodyText
          }];
        }
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


def _resolve_output_file(output_file: str, platform: str, keyword: str) -> Path | None:
    if output_file:
        return Path(output_file)
    if os.getenv("CRAWLER_ENABLE_MYSQL", "0") == "1":
        return None
    safe_keyword = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", keyword).strip("_")[:40] or "keyword"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return Path("output/browser_capture") / f"{platform}_{safe_keyword}_{stamp}.jsonl"


def _process_and_export(runner: PipelineRunner, item, export_path: Path | None) -> None:
    processed = runner.process(item)
    if export_path:
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with export_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(dict(ItemAdapter(processed)), ensure_ascii=False, default=str) + "\n")


def _mark_visible_fallback_item(item, requested_keyword: str, fallback_reason: str) -> None:
    payload = dict(item.get("raw_payload") or {})
    payload["source"] = "visible_dom_fallback"
    payload["requested_keyword"] = requested_keyword
    payload["fallback_reason"] = fallback_reason
    item["raw_payload"] = payload


def _mark_relaxed_manual_item(item, requested_keyword: str) -> None:
    item["keyword"] = requested_keyword
    payload = dict(item.get("raw_payload") or {})
    payload["source"] = "manual_search_visible_dom"
    payload["requested_keyword"] = requested_keyword
    payload["keyword_filter"] = "relaxed"
    item["raw_payload"] = payload


def _mark_exact_url_item(item, requested_keyword: str) -> None:
    payload = dict(item.get("raw_payload") or {})
    payload["source"] = "jd_exact_detail_url"
    payload["requested_keyword"] = requested_keyword
    if requested_keyword and matches_keyword(item.get("title"), requested_keyword):
        item["keyword"] = requested_keyword
    elif requested_keyword:
        payload["keyword_filter"] = "skipped_mismatch"
    item["raw_payload"] = payload


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
