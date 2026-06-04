# 一次买够 — 前端（微信小程序）

## 项目简介

本项目是"一次买够"网购比价平台的微信小程序前端，基于 uni-app（Vue 3 + TypeScript + SCSS）开发，编译目标为微信小程序（mp-weixin）。

前端作为用户交互层，通过 HTTP RESTful API 与后端（FastAPI）通信，负责商品搜索展示、多平台比价、用户登录、收藏管理、浏览历史和降价提醒等功能的界面呈现。前端不直接访问数据库或爬虫，所有数据均通过后端 API 获取。

## 与后端和爬虫的关系

本项目的三个子系统（爬虫 → 后端 → 前端）构成一条完整的数据流水线：

```
┌──────────────────────────────────────────────────────────────────┐
│                    爬虫 (crawler/)                                 │
│  Scrapy + Playwright 真浏览器 → 京东/淘宝商品采集                   │
│  → 数据清洗、去重、格式化 → 写入 MySQL 数据库                       │
│  → 每天定时运行，保证数据时效性                                     │
└────────────────────────┬─────────────────────────────────────────┘
                         │ 数据供给（MySQL 读写）
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    后端 (backend/)                                 │
│  FastAPI + Uvicorn → 从 MySQL / 内存种子数据加载商品               │
│  → 暴露 33 个 RESTful API 接口 (OpenAPI 3.0)                       │
│  → JWT 认证 / 商品搜索 / 个性化推荐 / 用户管理 / 浏览历史           │
│  → 微信 jscode2session 登录接口对接                                │
│  → API 文档：http://127.0.0.1:8000/docs                            │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP RESTful API (JSON)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    前端 (frontend/)  ← 当前项目                     │
│  uni-app (Vue 3 + Pinia + TypeScript + SCSS)                      │
│  → 编译为微信小程序 (mp-weixin)                                    │
│  → 8 个页面 + 7 个通用组件                                        │
│  → 通过封装的 request.ts 统一调用后端 API                          │
│  → Pinia 状态管理 / Token 本地持久化                               │
└──────────────────────────────────────────────────────────────────┘
```

### 数据流向详解

1. **爬虫 → 后端**：爬虫独立运行，将采集的商品数据（商品标题、价格、图片、店铺、销量、平台等）写入 MySQL。后端从 MySQL 加载数据到内存（支持种子数据降级），作为 API 的数据源。

2. **后端 → 前端**：前端通过 HTTP 请求调用后端 API。每次请求经过以下流程：

   ```
   用户操作 → 页面调用 API 函数 (src/api/index.ts)
         → request.ts 拦截器注入 Token (Authorization Header)
         → uni.request 发送 HTTP 请求到后端
         → 后端处理请求 (认证/业务逻辑/数据库查询)
         → 返回 JSON 响应 (统一 ApiResponse 格式)
         → request.ts 拦截器处理响应 (401 拦截/错误处理)
         → 页面/Store 更新数据和 UI
   ```

3. **前端完全不依赖爬虫**：前端开发者只需关注后端 API 接口规范，无需了解爬虫实现细节。爬虫的更新会自动反映在 API 返回的数据中。

### 三部分开发协作模式

| 场景 | 爬虫 | 后端 | 前端 |
|------|:----:|:----:|:----:|
| 纯前端 UI 开发 | 不需要 | 不需要（Mock 模式） | 独立开发 |
| 前后端联调 | 不需要（种子数据） | 运行中 | 运行中 |
| 真机预览 | 不需要 | 运行 + cpolar 穿透 | 运行中 |
| 完整流程验证 | 运行一次 | 运行中 | 运行中 |

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 框架 | uni-app 3.0 + Vue 3.4 | 一套代码编译多端 |
| 状态管理 | Pinia 3.0 | 模块化状态 + 持久化 |
| 语言 | TypeScript 4.9 | 类型安全 |
| 样式 | SCSS + rpx 响应式布局 | 适配不同屏幕 |
| 构建 | Vite 5.2 | 快速开发构建 |
| HTTP 客户端 | 封装 uni.request | Token 自动注入 |
| 目标平台 | 微信小程序 (mp-weixin) | 原生体验 |

