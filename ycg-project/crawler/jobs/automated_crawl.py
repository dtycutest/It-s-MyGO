"""全自动爬虫编排器 — 零手动干预的大规模多平台商品数据采集.

Usage:
  # 使用内置关键词库，全自动完成一次完整采集
  python -m jobs.automated_crawl

  # 从文件加载关键词
  python -m jobs.automated_crawl --keyword-file data/keywords_extended.txt

  # 守护进程模式：持续运行，定期采集
  python -m jobs.automated_crawl --daemon --interval-hours 6

  # 仅初始化/验证环境，不实际采集（CI/预检用）
  python -m jobs.automated_crawl --check-only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from scrapy.utils.project import get_project_settings

from onebuy_crawler.services.crawl_tasks import enqueue_task, PLATFORM_ALIASES
from onebuy_crawler.services.db import mysql_connection


BUILTIN_KEYWORDS = [
    "iPhone 15", "iPhone 14", "华为Mate 60", "小米14", "Redmi K70",
    "蓝牙耳机", "降噪耳机", "运动耳机", "无线耳机",
    "充电宝", "移动电源", "快充充电宝",
    "机械键盘", "无线鼠标", "游戏鼠标", "蓝牙键盘",
    "显示器", "4K显示器", "办公显示器",
    "抽纸", "卷纸", "湿巾",
    "洗衣液", "洗衣凝珠", "洗发水", "沐浴露", "牙膏", "电动牙刷",
    "速溶咖啡", "可口可乐", "气泡水",
    "中性笔", "笔记本",
    "Type-C数据线", "氮化镓充电器", "手机壳", "钢化膜",
]

OUTPUT_DIRS = [
    Path("output/browser_capture"),
    Path("output/browser_debug"),
    Path("output/product_images"),
]

MAX_DEBUG_AGE_DAYS = 7
MAX_DEBUG_SIZE_MB = 200
MAX_EXPORT_AGE_DAYS = 3


def main() -> None:
    parser = argparse.ArgumentParser(
        description="全自动爬虫编排器 — 零手动干预",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m jobs.automated_crawl                                        # 使用内置关键词，一次性采集
  python -m jobs.automated_crawl --keyword-file data/keywords_extended.txt  # 从文件加载
  python -m jobs.automated_crawl --daemon --interval-hours 6            # 守护进程模式
  python -m jobs.automated_crawl --check-only                           # 仅环境检查
        """,
    )
    parser.add_argument("--keyword", action="append", default=[], help="关键词，可多次使用")
    parser.add_argument("--keyword-file", default="", help="UTF-8 关键词文件")
    parser.add_argument("--use-builtin-keywords", action="store_true", default=True,
                        help="使用内置关键词库 (默认)")
    parser.add_argument("--no-builtin-keywords", action="store_true",
                        help="不使用内置关键词库")
    parser.add_argument("--platform", default="all", choices=["jd", "jingdong", "taobao", "all"])
    parser.add_argument("--rounds", type=int, default=1, help="爬取轮数")
    parser.add_argument("--task-limit", type=int, default=8,
                        help="每轮最多处理的任务数 (默认8)")
    parser.add_argument("--pages", type=int, default=1, help="每个任务爬取页数")
    parser.add_argument("--item-limit", type=int, default=20, help="每个任务最大商品数")
    parser.add_argument("--typing-delay-ms", type=int, default=80)
    parser.add_argument("--pre-search-delay-ms", type=int, default=600)
    parser.add_argument("--post-search-delay-ms", type=int, default=1200)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--failed-delay-minutes", type=int, default=10)
    parser.add_argument("--blocked-delay-minutes", type=int, default=45)
    parser.add_argument("--headless", action="store_true", default=True,
                        help="无头模式 (默认开启)")
    parser.add_argument("--no-headless", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--skip-init-schema", action="store_true")
    parser.add_argument("--refresh-prices", action="store_true",
                        help="采集后刷新已有商品价格")
    parser.add_argument("--expand-keywords", action="store_true", default=True,
                        help="从已有商品标题自动扩展关键词 (默认开启)")
    parser.add_argument("--no-expand-keywords", action="store_true")
    parser.add_argument("--keyword-expand-count", type=int, default=30,
                        help="自动扩展关键词上限")
    parser.add_argument("--cleanup", action="store_true", default=True,
                        help="采集后清理过期文件 (默认开启)")
    parser.add_argument("--no-cleanup", action="store_true")
    parser.add_argument("--daemon", action="store_true",
                        help="守护进程模式：持续运行，定期采集")
    parser.add_argument("--interval-hours", type=int, default=6,
                        help="守护进程采集间隔(小时)")
    parser.add_argument("--check-only", action="store_true",
                        help="仅检查环境，不执行采集")
    args = parser.parse_args()

    if args.check_only:
        _check_environment()
        return

    keywords = _collect_keywords(args)
    print(f"loaded {len(keywords)} keywords for {args.platform} platform(s)")

    if args.daemon:
        _run_daemon(args, keywords)
    else:
        _run_once(args, keywords)


def _check_environment() -> None:
    errors: list[str] = []
    warnings: list[str] = []

    print("=" * 50)
    print("环境检查")
    print("=" * 50)

    try:
        import scrapy
        print(f"  Scrapy: {scrapy.__version__}")
    except ImportError:
        errors.append("Scrapy 未安装: pip install scrapy")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        print("  Playwright + Chromium: OK")
    except ImportError:
        warnings.append("Playwright 未安装 → 运行: pip install playwright && playwright install chromium")
    except Exception as e:
        warnings.append(f"Playwright/Chromium 异常: {e}")

    try:
        import pymysql
        print("  PyMySQL: OK")
    except ImportError:
        errors.append("PyMySQL 未安装: pip install pymysql")

    settings = get_project_settings()
    try:
        with mysql_connection(settings) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM crawl_tasks")
                count = cursor.fetchone()[0]
            print(f"  MySQL ({settings.get('MYSQL_DATABASE')}): OK, crawl_tasks={count}")
    except Exception as e:
        warnings.append(f"MySQL 连接失败: {e}")

    for dir_path in OUTPUT_DIRS:
        dir_path.mkdir(parents=True, exist_ok=True)

    if errors:
        print(f"\n错误 ({len(errors)}):")
        for e in errors:
            print(f"  ❌ {e}")
    if warnings:
        print(f"\n警告 ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠️ {w}")
    if not errors and not warnings:
        print("\n  所有检查通过")


def _collect_keywords(args) -> list[str]:
    keywords: list[str] = []
    if not args.no_builtin_keywords and args.use_builtin_keywords:
        keywords.extend(BUILTIN_KEYWORDS)
    keywords.extend(args.keyword)
    if args.keyword_file:
        path = Path(args.keyword_file)
        if path.exists():
            keywords.extend(
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            )
    return list(dict.fromkeys(keywords))


def _run_once(args, keywords: list[str]) -> None:
    settings = get_project_settings()
    platforms = _resolve_platforms(args.platform)

    _print_banner("1. 入队任务")
    for keyword in keywords:
        for platform in platforms:
            enqueue_task(settings, keyword, platform, force=False)
    print(f"  {len(keywords)} keywords × {len(platforms)} platforms → {len(keywords) * len(platforms)} tasks enqueued")

    _print_banner("2. 执行采集")
    for round_no in range(1, max(1, args.rounds) + 1):
        print(f"  round {round_no}/{max(1, args.rounds)}")
        command = _build_run_command(args, keywords)
        result = subprocess.run(command, text=True)
        if result.returncode != 0:
            print(f"  round {round_no} exited with code {result.returncode}")
        if round_no < max(1, args.rounds):
            wait = 30
            print(f"  waiting {wait}s before next round...")
            time.sleep(wait)

    tasks_done = _count_tasks(settings, "success")
    tasks_failed = _count_tasks(settings, "failed")
    tasks_pending = _count_tasks(settings, "pending")
    print(f"\n  task summary: success={tasks_done}, failed={tasks_failed}, pending={tasks_pending}")

    if args.refresh_prices:
        _print_banner("3. 刷新价格")
        subprocess.run([sys.executable, "-m", "jobs.refresh_prices", "--limit", "100"], text=True)

    if not args.no_expand_keywords:
        _print_banner("4. 扩展关键词")
        _expand_keywords_from_db(settings, args.keyword_expand_count)

    if not args.no_cleanup:
        _print_banner("5. 清理磁盘")
        _cleanup_output_dirs()

    _print_banner("完成")
    print(f"  总采集任务: {tasks_done + tasks_failed}, 成功: {tasks_done}, 失败: {tasks_failed}")


def _run_daemon(args, keywords: list[str]) -> None:
    print(f"守护进程模式启动, 间隔 {args.interval_hours} 小时, Ctrl+C 停止")
    while True:
        round_start = time.time()
        _run_once(args, keywords)
        elapsed = time.time() - round_start
        sleep_seconds = max(60, args.interval_hours * 3600 - elapsed)
        next_run = datetime.now() + timedelta(seconds=sleep_seconds)
        print(f"\n  下次采集: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            time.sleep(sleep_seconds)
        except KeyboardInterrupt:
            print("\n  收到停止信号, 守护进程退出")
            break


def _build_run_command(args, keywords: list[str]) -> list[str]:
    command = [
        sys.executable, "-m", "jobs.run_crawl_tasks",
        "--limit", str(args.task_limit),
        "--platform", args.platform,
        "--pages", str(args.pages),
        "--item-limit", str(args.item_limit),
        "--typing-delay-ms", str(args.typing_delay_ms),
        "--pre-search-delay-ms", str(args.pre_search_delay_ms),
        "--post-search-delay-ms", str(args.post_search_delay_ms),
        "--max-retries", str(args.max_retries),
        "--failed-delay-minutes", str(args.failed_delay_minutes),
        "--blocked-delay-minutes", str(args.blocked_delay_minutes),
    ]
    if not args.no_headless:
        command.append("--headless")
    for keyword in keywords:
        command.extend(["--keyword", keyword])
    return command


def _resolve_platforms(platform: str) -> list[str]:
    if platform == "all":
        return ["jingdong", "taobao"]
    alias = PLATFORM_ALIASES.get(platform.strip().lower())
    return [alias] if alias else ["jingdong"]


def _count_tasks(settings, status: str) -> int:
    try:
        with mysql_connection(settings) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM crawl_tasks WHERE status = %s AND updated_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)",
                    (status,),
                )
                return cursor.fetchone()[0]
    except Exception:
        return 0


