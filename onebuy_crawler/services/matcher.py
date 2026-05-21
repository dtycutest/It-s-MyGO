from __future__ import annotations

import hashlib
import re
from typing import Mapping

from .normalizer import compact_fingerprint_text


MODEL_RE = re.compile(r"([a-zA-Z]+[\w-]*\s?\d+(?:\s?(?:pro|max|plus|ultra|mini|air|anc))?)", re.I)
CAPACITY_RE = re.compile(r"(\d+\s?(?:gb|tb|g|t))", re.I)
COLOR_RE = re.compile(r"(黑色|白色|蓝色|红色|绿色|金色|银色|灰色|粉色|紫色|深空黑|远峰蓝)")
GENERIC_MODEL_TOKENS = {"4g", "5g", "6g", "wifi6", "typec"}


def extract_match_tokens(title: str, specs: Mapping[str, str] | None = None) -> list[str]:
    normalized = compact_fingerprint_text(title)
    tokens: list[str] = []

    for match in MODEL_RE.finditer(title):
        token = match.group(1).replace(" ", "").lower()
        if token and token not in GENERIC_MODEL_TOKENS:
            tokens.append(token)

    for regex in (CAPACITY_RE, COLOR_RE):
        for match in regex.finditer(title):
            token = match.group(1).replace(" ", "").lower()
            if token and token not in GENERIC_MODEL_TOKENS:
                tokens.append(token)

    if specs:
        for key in sorted(specs):
            value = compact_fingerprint_text(specs[key])
            if value:
                tokens.append(value)

    if not tokens:
        tokens.append(normalized[:64])
    return list(dict.fromkeys(tokens))


def build_match_fingerprint(title: str, specs: Mapping[str, str] | None = None) -> str:
    tokens = "|".join(extract_match_tokens(title, specs))
    digest = hashlib.sha1(tokens.encode("utf-8")).hexdigest()[:16]
    return f"match:{digest}"


def likely_same_product(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return build_match_fingerprint(str(left.get("title", "")), left.get("specs") or {}) == build_match_fingerprint(
        str(right.get("title", "")), right.get("specs") or {}
    )