## 目录结构

```
frontend/
├── src/
│   ├── api/                    # API 封装层
│   │   ├── index.ts            # 19 个接口函数（搜索/商品/用户/收藏/历史/提醒）
│   │   └── types.ts            # 请求与响应的 TypeScript 类型定义
│   ├── stores/                 # Pinia 状态管理（4 个 Store）
│   │   ├── user.ts             # 用户登录状态、Token 管理、登录/登出
│   │   ├── product.ts          # 商品搜索、详情、推荐、热搜词
│   │   ├── favorite.ts         # 收藏添加/删除/列表
│   │   └── priceAlert.ts       # 降价提醒添加/删除/列表
│   ├── pages/                  # 8 个页面
│   │   ├── index/              # 首页 — 搜索栏 + 分类标签 + 推荐商品瀑布流
│   │   ├── searchResults/      # 搜索结果 — 商品列表 + 排序切换
│   │   ├── productDetail/      # 商品详情 — 多平台比价卡片 + 收藏/添加提醒
│   │   ├── userCenter/         # 用户中心 — 个人信息 + 收藏/足迹/提醒入口
│   │   ├── favorites/          # 收藏列表 — 添加/删除收藏商品
│   │   ├── history/            # 浏览历史 — 时间轴展示 + 去重
│   │   ├── priceAlerts/        # 降价提醒 — 目标价格管理 + 达标标记
│   │   └── login/              # 登录页 — 微信一键登录 + 模拟登录双入口
│   ├── components/             # 7 个通用组件
│   │   ├── ProductCard.vue     # 商品卡片（图片 + 价格 + 平台标签 + 差价）
│   │   ├── SearchBar.vue       # 搜索栏（输入 + 热搜词下拉）
│   │   ├── PlatformBadge.vue   # 平台标签（京东/淘宝/天猫颜色区分）
│   │   ├── PriceLabel.vue      # 价格标签（当前价 + 原价 + 折扣）
│   │   ├── NoData.vue          # 空数据占位
│   │   ├── LoadingIndicator.vue # 加载指示器
│   │   └── MoreHeader.vue      # "更多"页面通用头部
│   ├── utils/
│   │   ├── request.ts          # HTTP 请求封装（Token 注入 + 401 自动登出）
│   │   ├── storage.ts          # 本地存储封装（Token/用户信息持久化）
│   │   └── index.ts            # 通用工具函数（时间格式化、数字格式化等）
│   ├── styles/                 # SCSS 全局样式（颜色/字体/间距变量）
│   ├── static/                 # 静态资源（Logo、TabBar 图标）
│   ├── App.vue                 # 根组件（全局生命周期）
│   ├── main.ts                 # 入口（Store 初始化 + 全局挂载）
│   ├── pages.json              # 页面路由 + TabBar 配置 + 导航栏样式
│   └── manifest.json           # uni-app 应用配置（微信 AppID 占位）
├── .env.example                # 环境变量模板（复制为 .env 后填入实际地址）
├── package.json                # npm 依赖管理
├── tsconfig.json               # TypeScript 编译配置
└── vite.config.ts              # Vite 构建配置（uni-app 插件）
```

## 快速开始

### 1. 环境要求

- Node.js >= 18
- npm >= 9
- 微信开发者工具（最新稳定版）

### 2. 安装依赖

```bash
cd ycg-project/frontend
npm install
```

### 3. 配置后端地址

```bash
# 复制环境变量模板
cp .env.example .env
```

编辑 `.env`，设置后端 API 地址：

```env
# 本地开发（后端与开发者工具在同一台电脑）
VITE_API_BASE_URL=http://127.0.0.1:8000

# 局域网演示（手机与电脑在同一 WiFi）
VITE_API_BASE_URL=http://192.168.xxx.xxx:8000

# cpolar 内网穿透（真机扫码预览）
VITE_API_BASE_URL=https://xxxxxxxx.r32.cpolar.top
```

### 4. 编译运行

```bash
# 开发模式编译为微信小程序
npm run dev:mp-weixin
```

