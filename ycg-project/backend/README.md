# 一次买够 — 后端 API 服务

## 项目简介

本后端服务是"一次买够"网购比价平台的核心 API 层，基于 FastAPI + Uvicorn 开发，为微信小程序前端提供 RESTful API 接口。

后端作为数据中枢，从 MySQL 数据库（或内置种子数据）加载商品，通过 33 个 API 接口为前端提供商品搜索、多平台比价、用户认证、收藏管理、浏览历史、降价提醒和个性化推荐等服务。前端不直接访问数据库或爬虫，所有数据均通过后端 API 获取。

## 与爬虫和前端的关系

```
┌──────────────────────────────────────────────────────────────────┐
│                    爬虫 (crawler/)                                 │
│  Scrapy + Playwright → 京东/淘宝商品采集 → 写入 MySQL               │
└────────────────────────┬─────────────────────────────────────────┘
                         │ 数据供给
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    后端 (backend/)  ← 当前项目                     │
│  FastAPI + Uvicorn                                               │
│  → 从 MySQL / 种子数据加载商品                                     │
│  → 33 个 RESTful API 接口 (OpenAPI 3.0)                           │
│  → JWT 认证 + 微信 jscode2session 登录                            │
│  → 个性化推荐 / 搜索 / 用户管理                                    │
│  → API 文档：http://127.0.0.1:8000/docs                            │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP RESTful API (JSON)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    前端 (frontend/)                                │
│  uni-app → 微信小程序 → 调用 API 渲染界面                           │
└──────────────────────────────────────────────────────────────────┘
```

- **后端不依赖爬虫**：后端启动时优先从 MySQL 加载数据，若 MySQL 不可用则降级使用内置种子数据（`app/seed.json`），保证开发调试无需完整环境。
- **后端为前端提供数据**：前端通过 HTTP 调用后端 API 获取所有数据，两者通过统一的 `ApiResponse` 格式通信。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI 0.115 | 高性能异步框架，自动生成 OpenAPI 文档 |
| 服务器 | Uvicorn | ASGI 服务器，支持热重载 |
| 语言 | Python 3.12 | 类型注解 + 异步支持 |
| 数据库 | MySQL 8.0 (PyMySQL) | 可选，无 MySQL 时使用种子数据降级 |
| 认证 | JWT (python-jose) | 无状态 Token，支持 access/refresh 双 Token |
| 微信登录 | httpx 异步请求 | jscode2session 接口对接 |
| 配置 | python-dotenv | .env 环境变量加载 |

## 目录结构

```
backend/
├── app/
│   ├── main.py              # API 入口，33 个接口定义
│   ├── config.py            # 配置管理（MySQL + 微信 AppID/Secret）
│   ├── auth.py              # JWT 认证（Token 签发/验证/刷新）
│   ├── data.py              # 数据管理（内存存储 + MySQL 查询）
│   ├── models.py            # 数据库模型（SQLAlchemy ORM）
│   ├── schemas.py           # Pydantic 数据模型（请求/响应）
│   ├── seed_loader.py       # 种子数据加载（含图片 URL 校验）
│   ├── database.py          # 数据库连接管理
│   ├── wechat.py            # 微信登录（jscode2session）
│   └── seed.json            # 内置种子数据（商品、分类等）
├── scripts/
│   └── import_seed.py       # 种子数据导入脚本
├── tests/
│   └── test_api.py          # API 接口测试
├── .env.example              # 环境变量模板（复制为 .env 后填入实际值）
├── openapi.json              # OpenAPI 3.0 接口规范
└── requirements.txt          # Python 依赖清单
```

## 快速开始

### 1. 环境要求

- Python >= 3.12
- MySQL 8.0（可选，后端支持无数据库降级运行）

### 2. 安装依赖

```bash
cd ycg-project/backend
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env
```

编辑 `.env`，填入实际配置：

```env
# MySQL 配置（可选，不配置则使用内存种子数据）
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=onebuy
MYSQL_CHARSET=utf8mb4

# 微信小程序配置（需在微信公众平台申请）
WECHAT_APPID=your_wechat_appid
WECHAT_SECRET=your_wechat_secret
```

### 4. 启动服务

