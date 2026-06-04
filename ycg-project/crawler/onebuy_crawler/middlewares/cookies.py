from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ManualCookieMiddleware:
    """Attach manually exported browser cookies to platform requests.

    Supported formats:
    - env value: "a=b; c=d"
    - plain file: "a=b; c=d"
    - JSON object: {"pt_key": "...", "pt_pin": "..."}
    - JSON list from browser extensions: [{"name": "pt_key", "value": "..."}]
    - JSON platform map: {"jingdong": "a=b", "taobao": "c=d"}
    """

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        cookie_sources = {
            "jingdong": [
                settings.get("JD_COOKIE", ""),
                cls._read_cookie_file(settings.get("JD_COOKIE_FILE", "")),
            ],
            "taobao": [
                settings.get("TAOBAO_COOKIE", ""),
                cls._read_cookie_file(settings.get("TAOBAO_COOKIE_FILE", "")),
            ],
        }
        cookies = {
            platform: cls._normalize_cookie_value(platform, values)
            for platform, values in cookie_sources.items()
        }
        return cls(cookies)

    def __init__(self, cookies: dict[str, str]):
        self.cookies = cookies

    def process_request(self, request):
        platform_code = request.meta.get("platform_code")
        cookie = self.cookies.get(platform_code or "")
        if cookie:
            request.headers.setdefault("Cookie", cookie)
        return None

    @staticmethod
    def _read_cookie_file(path_value: str) -> str:
        if not path_value:
            return ""
        path = Path(path_value)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    @classmethod
    def _normalize_cookie_value(cls, platform: str, values: list[str]) -> str:
        for value in values:
            value = (value or "").strip()
            if not value:
                continue
            parsed = cls._try_json_cookie(platform, value)
            return parsed or value
        return ""

    @staticmethod
    def _try_json_cookie(platform: str, value: str) -> str:
        try:
            payload: Any = json.loads(value)
        except json.JSONDecodeError:
            return ""

        if isinstance(payload, dict):
            if platform in payload:
                nested = payload[platform]
                if isinstance(nested, str):
                    return nested
                payload = nested
            if isinstance(payload, dict):
                return "; ".join(f"{key}={val}" for key, val in payload.items() if val is not None)

        if isinstance(payload, list):
            pairs = []
            for cookie in payload:
                if isinstance(cookie, dict) and cookie.get("name") and cookie.get("value") is not None:
                    pairs.append(f"{cookie['name']}={cookie['value']}")
            return "; ".join(pairs)
        return ""
