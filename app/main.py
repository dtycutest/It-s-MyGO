from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from . import data
from .auth import token_store
from .schemas import (
    ApiResponse,
    AnalyticsEvent,
    BrowseHistoryItem,
    Category,
    Favorite,
    PaginatedResponse,
    Pagination,
    PriceAlert,
    Product,
    SearchRecord,
    TokenPair,
    User,
)


app = FastAPI(
    title="《一次买够》网购比价平台 API",
    version="1.0.0",
    description="基于需求规格说明与 openapi.json 实现的演示后端。",
)


class ApiHttpException(HTTPException):
    def __init__(self, status_code: int, code: int, message: str) -> None:
        super().__init__(status_code=status_code, detail={"code": code, "message": message, "data": None})


def paginate(items: List, page: int, page_size: int) -> PaginatedResponse:
    total = len(items)
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    start = (page - 1) * page_size
    end = start + page_size
    sliced = items[start:end]
    pagination = Pagination(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1 and total_pages > 0,
    )
    return PaginatedResponse(list=sliced, pagination=pagination)


def raise_api_error(code: int, message: str, status_code: int = 400) -> None:
    raise ApiHttpException(status_code=status_code, code=code, message=message)


def get_current_user(authorization: str = Header(None)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiHttpException(status_code=401, code=401001, message="未授权或令牌失效")
    token = authorization.split(" ", 1)[1]
    user_id = token_store.verify_access(token)
    if not user_id:
        raise ApiHttpException(status_code=401, code=401001, message="未授权或令牌失效")
    return data.default_user


@app.exception_handler(ApiHttpException)
async def handle_api_exception(_: Request, exc: ApiHttpException) -> JSONResponse:
    content = exc.detail if isinstance(exc.detail, dict) else ApiResponse.error(code=exc.status_code, message=str(exc.detail)).dict()
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 401:
        return JSONResponse(status_code=401, content=ApiResponse.error(code=401001, message="未授权或令牌失效").dict())
    content = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.get("/health", summary="健康检查", tags=["监控"])
def healthcheck() -> ApiResponse[str]:
    return ApiResponse.success("ok", message="服务正常")


@app.post("/auth/login", summary="微信登录", tags=["认证"], response_model=ApiResponse[TokenPair], include_in_schema=True)
def login(payload: dict = Body(...)) -> ApiResponse[TokenPair]:
    code = payload.get("code")
    raw_data = payload.get("raw_data")
    signature = payload.get("signature")
    if not code or not raw_data or not signature:
        raise_api_error(400001, "缺少必要的登录参数", status_code=400)
    token_pair = token_store.issue_tokens(data.default_user)
    return ApiResponse.success(token_pair, message="登录成功")


@app.post("/auth/refresh", summary="刷新Token", tags=["认证"], response_model=ApiResponse[TokenPair])
def refresh_token(payload: dict = Body(...)) -> ApiResponse[TokenPair]:
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise_api_error(400002, "缺少refresh_token", status_code=400)
    token_pair = token_store.refresh(refresh_token)
    if not token_pair:
        raise_api_error(401001, "refresh_token 无效或已过期", status_code=401)
    return ApiResponse.success(token_pair, message="刷新成功")


@app.post("/auth/logout", summary="登出", tags=["认证"], response_model=ApiResponse[None])
def logout(authorization: Optional[str] = Header(None)) -> ApiResponse[None]:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        token_store.revoke(token)
    return ApiResponse.success(None, message="登出成功")


@app.get("/products/search", summary="商品搜索", tags=["商品"], response_model=ApiResponse[PaginatedResponse[Product]])
def search_products(
    keyword: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None, ge=1),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    platform: Optional[str] = Query(None),
    sort: str = Query("price_asc", pattern="^(price_asc|price_desc|sales_desc|rating_desc)$"),
):
    data.record_search(keyword)
    keyword_lower = keyword.lower()
    results = [p for p in data.products if keyword_lower in p.title.lower()]
    if category_id:
        results = [p for p in results if p.category_id == category_id]
    if min_price is not None:
        results = [p for p in results if p.min_price >= min_price]
    if max_price is not None:
        results = [p for p in results if p.max_price <= max_price]
    if platform:
        platforms = {p.strip() for p in platform.split(",") if p.strip()}
        results = [
            p
            for p in results
            if any(pl.platform_code in platforms for pl in p.platforms)
        ]
    if sort == "price_asc":
        results.sort(key=lambda p: p.min_price)
    elif sort == "price_desc":
        results.sort(key=lambda p: p.max_price, reverse=True)
    elif sort == "sales_desc":
        results.sort(key=lambda p: sum(pl.sales_volume or 0 for pl in p.platforms), reverse=True)
    elif sort == "rating_desc":
        results.sort(
            key=lambda p: max(((pl.seller_rating or 0) for pl in p.platforms), default=0),
            reverse=True,
        )

    paged = paginate(results, page, page_size)
    return ApiResponse.success(paged)


