from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import count
from typing import Dict, List

from .schemas import (
    AnalyticsEvent,
    BrowseHistoryItem,
    Category,
    Favorite,
    PriceAlert,
    Product,
    SearchRecord,
    User,
    Platform,
)

now = datetime.now(timezone.utc)

default_user = User(
    user_id=10001,
    openid="oZxsulsr5z0GQyVQW-demo",
    nick_name="演示用户",
    avatar_url="https://cdn.example.com/avatars/demo_user.jpg",
    gender=1,
    province="浙江省",
    city="杭州市",
    created_at=now - timedelta(days=30),
    updated_at=now,
    vip_level=1,
    vip_expire_at=now + timedelta(days=60),
)

categories: List[Category] = [
    Category(category_id=1, name="手机数码", parent_id=0),
    Category(category_id=2, name="手机", parent_id=1),
    Category(category_id=3, name="笔记本电脑", parent_id=1),
    Category(category_id=4, name="生活家电", parent_id=0),
    Category(category_id=5, name="吸尘器", parent_id=4),
]

products: List[Product] = [
    Product(
        product_id="SKU20250315001",
        title="Apple iPhone 15 Pro Max 256GB",
        category_id=2,
        category_name="手机数码-手机",
        description="官方正品，A17 Pro芯片，四摄系统",
        image_url="https://cdn.ycg.com/products/SKU20250315001/main.jpg",
        images=[
            "https://cdn.ycg.com/products/SKU20250315001/image1.jpg",
            "https://cdn.ycg.com/products/SKU20250315001/image2.jpg",
        ],
        min_price=6699.0,
        max_price=6999.0,
        best_platform="京东",
        price_diff=300.0,
        specs={"color": "远峰蓝", "storage": "256GB", "warranty": "国行一年保修"},
        platforms=[
            Platform(
                platform_id=1,
                platform_name="淘宝",
                platform_code="taobao",
                price=6799.0,
                original_price=7299.0,
                discount_rate=7,
                in_stock=True,
                product_url="https://item.taobao.com/item.htm?id=iphone15-demo",
                seller_id="seller_tb_01",
                seller_name="苹果官方旗舰店",
                seller_rating=4.8,
                sales_volume=2200,
                stock_quantity=58,
                update_at=now - timedelta(hours=2),
            ),
            Platform(
                platform_id=2,
                platform_name="京东",
                platform_code="jingdong",
                price=6699.0,
                original_price=6999.0,
                discount_rate=4,
                in_stock=True,
                product_url="https://item.jd.com/iphone15-demo.html",
                seller_id="seller_jd_01",
                seller_name="京东自营",
                seller_rating=4.9,
                sales_volume=3200,
                stock_quantity=120,
                update_at=now - timedelta(hours=1),
            ),
        ],
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(hours=1),
    ),
    Product(
        product_id="SKU20250315002",
        title="Apple MacBook Air 15\" M3 16GB/512GB",
        category_id=3,
        category_name="手机数码-笔记本电脑",
        description="M3芯片轻薄本，续航持久，双雷雳接口",
        image_url="https://cdn.ycg.com/products/SKU20250315002/main.jpg",
        images=[
            "https://cdn.ycg.com/products/SKU20250315002/image1.jpg",
        ],
        min_price=11499.0,
        max_price=11899.0,
        best_platform="淘宝",
        price_diff=400.0,
        specs={"color": "深空灰", "memory": "16GB", "storage": "512GB"},
        platforms=[
            Platform(
                platform_id=1,
                platform_name="淘宝",
                platform_code="taobao",
                price=11499.0,
                original_price=12499.0,
                discount_rate=8,
                in_stock=True,
                product_url="https://item.taobao.com/item.htm?id=macbook15-demo",
                seller_id="seller_tb_02",
                seller_name="Apple官方旗舰店",
                seller_rating=4.9,
                sales_volume=870,
                stock_quantity=45,
                update_at=now - timedelta(hours=3),
            ),
            Platform(
                platform_id=2,
                platform_name="京东",
                platform_code="jingdong",
                price=11899.0,
                original_price=12599.0,
                discount_rate=6,
                in_stock=True,
                product_url="https://item.jd.com/macbook15-demo.html",
                seller_id="seller_jd_02",
                seller_name="京东自营",
                seller_rating=4.8,
                sales_volume=650,
                stock_quantity=33,
                update_at=now - timedelta(hours=4),
            ),
        ],
        created_at=now - timedelta(days=20),
        updated_at=now - timedelta(hours=3),
    ),
    Product(
        product_id="SKU20250315003",
        title="Dyson V15 Detect 无绳吸尘器",
        category_id=5,
        category_name="生活家电-吸尘器",
        description="激光探测微尘，智能自动吸力调节",
        image_url="https://cdn.ycg.com/products/SKU20250315003/main.jpg",
        images=["https://cdn.ycg.com/products/SKU20250315003/image1.jpg"],
        min_price=3899.0,
        max_price=4199.0,
        best_platform="京东",
        price_diff=300.0,
        specs={"color": "曜石黑", "battery": "60分钟"},
        platforms=[
            Platform(
                platform_id=1,
                platform_name="淘宝",
                platform_code="taobao",
                price=3999.0,
                original_price=4399.0,
                discount_rate=9,
                in_stock=True,
                product_url="https://item.taobao.com/item.htm?id=dysonv15-demo",
                seller_id="seller_tb_03",
                seller_name="戴森官方旗舰店",
                seller_rating=4.8,
                sales_volume=520,
                stock_quantity=80,
                update_at=now - timedelta(hours=6),
            ),
            Platform(
                platform_id=2,
                platform_name="京东",
                platform_code="jingdong",
                price=3899.0,
                original_price=4199.0,
                discount_rate=7,
                in_stock=True,
                product_url="https://item.jd.com/dysonv15-demo.html",
                seller_id="seller_jd_03",
                seller_name="京东自营",
                seller_rating=4.9,
                sales_volume=730,
                stock_quantity=60,
                update_at=now - timedelta(hours=5),
            ),
        ],
        created_at=now - timedelta(days=15),
        updated_at=now - timedelta(hours=6),
    ),
]

