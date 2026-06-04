# "一次买够" 前端开发指南

## 📋 项目概述

**项目名称**：一次买够网购比价平台  
**项目类型**：微信小程序 (uni-app + Vue 3)  
**技术栈**：uni-app + Vue 3 + Pinia + TypeScript + SCSS

## 🎯 核心功能

- 商品聚合搜索（支持多平台）
- 智能比价（价格对比、历史走势）
- 用户个性化（收藏、降价提醒、浏览历史）
- 一键购买（直接跳转原平台）

---

## 📁 核心文档索引

### 快速开始
- [快速开始指南](./快速开始指南.md) - 环境搭建和项目初始化
- [README](./README.md) - 项目概览和团队协作

### 架构设计
- [前端系统体系架构设计](./前端系统体系架构设计.md) - 完整架构说明
- [前端工作总结](./前端工作总结.md) - 进度总结和后续计划

### UI设计
- [微信小程序UI设计方案](./微信小程序UI设计方案.md) - 设计规范
- [小程序UI开发实现指南](./小程序UI开发实现指南.md) - 代码实现指南

### API集成
- [API_文档_完整版](./API_文档_完整版.md) - 完整API文档
- [API集成指南](./API集成指南.md) - 前端集成指南
- [openapi.json](./openapi.json) - OpenAPI规范
- [Postman_Collection.json](./Postman_Collection.json) - Postman测试集合

---

## 🚀 快速开始

### 环境准备

```bash
# 安装依赖
npm install -g @vue/cli @vue/cli-service-global
npm install -g @dcloudio/uvm  # uni-app CLI
```

### 项目结构

```
It's Mygo-frontend/
├── src/
│   ├── pages/                    # 页面组件
│   │   ├── index/                # 首页
│   │   ├── searchResults/        # 搜索结果页
│   │   ├── productDetail/        # 商品详情页
│   │   ├── productCompare/       # 商品对比页
│   │   ├── favorites/            # 我的收藏
│   │   ├── priceAlerts/          # 降价提醒
│   │   ├── history/              # 浏览历史
│   │   ├── category/             # 分类页
│   │   ├── userCenter/           # 用户中心
│   │   └── login/                # 登录页
│   ├── components/               # 组件库
│   │   ├── base/                 # 基础组件
│   │   └── business/             # 业务组件
│   ├── utils/                    # 工具函数
│   │   ├── request.js            # HTTP请求封装
│   │   ├── auth.js               # 认证工具
│   │   └── storage.js            # 本地存储
│   ├── stores/                   # Pinia状态管理
│   ├── api/                      # API模块
│   ├── styles/                   # 全局样式
│   ├── static/                   # 静态资源
│   └── App.vue                   # 根组件
├── uni.scss                      # 全局样式变量
├── pages.json                    # 页面配置
├── manifest.json                 # 应用配置
└── package.json                  # 项目依赖
```

---

## 🎨 设计系统

### 颜色系统

```scss
$primary-color: #FF6B35;      // 主色 - 橙红色
$secondary-color: #004E89;    // 辅助色 - 深蓝色
$success-color: #50C878;      // 成功色 - 绿色
$warning-color: #FFB81C;      // 警告色 - 黄色
$danger-color: #E4405F;       // 危险色 - 红色
```

### 字体系统

- 标题：H1(28px)、H2(20px)、H3(16px)
- 正文：14px
- 价格专用：突出显示，使用主色

### 组件库

核心业务组件：
- ProductCard - 商品卡片
- PriceLabel - 价格标签
- PlatformBadge - 平台徽章
- SearchBar - 搜索栏
- FilterPanel - 筛选面板
- PriceChart - 价格走势

---

## 🔌 API集成

### 请求封装

```javascript
// src/utils/request.js
import axios from 'axios';

const request = axios.create({
  baseURL: 'https://api.ycg.com/api/v1',
  timeout: 10000
});

// 请求拦截器
request.interceptors.request.use(config => {
  const token = uni.getStorageSync('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器
request.interceptors.response.use(
  response => {
    const { code, data, message } = response.data;
    if (code === 0) {
      return data;
    } else {
      uni.showToast({ title: message, icon: 'none' });
      return Promise.reject(new Error(message));
    }
  },
  error => {
    uni.showToast({ title: '网络错误', icon: 'none' });
    return Promise.reject(error);
  }
);

export default request;
```

### 商品搜索API

```javascript
// src/api/product.js
import request from '@/utils/request';

// 搜索商品
export function searchProducts(params) {
  return request({
    url: '/products/search',
    method: 'GET',
    params
  });
}

// 获取商品详情
export function getProductDetail(productId) {
  return request({
    url: `/products/${productId}`,
    method: 'GET'
  });
}

// 获取热搜词
export function getHotWords(limit = 10) {
  return request({
    url: '/search/hot-words',
    method: 'GET',
    params: { limit }
  });
}
```

---

## 📊 状态管理

使用 Pinia 进行状态管理：

```javascript
// src/stores/user.js
import { defineStore } from 'pinia';

export const useUserStore = defineStore('user', {
  state: () => ({
    token: '',
    userInfo: null
  }),
  
  actions: {
    setToken(token) {
      this.token = token;
      uni.setStorageSync('token', token);
    },
    
    async login(credentials) {
      const res = await loginApi(credentials);
      this.setToken(res.token);
      this.userInfo = res.user;
    }
  }
});
```

---

## 📱 开发进度

### 已完成
- ✅ 项目架构设计
- ✅ UI设计方案
- ✅ API接口设计
- ✅ 组件库规划

### 进行中
- 🔄 页面组件开发
- 🔄 API集成测试

### 待完成
- ⏳ 用户功能实现
- ⏳ 性能优化
- ⏳ 上线部署

---

## 📚 归档文档

其他历史文档和设计文件已归档至 `archive/` 目录，包括：
- 系统设计文档（Word格式）
- 开题报告和需求规格说明书
- 各类图表文件（MMD、PNG格式）
- 临时文档和效果图展示

---

**最后更新**：2026年4月26日  
**版本**：2.0  
**维护者**：前端开发团队
