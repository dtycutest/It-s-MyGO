# 一次买够爬虫模块使用说明

本目录是“一次买够”网购比价平台的独立爬虫工程，负责采集京东、淘宝商品数据，清洗后写入 MySQL，供后端接口和前端小程序做搜索、比价、详情展示和价格历史查询。

当前最稳定的工作流是：

1. 京东：优先使用“手动正常浏览器搜索 + 复制搜索页 HTML + 本地解析入库”，必要时再使用浏览器自动化或详情页 URL 补采。
2. 淘宝：使用持久化浏览器登录态，Playwright 监听 Network 响应并结合 DOM 兜底解析。
3. 数据入库：统一走 `CleaningPipeline -> DedupPipeline -> RawLogPipeline -> MySqlPipeline`，写入 `products`、`platform_offers`、`price_history`、`raw_crawl_records`。

## 目录结构

```text
onebuy_crawler/
  jobs/                         # 可直接运行的任务入口
    init_schema.py              # 初始化 MySQL 表和视图
    import_copied_search_html.py# 从手动复制的京东搜索页 HTML 导入商品
    browser_capture_search.py   # Playwright 浏览器采集入口
    auto_crawl.py               # 自动入队并处理补采任务
    query_products.py           # 查询 MySQL 中的商品缓存
    export_seed_data.py         # 导出可交付给前后端的测试数据包
    import_seed_data.py         # 导入测试数据包
  onebuy_crawler/
    services/                   # 解析、归一化、数据库、任务等服务代码
    pipelines/                  # 清洗、去重、原始日志、MySQL 入库
    spiders/                    # Scrapy spider
  data/
    exact_product_keywords.txt  # 型号级关键词
    compare_keywords.txt        # 宽泛比价关键词
    jd_urls.txt                 # 临时粘贴京东 HTML 或商品 URL
```

## 环境准备

在 Windows PowerShell 中运行。先进入你自己电脑上的项目目录，也就是包含 `scrapy.cfg`、`requirements.txt`、`jobs`、`onebuy_crawler` 这些文件和文件夹的目录：

```powershell
cd <你的项目路径>\onebuy_crawler

py -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

检查 Scrapy 项目是否能加载：

```powershell
.\.venv\Scripts\scrapy.exe list
```

应看到：

```text
jd_detail
jd_search
taobao_detail
taobao_search
```

## MySQL 配置

复制 `.env.example` 为 `.env`，填写自己的数据库密码：

```text
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=onebuy
CRAWLER_ENABLE_MYSQL=1
```

初始化数据库：

```powershell
.\.venv\Scripts\python.exe -m jobs.init_schema
```

成功时输出：

```text
Database schema initialized.
```

主要数据表和视图：

```text
products            聚合后的商品主表
platform_offers     各平台报价、店铺、链接、销量
price_history       价格历史
raw_crawl_records   失败原因和原始采集记录
crawl_tasks         后台补采任务
jd_products         京东商品查询视图
taobao_products     淘宝商品查询视图
```

## 京东采集方案

京东搜索页容易因为账号、IP、浏览器自动化特征触发“当前页面异常”“访问频繁”“切换账号”等页面。不要反复用脚本硬刷搜索页。当前推荐三种方式，按稳定性排序。

### 方案 A：复制京东搜索页 HTML 导入（推荐）

这是当前最稳定的京东方案。它不让爬虫打开京东网页，而是你用正常浏览器手动搜索，复制已经渲染出来的搜索结果 HTML，本地解析商品卡片。

适合：

```text
HUAWEI FreeBuds Pro 3
Logitech K380 蓝牙键盘
小米自带线充电宝 10000mAh 22.5W
Apple iPhone 15 128GB
```

步骤：

1. 用平时能正常登录京东的浏览器打开京东，搜索一个具体商品。
2. 等商品列表显示出来。
3. 按 `F12` 打开开发者工具，在 Console 执行：

```javascript
(() => {
  const html = document.documentElement.outerHTML;
  copy(html);
  console.log("已复制页面HTML，长度：", html.length);
})();
```

控制台显示 `undefined` 是正常的，`copy()` 没有返回值。只要能看到 `已复制页面HTML，长度：xxxx`，说明已经复制成功。

4. 把剪贴板内容粘贴到：

```text
data\jd_urls.txt
```

可以整页 HTML 全部粘贴进去。文件末尾出现“显示更多”“购物车”“客服”“插件版”等内容没有关系，解析器会只提取商品卡片。

5. 运行导入命令：

```powershell
$env:CRAWLER_ENABLE_MYSQL="1"

