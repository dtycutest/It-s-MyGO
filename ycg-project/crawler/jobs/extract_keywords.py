"""从已有商品标题中提取关键词，生成扩展关键词列表用于批量爬取."""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.db import mysql_connection


SKIP_WORDS = {
    "商品", "产品", "购买", "正品", "包邮", "现货", "全新", "官方", "旗舰",
    "自营", "京东", "淘宝", "天猫", "店铺", "旗舰店", "全国", "联保",
    "以旧换新", "百亿补贴", "限时", "秒杀", "优惠", "套餐", "礼盒",
    "赠品", "顺丰", "新品", "折扣", "原装", "国行", "授权", "直营",
    "到手价", "预售", "专用", "适用", "通用", "推荐", "热销", "爆款",
    "高品质", "超值", "特价", "促销", "批发", "一件", "代发",
    "男", "女", "学生", "儿童", "成人", "老人",
    "颜色", "款式", "型号", "规格", "尺寸", "重量", "材质",
    "黑色", "白色", "红色", "蓝色", "绿色", "黄色",
    "个", "件", "套", "箱", "盒", "包", "瓶", "袋", "支", "台",
}


def extract_keywords_from_titles(settings, min_count: int = 1, max_keywords: int = 100) -> list[tuple[str, int]]:
    counter: Counter = Counter()
    try:
        with mysql_connection(settings) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT title FROM products WHERE title IS NOT NULL AND title <> ''")
                rows = cursor.fetchall()
                for (title,) in rows:
                    words = re.findall(r"[\u4e00-\u9fff]{2,6}", title)
                    for w in words:
                        if w not in SKIP_WORDS:
                            counter[w] += 1
    except Exception as e:
        print(f"MySQL read failed, using empty result: {e}")

    return counter.most_common(max_keywords)


def extract_brand_keywords(settings) -> list[str]:
    brands: list[str] = []
    try:
        with mysql_connection(settings) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT DISTINCT seller_name FROM platform_offers "
                    "WHERE seller_name IS NOT NULL AND seller_name <> '' "
                    "AND seller_name NOT IN ('未分类', '其他', '课程演示数据')"
                )
                for (name,) in cursor.fetchall():
                    cleaned = name.strip()
                    if 2 <= len(cleaned) <= 8 and cleaned not in SKIP_WORDS:
                        brands.append(cleaned)
    except Exception as e:
        print(f"MySQL read failed: {e}")
    return list(dict.fromkeys(brands))[:30]


def main() -> None:
    parser = argparse.ArgumentParser(description="从已有商品标题中提取关键词")
    parser.add_argument("--output", default="data/generated_keywords.txt", help="输出文件路径")
    parser.add_argument("--max-keywords", type=int, default=80, help="最多提取关键词数")
    parser.add_argument("--min-count", type=int, default=1, help="最小出现次数")
    args = parser.parse_args()

    settings = get_project_settings()
    keywords = extract_keywords_from_titles(settings, min_count=args.min_count, max_keywords=args.max_keywords)
    brands = extract_brand_keywords(settings)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# 自动生成的关键词 - 来自已有商品标题")
    lines.append(f"# 共 {len(keywords)} 个关键词, {len(brands)} 个品牌")
    lines.append("")

    lines.append("# === 高频关键词 ===")
    for word, count in keywords:
        lines.append(f"{word}  # count={count}")

    if brands:
        lines.append("")
        lines.append("# === 品牌关键词 ===")
        for brand in brands:
            lines.append(brand)

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"generated {len(keywords)} keywords + {len(brands)} brands -> {output_path}")
    print(f"top 20: {', '.join(word for word, _ in keywords[:20])}")


if __name__ == "__main__":
    main()