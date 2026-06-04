# 一次买够 (It's MyGO)

网购比价平台，计算机综合项目实践。

## 项目结构

```
├── frontend/          # uni-app 前端（微信小程序 + H5）
├── backend/           # FastAPI 后端
└── crawler/           # Scrapy 爬虫模块
```

## 快速开始

### 前端
```bash
cd frontend
npm install
npm run dev:mp-weixin   # 微信小程序
npm run dev:h5          # H5 网页版
```

### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 爬虫
```bash
cd crawler
pip install -r requirements.txt
scrapy crawl <spider_name>
```