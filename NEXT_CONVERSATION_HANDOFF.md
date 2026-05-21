# 下一次对话交接总结：一次买够爬虫模块

## 当前目标

项目是“**一次买够**”网购比价平台。当前重点是实现爬虫模块，先聚焦 **京东数据获取**，后续再扩展淘宝。

用户负责爬虫部分，要求能够抓取商品数据并写入 MySQL，供后端接口查询：

- `products`
- `platform_offers`
- `price_history`
- `raw_crawl_records`

## 当前工作目录

```powershell
D:\study_file\Junior\ComprehensiveComputerProject\onebuy_crawler
```

虚拟环境：

```powershell
D:\study_file\Junior\ComprehensiveComputerProject\onebuy_crawler\.venv
```

Python：

```text
Python 3.14.2
```

## 已实现内容

已经从零实现了一个独立爬虫工程：

```text
onebuy_crawler/
  jobs/
    browser_capture_search.py
    run_search.py
    init_schema.py
    refresh_prices.py
    backfill_details.py
  onebuy_crawler/
    spiders/
      jd_search.py
      jd_detail.py
      taobao_search.py
      taobao_detail.py
    pipelines/
      cleaning.py
      dedup.py
      mysql.py
      raw_log.py
    services/
      browser_extractors.py
      pipeline_runner.py
      db.py
      matcher.py
      normalizer.py
      sku.py
```

其中最关键的是：

- `jobs/browser_capture_search.py`
  - 使用 Playwright 打开真实浏览器。
  - 监听浏览器 Network Response。
  - 同时从页面 DOM 做兜底提取。
  - 提取商品标题、价格、链接、店铺、图片等字段。
  - 继续复用现有 pipeline 写入 MySQL。

- `onebuy_crawler/services/browser_extractors.py`
  - 负责从京东/淘宝响应 JSON 或 DOM 行中提取 `RawProductItem`。
  - 已加入关键词过滤，防止京东推荐流脏数据混入。

- `onebuy_crawler/services/pipeline_runner.py`
  - 让非 Scrapy 入口也能复用：
    - `CleaningPipeline`
    - `DedupPipeline`
    - `RawLogPipeline`
    - `MySqlPipeline`

## 当前数据库状态

MySQL 数据库名：

```text
onebuy
```

`.env` 中已经开启：

```text
CRAWLER_ENABLE_MYSQL=1
CRAWLER_USE_COOKIES=0
```

不要在交接内容里暴露数据库密码。需要时直接读取项目 `.env`。

数据库初始化命令：

```powershell
.\.venv\Scripts\python.exe -m jobs.init_schema
```

## 已经验证通过

测试通过：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

结果：

```text
Ran 16 tests
OK
```

编译检查通过：

```powershell
.\.venv\Scripts\python.exe -m compileall jobs onebuy_crawler tests
```

Scrapy spider 能加载：

```powershell
.\.venv\Scripts\scrapy.exe list
```

输出包括：

```text
jd_detail
jd_search
taobao_detail
taobao_search
```

## 京东当前已成功

用户运行过：

```powershell
.\.venv\Scripts\python.exe -m jobs.browser_capture_search --platform jd --keyword "iPhone 15" --pages 1 --limit 20 --login-wait
```

输出：

```text
请在打开的浏览器中完成登录/定位后回到终端按 Enter 继续...
browser_capture finished: platform=jd, keyword=iPhone 15, items=20
```

这表示：

- 京东浏览器采集已经成功。
- 成功抓到 20 条 `iPhone 15` 相关商品。
- 如果 `.env` 中 `CRAWLER_ENABLE_MYSQL=1`，数据已经写入 MySQL。

## 如何查看京东入库结果

在项目目录运行：

```powershell
@'
from scrapy.utils.project import get_project_settings
from onebuy_crawler.services.db import mysql_connection

settings = get_project_settings()
with mysql_connection(settings) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT p.product_id, p.title, p.min_price, p.best_platform, o.product_url
            FROM products p
            JOIN platform_offers o ON p.product_id = o.product_id
            WHERE p.title LIKE %s
            ORDER BY p.updated_at DESC
            LIMIT 20
        """, ("%iPhone%15%",))
        for row in cur.fetchall():
            print(row)
'@ | .\.venv\Scripts\python.exe -
```

查看表数量：

```powershell
@'
from scrapy.utils.project import get_project_settings
from onebuy_crawler.services.db import mysql_connection

settings = get_project_settings()
with mysql_connection(settings) as conn:
    with conn.cursor() as cur:
        for table in ["products", "platform_offers", "price_history", "raw_crawl_records"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(table, cur.fetchone()[0])
'@ | .\.venv\Scripts\python.exe -
```

