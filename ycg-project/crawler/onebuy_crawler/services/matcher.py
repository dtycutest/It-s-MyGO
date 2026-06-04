from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Mapping

from .normalizer import compact_fingerprint_text


BRAND_ALIASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("apple", ("apple", "苹果", "iphone", "ipad", "airpods", "macbook")),
    ("huawei", ("huawei", "华为", "honor", "荣耀", "mate", "pura", "nova", "freebuds", "matebook")),
    ("xiaomi", ("xiaomi", "小米", "redmi", "红米", "米家")),
    ("samsung", ("samsung", "三星", "galaxy")),
    ("lenovo", ("lenovo", "联想", "thinkpad", "拯救者")),
    ("logitech", ("logitech", "罗技")),
    ("razer", ("razer", "雷蛇")),
    ("sony", ("sony", "索尼")),
    ("jbl", ("jbl",)),
    ("edifier", ("edifier", "漫步者")),
    ("anker", ("anker", "安克")),
    ("baseus", ("baseus", "倍思")),
    ("aoc", ("aoc",)),
    ("dell", ("dell", "戴尔")),
    ("philips", ("philips", "飞利浦")),
)

PRODUCT_TYPE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("case", ("手机壳", "保护壳", "保护套")),
    ("protector", ("钢化膜", "保护膜", "手机膜")),
    ("cable", ("数据线", "充电线")),
    ("charger", ("充电器", "快充头", "充电头")),
    ("phone", ("手机", "全网通", "双卡", "iphone", "mate", "pura", "redmi", "小米", "galaxy")),
    ("earphone", ("耳机", "蓝牙耳机", "airpods", "freebuds", "耳麦")),
    ("keyboard", ("键盘", "机械键盘", "蓝牙键盘")),
    ("monitor", ("显示器", "显示屏", "电竞屏")),
    ("powerbank", ("充电宝", "移动电源")),
    ("mouse", ("鼠标",)),
)

NOISE_WORDS = (
    "官方",
    "旗舰店",
    "官方旗舰",
    "自营",
    "京东",
    "淘宝",
    "天猫",
    "正品",
    "包邮",
    "现货",
    "新品",
    "全新",
    "国行",
    "原装",
    "授权",
    "直营",
    "店铺",
    "旗舰",
    "百亿补贴",
    "限时",
    "秒杀",
    "优惠",
    "套餐",
    "礼盒",
    "赠品",
    "赠",
    "送",
    "到手价",
    "预售",
    "顺丰",
    "全国联保",
    "以旧换新",
)

GENERIC_MODEL_TOKENS = {
    "3g",
    "4g",
    "5g",
    "6g",
    "wifi",
    "wifi6",
    "typec",
    "usb",
    "usbc",
    "2023",
    "2024",
    "2025",
    "2026",
}

COLOR_ALIASES = {
    "黑色": ("黑色", "雅黑", "亮黑", "曜石黑", "幻夜黑", "深空黑", "午夜色", "星空黑"),
    "白色": ("白色", "雪域白", "陶瓷白", "月光白", "星光色"),
    "蓝色": ("蓝色", "天蓝", "远峰蓝", "海蓝", "冰蓝", "钛蓝", "苍岭绿"),
    "红色": ("红色", "赤色"),
    "绿色": ("绿色", "青色", "墨绿", "薄荷绿", "苍岭绿"),
    "金色": ("金色", "香槟金", "土豪金"),
    "银色": ("银色", "钛银", "原色钛金属", "银白"),
    "灰色": ("灰色", "深空灰", "钛灰", "石墨色"),
    "粉色": ("粉色", "玫瑰金"),
    "紫色": ("紫色", "暗紫", "淡紫"),
}

CONDITION_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("used", ("二手", "二手机", "准新", "准新机", "资源机", "展示机", "官翻", "官换", "翻新", "激活无使用")),
    ("used", ("99新", "95新", "9成新", "九成新", "8成新", "八成新")),
    ("new", ("全新", "原封", "未拆封", "未激活", "新品")),
)


