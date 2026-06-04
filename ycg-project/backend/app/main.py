from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse

from . import data
from .auth import token_store
from .wechat import jscode2session
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
    return PaginatedResponse(items=sliced, pagination=pagination)


def raise_api_error(code: int, message: str, status_code: int = 400) -> None:
    raise ApiHttpException(status_code=status_code, code=code, message=message)


def get_current_user(authorization: str = Header(None)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiHttpException(status_code=401, code=401001, message="未授权或令牌失效")
    token = authorization.split(" ", 1)[1]
    user_id = token_store.verify_access(token)
    if not user_id:
        raise ApiHttpException(status_code=401, code=401001, message="未授权或令牌失效")
    user = data.find_user_by_id(user_id)
    if not user:
        raise ApiHttpException(status_code=401, code=401001, message="用户不存在")
    return user


def optional_get_current_user(authorization: str = Header(None)) -> Optional[User]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    user_id = token_store.verify_access(token)
    if not user_id:
        return None
    return data.find_user_by_id(user_id)


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


@app.get("/crawler/seed", summary="获取爬虫原始数据", tags=["爬虫"])
def get_seed_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    platform: Optional[str] = Query(None, description="按平台筛选: taobao, jingdong"),
):
    records = data.seed_records
    if platform:
        records = [r for r in records if r.get("platform_code") == platform]
    paged = paginate(records, page, page_size)
    return ApiResponse.success(paged)


@app.get("/crawler/stats", summary="获取爬虫数据统计", tags=["爬虫"])
def get_seed_stats():
    records = data.seed_records
    platform_counts: dict = {}
    category_counts: dict = {}
    for r in records:
        pc = r.get("platform_code", "unknown")
        platform_counts[pc] = platform_counts.get(pc, 0) + 1
        cat = r.get("category_text", "未分类")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    return ApiResponse.success({
        "total_records": len(records),
        "total_products": len(data.products),
        "platforms": platform_counts,
        "categories": category_counts,
    })


@app.post("/auth/login", summary="微信登录", tags=["认证"], response_model=ApiResponse[TokenPair], include_in_schema=True)
async def login(payload: dict = Body(...)) -> ApiResponse[TokenPair]:
    code = payload.get("code")
    raw_data = payload.get("raw_data", "{}")
    signature = payload.get("signature", "")

    # ------ 模拟登录（开发/测试用）------
    if code == "mock_dev_code":
        token_pair = token_store.issue_tokens(data.default_user)
        return ApiResponse.success(token_pair, message="模拟登录成功")

    if not code:
        raise_api_error(400001, "缺少登录凭证 code", status_code=400)

    # ------ 真实微信登录 ------
    # 1. 调用微信 jscode2session 换取 openid
    wx_result = await jscode2session(code)

    if "errcode" in wx_result and wx_result["errcode"] != 0:
        errcode = wx_result.get("errcode", -1)
        errmsg = wx_result.get("errmsg", "未知错误")
        raise_api_error(400003, f"微信登录失败 [{errcode}]: {errmsg}", status_code=400)

    openid: str = wx_result.get("openid", "")
    if not openid:
        raise_api_error(400004, "微信返回的 openid 为空", status_code=400)

    # 2. 解析用户信息（昵称、头像等）
    import json
    nick_name = "微信用户"
    avatar_url = ""
    try:
        user_info = json.loads(raw_data)
        nick_name = user_info.get("nickName", "微信用户")
        avatar_url = user_info.get("avatarUrl", "")
    except (json.JSONDecodeError, TypeError):
        pass

    # 3. 查找或创建用户
    user = data.find_user_by_openid(openid)
    if not user:
        user = data.create_user(openid, nick_name, avatar_url)

    # 4. 签发 Token
    token_pair = token_store.issue_tokens(user)
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
    keyword: str = Query("", min_length=0, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None, ge=1),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    platform: Optional[str] = Query(None),
    sort: str = Query("price_asc", pattern="^(price_asc|price_desc|sales_desc|rating_desc)$"),
    authorization: Optional[str] = Header(None),
):
    current_user = optional_get_current_user(authorization)
    if current_user is not None:
        data.record_search(current_user.user_id, keyword)
    keyword = keyword.strip()
    if not keyword:
        return ApiResponse.success(paginate([], page, page_size))

    keyword_lower = keyword.lower()

    # Split keyword into individual words (for multi-word matching)
    keyword_words = keyword_lower.split()
    kw_no_space = keyword_lower.replace(" ", "")

    scored: list[tuple[int, Product]] = []
    for p in data.products:
        title_lower = p.title.lower()
        title_no_space = title_lower.replace(" ", "")
        cat_name = (p.category_name or "").lower()
        score = 0
        matched_title = False

        # Level 1: Exact keyword match in title
        if keyword_lower in title_lower:
            matched_title = True
            pos = title_lower.index(keyword_lower)
            if pos == 0:
                score += 300  # Keyword at the very beginning
            elif pos < 10:
                score += 200  # Keyword near the beginning
            else:
                score += 100  # Keyword somewhere in title
        # Level 2: Keyword without spaces matches title without spaces
        elif kw_no_space and kw_no_space in title_no_space:
            matched_title = True
            score += 80
        # Level 3: All keyword words individually appear in the title
        elif len(keyword_words) >= 2:
            match_count = sum(1 for w in keyword_words if w in title_lower)
            if match_count >= len(keyword_words):
                matched_title = True
                score += 60  # All words matched
            elif match_count >= len(keyword_words) * 0.6:
                matched_title = True
                score += 30  # Most words matched
        # Level 4: Single keyword word appears in title (for short keywords)
        elif len(keyword_lower) >= 2:
            if keyword_lower in title_lower:
                matched_title = True
                score += 40

        # Category match (can be the sole reason for inclusion)
        cat_matched = keyword_lower in cat_name
        if cat_matched:
            if keyword_lower == cat_name:
                score += 100  # Exact category name match
            else:
                score += 60  # Partial category name match

        # Skip if neither title nor category matched
        if not matched_title and not cat_matched:
            continue

        # Price diff bonus (prioritize cross-platform products)
        if (p.price_diff or 0) > 0:
            score += 50

        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [p for _, p in scored]
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

    def sort_products(products: list, s: str) -> list:
        if s == "price_asc":
            products.sort(key=lambda p: p.min_price)
        elif s == "price_desc":
            products.sort(key=lambda p: p.max_price, reverse=True)
        elif s == "sales_desc":
            products.sort(key=lambda p: sum(pl.sales_volume or 0 for pl in p.platforms), reverse=True)
        elif s == "rating_desc":
            products.sort(
                key=lambda p: max(((pl.seller_rating or 0) for pl in p.platforms), default=0),
                reverse=True,
            )
        return products

    has_diff = [p for p in results if (p.price_diff or 0) > 0]
    no_diff = [p for p in results if (p.price_diff or 0) == 0]
    has_diff = sort_products(has_diff, sort)
    no_diff = sort_products(no_diff, sort)
    results = has_diff + no_diff

    paged = paginate(results, page, page_size)
    return ApiResponse.success(paged)


