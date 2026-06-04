# 一次买够 - 前端项目

一次买够是一个多平台商品比价与聚合搜索应用。

## 技术栈

- Vue 3
- TypeScript
- Pinia (状态管理)
- Vite (构建工具)
- SCSS (样式)

## 项目结构

```
ycg-miniproject/
├── src/
│   ├── api/                    # API 层
│   │   ├── index.ts           # API 模块
│   │   └── types.ts           # TypeScript 类型定义
│   ├── mock/                   # Mock 数据层
│   │   ├── data.ts            # 模拟数据
│   │   └── index.ts           # Mock API
│   ├── pages/                  # 页面
│   │   ├── index/             # 首页
│   │   ├── searchResults/     # 搜索结果页
│   │   ├── productDetail/     # 商品详情页
│   │   ├── userCenter/        # 用户中心页
│   │   └── login/             # 登录页
│   ├── stores/                 # Pinia 状态管理
│   │   ├── user.ts            # 用户状态
│   │   └── product.ts         # 商品状态
│   ├── styles/                 # 样式
│   │   ├── variables.scss     # 设计系统变量
│   │   └── common.scss        # 通用样式
│   ├── utils/                  # 工具函数
│   │   ├── index.ts
│   │   ├── request.ts         # 网络请求
│   │   └── storage.ts         # 本地存储
│   ├── App.vue                # 应用根组件
│   ├── main.ts                # 应用入口
│   └── env.d.ts               # 类型声明
├── index.html                 # HTML 入口
├── vite.config.ts             # Vite 配置
├── tsconfig.json              # TypeScript 配置
└── package.json               # 项目配置
```

## 快速开始

### 安装依赖

```bash
cd ycg-miniproject
npm install
```

### 运行项目

```bash
npm run dev
```

### 构建项目

```bash
npm run build
```

## 设计系统

### 颜色

| 名称 | 颜色 | 用途 |
|------|------|------|
| primary | #FF6B35 | 主色调，按钮、链接等 |
| success | #50C878 | 成功状态 |
| warning | #FFB81C | 警告状态 |
| danger | #E4405F | 错误状态 |

### 间距

- xs: 4px
- sm: 8px
- md: 12px
- lg: 16px
- xl: 24px

## Mock 数据

项目内置了完整的 Mock 数据层，方便开发：

- 商品搜索和详情
- 热门搜索词
- 用户登录
- 收藏和降价提醒
- 浏览历史

### 切换到真实后端

如需使用真实后端，修改 `src/api/index.ts` 中的 `USE_MOCK` 为 `false`。

## 开发进度

- [x] 项目基础架构
- [x] TypeScript 类型定义
- [x] API 层和 Mock 数据
- [x] 状态管理 (Pinia)
- [x] 设计系统
- [x] 首页
- [x] 搜索结果页
- [x] 商品详情页
- [x] 用户中心页
- [x] 登录页

## 浏览器支持

- Chrome (最新版)
- Firefox (最新版)
- Safari (最新版)
- Edge (最新版)