def extract_match_tokens(title: str, specs: Mapping[str, str] | None = None) -> list[str]:
    signature = extract_product_signature(title, specs)
    tokens: list[str] = []
    for key in ("product_type", "brand"):
        value = signature.get(key)
        if value:
            tokens.append(f"{key}:{value}")
    condition = signature.get("condition")
    if condition:
        tokens.append(f"condition:{condition}")
    tokens.extend(f"model:{token}" for token in signature["model_tokens"])
    tokens.extend(f"spec:{token}" for token in signature["spec_tokens"])
    if not signature["model_tokens"] or _needs_conservative_title_token(signature):
        tokens.append(f"title:{signature['fallback_text'][:72]}")
    return list(dict.fromkeys(tokens))


def extract_product_signature(title: str, specs: Mapping[str, str] | None = None) -> dict[str, object]:
    raw_title = unicodedata.normalize("NFKC", str(title or "")).lower()
    raw_specs = unicodedata.normalize("NFKC", " ".join(str(value) for value in (specs or {}).values())).lower()
    raw_combined = f"{raw_title} {raw_specs}".strip()
    text = _normalize_match_text(title)
    spec_text = _normalize_match_text(" ".join(str(value) for value in (specs or {}).values()))
    combined = f"{text} {spec_text}".strip()
    compact = compact_fingerprint_text(combined)

    brand = _extract_brand(combined)
    product_type = _extract_product_type(combined)
    condition = _extract_condition(raw_combined)
    model_tokens = _extract_model_tokens(combined)
    spec_tokens = _extract_spec_tokens(combined)
    fallback_text = _fallback_text(compact)

    return {
        "brand": brand,
        "product_type": product_type,
        "condition": condition,
        "model_tokens": model_tokens,
        "spec_tokens": spec_tokens,
        "fallback_text": fallback_text,
    }


def build_match_fingerprint(title: str, specs: Mapping[str, str] | None = None) -> str:
    tokens = "|".join(extract_match_tokens(title, specs))
    digest = hashlib.sha1(tokens.encode("utf-8")).hexdigest()[:16]
    return f"match:{digest}"


