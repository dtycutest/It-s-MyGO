# 一次买够爬虫模块

这是一个独立 Scrapy 工程，负责京东、淘宝商品搜索/详情采集、清洗去重、价格历史入库，并产出后端 `openapi.json` 所需的数据基础。

## 快速开始

```powershell
cd onebuy_crawler
py -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\scrapy list
```

## 是否使用 Scrapy

本项目已经使用 Scrapy，而且是标准 Scrapy 工程结构：

- `scrapy.cfg` 指向默认配置 `onebuy_crawler.settings`。
- `onebuy_crawler/settings.py` 配置 spider、middleware、pipeline、feed 导出和 MySQL 开关。
- `onebuy_crawler/spiders/` 下注册了 `jd_search`、`jd_detail`、`taobao_search`、`taobao_detail`。
- `jobs/run_search.py` 使用 `scrapy.crawler.CrawlerProcess` 启动 Scrapy spider。
- `onebuy_crawler/pipelines/` 负责清洗、去重、原始记录和 MySQL 入库。

可以用下面两条命令验证：

```powershell
.\.venv\Scripts\scrapy list
.\.venv\Scripts\python -m jobs.verify_scrapy
```

同时项目保留了 `jobs/browser_capture_search.py` 作为浏览器采集入口。它不是替代 Scrapy，而是在京东/淘宝搜索页出现动态渲染、风控页或空结构页时，用 Playwright 获取数据，然后复用同一套 Scrapy item 与 pipeline 完成清洗和入库。

## 常用任务

```powershell
# 搜索采集
.\.venv\Scripts\python -m jobs.run_search --keyword "iPhone 15" --platform jd --pages 1

# 详情补采
.\.venv\Scripts\python -m jobs.backfill_details --input urls.txt

# 价格刷新
.\.venv\Scripts\python -m jobs.refresh_prices --limit 100

# 前端查不到数据时，创建京东后台补采任务
.\.venv\Scripts\python -m jobs.enqueue_crawl_task --keyword "iPhone 15"

# 处理待补采任务
.\.venv\Scripts\python -m jobs.run_crawl_tasks --limit 5

# 全自动流程：初始化表、关键词入队、后台采集、可选刷新价格
.\.venv\Scripts\python -m jobs.auto_crawl --use-default-keywords --rounds 2 --task-limit 4 --refresh-prices

# 首次使用前准备京东登录态；后续自动采集会复用 browser_profiles/jd
.\.venv\Scripts\python -m jobs.prepare_browser_profile --platform jd

# 模拟后端按关键词查询数据库；查不到时可顺手创建补采任务
.\.venv\Scripts\python -m jobs.query_products --keyword "iPhone 15" --enqueue-missing

# 初始化数据库表
.\.venv\Scripts\python -m jobs.init_schema
```

