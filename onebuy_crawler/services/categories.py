from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from onebuy_crawler.constants import DEFAULT_CATEGORY_ID, DEFAULT_CATEGORY_NAME
from onebuy_crawler.services.normalizer import clean_text, normalize_title


GENERIC_CATEGORY_TEXT = {"", "未分类", "京东商品", "淘宝商品", "商品", "其他"}


@dataclass(frozen=True)
class Category:
    category_id: int
    category_name: str


CATEGORY_RULES: tuple[tuple[int, str, tuple[str, ...]], ...] = (
    (110, "手机-配件", ("手机壳", "保护壳", "保护套", "钢化膜", "手机膜", "保护膜")),
    (320, "数码配件-移动电源", ("充电宝", "移动电源", "毫安", "mah")),
    (310, "数码配件-耳机音频", ("蓝牙耳机", "耳机", "耳麦", "airpods", "freebuds", "enco", "buds")),
    (210, "电脑办公-键盘鼠标", ("机械键盘", "蓝牙键盘", "键盘", "鼠标", "青轴", "茶轴", "红轴")),
    (
        100,
        "手机-智能手机",
        ("iphone", "手机", "全网通", "双卡", "华为", "小米", "redmi", "红米", "荣耀", "oppo", "vivo", "galaxy"),
    ),
    (330, "电脑办公-显示器", ("显示器", "显示屏", "电竞屏", "英寸", "inch")),
    (300, "数码配件-充电器线材", ("充电器", "充电头", "快充头", "数据线", "充电线", "type-c", "type c", "lightning")),
)


def infer_category(title: Any = "", category_text: Any = "", keyword: Any = "") -> Category:
    explicit = clean_text(category_text)
    if explicit and explicit not in GENERIC_CATEGORY_TEXT:
        return Category(_category_id_for_name(explicit), explicit)

    title_category = _infer_from_text(title)
    if title_category:
        return title_category

    text = normalize_title(" ".join(clean_text(value) for value in (category_text, keyword) if clean_text(value))).lower()
    category = _infer_from_normalized_text(text)
    if category:
        return category
    return Category(DEFAULT_CATEGORY_ID, DEFAULT_CATEGORY_NAME)


def _infer_from_text(value: Any) -> Category | None:
    text = normalize_title(clean_text(value)).lower()
    return _infer_from_normalized_text(text)


def _infer_from_normalized_text(text: str) -> Category | None:
    if not text:
        return None
    compact = re.sub(r"\s+", "", text)
    for category_id, category_name, keywords in CATEGORY_RULES:
        if any(keyword.lower() in text or keyword.lower() in compact for keyword in keywords):
            return Category(category_id, category_name)
    return None


def _category_id_for_name(category_name: str) -> int:
    for category_id, rule_name, _keywords in CATEGORY_RULES:
        if category_name == rule_name or category_name.startswith(rule_name.split("-")[0]):
            return category_id
    return DEFAULT_CATEGORY_ID