def likely_same_product(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return build_match_fingerprint(str(left.get("title", "")), left.get("specs") or {}) == build_match_fingerprint(
        str(right.get("title", "")), right.get("specs") or {}
    )


def _normalize_match_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    text = re.sub(r"[\u200b\xa0]+", " ", text)
    text = re.sub(r"[【】\[\]（）(){}<>「」『』,，;；:：/|]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    for word in NOISE_WORDS:
        text = text.replace(word.lower(), " ")
    return re.sub(r"\s+", " ", text).strip()


def _extract_brand(text: str) -> str:
    compact = re.sub(r"\s+", "", text)
    for canonical, aliases in BRAND_ALIASES:
        for alias in aliases:
            alias_lower = alias.lower()
            if re.search(rf"(?<![a-z0-9]){re.escape(alias_lower)}(?![a-z0-9])", text) or alias_lower in compact:
                return canonical
    return ""


def _extract_product_type(text: str) -> str:
    compact = re.sub(r"\s+", "", text)
    for product_type, aliases in PRODUCT_TYPE_PATTERNS:
        if any(alias.lower() in compact for alias in aliases):
            return product_type
    return ""


def _extract_condition(text: str) -> str:
    compact = re.sub(r"\s+", "", text)
    for condition, aliases in CONDITION_PATTERNS:
        if any(alias.lower() in compact for alias in aliases):
            return condition
    return ""


def _extract_model_tokens(text: str) -> list[str]:
    patterns = (
        r"iphone\s*\d{1,2}(?:\s*(?:pro|max|plus|mini))*",
        r"airpods\s*(?:pro|max)?\s*(?:\d|一代|二代|三代|第[一二三四1234]代)?",
        r"mate\s*\d{1,3}(?:\s*(?:pro|rs|\+|x))*",
        r"pura\s*\d{1,3}(?:\s*(?:pro|ultra|\+))*",
        r"nova\s*\d{1,3}(?:\s*(?:pro|ultra|\+))*",
        r"freebuds\s*[a-z]*\s*\d*",
        r"redmi\s*(?:note\s*)?[a-z]?\d{1,3}(?:\s*(?:pro|turbo|max|ultra|\+|至尊版|至尊|冠军版))*",
        r"小米\s*\d{1,3}(?:\s*(?:pro|ultra|\+|至尊版|至尊|冠军版))*",
        r"galaxy\s*[a-z]\d{1,3}(?:\s*(?:ultra|plus|\+))*",
        r"[a-z]{1,8}\s*[-_]?\s*[a-z]?\d{2,5}[a-z0-9-]*",
    )
    tokens: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            token = _strip_brand_prefix(_compact_token(match.group(0)))
            if _valid_model_token(token):
                tokens.append(token)
    return list(dict.fromkeys(tokens))[:4]


def _extract_spec_tokens(text: str) -> list[str]:
    tokens: list[str] = []

    for match in re.finditer(r"(\d{1,2})\s*(?:gb|g)\s*\+\s*(\d{2,4})\s*(?:gb|g|tb|t)?", text, flags=re.I):
        tokens.append(f"{match.group(1)}gb+{_normalize_capacity(match.group(2), 'gb')}")

    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(tb|t|gb|g)\b", text, flags=re.I):
        capacity = _normalize_capacity(match.group(1), match.group(2))
        if capacity not in GENERIC_MODEL_TOKENS:
            tokens.append(capacity)

    for canonical, aliases in COLOR_ALIASES.items():
        if any(alias.lower() in text for alias in aliases):
            tokens.append(canonical)
            break

    for match in re.finditer(r"(\d{2,3})\s*键", text):
        tokens.append(f"{match.group(1)}key")
    for edition in ("至尊版", "至尊", "冠军版", "标准版", "青春版", "活力版"):
        if edition in text:
            tokens.append(edition)
    for switch in ("青轴", "茶轴", "红轴", "黑轴", "银轴", "静音轴", "矮轴"):
        if switch in text:
            tokens.append(switch)
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:英寸|寸|inch)", text, flags=re.I):
        tokens.append(f"{match.group(1)}inch")
    for match in re.finditer(r"(\d{3,5})\s*(?:mah|毫安)", text, flags=re.I):
        tokens.append(f"{match.group(1)}mah")
    for match in re.finditer(r"(\d{2,4})\s*w\b", text, flags=re.I):
        tokens.append(f"{match.group(1)}w")

    if "type c" in text or "type-c" in text or "usb c" in text or "usb-c" in text:
        tokens.append("usbc")
    if "lightning" in text:
        tokens.append("lightning")

    return list(dict.fromkeys(tokens))[:8]


def _needs_conservative_title_token(signature: Mapping[str, object]) -> bool:
    product_type = signature.get("product_type")
    spec_tokens = [str(token) for token in signature.get("spec_tokens") or []]
    if product_type == "phone":
        return not any(re.search(r"\d+(?:gb|tb)|\d+gb\+\d+gb", token) for token in spec_tokens)
    if product_type == "monitor":
        return not any(token.endswith("inch") for token in spec_tokens)
    if product_type == "powerbank":
        return not any(token.endswith("mah") or token.endswith("w") for token in spec_tokens)
    return False


def _normalize_capacity(number: str, unit: str) -> str:
    unit = unit.lower()
    number = number.rstrip(".0") if "." in number else number
    if unit == "t":
        unit = "tb"
    if unit == "g":
        unit = "gb"
    return f"{number}{unit}"


def _valid_model_token(token: str) -> bool:
    if not token or token in GENERIC_MODEL_TOKENS:
        return False
    if re.fullmatch(r"\d+", token):
        return False
    if re.fullmatch(r"\d+(?:gb|g|tb|t|w|mah)", token):
        return False
    return True


def _compact_token(value: str) -> str:
    return re.sub(r"[\s_-]+", "", value.lower())


def _strip_brand_prefix(token: str) -> str:
    for _canonical, aliases in BRAND_ALIASES:
        for alias in aliases:
            alias_token = _compact_token(alias)
            if token.startswith(alias_token) and len(token) > len(alias_token) + 1:
                return token[len(alias_token) :]
    return token


def _fallback_text(compact_text: str) -> str:
    text = compact_text
    for word in NOISE_WORDS:
        text = text.replace(word.lower(), "")
    return text