```bash
# 默认 http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. 查看 API 文档

启动后访问：
- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

### 6. 运行测试

```bash
python -m pytest tests/
```

## API 接口概览

后端共提供 33 个 RESTful API 接口，分为以下模块：

| 模块 | 接口数 | 主要接口 | 说明 |
|------|:------:|----------|------|
| 认证 | 3 | `/auth/login`、`/auth/refresh`、`/auth/logout` | 微信登录 + 模拟登录，JWT 双 Token |
| 商品搜索 | 4 | `/products/search`、`/products/{id}`、`/categories`、`/products/{id}/platforms` | 关键词搜索、详情、分类、平台报价 |
| 用户 | 2 | `/users/me`、`/users/me/profile` | 获取/更新用户信息 |
| 收藏 | 3 | `/favorites` | 收藏列表、添加、删除 |
| 浏览历史 | 3 | `/history` | 历史列表、添加、清空 |
| 降价提醒 | 3 | `/price-alerts` | 提醒列表、添加、删除（含价格达标标记） |
| 搜索记录 | 1 | `/search/history` | 用户搜索历史 |
| 热搜词 | 1 | `/search/hotwords` | 实时热搜词榜 |
| 推荐 | 2 | `/recommendations/personalized`、`/recommendations/hot` | 个性化推荐 + 热门推荐 |
| 分类 | 1 | `/categories` | 商品分类树 |
| 其他 | 10 | 平台筛选、价格统计等辅助接口 | 支撑前端展示 |

### 统一响应格式

所有接口返回统一的 `ApiResponse` 格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- `code = 0`：成功
- `code != 0`：业务错误，message 包含错误详情
- 分页接口 data 中包含 `items` + `pagination`（page, page_size, total, total_pages, has_next, has_prev）

### 认证方式

需要登录的接口在 Header 中添加：

```
Authorization: Bearer <access_token>
```

登录接口返回 `access_token`（短期有效）和 `refresh_token`（长期有效），前端自动管理 Token 刷新。

## 认证与登录流程

### 微信登录流程

```
1. 前端调用 uni.login() → 获取微信临时 code
2. 前端 POST /auth/login { code, raw_data, signature }
3. 后端调用微信 jscode2session(code) → 获取 openid
4. 后端根据 openid 查找或创建用户
5. 后端签发 JWT TokenPair → 返回前端
6. 前端存储 Token，后续请求携带 Authorization Header
```

### 模拟登录（开发用）

开发调试时无需微信环境，使用 `code=mock_dev_code` 即可登录演示账号：

```json
POST /auth/login
{
  "code": "mock_dev_code",
  "raw_data": "{}",
  "signature": ""
}
```

## 设计说明

### 数据加载策略

后端采用双层数据加载策略：

1. **MySQL 优先**：若配置了 MySQL 连接且数据库可用，从 MySQL 加载商品、用户、收藏等数据。
2. **种子数据降级**：若 MySQL 不可用，自动加载内置 `app/seed.json` 种子数据（包含示例商品、分类等），保证后端可独立运行。

种子数据加载器 (`seed_loader.py`) 包含图片 URL 校验功能，自动过滤指向商品详情页的无效图片链接，确保前端能正常展示商品图片。

### 个性化推荐算法

基于用户行为的品类偏好评分：

1. 分析用户收藏和浏览历史中的商品品类
2. 收藏品类权重 ×3，浏览品类权重 ×1
3. 优先展示偏好品类的商品，商品列表随机打乱保持新鲜感
4. 有跨平台比价关系的商品优先展示
5. 未登录用户随机展示商品

### 降价提醒逻辑

用户可为目标商品设置期望价格。系统在商品详情和提醒列表中自动比较当前价格与目标价格：

- 当前价格 ≤ 目标价格：标记为"已达标"，提醒用户购买
- 当前价格 > 目标价格：显示当前价格，持续监控

## 配置说明

| 环境变量 | 必填 | 说明 | 默认值 |
|----------|:----:|------|--------|
| `MYSQL_HOST` | 否 | MySQL 地址 | 127.0.0.1 |
| `MYSQL_PORT` | 否 | MySQL 端口 | 3306 |
| `MYSQL_USER` | 否 | MySQL 用户 | root |
| `MYSQL_PASSWORD` | 否 | MySQL 密码 | 空 |
| `MYSQL_DATABASE` | 否 | MySQL 数据库名 | onebuy |
| `MYSQL_CHARSET` | 否 | MySQL 字符集 | utf8mb4 |
| `WECHAT_APPID` | 是* | 微信小程序 AppID | 空 |
| `WECHAT_SECRET` | 是* | 微信小程序 Secret | 空 |

\* 真实微信登录必需，模拟登录无需配置。

**重要**：`.env` 文件包含敏感信息，已通过 `.gitignore` 排除，不会提交到仓库。仓库中仅保留 `.env.example` 模板文件。

## 开发与扩展建议

- 生产环境部署建议使用 `gunicorn + uvicorn workers` 并前置 Nginx 反向代理。
- 对接真实爬虫数据后，MySQL 成为主要数据源，种子数据仅作为降级方案。
- 可扩展功能：Redis 缓存热搜词、限流中间件、站内信通知等。

## 参考资料

- 项目对接文档：`项目最终对接记录文档.md`
- 接口规范：`openapi.json`（OpenAPI 3.0）
- 前端文档：`frontend/README.md`
- 主项目文档：根目录 `README.md`