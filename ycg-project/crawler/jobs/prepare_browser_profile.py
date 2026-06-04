from __future__ import annotations

import argparse
from pathlib import Path

from onebuy_crawler.services.proxy_pool import playwright_proxy_config


HOME_URLS = {
    "jd": "https://www.jd.com/?country=CN",
    "taobao": "https://www.taobao.com/",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a persistent browser profile for logged-in crawling.")
    parser.add_argument("--platform", required=True, choices=["jd", "taobao"])
    parser.add_argument("--profile-dir", default="", help="Persistent profile directory. Defaults to browser_profiles/<platform>.")
    parser.add_argument("--proxy", default="", help="Optional proxy, for example http://host:port.")
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir or f"browser_profiles/{args.platform}").resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Playwright is not installed. Run: .\\.venv\\Scripts\\pip install -r requirements.txt") from exc

    with sync_playwright() as p:
        context = _launch_context(p, profile_dir, args.proxy)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(HOME_URLS[args.platform], wait_until="domcontentloaded")
        print(f"profile_dir={profile_dir}")
        print("请在打开的浏览器中完成登录、地区选择和必要验证。完成后回到终端按 Enter 保存登录态...")
        input()
        try:
            page.wait_for_timeout(1000)
        finally:
            context.close()
    print(f"browser profile saved: platform={args.platform}, profile_dir={profile_dir}")


def _launch_context(playwright, profile_dir: Path, proxy_url: str = ""):
    kwargs = {
        "user_data_dir": str(profile_dir),
        "headless": False,
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


if __name__ == "__main__":
    main()