## 环境变量

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=onebuy
CRAWLER_ENABLE_MYSQL=0
CRAWLER_PROXY_LIST=
CRAWLER_PROXY_FILE=
CRAWLER_PROXY_MAX_FAILS=3
CRAWLER_PROXY_COOLDOWN_SECONDS=300
CRAWLER_PROXY_REQUIRED=0
CRAWLER_OBEY_ROBOTS=1
CRAWLER_USE_COOKIES=0
```

`CRAWLER_ENABLE_MYSQL=0` 时爬虫只会清洗并打印/导出数据，适合本地测试和答辩演示；设置为 `1` 后启用 MySQL pipeline。

## IP 代理池

项目支持代理池轮换，用来降低单一出口 IP 触发访问频繁的概率。代理需要使用你自己购买、授权或课程实验允许使用的代理资源，项目不会自动抓取免费代理。

可以直接用环境变量配置：

```powershell
$env:CRAWLER_PROXY_LIST="http://user:pass@1.2.3.4:8000,http://5.6.7.8:9000"
$env:CRAWLER_PROXY_MAX_FAILS="3"
$env:CRAWLER_PROXY_COOLDOWN_SECONDS="300"
```

也可以把代理写入文件，每行一个：

```text
# proxies.txt
http://user:pass@1.2.3.4:8000
http://5.6.7.8:9000
```

然后启用：

```powershell
$env:CRAWLER_PROXY_FILE="proxies.txt"
```

Scrapy 采集会为请求分配代理；当代理触发 403、407、429、5xx 或页面包含验证码/风控标记时，代理会累计失败次数，超过阈值后进入冷却期。

浏览器采集也可以使用代理池，但一个浏览器上下文只能使用一个代理：

```powershell
.\.venv\Scripts\python -m jobs.browser_capture_search --platform jd --keyword "华为 手机" --pages 1 --limit 20 --use-proxy-pool --login-wait
```

如果使用 CDP 连接已启动浏览器，需要在启动浏览器时设置代理：

```powershell
.\.venv\Scripts\python -m jobs.launch_debug_browser --port 9222 --proxy http://user:pass@1.2.3.4:8000 --url https://www.jd.com/
.\.venv\Scripts\python -m jobs.browser_capture_search --platform jd --keyword "华为 手机" --pages 1 --limit 20 --cdp-url http://127.0.0.1:9222 --login-wait
```

如果普通 Edge 浏览器能正常搜索，但 Playwright 独立 profile 显示访问频繁，可以关闭所有 Edge 窗口后，复用默认 Edge 用户数据目录启动调试浏览器：

```powershell
.\.venv\Scripts\python -m jobs.launch_debug_browser --port 9222 --use-default-user-data --url https://www.jd.com/
.\.venv\Scripts\python -m jobs.browser_capture_search --platform jd --keyword "华为 手机" --pages 1 --limit 20 --cdp-url http://127.0.0.1:9222 --login-wait
```

注意：第一条命令必须看到 `debug browser launched and verified` 后，才能运行第二条命令。如果提示 Edge 已经在运行，请先关闭所有 Edge 窗口和后台进程。

## 无 Cookie 抓取

当前默认不使用 Cookie：

```text
CRAWLER_USE_COOKIES=0
JD_COOKIE=
TAOBAO_COOKIE=
```

直接抓公开搜索页：

```powershell
$env:CRAWLER_USE_COOKIES="0"
$env:CRAWLER_OBEY_ROBOTS="0"
.\.venv\Scripts\python -m jobs.run_search --keyword "iPhone 15" --platform jd --pages 1
```

注意：无 Cookie 模式只能抓目标站公开返回的内容。如果目标站返回登录页、验证码页或空结构页，爬虫会记录失败原因，不做验证码破解或登录绕过。

## 浏览器采集模式（课程作业推荐）

对于淘宝、京东这类动态渲染页面，Scrapy 直接请求经常只能拿到风控页或骨架页。课程作业中更稳的方式是使用真实浏览器打开页面，监听 Network 响应并提取商品 JSON，同时从 DOM 做兜底提取。

安装浏览器采集依赖：

```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

首次采集前，建议先为京东准备一次持久化登录态：

```powershell
.\.venv\Scripts\python -m jobs.prepare_browser_profile --platform jd
```

命令会打开一个浏览器窗口。你在里面登录账号、选择地区并完成必要验证，回到终端按 Enter 后，登录态会保存在：

```text
browser_profiles/jd
```

后续 `jobs.browser_capture_search`、`jobs.run_crawl_tasks` 和 `jobs.auto_crawl` 默认都会复用这个目录，因此一般不需要重复登录。不要删除 `browser_profiles/jd` 目录，也不要同时用多个进程打开同一个 profile。

首次运行建议打开京东浏览器界面：

```powershell
.\.venv\Scripts\python -m jobs.browser_capture_search --platform jd --keyword "iPhone 15" --pages 1 --limit 20 --login-wait
```

`--login-wait` 会先打开平台首页，并在终端等待你按 Enter。你可以在浏览器里手动完成登录、定位或人机验证。程序不会读取 Cookie 文件，也不会破解验证码；它只复用浏览器自己的用户目录：

```text
browser_profiles/jd
```

后续如果 profile 已经可用，可以去掉 `--login-wait`。需要后台运行时加 `--headless`：

```powershell
.\.venv\Scripts\python -m jobs.browser_capture_search --platform jd --keyword "iPhone 15" --pages 1 --limit 20
```

入库前确认：

```powershell
.\.venv\Scripts\python -m jobs.init_schema
```

## 可选：手动登录抓取

如果需要抓取登录后的京东/淘宝页面：

