from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

BOT_NAME = "onebuy_crawler"

SPIDER_MODULES = ["onebuy_crawler.spiders"]
NEWSPIDER_MODULE = "onebuy_crawler.spiders"

ROBOTSTXT_OBEY = os.getenv("CRAWLER_OBEY_ROBOTS", "1").lower() not in {"0", "false", "no"}
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = float(os.getenv("CRAWLER_DOWNLOAD_DELAY", "2.0"))
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_TIMEOUT = 20
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
LOG_LEVEL = os.getenv("CRAWLER_LOG_LEVEL", "INFO")

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
}

USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]

RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [408, 429, 500, 502, 503, 504, 522, 524]

DOWNLOADER_MIDDLEWARES = {
    "onebuy_crawler.middlewares.headers.RandomUserAgentMiddleware": 410,
    "onebuy_crawler.middlewares.proxy.ProxyMiddleware": 420,
    "onebuy_crawler.middlewares.retry.PoliteRetryMiddleware": 540,
}

if os.getenv("CRAWLER_USE_COOKIES", "0").lower() in {"1", "true", "yes"}:
    DOWNLOADER_MIDDLEWARES["onebuy_crawler.middlewares.cookies.ManualCookieMiddleware"] = 415

ITEM_PIPELINES = {
    "onebuy_crawler.pipelines.cleaning.CleaningPipeline": 100,
    "onebuy_crawler.pipelines.dedup.DedupPipeline": 200,
    "onebuy_crawler.pipelines.raw_log.RawLogPipeline": 300,
}

if os.getenv("CRAWLER_CACHE_IMAGES", "0").lower() in {"1", "true", "yes"}:
    ITEM_PIPELINES["onebuy_crawler.pipelines.image_cache.ImageCachePipeline"] = 250

if os.getenv("CRAWLER_ENABLE_MYSQL", "0") == "1":
    ITEM_PIPELINES["onebuy_crawler.pipelines.mysql.MySqlPipeline"] = 400

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "onebuy")
MYSQL_CHARSET = "utf8mb4"

CRAWLER_PROXY_LIST = [
    proxy.strip()
    for proxy in os.getenv("CRAWLER_PROXY_LIST", "").split(",")
    if proxy.strip()
]
CRAWLER_PROXY_FILE = os.getenv("CRAWLER_PROXY_FILE", "")
CRAWLER_PROXY_MAX_FAILS = int(os.getenv("CRAWLER_PROXY_MAX_FAILS", "3"))
CRAWLER_PROXY_COOLDOWN_SECONDS = int(os.getenv("CRAWLER_PROXY_COOLDOWN_SECONDS", "300"))
CRAWLER_PROXY_REQUIRED = os.getenv("CRAWLER_PROXY_REQUIRED", "0").lower() in {"1", "true", "yes"}
CRAWLER_IMAGE_STORE = os.getenv("CRAWLER_IMAGE_STORE", "output/product_images")
CRAWLER_IMAGE_PUBLIC_BASE_URL = os.getenv("CRAWLER_IMAGE_PUBLIC_BASE_URL", "")
CRAWLER_IMAGE_TIMEOUT = int(os.getenv("CRAWLER_IMAGE_TIMEOUT", "10"))

JD_COOKIE = os.getenv("JD_COOKIE", "")
TAOBAO_COOKIE = os.getenv("TAOBAO_COOKIE", "")
JD_COOKIE_FILE = os.getenv("JD_COOKIE_FILE", "")
TAOBAO_COOKIE_FILE = os.getenv("TAOBAO_COOKIE_FILE", "")

FEEDS = {
    "output/%(name)s_%(time)s.jsonl": {
        "format": "jsonlines",
        "encoding": "utf8",
        "overwrite": False,
    }
}
