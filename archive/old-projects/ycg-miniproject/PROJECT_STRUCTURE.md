# 项目结构说明

## 目录结构

```
ycg-miniproject/
├── src/
│   ├── api/                    # API 层
│   │   ├── index.ts           # 所有 API 模块
│   │   └── types.ts           # TypeScript 类型定义
│   │
│   ├── components/            # 组件目录
│   │   ├── base/              # 基础组件
│   │   └── business/          # 业务组件
│   │
│   ├── pages/                 # 页面目录
│   │   ├── index/            # 首页
│   │   ├── searchResults/    # 搜索结果页
│   │   ├── productDetail/    # 商品详情页
│   │   ├── userCenter/       # 用户中心页
│   │   └── login/            # 登录页
│   │
│   ├── stores/                # Pinia 状态管理
│   │   ├── user.ts           # 用户状态
│   │   └── product.ts        # 商品状态
│   │
│   ├── styles/                # 全局样式
│   │   ├── variables.scss    # 设计系统变量
│   │   └── common.scss       # 通用样式和工具类
│   │
│   ├── utils/                 # 工具函数
│   │   ├── index.ts
│   │   ├── request.ts        # 网络请求封装
│   │   └── storage.ts        # 本地存储
│   │
│   ├── static/                # 静态资源
│   ├── App.vue               # 应用根组件
│   └── main.ts               # 应用入口
│
├── manifest.json              # 应用配置
├── pages.json                 # 页面路由配置
├── package.json               # 依赖管理
├── tsconfig.json              # TypeScript 配置
├── vite.config.ts             # Vite 配置
├── .env.example               # 环境变量示例
├── README.md                  # 项目说明
└── PROJECT_STRUCTURE.md       # 本文件
```

## 核心功能模块

### 1. API 层 (`src/api/`)
- **类型定义**: 完整的 TypeScript 类型
- **API 模块**:
  - `authApi` - 认证相关（登录、刷新 Token、登出）
  - `productApi` - 商品相关（搜索、详情、分类）
  - `searchApi` - 搜索相关（热搜词）
  - `userApi` - 用户相关（获取/更新用户信息）
  - `favoriteApi` - 收藏相关
  - `priceAlertApi` - 降价提醒相关
  - `browseHistoryApi` - 浏览历史
  - `searchRecordApi` - 搜索记录
  - `recommendationApi` - 个性化推荐
  - `analyticsApi` - 事件上报

### 2. 状态管理 (`src/stores/`)
- **user.ts**: 用户登录状态、用户信息
- **product.ts**: 搜索结果、当前商品详情、热搜词

### 3. 工具层 (`src/utils/`)
- **request.ts**: 统一网络请求封装，含错误处理、认证等
- **storage.ts**: 本地存储封装

### 4. 设计系统 (`src/styles/`)
- **颜色系统**: 主色、辅助色、功能色、中性色
- **间距系统**: xs(4px) / sm(8px) / md(12px) / lg(16px) / xl(24px) / xxl(32px)
- **圆角系统**: sm / md / lg / full
- **字体系统**: 字号定义、颜色定义

## 页面功能

| 页面 | 功能 |
|------|------|
| 首页 | 搜索框、热搜词展示、搜索功能入口 |
| 搜索结果页 | 商品列表、下拉加载、排序过滤 |
| 商品详情页 | 商品信息、各平台比价、收藏、购买跳转 |
| 用户中心 | 用户信息展示、菜单导航（收藏、降价提醒、浏览历史） |
| 登录页 | 微信一键登录 |

## 技术特性

- ✅ TypeScript 类型安全
- ✅ Pinia 状态管理
- ✅ 设计系统
- ✅ 统一 API 封装
- ✅ 错误处理机制
- ✅ 事件上报集成