1. 在浏览器里手动登录目标平台。
2. 使用 Cookie 编辑器扩展导出 Cookie，或在开发者工具 Network 请求里复制完整 `Cookie` 请求头。
3. 设置 `CRAWLER_USE_COOKIES=1`，并将京东 Cookie 写入 `cookies/jd.cookie`，淘宝 Cookie 写入 `cookies/taobao.cookie`。文件内容可以是 `a=b; c=d` 字符串，也可以是浏览器扩展导出的 JSON 列表。
4. 需要入库时配置 MySQL 并开启：

```powershell
$env:CRAWLER_ENABLE_MYSQL="1"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="你的密码"
$env:MYSQL_DATABASE="onebuy"
.\.venv\Scripts\python -m jobs.init_schema
```

5. 运行采集：

```powershell
.\.venv\Scripts\python -m jobs.run_search --keyword "iPhone 15" --platform jd --pages 1
```

默认 `CRAWLER_OBEY_ROBOTS=1`。如果你确认有课程演示、授权测试或自担风险的本地实验需求，可以临时设置 `CRAWLER_OBEY_ROBOTS=0`，但不要用于绕过验证码、登录风控或高频访问。

## 数据表

- `products`：聚合商品，面向后端搜索和详情接口。
- `platform_offers`：单平台报价和店铺信息。
- `price_history`：价格历史，用于 90 天趋势和降价提醒。
- `raw_crawl_records`：原始抓取摘要、解析状态、失败原因。
- `crawl_tasks`：后台补采任务，当前端搜索缺失或数据过期时写入。

## 缺失数据补采流程

前端和后端联调时，不建议在用户搜索请求里同步启动爬虫。推荐流程是：

```text
前端搜索关键词
后端先查 products/platform_offers
有数据则立即返回
无数据则写入 crawl_tasks，并返回“暂未收录，正在补充”
后台脚本低频处理 crawl_tasks
采集成功后写入 products/platform_offers/price_history
```

手动创建京东补采任务：

```powershell
.\.venv\Scripts\python -m jobs.enqueue_crawl_task --keyword "iPhone 15"
```

模拟后端查库；没有缓存时创建补采任务：

```powershell
.\.venv\Scripts\python -m jobs.query_products --keyword "iPhone 15" --enqueue-missing
```

处理任务：

```powershell
.\.venv\Scripts\python -m jobs.run_crawl_tasks --limit 5 --pages 1 --item-limit 20
```

如果京东需要复用已打开的 Edge 调试浏览器：

```powershell
.\.venv\Scripts\python -m jobs.launch_debug_browser --port 9222 --use-default-user-data --url https://www.jd.com/?country=CN
.\.venv\Scripts\python -m jobs.run_crawl_tasks --limit 1 --jd-cdp-url http://127.0.0.1:9222 --manual-search-wait
```

任务失败时不会删除旧商品数据。遇到 `jd_access_too_frequent`、`jd_search_redirected_to_home`、验证码或风控页时，任务会进入延迟重试状态，前端继续使用数据库中的历史有效数据。

## 全自动采集流程

不需要人工打开搜索页时，推荐使用全自动入口：

```powershell
.\.venv\Scripts\python -m jobs.auto_crawl --use-default-keywords --rounds 2 --task-limit 4 --pages 1 --item-limit 20 --refresh-prices
```

也可以指定关键词，默认只跑京东：

```powershell
.\.venv\Scripts\python -m jobs.auto_crawl --keyword "iPhone 15" --keyword "蓝牙耳机" --rounds 1
```

或使用关键词文件，每行一个关键词：

```text
# keywords.txt
iPhone 15
华为 手机
小米 手机
蓝牙耳机
机械键盘
```

```powershell
.\.venv\Scripts\python -m jobs.auto_crawl --keyword-file keywords.txt --rounds 2 --task-limit 5
```

全自动流程会做四件事：

```text
初始化 MySQL 表结构
把关键词写入 crawl_tasks
自动处理到期任务并写入 products/platform_offers/price_history
可选刷新已有商品详情价格
```

如果京东返回验证码、访问频繁、搜索被重定向等情况，程序不会破解或绕过验证，而是把任务标记为 `blocked` 或 `failed`，按延迟时间自动重试。前端仍然读取数据库里的历史有效数据。

## 合规边界

工程内置 robots、限速、重试、代理和失败记录。若目标站点禁止抓取、出现验证码或访问阻断，爬虫会记录失败原因，不实现验证码破解、登录绕过或违反目标站规则的行为。