def _expand_keywords_from_db(settings, max_keywords: int) -> None:
    skip_words = {
        "商品", "产品", "购买", "正品", "包邮", "现货", "全新", "官方", "旗舰",
        "自营", "京东", "淘宝", "天猫", "店铺", "旗舰店", "全国", "联保",
        "以旧换新", "百亿补贴", "限时", "秒杀", "优惠", "套餐", "礼盒", "赠品",
        "顺丰", "新品", "折扣", "原装", "国行", "授权", "直营", "到手价", "预售",
        "专用", "适用", "通用", "推荐", "热销", "爆款",
        "男", "女", "学生", "儿童", "成人", "老人",
        "颜色", "款式", "型号", "规格", "尺寸",
        "个", "件", "套", "箱", "盒", "包", "瓶", "袋", "支", "台",
    }

    counter: Counter = Counter()
    try:
        with mysql_connection(settings) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT DISTINCT keyword FROM crawl_tasks WHERE status = 'success'"
                )
                for (kw,) in cursor.fetchall():
                    counter[str(kw)] -= 99

                cursor.execute(
                    "SELECT title FROM products WHERE updated_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
                )
                for (title,) in cursor.fetchall():
                    words = re.findall(r"[\u4e00-\u9fff]{2,4}", title or "")
                    for w in words:
                        if w not in skip_words:
                            counter[w] += 1
    except Exception as e:
        print(f"  keyword expansion skipped: {e}")
        return

    new_keywords = [kw for kw, cnt in counter.most_common() if cnt >= 0][:max_keywords]
    if not new_keywords:
        print("  no new keywords found")
        return

    for kw in new_keywords:
        for platform_code in ["jingdong", "taobao"]:
            enqueue_task(settings, kw, platform_code, force=False)
    print(f"  expanded {len(new_keywords)} keywords: {', '.join(new_keywords[:10])}...")