@app.get("/products/categories", summary="获取商品分类", tags=["商品"], response_model=ApiResponse[List[Category]])
def get_categories(parent_id: int = Query(0, ge=0)):
    cats = data.get_categories_by_parent(parent_id)
    return ApiResponse.success(cats)


@app.get("/products/{product_id}", summary="获取商品详情", tags=["商品"], response_model=ApiResponse[Product])
def get_product(product_id: str = Path(..., max_length=32)):
    product = data.find_product(product_id)
    if not product:
        raise_api_error(404001, "商品未找到", status_code=404)
    return ApiResponse.success(product)


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
        user.nick_name = nick_name
    if avatar_url:
        user.avatar_url = avatar_url
    if gender is not None:
        user.gender = gender
    user.updated_at = datetime.now(timezone.utc)
    return ApiResponse.success(user, message="更新成功")


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
        product_image=product.image_url or "",
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
    user_history = [h for h in data.browse_history if h.user_id == user.user_id]
    history = sorted(user_history, key=lambda h: h.viewed_at, reverse=True)
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
    data.browse_history = [h for h in data.browse_history if not (h.user_id == user.user_id and h.product_id == product_id)]
    item = BrowseHistoryItem(
        history_id=data.next_history_id(),
        user_id=user.user_id,
        product_id=product_id,
        product_title=product.title,
        product_image=product.image_url or "",
        viewed_at=datetime.now(timezone.utc),
    )
    data.browse_history.insert(0, item)
    return ApiResponse.success(item, message="添加成功")


@app.delete("/users/browse-history", summary="清除浏览历史", tags=["浏览历史"], response_model=ApiResponse[None])
def clear_browse_history(user: User = Depends(get_current_user)):
    data.browse_history = [h for h in data.browse_history if h.user_id != user.user_id]
    return ApiResponse.success(None, message="清除成功")


@app.get("/users/search-records", summary="获取搜索记录", tags=["搜索记录"], response_model=ApiResponse[PaginatedResponse[SearchRecord]])
def list_search_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    user_records = [r for r in data.search_records if r.user_id == user.user_id]
    sorted_records = sorted(user_records, key=lambda r: r.searched_at, reverse=True)
    paged = paginate(sorted_records, page, page_size)
    return ApiResponse.success(paged)