favorites: List[Favorite] = [
    Favorite(
        favorite_id=1,
        user_id=default_user.user_id,
        product_id=products[0].product_id,
        product_title=products[0].title,
        product_image=products[0].image_url,
        product_min_price=products[0].min_price,
        notes="618打折再买",
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=1),
    )
]

price_alerts: List[PriceAlert] = [
    PriceAlert(
        alert_id=1,
        user_id=default_user.user_id,
        product_id=products[1].product_id,
        product_title=products[1].title,
        target_price=10999.0,
        current_price=products[1].min_price,
        platform_filter=["taobao", "jingdong"],
        is_enabled=True,
        is_triggered=False,
        created_at=now - timedelta(days=7),
        updated_at=now - timedelta(days=2),
    )
]

browse_history: List[BrowseHistoryItem] = [
    BrowseHistoryItem(
        history_id=1,
        product_id=products[2].product_id,
        product_title=products[2].title,
        viewed_at=now - timedelta(hours=12),
    ),
    BrowseHistoryItem(
        history_id=2,
        product_id=products[0].product_id,
        product_title=products[0].title,
        viewed_at=now - timedelta(hours=6),
    ),
]

search_records: List[SearchRecord] = [
    SearchRecord(keyword="iPhone 15", searched_at=now - timedelta(days=1)),
    SearchRecord(keyword="MacBook Air", searched_at=now - timedelta(days=2)),
    SearchRecord(keyword="Dyson 吸尘器", searched_at=now - timedelta(days=2, hours=5)),
]

analytics_events: List[AnalyticsEvent] = []

favorite_id_seq = count(start=len(favorites) + 1)
price_alert_id_seq = count(start=len(price_alerts) + 1)
history_id_seq = count(start=len(browse_history) + 1)


def next_favorite_id() -> int:
    return next(favorite_id_seq)


def next_price_alert_id() -> int:
    return next(price_alert_id_seq)


def next_history_id() -> int:
    return next(history_id_seq)


def find_product(product_id: str) -> Product | None:
    return next((p for p in products if p.product_id == product_id), None)


def get_categories_by_parent(parent_id: int) -> List[Category]:
    return [c for c in categories if c.parent_id == parent_id]


def record_search(keyword: str) -> None:
    search_records.insert(0, SearchRecord(keyword=keyword, searched_at=datetime.now(timezone.utc)))
    if len(search_records) > 100:
        del search_records[100:]


def add_analytics_event(event: AnalyticsEvent) -> None:
    analytics_events.append(event)
    if len(analytics_events) > 500:
        del analytics_events[0:100]
