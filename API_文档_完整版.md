# 《一次买够》网购比价平台 - 前端 API 文档 v2.0

> 本文档以项目 `src/api/index.ts` 为基准，对标 `openapi.json` 校验后生成。供后端开发人员参考需要实现的接口及数据格式。

---

## 目录
1. [通用规范](#1-通用规范)
2. [认证模块（auth）](#2-认证模块auth)
3. [商品模块（product）](#3-商品模块product)
4. [搜索模块（search）](#4-搜索模块search)
5. [用户模块（user）](#5-用户模块user)
6. [收藏模块（favorite）](#6-收藏模块favorite)
7. [降价提醒模块（priceAlert）](#7-降价提醒模块pricealert)
8. [浏览历史模块（browseHistory）](#8-浏览历史模块browsehistory)
9. [搜索记录模块（searchRecord）](#9-搜索记录模块searchrecord)
10. [推荐模块（recommendation）](#10-推荐模块recommendation)
11. [分析模块（analytics）](#11-分析模块analytics)

---

## 1. 通用规范

### 1.1 环境

| 环境 | 地址 |
|------|------|
| 生产 | `https://api.ycg.com/api/v1` |
| 测试 | `https://test-api.ycg.com/api/v1` |
| 开发 | `http://localhost:8080/api/v1` |

### 1.2 统一响应格式 `ApiResponse<T>`

```typescript
interface ApiResponse<T = any> {
  code: number;    // 0=成功，非0=失败
  message: string; // 提示信息
  data: T;         // 业务数据
}
```

### 1.3 分页响应格式 `PaginatedResponse<T>`

所有列表类接口均使用此结构：

```typescript
interface PaginatedResponse<T> {
  list: T[];       // 数据列表
  pagination: {
    page: number;        // 当前页（从1开始）
    page_size: number;   // 每页数量
    total: number;       // 总数
    total_pages: number; // 总页数
    has_next: boolean;   // 是否有下一页
    has_prev: boolean;   // 是否有上一页
  };
}
```

### 1.4 鉴权

除特别标注外，所有接口均需在请求头中携带：

```http
Authorization: Bearer {access_token}
```

---

## 2. 认证模块（auth）

### 2.1 微信登录

```typescript
authApi.login(data: LoginRequest): Promise<ApiResponse<LoginResponse>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `POST /auth/login` |
| **需要鉴权** | 否 |

**请求体 `LoginRequest`：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `code` | string | ✅ | 微信授权 code |
| `raw_data` | string | ✅ | 微信原始数据 |
| `signature` | string | ✅ | 微信签名 |

**响应 `LoginResponse`：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `access_token` | string | JWT 访问令牌 |
| `refresh_token` | string | 刷新令牌 |
| `expires_in` | number | 令牌有效期（秒） |
| `user_id` | number | 用户唯一 ID |
| `openid` | string | 微信 OpenID |

### 2.2 刷新 Token

```typescript
authApi.refresh(refresh_token: string): Promise<ApiResponse<{ access_token, refresh_token, expires_in }>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `POST /auth/refresh` |
| **需要鉴权** | 否 |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `refresh_token` | string | ✅ | 刷新令牌 |

**响应：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `access_token` | string | 新的 JWT 访问令牌 |
| `refresh_token` | string | 新的刷新令牌 |
| `expires_in` | number | 有效期（秒） |

### 2.3 登出

```typescript
authApi.logout(): Promise<ApiResponse<null>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `POST /auth/logout` |
| **需要鉴权** | ✅ |

**响应**：data 为 `null`。

---

## 3. 商品模块（product）

### 3.1 商品搜索

```typescript
productApi.search(params: SearchParams): Promise<ApiResponse<PaginatedResponse<Product>>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /products/search` |
| **需要鉴权** | 否 |

**查询参数 `SearchParams`：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `keyword` | string | ✅ | 搜索关键词（1~100字符） |
| `page` | number | | 页码，默认 1 |
| `page_size` | number | | 每页数量，默认 20，最大 100 |
| `category_id` | number | | 分类 ID 筛选 |
| `min_price` | number | | 最低价格筛选 |
| `max_price` | number | | 最高价格筛选 |
| `platform` | string | | 平台筛选，多平台逗号分隔（如 `taobao,jingdong`） |
| `sort` | enum | | 排序方式：`price_asc` / `price_desc` / `sales_desc` / `rating_desc` |

**返回的 `Product` 数据结构：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `product_id` | string | ✅ | 商品唯一 ID（如 `SKU20250315001`） |
| `title` | string | ✅ | 商品标题 |
| `category_id` | number | ✅ | 分类 ID |
| `category_name` | string | | 分类名称 |
| `image_url` | string | ✅ | 商品主图 URL |
| `images` | string[] | | 多张商品图片 |
| `platforms` | Platform[] | ✅ | 多平台比价列表 |
| `min_price` | number | ✅ | 最低价 |
| `max_price` | number | ✅ | 最高价 |
| `price_diff` | number | | 最高价与最低价差价 |
| `best_platform` | string | | 最优价平台名称 |
| `description` | string | | 商品描述 |
| `specs` | object | | 规格信息（键值对） |
| `created_at` | string | ✅ | 创建时间（ISO 8601） |
| `updated_at` | string | ✅ | 更新时间（ISO 8601） |

**子结构 `Platform`（平台比价信息）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `platform_id` | number | ✅ | 平台 ID：1=淘宝 2=京东 3=拼多多 4=亚马逊 5=其他 |
| `platform_name` | string | ✅ | 平台名称（淘宝/京东/拼多多/亚马逊/其他） |
| `platform_code` | string | ✅ | 平台代码（taobao/jingdong/pinduoduo/amazon/other） |
| `price` | number | ✅ | 当前售价（元） |
| `original_price` | number | | 原价（元） |
| `discount_rate` | number | | 折扣率（百分比，如 25 表示 7.5 折） |
| `sales_volume` | number | | 30 天内销量 |
| `seller_name` | string | | 卖家/店铺名称 |
| `seller_rating` | number | | 卖家评分（0~5） |
| `seller_id` | string | | 卖家 ID |
| `product_url` | string | | 该平台商品详情页链接 |
| `in_stock` | boolean | ✅ | 是否有货 |
| `stock_quantity` | number | | 库存数量 |
| `update_at` | string | ✅ | 该平台信息更新时间 |

### 3.2 商品详情

```typescript
productApi.detail(product_id: string): Promise<ApiResponse<Product>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /products/{product_id}` |
| **需要鉴权** | 否 |

**路径参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `product_id` | string | ✅ | 商品 ID |

**返回**：单个 `Product` 对象（结构同 3.1）。

### 3.3 商品分类

```typescript
productApi.categories(parent_id: number): Promise<ApiResponse<Category[]>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /products/categories` |
| **需要鉴权** | 否 |

**查询参数：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `parent_id` | number | 0 | 父分类 ID，0=获取顶级分类 |

**返回的 `Category` 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `category_id` | number | 分类 ID |
| `name` | string | 分类名称 |
| `parent_id` | number | 父分类 ID，0 表示顶级 |
| `children` | Category[] | 子分类列表（可选） |

---

## 4. 搜索模块（search）

### 4.1 热搜词

```typescript
searchApi.hotWords(limit: number): Promise<ApiResponse<HotWord[]>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /search/hot-words` |
| **需要鉴权** | 否 |

**查询参数：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `limit` | number | 10 | 返回数量，最大 50 |

**返回的 `HotWord` 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `keyword` | string | 热搜关键词 |
| `count` | number | 搜索次数/热度 |
| `rank` | number | 排名 |

---

## 5. 用户模块（user）

### 5.1 获取用户信息

```typescript
userApi.getProfile(): Promise<ApiResponse<User>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /users/profile` |
| **需要鉴权** | ✅ |

**返回的 `User` 结构：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `user_id` | number | ✅ | 用户唯一 ID |
| `openid` | string | ✅ | 微信 OpenID |
| `nick_name` | string | ✅ | 昵称 |
| `avatar_url` | string | | 头像 URL |
| `gender` | number | | 性别：0=女 1=男 2=保密 |
| `province` | string | | 省份 |
| `city` | string | | 城市 |
| `created_at` | string | ✅ | 注册时间 |
| `updated_at` | string | ✅ | 最后更新时间 |
| `vip_level` | number | ✅ | VIP 等级：0=普通 1=VIP |
| `vip_expire_at` | string | | VIP 到期时间（null 表示未开通） |

### 5.2 更新用户信息

```typescript
userApi.updateProfile(data: UpdateUserRequest): Promise<ApiResponse<User>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `PUT /users/profile` |
| **需要鉴权** | ✅ |

**请求体 `UpdateUserRequest`（所有字段均可选）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `nick_name` | string | 新昵称 |
| `avatar_url` | string | 新头像 URL |
| `gender` | number | 性别：0=未知 1=男 2=女 |

---

## 6. 收藏模块（favorite）

### 6.1 获取收藏列表

```typescript
favoriteApi.list(page, page_size): Promise<ApiResponse<PaginatedResponse<Favorite>>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /users/favorites` |
| **需要鉴权** | ✅ |

**查询参数**：`page`（默认 1）、`page_size`（默认 20，最大 100）。

**返回的 `Favorite` 结构：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `favorite_id` | number | ✅ | 收藏记录 ID |
| `user_id` | number | ✅ | 用户 ID |
| `product_id` | string | ✅ | 商品 ID |
| `product_title` | string | | 商品标题 |
| `product_image` | string | | 商品主图 |
| `product_min_price` | number | | 商品当前最低价 |
| `notes` | string | | 收藏备注 |
| `created_at` | string | ✅ | 收藏时间 |
| `updated_at` | string | ✅ | 更新时间 |

### 6.2 添加收藏

```typescript
favoriteApi.add(data: AddFavoriteRequest): Promise<ApiResponse<Favorite>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `POST /users/favorites` |
| **需要鉴权** | ✅ |

**请求体 `AddFavoriteRequest`：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `product_id` | string | ✅ | 要收藏的商品 ID |
| `notes` | string | | 收藏备注（可选） |

### 6.3 更新收藏备注

```typescript
favoriteApi.update(favorite_id, data: UpdateFavoriteRequest): Promise<ApiResponse<Favorite>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `PUT /users/favorites/{favorite_id}` |
| **需要鉴权** | ✅ |

**路径参数**：`favorite_id`（收藏记录 ID）。

**请求体 `UpdateFavoriteRequest`：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `notes` | string | ✅ | 新的备注内容 |

### 6.4 取消收藏

```typescript
favoriteApi.remove(favorite_id: number): Promise<ApiResponse<null>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `DELETE /users/favorites/{favorite_id}` |
| **需要鉴权** | ✅ |

**路径参数**：`favorite_id`。

---

## 7. 降价提醒模块（priceAlert）

### 7.1 获取降价提醒列表

```typescript
priceAlertApi.list(page, page_size, status): Promise<ApiResponse<PaginatedResponse<PriceAlert>>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /users/price-alerts` |
| **需要鉴权** | ✅ |

**查询参数：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | number | 1 | 页码 |
| `page_size` | number | 20 | 每页数量，最大 100 |
| `status` | enum | `all` | 状态筛选：`all` / `triggered` / `untriggered` |

**返回的 `PriceAlert` 结构：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `alert_id` | number | ✅ | 提醒 ID |
| `user_id` | number | ✅ | 用户 ID |
| `product_id` | string | ✅ | 商品 ID |
| `product_title` | string | | 商品标题 |
| `target_price` | number | ✅ | 目标价格（元），低于此价触发 |
| `current_price` | number | | 当前最低价格（元） |
| `is_triggered` | boolean | ✅ | 是否已触发 |
| `triggered_at` | string | | 触发时间（未触发为 null） |
| `is_enabled` | boolean | ✅ | 是否启用 |
| `platform_filter` | string[] | | 监控的平台列表（空=全部） |
| `created_at` | string | ✅ | 创建时间 |
| `updated_at` | string | ✅ | 更新时间 |

### 7.2 创建降价提醒

```typescript
priceAlertApi.create(data: CreatePriceAlertRequest): Promise<ApiResponse<PriceAlert>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `POST /users/price-alerts` |
| **需要鉴权** | ✅ |

**请求体 `CreatePriceAlertRequest`：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `product_id` | string | ✅ | 商品 ID |
| `target_price` | number | ✅ | 目标价格（元） |
| `platform_filter` | string[] | | 监控平台列表，如 `["taobao","jingdong"]` |

### 7.3 更新降价提醒

```typescript
priceAlertApi.update(alert_id, data: UpdatePriceAlertRequest): Promise<ApiResponse<PriceAlert>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `PUT /users/price-alerts/{alert_id}` |
| **需要鉴权** | ✅ |

**路径参数**：`alert_id`。

**请求体 `UpdatePriceAlertRequest`（所有字段均可选）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `target_price` | number | 新的目标价格 |
| `is_enabled` | boolean | 是否启用提醒 |

### 7.4 删除降价提醒

```typescript
priceAlertApi.delete(alert_id: number): Promise<ApiResponse<null>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `DELETE /users/price-alerts/{alert_id}` |
| **需要鉴权** | ✅ |

**路径参数**：`alert_id`。

---

## 8. 浏览历史模块（browseHistory）

### 8.1 获取浏览历史

```typescript
browseHistoryApi.list(page, page_size): Promise<ApiResponse<PaginatedResponse<BrowseHistory>>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /users/browse-history` |
| **需要鉴权** | ✅ |

**查询参数**：`page`、`page_size`。

**返回的 `BrowseHistory` 结构：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `history_id` | number | ✅ | 记录 ID |
| `user_id` | number | ✅ | 用户 ID |
| `product_id` | string | ✅ | 商品 ID |
| `product_title` | string | | 商品标题 |
| `product_image` | string | | 商品主图 |
| `viewed_at` | string | ✅ | 浏览时间（ISO 8601） |

### 8.2 添加浏览历史

```typescript
browseHistoryApi.add(data: AddBrowseHistoryRequest): Promise<ApiResponse<null>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `POST /users/browse-history` |
| **需要鉴权** | ✅ |

**请求体：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `product_id` | string | ✅ | 浏览的商品 ID |

### 8.3 清除浏览历史

```typescript
browseHistoryApi.clear(): Promise<ApiResponse<null>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `DELETE /users/browse-history` |
| **需要鉴权** | ✅ |

**返回**：data 为 `null`。

---

## 9. 搜索记录模块（searchRecord）

### 9.1 获取搜索记录

```typescript
searchRecordApi.list(page, page_size): Promise<ApiResponse<PaginatedResponse<SearchRecord>>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /users/search-records` |
| **需要鉴权** | ✅ |

**查询参数**：`page`、`page_size`。

**返回的 `SearchRecord` 结构：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `record_id` | number | ✅ | 记录 ID |
| `user_id` | number | ✅ | 用户 ID |
| `keyword` | string | ✅ | 搜索关键词 |
| `search_count` | number | ✅ | 搜索次数 |
| `created_at` | string | ✅ | 首次搜索时间 |
| `updated_at` | string | ✅ | 最近搜索时间 |

---

## 10. 推荐模块（recommendation）

### 10.1 个性化推荐

```typescript
recommendationApi.personalized(page, page_size): Promise<ApiResponse<PaginatedResponse<Product>>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `GET /recommendations/personalized` |
| **需要鉴权** | ✅ |

**查询参数**：`page`（默认 1）、`page_size`（默认 20）。

**返回**：分页的 `Product[]` 列表（结构同 3.1）。

---

## 11. 分析模块（analytics）

### 11.1 上报用户行为

```typescript
analyticsApi.track(data: TrackEventRequest): Promise<ApiResponse<null>>
```

| 项目 | 说明 |
|------|------|
| **方法/路径** | `POST /analytics/events` |
| **需要鉴权** | ✅ |

**请求体 `TrackEventRequest`：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `event_type` | string | ✅ | 事件类型：`search` / `product_click` / `add_favorite` / `remove_favorite` / `alert_set` / `purchase_redirect` |
| `product_id` | string | | 关联商品 ID（与商品相关事件时使用） |
| `platform` | string | | 平台代码（点击平台时使用） |
| `timestamp` | string | ✅ | 事件发生时间（ISO 8601） |
| `metadata` | object | | 附加元数据（如搜索事件携带 keyword） |

---

## 附录：接口完整一览

| # | 模块 | 方法 | 路径 | 鉴权 |
|---|------|------|------|:--:|
| 1 | 认证 | POST | `/auth/login` | ❌ |
| 2 | 认证 | POST | `/auth/refresh` | ❌ |
| 3 | 认证 | POST | `/auth/logout` | ✅ |
| 4 | 商品 | GET | `/products/search` | ❌ |
| 5 | 商品 | GET | `/products/{product_id}` | ❌ |
| 6 | 商品 | GET | `/products/categories` | ❌ |
| 7 | 搜索 | GET | `/search/hot-words` | ❌ |
| 8 | 用户 | GET | `/users/profile` | ✅ |
| 9 | 用户 | PUT | `/users/profile` | ✅ |
| 10 | 收藏 | GET | `/users/favorites` | ✅ |
| 11 | 收藏 | POST | `/users/favorites` | ✅ |
| 12 | 收藏 | PUT | `/users/favorites/{favorite_id}` | ✅ |
| 13 | 收藏 | DELETE | `/users/favorites/{favorite_id}` | ✅ |
| 14 | 降价提醒 | GET | `/users/price-alerts` | ✅ |
| 15 | 降价提醒 | POST | `/users/price-alerts` | ✅ |
| 16 | 降价提醒 | PUT | `/users/price-alerts/{alert_id}` | ✅ |
| 17 | 降价提醒 | DELETE | `/users/price-alerts/{alert_id}` | ✅ |
| 18 | 浏览历史 | GET | `/users/browse-history` | ✅ |
| 19 | 浏览历史 | POST | `/users/browse-history` | ✅ |
| 20 | 浏览历史 | DELETE | `/users/browse-history` | ✅ |
| 21 | 搜索记录 | GET | `/users/search-records` | ✅ |
| 22 | 推荐 | GET | `/recommendations/personalized` | ✅ |
| 23 | 分析 | POST | `/analytics/events` | ✅ |

---

> **文档版本**：v2.0 | **基准文件**：`src/api/index.ts` + `src/api/types.ts` | **对标规范**：`openapi.json` v1.0.0 | **校验结果**：23/23 端点一致，类型字段已修复对齐