## 重要背景：为什么不用纯 Scrapy 抓京东/淘宝搜索页

纯 Scrapy 请求京东搜索页时：

- 京东会跳转到 `risk_handler` 风控页。
- 后来改用 Playwright 浏览器采集后，京东可以成功抓到数据。

纯 Scrapy 请求淘宝搜索页时：

- 淘宝返回 CSR 骨架页或无商品 JSON。
- 目前淘宝还没有重点实现，下一步可以参考京东浏览器采集方式继续增强。

## 当前浏览器采集机制

浏览器 profile 持久化目录：

```text
browser_profiles/jd
browser_profiles/taobao
```

这些目录已被 `.gitignore` 忽略，不要提交。

使用方式：

第一次建议：

```powershell
.\.venv\Scripts\python.exe -m jobs.browser_capture_search --platform jd --keyword "iPhone 15" --pages 1 --limit 20 --login-wait
```

如果浏览器 profile 已经登录/可用，之后可以：

```powershell
.\.venv\Scripts\python.exe -m jobs.browser_capture_search --platform jd --keyword "iPhone 15" --pages 1 --limit 20 --headless
```

## 已修复过的问题

1. Python 找不到问题
   - 原因不是用户 Python 损坏，而是之前 Codex 默认沙箱访问不到 `C:\Users\dl\AppData\...` 下的 Python。
   - 现在已确认 `.venv` 能正常运行。

2. Scrapy 2.15 弃用警告
   - 已将 spider 入口从 `start_requests()` 更新为 `async start()`。
   - 已调整中间件和 pipeline 签名。

3. 京东 Playwright 报错
   - 报错：
     - `Page.goto interrupted by another navigation to https://global.jd.com/`
     - `CancelledError`
   - 已修复：
     - 京东优先从 `https://www.jd.com/` 首页搜索框发起搜索。
     - 如果导航被其他跳转打断，会等待页面稳定。
     - response 回调读取响应失败时不再导致进程崩溃。

4. 京东脏数据问题
   - 之前可能抓到推荐流里和关键词无关的商品。
   - 已在 `browser_extractors.py` 加关键词过滤。
   - 例如 `iPhone 15` 会要求标题同时包含 `iPhone` 和 `15`。

5. `--limit` 不严格问题
   - 已修复。
   - 单个网络响应返回很多商品时，也会严格截断到指定 limit。

## 下一步建议

1. 先确认京东数据入库质量：

```powershell
.\.venv\Scripts\python.exe -m jobs.browser_capture_search --platform jd --keyword "iPhone 15" --pages 1 --limit 20 --login-wait
```

然后查询 `products/platform_offers/price_history`。

2. 多抓几个京东关键词，形成课程项目演示数据：

```powershell
.\.venv\Scripts\python.exe -m jobs.browser_capture_search --platform jd --keyword "华为 手机" --pages 1 --limit 20
.\.venv\Scripts\python.exe -m jobs.browser_capture_search --platform jd --keyword "小米 手机" --pages 1 --limit 20
.\.venv\Scripts\python.exe -m jobs.browser_capture_search --platform jd --keyword "蓝牙耳机" --pages 1 --limit 20
```

3. 清理之前误抓的京东推荐流脏数据。
   - 注意：不要直接删除全部数据。
   - 可以只删除标题不匹配关键词、或采集时间早于关键词过滤修复前的记录。
   - 如需执行删除，先备份或让用户确认。

4. 后续增强：
   - 优化京东字段提取：店铺、销量、图片、评论数。
   - 增加详情页补采。
   - 再做淘宝浏览器采集。
   - 给后端提供查询 SQL 或接口样例。

## 写进课程报告的描述

可以这样概括：

```text
本项目爬虫模块采用 Playwright 浏览器自动化方案，启动真实浏览器访问京东搜索页，
通过手动登录和浏览器 profile 持久化保持普通用户访问状态。程序监听页面加载过程中的
Network Response，并结合 DOM 兜底解析，提取商品标题、价格、店铺、图片、详情链接等字段。
采集到的数据经过统一清洗、去重、SKU 生成和价格历史记录流程，最终写入 MySQL 的
products、platform_offers、price_history 等表，为后端商品搜索、比价和价格趋势功能提供数据基础。
```

## 新对话继续时可以直接说

```text
请读取 onebuy_crawler/NEXT_CONVERSATION_HANDOFF.md，继续“一次买够”爬虫任务。
当前京东 browser_capture_search 已经能抓到数据并入库，下一步请帮我检查数据库结果、
清理脏数据，并继续完善京东字段质量或淘宝采集。
```
