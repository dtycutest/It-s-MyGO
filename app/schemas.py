from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, HttpUrl

"""
Schema definitions aligned with openapi.json.
Field descriptions keep the original Chinese wording from the requirement doc;
see README for the English overview of each domain object.
"""


class Platform(BaseModel):
    platform_id: int = Field(..., description="平台ID")
    platform_name: str = Field(..., description="平台名称")
    platform_code: str = Field(..., description="平台代码")
    price: float = Field(..., ge=0, description="当前价格")
    original_price: Optional[float] = Field(None, ge=0, description="原价")
    discount_rate: Optional[int] = Field(None, ge=0, le=100, description="折扣率")
    in_stock: bool = True
    product_url: Optional[HttpUrl] = None
    seller_id: Optional[str] = None
    seller_name: Optional[str] = None
    seller_rating: Optional[float] = Field(None, ge=0, le=5)
    sales_volume: Optional[int] = Field(None, ge=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    update_at: Optional[datetime] = None


class Product(BaseModel):
    product_id: str
    title: str
    category_id: int
    category_name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    images: List[HttpUrl] = []
    min_price: float
    max_price: float
    best_platform: Optional[str] = None
    price_diff: Optional[float] = None
    specs: Dict[str, str] = {}
    platforms: List[Platform] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Category(BaseModel):
    category_id: int
    name: str
    parent_id: int = 0


class User(BaseModel):
    user_id: int
    openid: str
    nick_name: str
    avatar_url: Optional[HttpUrl] = None
    gender: int = 2
    province: Optional[str] = None
    city: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    vip_level: int = 0
    vip_expire_at: Optional[datetime] = None


class Favorite(BaseModel):
    favorite_id: int
    user_id: int
    product_id: str
    product_title: str
    product_image: Optional[HttpUrl] = None
    product_min_price: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PriceAlert(BaseModel):
    alert_id: int
    user_id: int
    product_id: str
    product_title: str
    target_price: float
    current_price: Optional[float] = None
    platform_filter: Optional[List[str]] = None
    is_enabled: bool = True
    is_triggered: bool = False
    triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class BrowseHistoryItem(BaseModel):
    history_id: int
    product_id: str
    product_title: str
    viewed_at: datetime


class SearchRecord(BaseModel):
    keyword: str
    searched_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user_id: int
    openid: str


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    list: List[T]
    pagination: Pagination


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None

    @staticmethod
    def success(data: Optional[T] = None, message: str = "ok") -> "ApiResponse[T]":
        return ApiResponse(code=0, message=message, data=data)

    @staticmethod
    def error(code: int, message: str) -> "ApiResponse[Any]":
        return ApiResponse(code=code, message=message, data=None)


class AnalyticsEvent(BaseModel):
    event_type: str
    product_id: Optional[str] = None
    platform: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