编译产物位于 `dist/dev/mp-weixin/`。

### 5. 微信开发者工具导入

1. 打开微信开发者工具
2. 导入项目 → 选择 `dist/dev/mp-weixin` 目录
3. AppID 填写你自己的小程序 AppID（在微信公众平台申请），或选择"测试号"
4. 设置 → 勾选"不校验合法域名"（开发阶段必需）
5. 开始调试

### 6. 类型检查

```bash
npm run type-check
```

## 页面功能说明

| 页面 | 路径 | 登录要求 | 主要功能 | 调用的后端 API |
|------|------|:--------:|----------|---------------|
| 首页 | pages/index/index | 无需 | 搜索商品、分类筛选、推荐瀑布流 | 搜索、推荐、热搜词、分类 |
| 搜索结果 | pages/searchResults/searchResults | 无需 | 商品列表展示、排序切换（价格/销量） | 搜索（关键词+分类+排序） |
| 商品详情 | pages/productDetail/productDetail | 无需 | 多平台比价卡片、收藏、设置降价提醒、复制链接 | 商品详情、收藏、降价提醒 |
| 用户中心 | pages/userCenter/userCenter | 可选 | 用户信息、收藏数/足迹数/提醒数统计 | 用户信息、收藏列表、历史列表、提醒列表 |
| 登录 | pages/login/login | 入口 | 微信一键登录 + 模拟登录双入口 | 登录（微信/模拟）、获取用户信息 |
| 收藏列表 | pages/favorites/favorites | 需登录 | 收藏商品管理、取消收藏 | 收藏列表、删除收藏 |
| 浏览历史 | pages/history/history | 需登录 | 浏览记录时间轴、自动去重 | 历史列表、添加历史（详情页自动调用） |
| 降价提醒 | pages/priceAlerts/priceAlerts | 需登录 | 目标价格管理、达标自动标记 | 提醒列表、添加提醒、删除提醒 |

## 状态管理架构

```
┌────────────────────────────────────────────────────┐
│                    Pinia Stores                     │
├────────────┬───────────┬────────────┬──────────────┤
│ userStore  │productStore│favoriteStore│priceAlertStr│
├────────────┼───────────┼────────────┼──────────────┤
│ token      │ searchRes │ favorites  │ alerts       │
│ userInfo   │ productDet│ loading    │ loading      │
│ isLoggedIn │ recommend │ error      │ error        │
│ login()    │ hotWords  │ add()      │ add()        │
│ logout()   │ categories│ remove()   │ remove()     │
│ init()     │ search()  │ list()     │ list()       │
├────────────┴───────────┴────────────┴──────────────┤
│              storage.ts (本地持久化)                 │
│   Token / RefreshToken → uni.storage               │
└────────────────────────────────────────────────────┘
```

- **userStore**：管理登录状态和 Token。应用启动时自动调用 `init()` 验证本地 Token 有效性，无效则清除。`isLoggedIn` 为 computed 属性，仅在 Token 验证通过后才为 true。
- **productStore**：管理搜索、详情、推荐等商品相关数据，支持分页加载。
- **favoriteStore / priceAlertStore**：管理收藏和降价提醒的增删查操作。

## API 调用与认证流程

### 请求拦截器 (request.ts)

所有 API 请求经过统一的请求/响应拦截器处理：

```
发起请求 → request.ts 拦截
         → 自动注入 Authorization: Bearer <token>
         → 发送到后端 API
         → 接收响应
         → 检查是否 401 (Token 过期)
         → 是：清除本地 Token → 跳转登录页
         → 否：解析 ApiResponse 格式 → 返回 data
```

### 认证流程

```
1. 用户点击登录 → 调用 uni.login() 获取微信 code
2. POST /auth/login { code, raw_data } → 后端返回 { access_token, refresh_token }
3. 前端存储 Token 到 uni.storage（持久化）
4. 后续所有请求自动携带 Authorization Header
5. 应用重启 → userStore.init() 用本地 Token 调用 /users/me 验证有效性
```

### Mock 模式

