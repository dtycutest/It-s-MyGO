from __future__ import annotations

PLATFORMS = {
    "taobao": {"platform_id": 1, "platform_name": "淘宝", "host": "s.taobao.com"},
    "jingdong": {"platform_id": 2, "platform_name": "京东", "host": "search.jd.com"},
    "pinduoduo": {"platform_id": 3, "platform_name": "拼多多", "host": "mobile.yangkeduo.com"},
    "amazon": {"platform_id": 4, "platform_name": "亚马逊", "host": "www.amazon.cn"},
    "other": {"platform_id": 5, "platform_name": "其他", "host": ""},
}

DEFAULT_CATEGORY_ID = 0
DEFAULT_CATEGORY_NAME = "未分类"

ANTI_BOT_MARKERS = (
    "验证码",
    "安全验证",
    "滑块",
    "captcha",
    "verify",
    "访问过于频繁",
    "risk_handler",
    "baxia",
)