.\.venv\Scripts\python.exe -m jobs.import_copied_search_html `
  --keyword "Logitech K380 蓝牙键盘" `
  --input data\jd_urls.txt `
  --limit 20
```

换商品时只改 `--keyword`：

```powershell
.\.venv\Scripts\python.exe -m jobs.import_copied_search_html --keyword "HUAWEI FreeBuds Pro 3" --input data\jd_urls.txt --limit 20
.\.venv\Scripts\python.exe -m jobs.import_copied_search_html --keyword "小米自带线充电宝 10000mAh 22.5W" --input data\jd_urls.txt --limit 20
```

导入成功示例：

```text
copied search HTML import finished: keyword=Logitech K380 蓝牙键盘, rows=25, matched=5, imported=5, mysql=1
```

说明：

```text
rows     从 HTML 中解析到的商品卡片数量
matched 通过关键词过滤后的商品数量
imported 实际送入 pipeline 的商品数量
mysql=1 表示写入 MySQL；mysql=0 表示只走本地导出/测试
```

如果某个商品匹配数量太少，常见原因是关键词太严格。可以先用更宽松的关键词导入或查询，例如：

```powershell
.\.venv\Scripts\python.exe -m jobs.import_copied_search_html --keyword "小米 充电宝" --input data\jd_urls.txt --limit 20
```

### 方案 B：浏览器自动采集

如果京东没有弹异常页，可以使用 Playwright 浏览器采集。首次使用先保存登录态：

```powershell
.\.venv\Scripts\python.exe -m jobs.prepare_browser_profile --platform jd --profile-dir browser_profiles\jd_new
```

在弹出的浏览器里登录京东、选择地区、确认搜索能正常显示商品，然后回终端按 Enter 保存。

采集：

```powershell
.\.venv\Scripts\python.exe -m jobs.browser_capture_search `
  --platform jd `
  --keyword "HUAWEI FreeBuds Pro 3" `
  --profile-dir browser_profiles\jd_new `
  --pages 1 `
  --limit 20 `
  --timeout 35 `
  --manual-verify-on-failure `
  --keep-open-on-failure
```

如果换账号，建议新建 profile，不要覆盖旧目录：

```powershell
.\.venv\Scripts\python.exe -m jobs.prepare_browser_profile --platform jd --profile-dir browser_profiles\jd_new
```

后续所有命令都带上：

```text
--profile-dir browser_profiles\jd_new
```

### 方案 C：商品详情 URL 补采

如果已经有具体商品详情链接，也可以补采。把链接放到：

```text
data\jd_urls.txt
```

一行一个，例如：

```text
https://item.jd.com/10078322255876.html
https://item.jd.com/10222031807639.html
```

运行：

```powershell
.\.venv\Scripts\python.exe -m jobs.browser_capture_search `
  --platform jd `
  --keyword "Logitech K380 蓝牙键盘" `
  --jd-url-file data\jd_urls.txt `
  --limit 20 `
  --timeout 25 `
  --headless
```

注意：详情页补采会逐个打开商品页，比“复制 HTML 导入”慢，也更容易被详情页加载或风控卡住。能用方案 A 时优先用方案 A。

## 淘宝采集方案

淘宝比京东更容易触发登录或安全验证。当前实现同样使用真实浏览器登录态，监听淘宝 `mtop/h5api/search` 等 Network 响应，并结合 DOM 兜底解析。

首次准备淘宝登录态：

```powershell
.\.venv\Scripts\python.exe -m jobs.prepare_browser_profile --platform taobao
```

在弹出的浏览器中登录淘宝并完成必要验证，确认能搜索并看到商品后，回终端按 Enter 保存。

采集：

```powershell
.\.venv\Scripts\python.exe -m jobs.browser_capture_search `
  --platform taobao `
  --keyword "Logitech K380 蓝牙键盘" `
  --pages 1 `
  --limit 20 `
  --timeout 35 `
  --manual-verify-on-failure `
  --keep-open-on-failure
```

也可以用自动任务入口：

```powershell
.\.venv\Scripts\python.exe -m jobs.auto_crawl `
  --platform taobao `
  --keyword "Logitech K380 蓝牙键盘" `
  --force `
  --rounds 1 `
  --task-limit 1 `
  --pages 1 `
  --item-limit 20 `
  --timeout 35