def _cleanup_output_dirs() -> None:
    now = datetime.now()
    cleaned = 0

    for base_dir in OUTPUT_DIRS:
        if not base_dir.exists():
            continue
        cutoff_debug = now - timedelta(days=MAX_DEBUG_AGE_DAYS)
        cutoff_export = now - timedelta(days=MAX_EXPORT_AGE_DAYS)

        for file_path in base_dir.iterdir():
            if not file_path.is_file():
                continue
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_path.suffix in (".html", ".png"):
                    if mtime < cutoff_debug:
                        file_path.unlink()
                        cleaned += 1
                elif file_path.suffix == ".jsonl":
                    if mtime < cutoff_export:
                        file_path.unlink()
                        cleaned += 1
            except OSError:
                pass

        total_size = sum(f.stat().st_size for f in base_dir.iterdir() if f.is_file())
        if total_size > MAX_DEBUG_SIZE_MB * 1024 * 1024:
            files = sorted(
                [f for f in base_dir.iterdir() if f.is_file()],
                key=lambda f: f.stat().st_mtime,
            )
            while total_size > MAX_DEBUG_SIZE_MB * 1024 * 1024 and files:
                old = files.pop(0)
                total_size -= old.stat().st_size
                try:
                    old.unlink()
                    cleaned += 1
                except OSError:
                    pass

    if cleaned:
        print(f"  cleaned {cleaned} old files")


def _print_banner(title: str) -> None:
    print(f"\n{'─' * 40}")
    print(f"  {title}")
    print(f"{'─' * 40}")


if __name__ == "__main__":
    main()