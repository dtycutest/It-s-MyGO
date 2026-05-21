"""Compatibility helpers so pure unit tests can run before Scrapy is installed."""

from __future__ import annotations

try:  # pragma: no cover - exercised when Scrapy is installed.
    import scrapy as scrapy  # type: ignore
except Exception:  # pragma: no cover - fallback keeps local tests lightweight.

    class _Field(dict):
        pass

    class _Item(dict):
        pass

    class _Request:
        def __init__(self, url: str, callback=None, meta=None, dont_filter: bool = False, **kwargs):
            self.url = url
            self.callback = callback
            self.meta = meta or {}
            self.dont_filter = dont_filter
            self.kwargs = kwargs

    class _Spider:
        name = "fallback_spider"

        def __init__(self, *args, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class _ScrapyModule:
        Item = _Item
        Field = _Field
        Request = _Request
        Spider = _Spider

    scrapy = _ScrapyModule()
