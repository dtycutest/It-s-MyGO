from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from onebuy_crawler.services.db import mysql_connection
from onebuy_crawler.services.normalizer import clean_text


PLATFORM_ALIASES = {
    "jd": "jingdong",
    "jingdong": "jingdong",
    "taobao": "taobao",
}
RUNNABLE_STATUSES = ("pending", "failed", "blocked")
BLOCKED_FAILURE_REASONS = {
    "jd_access_too_frequent",
    "jd_browser_capture_no_items",
    "jd_captcha_or_security_check",
    "jd_risk_handler",
    "jd_search_redirected_to_home",
    "taobao_captcha_or_security_check",
    "taobao_login_required",
}


@dataclass(frozen=True)
class CrawlTask:
    id: int
    keyword: str
    platform_code: str
    status: str
    retry_count: int


def normalize_task_platform(platform: str) -> str:
    platform_code = PLATFORM_ALIASES.get(clean_text(platform).lower())
    if not platform_code:
        raise ValueError(f"Unsupported platform: {platform}")
    return platform_code


def task_platform_to_capture_platform(platform_code: str) -> str:
    return "jd" if platform_code == "jingdong" else platform_code


def enqueue_task(settings, keyword: str, platform_code: str, force: bool = False) -> None:
    keyword = clean_text(keyword)
    platform_code = normalize_task_platform(platform_code)
    if not keyword:
        raise ValueError("keyword is required")

    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            if force:
                cursor.execute(
                    """
                    INSERT INTO crawl_tasks
                        (keyword, platform_code, status, retry_count, last_error, next_run_at)
                    VALUES (%s, %s, 'pending', 0, NULL, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        status='pending',
                        retry_count=0,
                        last_error=NULL,
                        next_run_at=CURRENT_TIMESTAMP,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (keyword, platform_code),
                )
                return

            cursor.execute(
                """
                INSERT INTO crawl_tasks
                    (keyword, platform_code, status, retry_count, last_error, next_run_at)
                VALUES (%s, %s, 'pending', 0, NULL, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE
                    status=CASE
                        WHEN status IN ('running', 'success') THEN status
                        ELSE 'pending'
                    END,
                    next_run_at=CASE
                        WHEN status IN ('running', 'success') THEN next_run_at
                        ELSE CURRENT_TIMESTAMP
                    END,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (keyword, platform_code),
            )


def enqueue_tasks(settings, keyword: str, platforms: Iterable[str], force: bool = False) -> None:
    for platform in platforms:
        enqueue_task(settings, keyword, platform, force=force)


def load_due_tasks(
    settings,
    limit: int,
    platform: str = "",
    max_retries: int = 3,
    keywords: Iterable[str] | None = None,
) -> list[CrawlTask]:
    where = [
        "status IN ('pending', 'failed', 'blocked')",
        "next_run_at <= CURRENT_TIMESTAMP",
        "retry_count < %s",
    ]
    params: list[object] = [max_retries]
    if platform:
        where.append("platform_code = %s")
        params.append(normalize_task_platform(platform))
    keyword_list = [clean_text(keyword) for keyword in (keywords or []) if clean_text(keyword)]
    if keyword_list:
        where.append("keyword IN (" + ",".join(["%s"] * len(keyword_list)) + ")")
        params.extend(keyword_list)

    params.append(limit)
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT id, keyword, platform_code, status, retry_count
                FROM crawl_tasks
                WHERE {' AND '.join(where)}
                ORDER BY next_run_at ASC, updated_at ASC, id ASC
                LIMIT %s
                """,
                params,
            )
            return [
                CrawlTask(
                    id=int(row[0]),
                    keyword=str(row[1]),
                    platform_code=str(row[2]),
                    status=str(row[3]),
                    retry_count=int(row[4]),
                )
                for row in cursor.fetchall()
            ]


def mark_running(settings, task_id: int) -> None:
    _update_task(settings, task_id, status="running", last_error=None)


def mark_success(settings, task_id: int) -> None:
    _update_task(settings, task_id, status="success", last_error=None)


def mark_failed(
    settings,
    task_id: int,
    reason: str,
    retry_count: int,
    failed_delay_minutes: int = 15,
    blocked_delay_minutes: int = 60,
) -> None:
    reason = clean_text(reason)[:255] or "capture_failed"
    blocked = reason in BLOCKED_FAILURE_REASONS
    status = "blocked" if blocked else "failed"
    delay = blocked_delay_minutes if blocked else failed_delay_minutes
    next_run_at = datetime.now() + timedelta(minutes=max(1, delay))
    _update_task(
        settings,
        task_id,
        status=status,
        retry_count=retry_count,
        last_error=reason,
        next_run_at=next_run_at,
    )


def _update_task(
    settings,
    task_id: int,
    status: str,
    retry_count: int | None = None,
    last_error: str | None = None,
    next_run_at: datetime | None = None,
) -> None:
    assignments = ["status=%s", "last_error=%s", "updated_at=CURRENT_TIMESTAMP"]
    params: list[object] = [status, last_error]
    if retry_count is not None:
        assignments.append("retry_count=%s")
        params.append(retry_count)
    if next_run_at is not None:
        assignments.append("next_run_at=%s")
        params.append(next_run_at.strftime("%Y-%m-%d %H:%M:%S"))
    params.append(task_id)

    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"UPDATE crawl_tasks SET {', '.join(assignments)} WHERE id=%s",
                params,
            )
