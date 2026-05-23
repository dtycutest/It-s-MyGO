from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from onebuy_crawler.item_adapter import ItemAdapter


class ImageCachePipeline:
    """Optionally cache product images and rewrite image_url to a public static URL."""

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.store = Path(settings.get("CRAWLER_IMAGE_STORE", "output/product_images"))
        self.public_base_url = str(settings.get("CRAWLER_IMAGE_PUBLIC_BASE_URL", "") or "").rstrip("/")
        self.timeout = settings.getint("CRAWLER_IMAGE_TIMEOUT", 10)
        self.store.mkdir(parents=True, exist_ok=True)

    def process_item(self, item):
        adapter = ItemAdapter(item)
        if adapter.get("parse_status") and adapter.get("parse_status") != "ok":
            return item

        image_url = str(adapter.get("image_url") or "").strip()
        if not _looks_like_remote_image(image_url):
            return item

        rel_path = self._relative_path(adapter, image_url)
        target = self.store / rel_path
        if not target.exists():
            try:
                self._download(image_url, target)
            except OSError:
                return item

        if self.public_base_url:
            public_url = f"{self.public_base_url}/{rel_path.as_posix()}"
            adapter["image_url"] = public_url
            adapter["images"] = [public_url]
        return item

    def _relative_path(self, adapter: ItemAdapter, image_url: str) -> Path:
        platform = _safe_part(adapter.get("platform_code") or "platform")
        sku = _safe_part(adapter.get("source_sku_id") or "")
        if not sku:
            sku = hashlib.sha1(image_url.encode("utf-8")).hexdigest()[:20]
        return Path(platform) / f"{sku}{_image_extension(image_url)}"

    def _download(self, image_url: str, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        request = Request(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
                "Referer": "https://www.jd.com/",
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type.lower() and not _image_extension(image_url):
                return
            target.write_bytes(response.read())


def _looks_like_remote_image(value: str) -> bool:
    if not value or value.startswith("data:"):
        return False
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False
    return bool(parsed.netloc and parsed.path.strip("/"))


def _image_extension(image_url: str) -> str:
    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return suffix
    return ".jpg"


def _safe_part(value) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[^0-9a-zA-Z_-]+", "_", text).strip("_")[:80]
