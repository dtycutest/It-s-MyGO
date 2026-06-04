"""浏览器登录配置助手 — 一次性手动登录，保存 Cookie 供自动爬虫复用.

Usage:
  python -m jobs.setup_browser_profile --platform jd
  python -m jobs.setup_browser_profile --platform taobao
  python -m jobs.setup_browser_profile --platform all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from onebuy_crawler.anti_detect import (
    get_stealth_context_args,
    apply_stealth_to_page,
    BROWSER_PROFILE_DIR,
    EXTRA_HTTP_HEADERS,
)

COOKIE_DIR = Path("cookies")


def main() -> None:
    parser = argparse.ArgumentParser(description="浏览器登录配置助手")
    parser.add_argument("--platform", required=True, choices=["jd", "jingdong", "taobao", "all"])
    parser.add_argument("--headless", action="store_true", help="无头模式 (不推荐，登录需要可见窗口)")
    parser.add_argument("--no-stealth", action="store_true", help="禁用反检测脚本 (调试用)")
    args = parser.parse_args()

    platforms = _resolve_platforms(args.platform)
    BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    COOKIE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        for platform_code in platforms:
            _setup_profile(p, platform_code, headless=args.headless, no_stealth=args.no_stealth)

    print("\n所有平台登录配置完成")
    print("验证登录: python -m jobs.browser_capture_search --platform jd --keyword test --login-wait")
    print("运行自动爬虫: python -m jobs.automated_crawl --platform all")


def _setup_profile(p, platform_code: str, headless: bool = False, no_stealth: bool = False) -> None:
    config = _get_platform_config(platform_code)
    profile_path = BROWSER_PROFILE_DIR / platform_code
    cookie_path = COOKIE_DIR / f"{platform_code}.cookie"

    print(f"\n{'='*60}")
    print(f"  配置 {config['name']} 浏览器登录")
    print(f"{'='*60}")
    print(f"  1. 浏览器将打开 {config['name']} 首页")
    print(f"  2. 请手动点击页面上的 '登录' 按钮")
    print(f"  3. 完成登录（扫码/账号密码/验证码）")
    print(f"  4. 登录成功后，回到此终端按 Enter 保存")
    print(f"  配置文件: {profile_path}")
    print(f"  Cookie 保存: {cookie_path}")
    sys.stdout.flush()

    kwargs = get_stealth_context_args(headless)
    kwargs["user_data_dir"] = str(profile_path)

    for channel in ("msedge", "chrome", "chromium"):
        try:
            context = p.chromium.launch_persistent_context(channel=channel, **kwargs)
            print(f"  使用浏览器: {channel}")
            break
        except Exception:
            continue
    else:
        context = p.chromium.launch_persistent_context(**kwargs)
        print("  使用浏览器: chromium (内置)")

    for page in context.pages:
        apply_stealth_to_page(page)
        if not no_stealth:
            try:
                page.set_extra_http_headers(EXTRA_HTTP_HEADERS)
            except Exception:
                pass
    context.on("page", apply_stealth_to_page)

    page = context.pages[0] if context.pages else context.new_page()
    page.goto(config["home_url"], wait_until="domcontentloaded", timeout=30000)
    print(f"  已打开首页: {config['home_url']}")
    print(f"  请在页面上找到并点击 '登录' 按钮，完成登录...")
    sys.stdout.flush()

    input("\n  登录完成后按 Enter 保存 Cookie...")

    cookies = context.cookies()
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    cookie_path.write_text(cookie_str, encoding="utf-8")
    print(f"  Cookie 已保存到 {cookie_path} ({len(cookies)} 条)")

    context.close()
    print(f"  浏览器配置文件已保存到 {profile_path}")


def _get_platform_config(platform_code: str) -> dict:
    configs = {
        "jingdong": {
            "name": "京东",
            "home_url": "https://www.jd.com/",
            "search_url": "https://search.jd.com/Search?keyword=test",
        },
        "taobao": {
            "name": "淘宝",
            "home_url": "https://www.taobao.com/",
            "search_url": "https://s.taobao.com/search?q=test",
        },
    }
    return configs.get(platform_code, configs["jingdong"])


def _resolve_platforms(platform: str) -> list[str]:
    if platform in ("all",):
        return ["jingdong", "taobao"]
    alias_map = {"jd": "jingdong", "jingdong": "jingdong", "taobao": "taobao"}
    return [alias_map.get(platform.strip().lower(), "jingdong")]


if __name__ == "__main__":
    main()