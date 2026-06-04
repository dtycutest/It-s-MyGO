"""Load products from MySQL (with JSON fallback) and transform into backend schema objects."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List

from .schemas import Category, Platform, Product

SEED_PATH = Path(__file__).resolve().parent.parent.parent / "crawler" / "data" / "onebuy_seed_records_all.json"

PLATFORM_CODE_TO_ID: Dict[str, int] = {
    "taobao": 1,
    "jingdong": 2,
    "pinduoduo": 3,
    "amazon": 4,
    "other": 5,
}


def _is_valid_image_url(url: str | None) -> bool:
    """Check if a URL points to an actual image (not a product detail page)."""
    if not url or not isinstance(url, str) or not url.strip():
        return False
    url_lower = url.lower()
    # Must start with http/https
    if not (url_lower.startswith('http://') or url_lower.startswith('https://')):
        return False
    # Must have an image extension or be from a CDN known to serve images
    if re.search(r'\.(jpg|jpeg|png|gif|webp|avif|bmp)(\?|$|_)', url_lower, re.I):
        return True
    # Known image CDN domains
    image_cdn_patterns = [
        r'//img\d*\.360buyimg\.com/',     # JD CDN
        r'//g-search\d*\.alicdn\.com/',    # Taobao search CDN
        r'//gw\.alicdn\.com/',             # Taobao GW CDN
        r'//img\.alicdn\.com/',            # Taobao img CDN
    ]
    for pattern in image_cdn_patterns:
        if re.search(pattern, url_lower):
            return True
    # Known product page URLs are NOT images
    not_image_patterns = [
        r'//item\.jd\.com/',
        r'//item\.taobao\.com/',
        r'//detail\.tmall\.com/',
        r'//detail\.jd\.com/',
    ]
    for pattern in not_image_patterns:
        if re.search(pattern, url_lower):
            return False
    # If it has a product page-like structure, treat as non-image
    if re.search(r'/item\.htm', url_lower):
        return False
    # Unknown - accept it
    return True


def _parse_float(value: str | None) -> float | None:
    if not value or not str(value).strip():
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _parse_int(value: str | None) -> int | None:
    if not value or not str(value).strip():
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _map_platform_name(code: str) -> str:
    mapping = {
        "taobao": "淘宝",
        "jingdong": "京东",
        "pinduoduo": "拼多多",
        "amazon": "亚马逊",
        "other": "其他",
    }
    return mapping.get(code, "其他")


def _build_categories(category_names: List[str]) -> List[Category]:
    cat_map: Dict[str, int] = {}
    cat_list: List[Category] = []
    cat_id = 1

    for path in category_names:
        if not path:
            continue
        parts = path.split("-")
        for i, part in enumerate(parts):
            key = "-".join(parts[: i + 1])
            if key not in cat_map:
                parent_key = "-".join(parts[:i]) if i > 0 else ""
                parent_id = cat_map.get(parent_key, 0)
                cat_map[key] = cat_id
                cat_list.append(Category(category_id=cat_id, name=part, parent_id=parent_id))
                cat_id += 1
    return cat_list


def _load_from_json() -> tuple[List[Product], List[Category], List[dict]]:
    """Fallback: load from JSON seed file."""
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    records: List[dict] = data.get("records", [])
    category_names = list({r.get("category_text", "") for r in records if r.get("category_text")})
    categories = _build_categories(category_names)

    cat_path_to_id: Dict[str, int] = {}
    for rec in records:
        path = rec.get("category_text", "")
        if path and path not in cat_path_to_id:
            for cat in categories:
                parts = [cat.name]
                parent_id = cat.parent_id
                while parent_id:
                    parent = next((c for c in categories if c.category_id == parent_id), None)
                    if parent:
                        parts.insert(0, parent.name)
                        parent_id = parent.parent_id
                    else:
                        break
                full = "-".join(parts)
                if full == path:
                    cat_path_to_id[path] = cat.category_id
                    break

    groups: Dict[str, List[dict]] = {}
    for rec in records:
        pid = rec["product_id"]
        groups.setdefault(pid, []).append(rec)

    products: List[Product] = []
    for product_id, group in groups.items():
        first = group[0]
        title = first["title"]
        category_text = first.get("category_text", "")
        category_id = cat_path_to_id.get(category_text, 0)

        platforms: List[Platform] = []
        prices: List[float] = []

        for rec in group:
            platform_code = rec["platform_code"]
            platform_id = PLATFORM_CODE_TO_ID.get(platform_code, 5)
            platform_name = _map_platform_name(platform_code)
            price = _parse_float(rec.get("price_text")) or 0.0
            original_price = _parse_float(rec.get("original_price_text"))
            sales_volume = _parse_int(rec.get("sales_text"))

            if price > 0:
                prices.append(price)

            discount_rate = None
            if original_price and original_price > 0 and price > 0:
                discount_rate = int(max(0, min(100, (1 - price / original_price) * 100)))

            crawl_time = rec.get("crawl_time")
            update_at = None
            if crawl_time:
                try:
                    update_at = datetime.strptime(crawl_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass

            platform = Platform(
                platform_id=platform_id,
                platform_name=platform_name,
                platform_code=platform_code,
                price=price,
                original_price=original_price,
                discount_rate=discount_rate,
                in_stock=rec.get("in_stock", True),
                product_url=rec.get("product_url"),
                seller_id=rec.get("seller_id") or rec.get("source_sku_id"),
                seller_name=rec.get("seller_name") or None,
                seller_rating=_parse_float(rec.get("seller_rating_text")),
                sales_volume=sales_volume,
                stock_quantity=rec.get("stock_quantity"),
                update_at=update_at,
            )
            platforms.append(platform)

        min_price = min(prices) if prices else 0.0
        max_price = max(prices) if prices else 0.0
        price_diff = round(max_price - min_price, 2)

        best_platform = ""
        if platforms and prices:
            best_idx = prices.index(min_price)
            best_platform = platforms[best_idx].platform_name

        now = datetime.now(timezone.utc)

        raw_image_url = first.get("image_url")
        if not _is_valid_image_url(raw_image_url):
            raw_image_url = None

        product = Product(
            product_id=product_id,
            title=title,
            category_id=category_id,
            category_name=category_text,
            description="",
            image_url=raw_image_url,
            images=[raw_image_url] if raw_image_url else [],
            min_price=min_price,
            max_price=max_price,
            best_platform=best_platform,
            price_diff=price_diff,
            specs=first.get("specs") or {},
            platforms=platforms,
            created_at=now,
            updated_at=now,
        )
        products.append(product)

    return products, categories, records


def _load_from_mysql() -> tuple[List[Product], List[Category], List[dict]] | None:
    """Try loading from MySQL. Returns None if MySQL is empty or unavailable."""
    try:
        from .database import SessionLocal
        from .models import ProductModel, PlatformOfferModel
    except Exception:
        return None

    db = SessionLocal()
    try:
        products_db = db.query(ProductModel).all()
        if not products_db:
            return None

        category_names = list({p.category_name for p in products_db if p.category_name and p.category_name != "未分类"})
        categories = _build_categories(category_names)

        cat_path_to_id: Dict[str, int] = {}
        for path in category_names:
            if path in cat_path_to_id:
                continue
            for cat in categories:
                parts = [cat.name]
                parent_id = cat.parent_id
                while parent_id:
                    parent = next((c for c in categories if c.category_id == parent_id), None)
                    if parent:
                        parts.insert(0, parent.name)
                        parent_id = parent.parent_id
                    else:
                        break
                full = "-".join(parts)
                if full == path:
                    cat_path_to_id[path] = cat.category_id
                    break

        products: List[Product] = []
        raw_records: List[dict] = []

        for p in products_db:
            category_text = p.category_name or "未分类"
            category_id = cat_path_to_id.get(category_text, 0)

            platforms: List[Platform] = []
            prices: List[float] = []

            for offer in p.offers:
                price = float(offer.price)
                if price > 0:
                    prices.append(price)

                original_price = float(offer.original_price) if offer.original_price else None
                discount_rate = None
                if original_price and original_price > 0 and price > 0:
                    discount_rate = int(max(0, min(100, (1 - price / original_price) * 100)))

                platform = Platform(
                    platform_id=offer.platform_id,
                    platform_name=offer.platform_name,
                    platform_code=offer.platform_code,
                    price=price,
                    original_price=original_price,
                    discount_rate=discount_rate,
                    in_stock=offer.in_stock,
                    product_url=offer.product_url,
                    seller_id=offer.seller_id,
                    seller_name=offer.seller_name,
                    seller_rating=float(offer.seller_rating) if offer.seller_rating else None,
                    sales_volume=offer.sales_volume,
                    stock_quantity=offer.stock_quantity,
                    update_at=offer.update_at,
                )
                platforms.append(platform)

                raw_records.append({
                    "product_id": p.product_id,
                    "platform_code": offer.platform_code,
                    "platform_name": offer.platform_name,
                    "source_sku_id": offer.source_sku_id,
                    "title": p.title,
                    "price_text": str(offer.price),
                    "original_price_text": str(offer.original_price) if offer.original_price else "",
                    "sales_text": str(offer.sales_volume) if offer.sales_volume else "",
                    "seller_name": offer.seller_name or "",
                    "seller_rating_text": str(offer.seller_rating) if offer.seller_rating else "",
                    "seller_id": offer.seller_id or "",
                    "image_url": p.image_url or "",
                    "product_url": offer.product_url or "",
                    "category_text": p.category_name,
                    "promo_info": "",
                    "specs": p.specs if isinstance(p.specs, dict) else {},
                    "in_stock": offer.in_stock,
                    "stock_quantity": offer.stock_quantity,
                    "crawl_time": offer.update_at.strftime("%Y-%m-%d %H:%M:%S") if offer.update_at else "",
                })

            min_price = min(prices) if prices else 0.0
            max_price = max(prices) if prices else 0.0
            price_diff = round(max_price - min_price, 2)

            best_platform = ""
            if platforms and prices:
                best_idx = prices.index(min_price)
                best_platform = platforms[best_idx].platform_name

            images = p.images if isinstance(p.images, list) else ([p.image_url] if p.image_url else [])
            images = [img for img in images if _is_valid_image_url(img)]

            valid_image_url = p.image_url if _is_valid_image_url(p.image_url) else (images[0] if images else None)

            product = Product(
                product_id=p.product_id,
                title=p.title,
                category_id=category_id,
                category_name=category_text,
                description=p.description or "",
                image_url=valid_image_url,
                images=images,
                min_price=min_price,
                max_price=max_price,
                best_platform=best_platform,
                price_diff=price_diff,
                specs=p.specs if isinstance(p.specs, dict) else {},
                platforms=platforms,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            products.append(product)

        return products, categories, raw_records
    except Exception as e:
        print(f"[seed_loader] MySQL load failed: {e}, falling back to JSON")
        return None
    finally:
        db.close()


def _extract_model_tokens(title: str) -> set:
    """Extract model-identifying tokens from a product title."""
    t = title.lower()
    tokens = set()

    # iPhone models: iPhone 15, iPhone15, iPhone 15 Pro Max, etc
    iphone_match = re.findall(r'iphone\s*(\d+)\s*(pro)?\s*(max)?\s*(plus)?\s*(mini)?', t)
    if iphone_match:
        for m in iphone_match:
            parts = ['iphone']
            for p in m:
                if p:
                    parts.append(p)
            tokens.add('_'.join(parts))
    else:
        m = re.findall(r'iphone', t)
        if m:
            tokens.add('iphone')

    # iPad models
    m = re.findall(r'ipad\s*(air|pro|mini)?\s*(\d+)?', t)
    for model, num in m:
        if model or num:
            tokens.add(f'ipad_{model}_{num}'.strip('_'))
        else:
            tokens.add('ipad')

    # 小米/红米 models
    m = re.findall(r'(小米|红米|redmi|xiao?mi)\s*(\d+[a-z]*)', t)
    for brand, model in m:
        tokens.add(f'{brand}{model}'.replace(' ', ''))

    # 华为 models
    m = re.findall(r'(华为|huawei|mate|pura|nova|畅享)\s*(\d+[a-z]*)', t)
    for brand, model in m:
        if model:
            tokens.add(f'{brand}{model}'.replace(' ', ''))

    # 三星 models
    m = re.findall(r'(三星|samsung|galaxy)\s*(s\d+|note\d+|a\d+|z\s*(flip|fold)\d*)', t)
    for brand, model in m:
        if model:
            tokens.add(f'{brand}{model}'.replace(' ', ''))

    # 联想 models
    m = re.findall(r'(联想|lenovo|thinkpad|thinkbook|yoga|小新)\s*(\d+[a-z]*)', t)
    for brand, model in m:
        if model:
            tokens.add(f'{brand}{model}'.replace(' ', ''))

    # 戴尔/惠普/华硕 models
    m = re.findall(r'(戴尔|dell|惠普|hp|华硕|asus)\s*(\d+[a-z]*)', t)
    for brand, model in m:
        if model:
            tokens.add(f'{brand}{model}'.replace(' ', ''))

    # 罗技 models
    m = re.findall(r'(罗技|logitech)\s*(k\d+|m\d+|g\d+|mx\s*\d+)', t)
    for brand, model in m:
        if model:
            tokens.add(f'{brand}{model}'.replace(' ', ''))

    # 维达 models
    m = re.findall(r'(维达|vinda)\s*(v\d+[a-z]*)', t)
    for brand, model in m:
        if model:
            tokens.add(f'{brand}{model}'.replace(' ', ''))

    # 晨光 models
    m = re.findall(r'(晨光|m&g)\s*(k\d+|agp\w*)', t)
    for brand, model in m:
        if model:
            tokens.add(f'{brand}{model}'.replace(' ', ''))

    # 蓝月亮 models
    m = re.findall(r'蓝月亮', t)
    if m:
        m2 = re.findall(r'(\d+kg|\d+\.\d+kg|\d+g|\d+\.\d+g)', t)
        if m2:
            for spec in m2:
                tokens.add(f'蓝月亮_{spec}')
        else:
            tokens.add('蓝月亮')

    # 云南白药
    m = re.findall(r'云南白药', t)
    if m:
        tokens.add('云南白药牙膏')

    # 海飞丝
    m = re.findall(r'海飞丝', t)
    if m:
        m2 = re.findall(r'(\d+ml|\d+\.\d+ml|\d+g|\d+\.\d+g)', t)
        if m2:
            for spec in m2:
                tokens.add(f'海飞丝_{spec}')
        else:
            tokens.add('海飞丝')

    # 多芬
    m = re.findall(r'多芬', t)
    if m:
        m2 = re.findall(r'(\d+ml|\d+\.\d+ml|\d+g|\d+\.\d+g)', t)
        if m2:
            for spec in m2:
                tokens.add(f'多芬_{spec}')
        else:
            tokens.add('多芬')

    # 雀巢咖啡
    m = re.findall(r'雀巢', t)
    if m:
        tokens.add('雀巢咖啡')

    # 可口可乐
    m = re.findall(r'可口可乐|coca.cola', t)
    if m:
        m2 = re.findall(r'(\d+ml|\d+\.\d+ml|\d+罐|\d+瓶)', t)
        if m2:
            for spec in m2:
                tokens.add(f'可乐_{spec}')
        else:
            tokens.add('可口可乐')

    # 余华/活着
    m = re.findall(r'余华|活着', t)
    if m:
        tokens.add('余华_活着')

    # Storage capacity
    m = re.findall(r'(\d+gb|\d+tb|\d+g)', t)
    for cap in m:
        tokens.add(cap)

    # General spec: weight/size
    m = re.findall(r'(\d+ml|\d+\.\d+ml|\d+l|\d+\.\d+l)', t)
    for spec in m:
        tokens.add(spec)

    # 5G / 全网通 etc - these are too generic, skip
    # But keep things like "英寸" with preceding number
    m = re.findall(r'(\d+\.?\d*英寸)', t)
    for spec in m:
        tokens.add(spec)

    return tokens


def _extract_keywords(title: str) -> set:
    """Extract meaningful keywords from title (after removing brackets/promos)."""
    t = title.lower()
    # Remove promo text in brackets
    t = re.sub(r'[【\[（(][^】\]）)]*[】\]）)]', ' ', t)
    t = re.sub(r'[，,。.、/；;：:！!？?]', ' ', t)

    noise = ['正品', '包邮', '现货', '全新', '官方', '旗舰', '自营', '京东', '淘宝',
             '天猫', '店铺', '旗舰店', '全国', '联保', '以旧换新', '百亿补贴', '限时',
             '秒杀', '优惠', '套餐', '礼盒', '赠品', '顺丰', '新品', '折扣', '原装',
             '国行', '授权', '直营', '到手价', '预售', '花呗', '三期', '免息', '碎屏险',
             '质保', '配件', '礼包', '行情', '报价', '价格', '评测', '京配', '速发',
             '公开版', '支持', '分期', '首付', '资源机', '限时', '抢购', '补贴', '直营',
             '优惠', '赠', '送', '商品', '产品', '购买', '双卡', '双待', '美版', '无锁',
             '中国', '移动', '联通', '电信', '手机', '平板', '电脑', '蓝牙', '键盘',
             '充电', '移动电源', '充电宝', '适用', '适配', '通用', '兼容', '颜色',
             '黑色', '白色', '蓝色', '红色', '绿色', '粉色', '灰色', '金色', '银色',
             '原色', '钛金属', '钛', '金色', '紫色', '黄色', '橙色', '棕色', '网通',
             '双卡双待', '全网通', 'apple', '苹果', 'android', '安卓', 'type-c', 'typec',
             'usb', 'micro', 'lightning', '快充', '闪充', '无线', '有线', 'type',
             '品牌', '型号', '款式', '版本', '高配', '低配', '标配', '顶配', '配置',
             '容量', '内存', '存储', '运行', '处理器', '芯片', 'cpu', 'gpu', '屏幕',
             '显示器', '显示', '分辨率', '高清', '超清', '4k', '2k', '1080p', '720p',
             '电池', '续航', '待机', '充电器', '数据线', '耳机', '充电头', '充电线',
             '保护壳', '保护套', '贴膜', '钢化膜', '手机壳', '手机套', '手机膜',
             '套装', '组合', '搭配', '选择', '备注', '留言', '咨询', '客服',
             '免邮', '快递', '物流', '发货', '配送', '自提', '门店', '线下', '实体',
             '体验', '试用', '退换', '保修', '售后', '服务', '保障', '放心', '安心',
             '品质', '质量', '正品保证', '假一赔十', '假一赔三', '假一赔百', '支持',
             '提供', '赠送', '附赠', '额外', '附加', '配件', '礼包', '大礼包',
             'g', 'gb', 'kg', 'ml', 'l', 'mm', 'cm', 'm', '寸', '英寸', '吋',
             '经典', '新款', '最新', '爆款', '热销', '人气', '推荐', '排行', '榜首',
             '冠军', '第一', '首选', '必买', '值得', '性价比', '实惠', '便宜', '划算',
             '超值', '特价', '促销', '活动', '618', '双11', '双十二', '年货', '春节',
             '元旦', '五一', '十一', '国庆', '中秋', '端午', '清明', '圣诞', '元旦',
             '过年', '开学', '毕业', '实习', '上班', '办公', '家用', '学生', '儿童',
             '成人', '老人', '男士', '女士', '男女', '中性', '通用', '便携', '迷你',
             '小型', '大型', '超薄', '轻薄', '厚重', '大容量', '小容量', '标准', '普通',
             '基础', '入门', '高级', '专业', '旗舰', '至尊', '豪华', '尊享', '尊贵',
             '定制', '个性化', '定制logo', '定制图案', '定制文字', '定制颜色', '定制款式',
             '国行正品', '官方正品', '正品保证', '正品保障', '正品授权', '官方授权',
             '官方旗舰', '官方旗舰店', '官方直营', '官方直营店', '官方自营', '官方自营店',
             '店保', '年', '年+', '店保年', '配件礼包+店保年', '全网通+配件礼包',
             '全网通+质保年+配件礼包',
            ]
    noise = {w.lower() for w in noise}

    tokens = set()
    for part in t.split():
        part = part.strip()
        if len(part) >= 2 and part not in noise:
            tokens.add(part)
    return tokens


def _enhance_cross_platform(products: List[Product]) -> List[Product]:
    """Merge products that are the same item across platforms using model tokens.

    Strategy:
    1. Extract model tokens from each title (iPhone model, capacity, brand+model)
    2. Match products with shared model tokens
    3. Price must be within 40% of each other
    4. Same category required
    5. Best match wins (most tokens shared, closest price)
    """
    if len(products) < 2:
        return products

    # Build token index for each product
    product_tokens: dict[str, set] = {}
    for p in products:
        model_tokens = _extract_model_tokens(p.title)
        if model_tokens:
            product_tokens[p.product_id] = model_tokens

    single_platform = [p for p in products if len({pl.platform_code for pl in p.platforms}) <= 1]
    if len(single_platform) < 2:
        return products

    merged_pids: set = set()
    matched_pairs: list[tuple[int, float, Product, Product]] = []

    for i, p1 in enumerate(single_platform):
        if p1.product_id in merged_pids:
            continue
        p1_platforms = {pl.platform_code for pl in p1.platforms}
        t1 = product_tokens.get(p1.product_id, set())
        if len(t1) < 1:
            continue

        p1_price = p1.min_price if p1.min_price > 0 else p1.max_price
        if p1_price <= 0:
            continue

        best_match = None
        best_score = 0.0

        for j, p2 in enumerate(single_platform):
            if i == j or p2.product_id in merged_pids:
                continue
            p2_platforms = {pl.platform_code for pl in p2.platforms}
            if p1_platforms == p2_platforms:
                continue

            t2 = product_tokens.get(p2.product_id, set())
            if len(t2) < 1:
                continue

            common = t1 & t2
            if len(common) < 1:
                continue

            union = t1 | t2
            jaccard = len(common) / len(union) if union else 0

            p2_price = p2.min_price if p2.min_price > 0 else p2.max_price
            if p2_price <= 0:
                continue
            price_ratio = min(p1_price, p2_price) / max(p1_price, p2_price)

            if price_ratio < 0.55:
                continue

            if p1.category_name != p2.category_name:
                continue

            # Score: more shared tokens + better price similarity
            score = len(common) * 0.6 + price_ratio * 0.4

            if score > best_score:
                best_score = score
                best_match = (len(common), price_ratio, p1, p2)

        if best_match:
            matched_pairs.append(best_match)

    matched_pairs.sort(key=lambda x: (x[0], x[1]), reverse=True)

    used_pids: set = set()
    for common_count, price_ratio, p1, p2 in matched_pairs:
        if p1.product_id in used_pids or p2.product_id in used_pids:
            continue
        if p1.product_id in merged_pids or p2.product_id in merged_pids:
            continue

        p1_platform_codes = {pl.platform_code for pl in p1.platforms}
        for pl in p2.platforms:
            if pl.platform_code not in p1_platform_codes:
                p1.platforms.append(pl)
                p1_platform_codes.add(pl.platform_code)

        prices = [pl.price for pl in p1.platforms if pl.price > 0]
        if prices:
            p1.min_price = min(prices)
            p1.max_price = max(prices)
            p1.price_diff = round(p1.max_price - p1.min_price, 2)
            best_idx = prices.index(p1.min_price)
            p1.best_platform = p1.platforms[best_idx].platform_name

        p2_images = p2.images if isinstance(p2.images, list) else []
        p1_images = p1.images if isinstance(p1.images, list) else []
        for img in p2_images:
            if img not in p1_images:
                p1_images.append(img)
        p1.images = p1_images

        merged_pids.add(p2.product_id)
        used_pids.add(p1.product_id)
        used_pids.add(p2.product_id)

    if merged_pids:
        print(f"[seed_loader] Cross-platform merge: {len(merged_pids)} products merged")

    result = [p for p in products if p.product_id not in merged_pids]
    return result


def load_seed() -> tuple[List[Product], List[Category], List[dict]]:
    """Load seed data: try MySQL first, fall back to JSON."""
    mysql_result = _load_from_mysql()
    if mysql_result is not None:
        print("[seed_loader] Loaded data from MySQL")
        products, categories, records = mysql_result
    else:
        print("[seed_loader] Loading data from JSON seed file")
        products, categories, records = _load_from_json()

    products = _enhance_cross_platform(products)
    return products, categories, records