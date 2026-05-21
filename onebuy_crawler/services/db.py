from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS products (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        product_id VARCHAR(32) NOT NULL UNIQUE,
        match_fingerprint VARCHAR(64) NOT NULL,
        title VARCHAR(512) NOT NULL,
        category_id INT NOT NULL DEFAULT 0,
        category_name VARCHAR(128) NOT NULL DEFAULT '未分类',
        image_url VARCHAR(512),
        images JSON NULL,
        description VARCHAR(1024),
        specs JSON NULL,
        min_price DECIMAL(10,2) NOT NULL DEFAULT 0,
        max_price DECIMAL(10,2) NOT NULL DEFAULT 0,
        price_diff DECIMAL(10,2) NOT NULL DEFAULT 0,
        best_platform VARCHAR(32),
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        KEY idx_products_match (match_fingerprint),
        KEY idx_products_title (title)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS platform_offers (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        product_id VARCHAR(32) NOT NULL,
        platform_id INT NOT NULL,
        platform_name VARCHAR(32) NOT NULL,
        platform_code VARCHAR(16) NOT NULL,
        source_sku_id VARCHAR(256) NOT NULL,
        price DECIMAL(10,2) NOT NULL DEFAULT 0,
        original_price DECIMAL(10,2),
        discount_rate INT,
        sales_volume BIGINT,
        seller_name VARCHAR(128),
        seller_rating DECIMAL(3,2),
        seller_id VARCHAR(64),
        product_url VARCHAR(1024),
        in_stock TINYINT(1) NOT NULL DEFAULT 1,
        stock_quantity INT,
        update_at DATETIME NOT NULL,
        UNIQUE KEY uk_offer_source (platform_code, source_sku_id),
        KEY idx_offer_product (product_id),
        CONSTRAINT fk_offer_product FOREIGN KEY (product_id) REFERENCES products(product_id)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS price_history (
        record_id BIGINT PRIMARY KEY AUTO_INCREMENT,
        product_id VARCHAR(32) NOT NULL,
        platform_code VARCHAR(16) NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        promo_info VARCHAR(255),
        crawl_time DATETIME NOT NULL,
        KEY idx_price_product_time (product_id, crawl_time),
        CONSTRAINT fk_price_product FOREIGN KEY (product_id) REFERENCES products(product_id)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_crawl_records (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        platform_code VARCHAR(16) NOT NULL,
        source_sku_id VARCHAR(256),
        url VARCHAR(1024),
        keyword_value VARCHAR(128),
        parse_status VARCHAR(32) NOT NULL,
        failure_reason VARCHAR(255),
        raw_payload JSON NULL,
        crawl_time DATETIME NOT NULL,
        KEY idx_raw_status (platform_code, parse_status, crawl_time)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS crawl_tasks (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        keyword VARCHAR(128) NOT NULL,
        platform_code VARCHAR(16) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'pending',
        retry_count INT NOT NULL DEFAULT 0,
        last_error VARCHAR(255),
        next_run_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uk_task_keyword_platform (keyword, platform_code),
        KEY idx_task_status_next_run (status, next_run_at),
        KEY idx_task_keyword (keyword)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]


@contextmanager
def mysql_connection(settings, database: str | None = None) -> Iterator[object]:
    import pymysql

    selected_database = settings.get("MYSQL_DATABASE") if database is None else database
    conn = pymysql.connect(
        host=settings.get("MYSQL_HOST"),
        port=settings.getint("MYSQL_PORT"),
        user=settings.get("MYSQL_USER"),
        password=settings.get("MYSQL_PASSWORD"),
        database=selected_database or None,
        charset=settings.get("MYSQL_CHARSET", "utf8mb4"),
        autocommit=False,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