@app.get("/search/hot-words", summary="获取热搜词", tags=["搜索记录"], response_model=ApiResponse[List[dict]])
def hot_words(limit: int = Query(10, ge=1, le=50)):
    from collections import Counter

    keyword_counter: Counter = Counter()

    # 1. 搜索记录中的关键词（权重最高）
    for r in data.search_records:
        keyword_counter[r.keyword] += 5

    # 2. 从商品标题中提取有意义的搜索词
    for p in data.products:
        title = p.title
        # 提取品牌名和型号组合
        brand_patterns = [
            r'(苹果|华为|小米|红米|三星|OPPO|vivo|荣耀|一加|真我|魅族|联想|戴尔|惠普|华硕|宏碁|微软|罗技|雷蛇|赛睿|金士顿|闪迪|西部数据|希捷|英特尔|AMD|英伟达|海飞丝|多芬|清扬|潘婷|沙宣|力士|舒肤佳|佳洁士|高露洁|云南白药|黑人|冷酸灵|两面针|维达|清风|洁柔|心相印|得宝|蓝月亮|立白|汰渍|奥妙|碧浪|超能|雕牌|晨光|得力|真彩|齐心|广博|宝克|雀巢|麦斯威尔|星巴克|瑞幸|可口可乐|百事|农夫山泉|怡宝|康师傅|统一|白象|汤达人|合味道|周黑鸭|绝味|良品铺子|三只松鼠|百草味|旺旺|徐福记|大白兔|德芙|费列罗|好时|士力架|奥利奥|乐事|品客|可比克|伊利|蒙牛|光明|安慕希|纯甄|特仑苏|金典|余华|莫言|刘慈欣|东野圭吾|村上春树|汪曾祺|三毛|张爱玲|鲁迅|老舍|巴金|路遥|贾平凹|陈忠实|史铁生|王小波|韩寒|郭敬明|江南|蔡骏|秦明|东野圭吾|JK罗琳|J.K.罗琳|田中芳树|米泽穗信|中岛敦|芥川龙之介|川端康成|太宰治|夏目漱石|三岛由纪夫|谷崎润一郎|司马辽太郎|吉川英治|山冈庄八|海明威|马尔克斯|博尔赫斯|卡尔维诺|毛姆|奥威尔|赫胥黎|阿西莫夫|克拉克|布拉德伯里|勒古恩|阿特伍德|冯内古特|斯蒂芬|菲利普|阿加莎|柯南|福尔摩斯|波洛|马普尔|奎因|钱德勒|哈米特|布洛克|康奈利|帕特森|格里森姆|图灵|爱因斯坦|霍金|费曼|达尔文|牛顿|伽利略|哥白尼|门捷列夫|居里夫人|袁隆平|屠呦呦|钟南山|李兰娟|张文宏|全部)',
        ]
        for pattern in brand_patterns:
            matches = re.findall(pattern, title)
            for m in matches:
                if len(m) >= 2 and m not in {'手机', '电脑', '平板', '全部', '耳机', '键盘', '鼠标', '充电', '蓝牙', '无线', '有线', '通用', '适用', '适配', '兼容'}:
                    keyword_counter[m] += 3

        # 提取 "品牌+型号" 组合
        model_patterns = [
            r'(iPhone\s*\d+|iPad\s*\w*|MacBook\s*\w*)',
            r'(小米\s*\d+|红米\s*\w+|Redmi\s*\w+)',
            r'(华为\s*\w+\s*\d+|Mate\s*\d+|Pura\s*\d+|nova\s*\d+)',
            r'(三星\s*\w+\s*\d+|Galaxy\s*\w+)',
            r'(联想\s*\w+\s*\d+|ThinkPad\s*\w+|Yoga\s*\w+)',
            r'(戴尔\s*\w+\s*\d+|惠普\s*\w+\s*\d+|华硕\s*\w+\s*\d+)',
            r'(罗技\s*\w+\s*\d+|Logitech\s*\w+)',
            r'(维达\s*\w+\s*\d+|Vinda\s*\w+)',
            r'(晨光\s*\w+\s*\d+|M&G\s*\w+)',
            r'(海飞丝\s*\w+|多芬\s*\w+)',
            r'(蓝月亮\s*\w+|立白\s*\w+)',
            r'(雀巢\s*\w+|麦斯威尔\s*\w+)',
            r'(可口可乐\s*\w+|百事\s*\w+)',
            r'(云南白药\s*\w+)',
            r'(得力\s*\w+|真彩\s*\w+)',
            r'(杜蕾斯|杰士邦|冈本|第六感|大象|名流|倍力乐|赤尾|尚牌|诺丝|第6感|高邦|双蝶|多乐士|挑战者|私激|涩井|相模|丸|零感|超薄|至尊|air|001|002|003|超润|热感|冰感|螺纹|颗粒|凸点|延时|持久|玻尿酸|润滑|草莓|香草|巧克力|薄荷|橙味|苹果|香蕉|葡萄|柠檬|蜜桃|樱花|玫瑰|茉莉|薰衣草|芦荟|胶原|蛋白|维生素|维E|维C|玻尿酸|水溶|硅油|乳胶|聚氨酯|天然胶乳|橡胶|男用|女用|男女|情趣|计生|成人|安全套|避孕套|避孕|套套|tt)',
        ]
        for pattern in model_patterns:
            matches = re.findall(pattern, title, re.IGNORECASE)
            for m in matches:
                if isinstance(m, tuple):
                    m = ''.join(m)
                m = m.strip().lower()
                if len(m) >= 2:
                    keyword_counter[m] += 3

        # 提取品类名（只用最后一级）
        if p.category_name and p.category_name != "未分类":
            cat = p.category_name.split("-")[-1] if "-" in p.category_name else p.category_name
            if len(cat) >= 2:
                keyword_counter[cat] += 2

    # 3. 过滤无效词
    skip_words = {
        '商品', '产品', '购买', '正品', '包邮', '现货', '全新', '官方', '旗舰', '自营',
        '京东', '淘宝', '天猫', '店铺', '旗舰店', '全国', '联保', '以旧换新', '百亿补贴',
        '限时', '秒杀', '优惠', '套餐', '礼盒', '赠品', '顺丰', '新品', '折扣', '原装',
        '国行', '授权', '直营', '到手价', '预售', '通用', '适用', '适配', '兼容', '颜色',
        '黑色', '白色', '蓝色', '红色', '绿色', '粉色', '灰色', '金色', '银色',
        '手机', '电脑', '平板', '全部', '耳机', '键盘', '鼠标', '充电', '蓝牙',
        '无线', '有线', '配置', '版本', '款式', '型号', '品牌', '容量', '内存', '存储',
        '经典', '新款', '最新', '爆款', '热销', '人气', '推荐', '排行', '榜首',
        '冠军', '第一', '首选', '必买', '值得', '性价比', '实惠', '便宜', '划算',
        '支持', '提供', '赠送', '附赠', '额外', '附加', '配件', '礼包', '大礼包',
        'air', 'pro', 'max', 'mini', 'plus', 'ultra', 'lite', 'se',
    }
    for w in skip_words:
        keyword_counter.pop(w, None)

    ranking = [kw for kw, _ in keyword_counter.most_common(limit)]
    result = [{"keyword": kw, "count": keyword_counter[kw], "rank": i + 1} for i, kw in enumerate(ranking)]
    return ApiResponse.success(result)


