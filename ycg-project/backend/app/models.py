from __future__ import annotations

import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DECIMAL, DateTime, ForeignKey, JSON, Boolean,
    Index, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    match_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category_name: Mapped[str] = mapped_column(String(128), nullable=False, default="未分类")
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    images: Mapped[str | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    specs: Mapped[str | None] = mapped_column(JSON, nullable=True)
    min_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)
    max_price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)
    price_diff: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)
    best_platform: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    offers: Mapped[list["PlatformOfferModel"]] = relationship(back_populates="product", lazy="selectin")
    price_records: Mapped[list["PriceHistoryModel"]] = relationship(back_populates="product", lazy="selectin")

    __table_args__ = (
        Index("idx_products_match", "match_fingerprint"),
        Index("idx_products_title", "title"),
    )


class PlatformOfferModel(Base):
    __tablename__ = "platform_offers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(32), ForeignKey("products.product_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    platform_id: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_name: Mapped[str] = mapped_column(String(32), nullable=False)
    platform_code: Mapped[str] = mapped_column(String(16), nullable=False)
    source_sku_id: Mapped[str] = mapped_column(String(256), nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, default=0)
    original_price: Mapped[float | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    discount_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sales_volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    seller_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    seller_rating: Mapped[float | None] = mapped_column(DECIMAL(3, 2), nullable=True)
    seller_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    product_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    stock_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    product: Mapped["ProductModel"] = relationship(back_populates="offers")

    __table_args__ = (
        UniqueConstraint("platform_code", "source_sku_id", name="uk_offer_source"),
        Index("idx_offer_product", "product_id"),
    )


class PriceHistoryModel(Base):
    __tablename__ = "price_history"

    record_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(32), ForeignKey("products.product_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    platform_code: Mapped[str] = mapped_column(String(16), nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    promo_info: Mapped[str | None] = mapped_column(String(255), nullable=True)
    crawl_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    product: Mapped["ProductModel"] = relationship(back_populates="price_records")

    __table_args__ = (
        Index("idx_price_product_time", "product_id", "crawl_time"),
    )