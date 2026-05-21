from __future__ import annotations

import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


@dataclass
class ProxyState:
    url: str
    fail_count: int = 0
    cool_until: float = 0.0
    use_count: int = 0

    def available(self, now: float | None = None) -> bool:
        if now is None:
            now = time.time()
        return self.cool_until <= now


class ProxyPool:
    def __init__(self, proxies: list[str], max_fails: int = 3, cooldown_seconds: int = 300):
        self.max_fails = max(1, int(max_fails))
        self.cooldown_seconds = max(1, int(cooldown_seconds))
        self._states = [ProxyState(url) for url in _dedupe(_normalize_proxy(proxy) for proxy in proxies)]

    @property
    def enabled(self) -> bool:
        return bool(self._states)

    def choose(self) -> str | None:
        if not self._states:
            return None
        now = time.time()
        available = [state for state in self._states if state.available(now)]
        if not available:
            return None
        min_uses = min(state.use_count for state in available)
        candidates = [state for state in available if state.use_count == min_uses]
        state = random.choice(candidates)
        state.use_count += 1
        return state.url

    def report_success(self, proxy_url: str | None) -> None:
        state = self._find(proxy_url)
        if not state:
            return
        state.fail_count = 0
        state.cool_until = 0.0

    def report_failure(self, proxy_url: str | None) -> None:
        state = self._find(proxy_url)
        if not state:
            return
        state.fail_count += 1
        if state.fail_count >= self.max_fails:
            state.cool_until = time.time() + self.cooldown_seconds

    def _find(self, proxy_url: str | None) -> ProxyState | None:
        if not proxy_url:
            return None
        normalized = _normalize_proxy(proxy_url)
        for state in self._states:
            if state.url == normalized:
                return state
        return None


def load_proxies_from_settings(settings: Any) -> list[str]:
    proxies: list[str] = []
    raw_list = settings.get("CRAWLER_PROXY_LIST", "")
    if isinstance(raw_list, str):
        proxies.extend(_split_proxy_text(raw_list))
    else:
        proxies.extend(str(proxy).strip() for proxy in raw_list if str(proxy).strip())

    proxy_file = settings.get("CRAWLER_PROXY_FILE", "")
    if proxy_file:
        path = Path(str(proxy_file))
        if path.exists():
            proxies.extend(_split_proxy_text(path.read_text(encoding="utf-8")))
    return _dedupe(_normalize_proxy(proxy) for proxy in proxies)


def playwright_proxy_config(proxy_url: str | None) -> dict[str, str] | None:
    if not proxy_url:
        return None
    parsed = urlsplit(_normalize_proxy(proxy_url))
    server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    config = {"server": server}
    if parsed.username:
        config["username"] = parsed.username
    if parsed.password:
        config["password"] = parsed.password
    return config


def _split_proxy_text(value: str) -> list[str]:
    proxies: list[str] = []
    for line in value.replace(",", "\n").splitlines():
        proxy = line.strip()
        if not proxy or proxy.startswith("#"):
            continue
        proxies.append(proxy)
    return proxies


def _normalize_proxy(proxy: str) -> str:
    proxy = str(proxy).strip()
    if not proxy:
        return ""
    if "://" not in proxy:
        proxy = "http://" + proxy
    return proxy


def _dedupe(values) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