```

如果淘宝跳到登录、安全验证、访问受限页面，程序不会破解验证码。请在浏览器里手动完成验证后继续。

## 查询和验收

查询京东结果：

```powershell
.\.venv\Scripts\python.exe -m jobs.query_products --keyword "Logitech K380 蓝牙键盘" --platform jd --page 1 --page-size 10
```

查询淘宝结果：

```powershell
.\.venv\Scripts\python.exe -m jobs.query_products --keyword "Logitech K380 蓝牙键盘" --platform taobao --page 1 --page-size 10
```

查询全部平台：

```powershell
.\.venv\Scripts\python.exe -m jobs.query_products --keyword "Logitech K380 蓝牙键盘" --platform all --page 1 --page-size 10
```

项目里有一份型号级关键词文件：

```text
data\exact_product_keywords.txt
```

当前包含：

```text
Apple iPhone 15 128GB
HUAWEI FreeBuds Pro 3
Logitech K380 蓝牙键盘
小米自带线充电宝 10000mAh 22.5W
```

## 导出数据给前后端测试

前后端联调不建议依赖实时爬虫。推荐先把你本机已经抓到的 MySQL 数据导出成 JSON 数据包，交给其他同学导入。

### 导出测试数据包

导出型号级测试数据：

```powershell
.\.venv\Scripts\python.exe -m jobs.export_seed_data `
  --keyword-file data\exact_product_keywords.txt `
  --platform all `
  --limit 500 `
  --output data\seed.json
```

只导出京东：

```powershell
.\.venv\Scripts\python.exe -m jobs.export_seed_data `
  --keyword-file data\exact_product_keywords.txt `
  --platform jd `
  --limit 500 `
  --output data\team_seed_products_jd.json
```

导出后，把下面文件发给前后端同学：

```text
data\seed.json
data\exact_product_keywords.txt
README.md
requirements.txt
.env.example
```

如果前后端只需要看数据结构，可以直接打开 JSON；如果要在他们本机后端联调，按下一节导入 MySQL。

### 同学导入测试数据包

同学拿到数据包后，在自己的项目目录运行：

```powershell
# 示例：把路径替换成自己本机实际保存 onebuy_crawler 的位置
cd <你的项目路径>\onebuy_crawler

$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="他们自己的 MySQL 密码"
$env:MYSQL_DATABASE="onebuy"
$env:CRAWLER_ENABLE_MYSQL="1"

.\.venv\Scripts\python.exe -m jobs.init_schema

.\.venv\Scripts\python.exe -m jobs.import_seed_data `
  --seed-file data\seed.json `
  --platform all
```

如果数据库中已有数据，只想补缺：

```powershell
.\.venv\Scripts\python.exe -m jobs.import_seed_data `
  --seed-file data\seed.json `
  --platform all `
  --only-missing `
  --min-count 3
```

导入后验证：

```powershell
.\.venv\Scripts\python.exe -m jobs.query_products --keyword "Apple iPhone 15 128GB" --platform all --page 1 --page-size 10
.\.venv\Scripts\python.exe -m jobs.query_products --keyword "Logitech K380 蓝牙键盘" --platform all --page 1 --page-size 10
```

## 常见问题

### 京东页面出现“当前页面异常”

这是京东风控页，页面里没有商品数据。不要继续用脚本刷新。改用“方案 A：复制京东搜索页 HTML 导入”。

### `copy(...)` 后控制台显示 `undefined`

正常。浏览器控制台的 `copy()` 没有返回值，但已经把内容复制到剪贴板。

### `jd_urls.txt` 末尾有“显示更多”“购物车”

正常。整页 HTML 包含很多非商品区域，解析器会只读取商品卡片里的 `data-sku`、标题、价格、图片、销量等字段。

### 小米充电宝只导入很少

通常是关键词过严。现在代码已经兼容 `小米自带线充电宝`、`小米 充电宝 自带线`、`10000mAh`、`10000毫安`、`22.5W/22.5w` 等写法。仍然太少时，可以先用宽关键词导入：

```powershell
.\.venv\Scripts\python.exe -m jobs.import_copied_search_html --keyword "小米 充电宝" --input data\jd_urls.txt --limit 20
```

### 想离线测试，不写 MySQL

设置：

```powershell
$env:CRAWLER_ENABLE_MYSQL="0"
```

然后导出 JSONL：

```powershell
.\.venv\Scripts\python.exe -m jobs.import_copied_search_html `
  --keyword "Logitech K380 蓝牙键盘" `
  --input data\jd_urls.txt `
  --limit 10 `
  --output-file output\k380_debug.jsonl
```

## 开发检查

运行单元测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

编译检查：

```powershell
.\.venv\Scripts\python.exe -m compileall jobs onebuy_crawler tests
```

## 合规边界

本项目用于课程设计和联调演示。采集时应低频运行，优先使用已正常显示的页面内容，不实现验证码破解、登录绕过或高频请求。目标站点提示访问异常、验证码或访问频繁时，应停止自动化采集，使用本地缓存、导出的测试数据包或手动复制 HTML 的方式保障前后端联调。


