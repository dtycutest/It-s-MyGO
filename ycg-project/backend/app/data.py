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
)
from .seed_loader import load_seed

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

# 用户存储（内存）：按 openid 索引
users: List[User] = [default_user]
user_openid_index: Dict[str, User] = {default_user.openid: default_user}
user_id_seq = count(start=10002)


def find_user_by_openid(openid: str) -> User | None:
    return user_openid_index.get(openid)


def find_user_by_id(user_id: int) -> User | None:
    return next((u for u in users if u.user_id == user_id), None)


def create_user(openid: str, nick_name: str = "微信用户", avatar_url: str = "") -> User:
    user_id = next(user_id_seq)
    user = User(
        user_id=user_id,
        openid=openid,
        nick_name=nick_name or "微信用户",
        avatar_url=avatar_url or "",
        gender=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        vip_level=0,
    )
    users.append(user)
    user_openid_index[openid] = user
    return user

# Load products and categories from crawled seed.json
_cached_products, _cached_categories, _cached_seed_records = load_seed()
products: List[Product] = _cached_products
categories: List[Category] = _cached_categories
seed_records: List[dict] = _cached_seed_records

# Pick products with good platform coverage for seed favorites/alerts
_seed_p0 = products[0] if len(products) > 0 else None
_seed_p1 = products[1] if len(products) > 1 else _seed_p0

favorites: List[Favorite] = []
if _seed_p0:
    favorites.append(
        Favorite(
            favorite_id=1,
            user_id=default_user.user_id,
            product_id=_seed_p0.product_id,
            product_title=_seed_p0.title,
            product_image=_seed_p0.image_url,
            product_min_price=_seed_p0.min_price,
            notes="618打折再买",
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=1),
        )
    )

price_alerts: List[PriceAlert] = []
if _seed_p1:
    price_alerts.append(
        PriceAlert(
            alert_id=1,
            user_id=default_user.user_id,
            product_id=_seed_p1.product_id,
            product_title=_seed_p1.title,
            product_image=_seed_p1.image_url or "",
            target_price=_seed_p1.min_price * 0.9 if _seed_p1.min_price > 0 else 100,
            current_price=_seed_p1.min_price,
            platform_filter=["taobao", "jingdong"],
            is_enabled=True,
            is_triggered=False,
            created_at=now - timedelta(days=7),
            updated_at=now - timedelta(days=2),
        )
    )

browse_history: List[BrowseHistoryItem] = []
for i, prod in enumerate(products[:4]):
    browse_history.append(
            BrowseHistoryItem(
                history_id=i + 1,
                user_id=default_user.user_id,
                product_id=prod.product_id,
                product_title=prod.title,
                product_image=prod.image_url or "",
                viewed_at=now - timedelta(hours=12 - i * 6),
        )
    )

search_records: List[SearchRecord] = [
    SearchRecord(keyword="小米充电宝", searched_at=now - timedelta(days=1), user_id=default_user.user_id),
    SearchRecord(keyword="罗技键盘", searched_at=now - timedelta(days=2), user_id=default_user.user_id),
    SearchRecord(keyword="iPhone 15", searched_at=now - timedelta(days=2, hours=5), user_id=default_user.user_id),
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


def record_search(user_id: int, keyword: str) -> None:
    search_records.insert(0, SearchRecord(user_id=user_id, keyword=keyword, searched_at=datetime.now(timezone.utc)))
    if len(search_records) > 100:
        del search_records[100:]


def add_analytics_event(event: AnalyticsEvent) -> None:
    analytics_events.append(event)
    if len(analytics_events) > 500:
        del analytics_events[0:100]