@app.get("/recommendations/personalized", summary="获取个性化推荐", tags=["推荐"], response_model=ApiResponse[PaginatedResponse[Product]])
def personalized_recommendations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: Optional[User] = Depends(optional_get_current_user),
):
    import random

    product_index = {p.product_id: p for p in data.products}
    category_scores: dict[str, int] = {}

    if user is not None:
        for fav in data.favorites:
            if fav.user_id == user.user_id:
                product = product_index.get(fav.product_id)
                if product and product.category_name:
                    category_scores[product.category_name] = category_scores.get(product.category_name, 0) + 3

        for bh in data.browse_history:
            if bh.user_id == user.user_id:
                product = product_index.get(bh.product_id)
                if product and product.category_name:
                    category_scores[product.category_name] = category_scores.get(product.category_name, 0) + 1

    if category_scores:
        pref_products = [p for p in data.products if category_scores.get(p.category_name or "", 0) > 0]
        other_products = [p for p in data.products if category_scores.get(p.category_name or "", 0) == 0]
        random.shuffle(pref_products)
        random.shuffle(other_products)
        shuffled = pref_products + other_products
    else:
        shuffled = list(data.products)
        random.shuffle(shuffled)

    # 优先展示有比价关系的商品（跨平台商品排前面），同级内随机排序
    shuffled.sort(
        key=lambda p: ((1 if (p.price_diff and p.price_diff > 0) else 0), random.random()),
        reverse=True,
    )

    paged = paginate(shuffled, page, page_size)
    return ApiResponse.success(paged)


@app.post("/analytics/events", summary="上报用户行为", tags=["分析"], response_model=ApiResponse[None])
def report_event(event: AnalyticsEvent = Body(...), user: Optional[User] = Depends(optional_get_current_user)):
    data.add_analytics_event(event)
    return ApiResponse.success(None, message="上报成功")