前端支持 Mock 模式用于独立开发调试。在 `src/api/index.ts` 中设置：

```typescript
const USE_MOCK = false; // true = 使用本地假数据，false = 调用真实 API
```

Mock 模式启用时，所有 API 函数返回本地硬编码数据，无需后端运行即可进行 UI 开发。

## 与后端 API 的对应关系

前端 API 层 (`src/api/index.ts`) 封装了 19 个接口函数，与后端的 33 个接口一一对应：

| 前端函数 | HTTP 方法 | 后端路由 | 说明 |
|----------|-----------|----------|------|
| `searchApi.search()` | GET | `/search` | 商品搜索 |
| `searchApi.hotwords()` | GET | `/search/hotwords` | 热搜词 |
| `productApi.getDetail()` | GET | `/products/{id}` | 商品详情 |
| `productApi.getRecommendations()` | GET | `/recommendations/personalized` | 个性化推荐 |
| `categoryApi.list()` | GET | `/categories` | 分类列表 |
| `authApi.login()` | POST | `/auth/login` | 微信登录 |
| `userApi.getProfile()` | GET | `/users/me` | 用户信息 |
| `favoriteApi.list()` | GET | `/favorites` | 收藏列表 |
| `favoriteApi.add()` | POST | `/favorites` | 添加收藏 |
| `favoriteApi.remove()` | DELETE | `/favorites/{id}` | 删除收藏 |
| `browseHistoryApi.list()` | GET | `/history` | 浏览历史 |
| `browseHistoryApi.add()` | POST | `/history` | 记录浏览 |
| `priceAlertApi.list()` | GET | `/price-alerts` | 提醒列表 |
| `priceAlertApi.add()` | POST | `/price-alerts` | 添加提醒 |
| `priceAlertApi.remove()` | DELETE | `/price-alerts/{id}` | 删除提醒 |

## 登录模式说明

项目支持两种登录方式，可在登录页切换：

| 登录方式 | 说明 | 使用场景 |
|----------|------|----------|
| 微信一键登录 | 真实微信 jscode2session 登录，需微信公众平台配置 | 真机测试、正式发布 |
| 模拟登录 | 使用 `code=mock_dev_code` 直接登录演示账号 | 开发调试、无需微信环境 |

两种登录方式均返回 JWT Token，后续请求携带方式完全相同。

## 注意事项

### 开发阶段

- 微信小程序不支持直接跳转外部电商链接，商品详情页点击平台卡片会复制链接到剪贴板。
- 开发阶段需在微信开发者工具中勾选 **"不校验合法域名"**，否则无法请求本地后端。
- 图片加载失败时，前端会自动显示占位提示，不会导致页面崩溃。

### 真机预览

- 微信开发者工具 → 预览 → 扫码 → 手机预览。
- 真机预览时，手机无法直接访问 `127.0.0.1`，需使用 **cpolar 内网穿透** 将后端暴露到公网。
- cpolar 启动命令（在后端目录执行）：
  ```bash
  cpolar http 8000
  ```
- 获取 cpolar 生成的公网 URL（如 `https://xxxxxxxx.r32.cpolar.top`），更新前端 `.env` 中的 `VITE_API_BASE_URL`。
- 注意：cpolar 免费版域名会定期变化，每次重启需更新 `.env` 并重新编译前端。

### 体验版发布

- 微信开发者工具 → 上传 → 填写版本号和备注 → 上传代码。
- 登录微信公众平台 → 版本管理 → 选择上传的版本 → 设为体验版。
- 体验版需在公众平台添加体验成员，成员微信扫码即可使用。
- 上传前确保 `manifest.json` 中 `mp-weixin.appid` 已替换为真实的微信小程序 AppID。

### 与后端和爬虫的协调

- 前端展示的数据完全依赖后端 API 返回的内容。如果数据不对，先检查后端 API 响应（通过 `/docs` 页面测试）。
- 后端种子数据仅包含少量示例商品，完整数据需要运行爬虫采集。
- 三个子系统的开发顺序建议：**爬虫（数据准备）→ 后端（API 开发 + 联调）→ 前端（UI 开发 + 对接）**。