@app.get("/products/{product_id}", summary="获取商品详情", tags=["商品"], response_model=ApiResponse[Product])
def get_product(product_id: str = Path(..., max_length=32)):
    product = data.find_product(product_id)
    if not product:
        raise_api_error(404001, "商品未找到", status_code=404)
    return ApiResponse.success(product)


@app.get("/products/categories", summary="获取商品分类", tags=["商品"], response_model=ApiResponse[List[Category]])
def get_categories(parent_id: int = Query(0, ge=0)):
    cats = data.get_categories_by_parent(parent_id)
    return ApiResponse.success(cats)


@app.get("/users/profile", summary="获取用户信息", tags=["用户"], response_model=ApiResponse[User])
def get_profile(user: User = Depends(get_current_user)):
    return ApiResponse.success(user)


@app.put("/users/profile", summary="更新用户信息", tags=["用户"], response_model=ApiResponse[User])
def update_profile(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
):
    nick_name = payload.get("nick_name")
    avatar_url = payload.get("avatar_url")
    gender = payload.get("gender")
    if nick_name:
        data.default_user.nick_name = nick_name
    if avatar_url:
        data.default_user.avatar_url = avatar_url
    if gender is not None:
        data.default_user.gender = gender
    data.default_user.updated_at = datetime.now(timezone.utc)
    return ApiResponse.success(data.default_user, message="更新成功")


@app.get("/users/favorites", summary="获取收藏列表", tags=["收藏"], response_model=ApiResponse[PaginatedResponse[Favorite]])
def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    user_favs = [f for f in data.favorites if f.user_id == user.user_id]
    paged = paginate(user_favs, page, page_size)
    return ApiResponse.success(paged)


@app.post("/users/favorites", summary="添加收藏", tags=["收藏"], response_model=ApiResponse[Favorite])
def add_favorite(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
):
    product_id = payload.get("product_id")
    notes = payload.get("notes")
    if not product_id:
        raise_api_error(400101, "product_id 不能为空")
    product = data.find_product(product_id)
    if not product:
        raise_api_error(404002, "商品不存在", status_code=404)
    existing = next((f for f in data.favorites if f.user_id == user.user_id and f.product_id == product_id), None)
    if existing:
        return ApiResponse.success(existing, message="已存在相同收藏")
    favorite = Favorite(
        favorite_id=data.next_favorite_id(),
        user_id=user.user_id,
        product_id=product_id,
        product_title=product.title,
        product_image=product.image_url,
        product_min_price=product.min_price,
        notes=notes,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    data.favorites.insert(0, favorite)
    return ApiResponse.success(favorite, message="收藏成功")


@app.put("/users/favorites/{favorite_id}", summary="更新收藏备注", tags=["收藏"], response_model=ApiResponse[Favorite])
def update_favorite(
    favorite_id: int = Path(..., ge=1),
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
):
    fav = next((f for f in data.favorites if f.favorite_id == favorite_id and f.user_id == user.user_id), None)
    if not fav:
        raise_api_error(404003, "收藏不存在", status_code=404)
    notes = payload.get("notes")
    fav.notes = notes
    fav.updated_at = datetime.now(timezone.utc)
    return ApiResponse.success(fav, message="更新成功")


@app.delete("/users/favorites/{favorite_id}", summary="移除收藏", tags=["收藏"], response_model=ApiResponse[None])
def delete_favorite(
    favorite_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
):
    index = next((i for i, f in enumerate(data.favorites) if f.favorite_id == favorite_id and f.user_id == user.user_id), None)
    if index is None:
        raise_api_error(404004, "收藏不存在", status_code=404)
    data.favorites.pop(index)
    return ApiResponse.success(None, message="删除成功")


@app.get("/users/price-alerts", summary="获取降价提醒列表", tags=["降价提醒"], response_model=ApiResponse[PaginatedResponse[PriceAlert]])
def list_price_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query("all", pattern="^(all|triggered|untriggered)$"),
    user: User = Depends(get_current_user),
):
    alerts = [a for a in data.price_alerts if a.user_id == user.user_id]
    if status == "triggered":
        alerts = [a for a in alerts if a.is_triggered]
    elif status == "untriggered":
        alerts = [a for a in alerts if not a.is_triggered]
    paged = paginate(alerts, page, page_size)
    return ApiResponse.success(paged)


