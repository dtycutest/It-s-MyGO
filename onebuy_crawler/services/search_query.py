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
    return " AND ".join([f"{column} LIKE %s"] * len(tokens)), [f"%{token}%" for token in tokens]
