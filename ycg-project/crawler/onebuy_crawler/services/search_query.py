from __future__ import annotations

import re

from onebuy_crawler.services.normalizer import clean_text


def title_keyword_clause(keyword: str, column: str = "p.title") -> tuple[str, list[str]]:
    keyword = clean_text(keyword)
    tokens = [token for token in re.split(r"\s+", keyword) if token]
    if not tokens and keyword:
        tokens = [keyword]
    if not tokens:
        return "1=1", []
    clauses = []
    params: list[str] = []
    for token in tokens:
        alternatives = _token_alternatives(token)
        if len(alternatives) == 1:
            clauses.append(f"{column} LIKE %s")
        else:
            clauses.append("(" + " OR ".join([f"{column} LIKE %s"] * len(alternatives)) + ")")
        params.extend(f"%{alternative}%" for alternative in alternatives)
    return " AND ".join(clauses), params


def _token_alternatives(token: str) -> list[str]:
    brand_aliases = {
        "apple": ["Apple", "苹果"],
        "iphone": ["iPhone", "苹果"],
        "huawei": ["HUAWEI", "华为"],
        "logitech": ["Logitech", "罗技"],
        "xiaomi": ["Xiaomi", "小米"],
        "mi": ["MI", "小米"],
    }
    alias_values = brand_aliases.get(token.lower())
    if alias_values:
        return alias_values

    match = re.fullmatch(r"(\d+)\s*(gb|g|tb|t)", token, flags=re.I)
    if not match:
        return [token]
    number, unit = match.groups()
    unit = unit.lower()
    if unit in {"gb", "g"}:
        return [f"{number}GB", f"{number}G"]
    return [f"{number}TB", f"{number}T"]
