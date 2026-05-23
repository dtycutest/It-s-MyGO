from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from scrapy.utils.project import get_project_settings

from onebuy_crawler.item_adapter import ItemAdapter
from onebuy_crawler.services.browser_extractors import extract_from_dom
from onebuy_crawler.services.copied_search_html import extract_jd_rows_from_copied_html
from onebuy_crawler.services.pipeline_runner import PipelineRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Import products from manually copied JD search-result HTML.")
    parser.add_argument("--keyword", required=True, help="Exact product keyword used for filtering and tagging.")
    parser.add_argument("--input", default="data/jd_urls.txt", help="UTF-8 file containing copied JD search HTML.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output-file", default="", help="Optional JSONL export path.")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        raise SystemExit(f"input file not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")
    rows = extract_jd_rows_from_copied_html(text, max_rows=max(args.limit * 5, args.limit))
    items = extract_from_dom("jd", rows, args.keyword)
    items = items[: args.limit]

    runner = PipelineRunner(get_project_settings())
    output_path = Path(args.output_file) if args.output_file else None
    imported = 0
    for item in items:
        processed = runner.process(item)
        imported += 1
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(dict(ItemAdapter(processed)), ensure_ascii=False, default=str) + "\n")

    mysql_enabled = os.getenv("CRAWLER_ENABLE_MYSQL", "0") == "1"
    print(
        f"copied search HTML import finished: keyword={args.keyword}, "
        f"rows={len(rows)}, matched={len(items)}, imported={imported}, mysql={int(mysql_enabled)}"
    )


if __name__ == "__main__":
    main()