@app.post("/users/price-alerts", summary="创建降价提醒", tags=["降价提醒"], response_model=ApiResponse[PriceAlert])
def create_price_alert(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
):
    product_id = payload.get("product_id")
    target_price = payload.get("target_price")
    platform_filter = payload.get("platform_filter")
    if not product_id or target_price is None:
        raise_api_error(400201, "product_id 和 target_price 必填")
    product = data.find_product(product_id)
    if not product:
        raise_api_error(404005, "商品不存在", status_code=404)
    alert = PriceAlert(
        alert_id=data.next_price_alert_id(),
        user_id=user.user_id,
        product_id=product_id,
        product_title=product.title,
        target_price=float(target_price),
        current_price=product.min_price,
        platform_filter=platform_filter,
        is_enabled=True,
        is_triggered=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    data.price_alerts.insert(0, alert)
    return ApiResponse.success(alert, message="提醒创建成功")


@app.put("/users/price-alerts/{alert_id}", summary="更新降价提醒", tags=["降价提醒"], response_model=ApiResponse[PriceAlert])
def update_price_alert(
    alert_id: int = Path(..., ge=1),
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
):
    alert = next((a for a in data.price_alerts if a.alert_id == alert_id and a.user_id == user.user_id), None)
    if not alert:
        raise_api_error(404006, "提醒不存在", status_code=404)
    if "target_price" in payload and payload["target_price"] is not None:
        alert.target_price = float(payload["target_price"])
    if "is_enabled" in payload and payload["is_enabled"] is not None:
        alert.is_enabled = bool(payload["is_enabled"])
    alert.updated_at = datetime.now(timezone.utc)
    return ApiResponse.success(alert, message="更新成功")


@app.delete("/users/price-alerts/{alert_id}", summary="删除降价提醒", tags=["降价提醒"], response_model=ApiResponse[None])
def delete_price_alert(
    alert_id: int = Path(..., ge=1),
    user: User = Depends(get_current_user),
):
    index = next((i for i, a in enumerate(data.price_alerts) if a.alert_id == alert_id and a.user_id == user.user_id), None)
    if index is None:
        raise_api_error(404007, "提醒不存在", status_code=404)
    data.price_alerts.pop(index)
    return ApiResponse.success(None, message="删除成功")


@app.get("/users/browse-history", summary="获取浏览历史", tags=["浏览历史"], response_model=ApiResponse[PaginatedResponse[BrowseHistoryItem]])
def list_browse_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    history = sorted(data.browse_history, key=lambda h: h.viewed_at, reverse=True)
    paged = paginate(history, page, page_size)
    return ApiResponse.success(paged)


@app.post("/users/browse-history", summary="添加浏览历史", tags=["浏览历史"], response_model=ApiResponse[BrowseHistoryItem])
def add_browse_history(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
):
    product_id = payload.get("product_id")
    if not product_id:
        raise_api_error(400301, "product_id 不能为空")
    product = data.find_product(product_id)
    if not product:
        raise_api_error(404008, "商品不存在", status_code=404)
    item = BrowseHistoryItem(
        history_id=data.next_history_id(),
        product_id=product_id,
        product_title=product.title,
        viewed_at=datetime.now(timezone.utc),
    )
    data.browse_history.insert(0, item)
    return ApiResponse.success(item, message="添加成功")


@app.delete("/users/browse-history", summary="清除浏览历史", tags=["浏览历史"], response_model=ApiResponse[None])
def clear_browse_history(user: User = Depends(get_current_user)):
    data.browse_history.clear()
    return ApiResponse.success(None, message="清除成功")


@app.get("/users/search-records", summary="获取搜索记录", tags=["搜索记录"], response_model=ApiResponse[PaginatedResponse[SearchRecord]])
def list_search_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    sorted_records = sorted(data.search_records, key=lambda r: r.searched_at, reverse=True)
    paged = paginate(sorted_records, page, page_size)
    return ApiResponse.success(paged)


@app.get("/search/hot-words", summary="获取热搜词", tags=["搜索记录"], response_model=ApiResponse[List[str]])
def hot_words(limit: int = Query(10, ge=1, le=50)):
    keywords = [r.keyword for r in data.search_records]
    ranking: List[str] = []
    for kw in keywords:
        if kw not in ranking:
            ranking.append(kw)
        if len(ranking) >= limit:
            break
    return ApiResponse.success(ranking[:limit])


@app.get("/recommendations/personalized", summary="获取个性化推荐", tags=["推荐"], response_model=ApiResponse[PaginatedResponse[Product]])
def personalized_recommendations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    fallback_time = datetime.now(timezone.utc)
    sorted_products = sorted(
        data.products, key=lambda p: p.updated_at or fallback_time, reverse=True
    )
    paged = paginate(sorted_products, page, page_size)
    return ApiResponse.success(paged)


@app.post("/analytics/events", summary="上报用户行为", tags=["分析"], response_model=ApiResponse[None])
def report_event(event: AnalyticsEvent = Body(...), user: User = Depends(get_current_user)):
    data.add_analytics_event(event)
    return ApiResponse.success(None, message="上报成功")
