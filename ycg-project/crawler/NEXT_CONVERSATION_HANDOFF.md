# 下一次对话交接总结：一次买够爬虫模块

## 当前目标

项目是“**一次买够**”网购比价平台。爬虫模块负责采集京东、淘宝商品数据，清洗后写入 MySQL，供后端接口和前端小程序做搜索、比价、详情展示、价格历史和购买跳转。

当前验收重点已经从“尽量自动爬任意搜索词”调整为“稳定准备一批可展示的真实商品数据”：

- 京东：使用 **正常浏览器手动搜索 + 复制搜索结果 HTML + 本地解析入库** 作为主路径。
- 淘宝：使用 **CDP 连接真实 Edge + 手动搜索到结果页 + 当前页采集** 作为主路径。
- 商品：已经完成一批真实商品数据采集、手动价格清洗和导出。`南孚 5号电池 40粒` 已不再作为当前验收商品，不需要补抓；商品数量不要求京东/淘宝完全平衡。

## 当前工作目录

```powershell
D:\study_file\Junior\ComprehensiveComputerProject\onebuy_crawler
```

虚拟环境：

```powershell
D:\study_file\Junior\ComprehensiveComputerProject\onebuy_crawler\.venv
```

## 数据库和入库流程

MySQL 数据库名：

```text
onebuy
```

`.env` 中应开启：

```text
CRAWLER_ENABLE_MYSQL=1
```

不要在交接内容里暴露数据库密码。需要时直接读取项目 `.env`。

初始化数据库：

```powershell
.\.venv\Scripts\python.exe -m jobs.init_schema
```

采集到的数据统一走：

```text
CleaningPipeline -> DedupPipeline -> RawLogPipeline -> MySqlPipeline
```

主要表：

```text
products
platform_offers
price_history
raw_crawl_records
crawl_tasks
```

## 当前数据状态

最近一次整理后，数据库已经完成手动清洗后的结构修复：

```text
products=194
platform_offers=229
price_history=247
京东报价=106
淘宝报价=123
products_without_offers=0
offers_without_product=0
history_without_product=0
missing_url=0
bad_price=0
summary_mismatch=0
```

已处理的问题：

- 合并了手动删除后残留的重复商品分组。
- 重新汇总了 `products.min_price`、`max_price`、`price_diff`、`best_platform`。
- 删除了最后一条规格混入的雀巢咖啡异常记录。
- 分类重建检查为 0 个更新候选。

## 当前稳定采集方案

### 京东：HTML 导入为主

京东自动浏览器搜索现在不稳定，常见现象是搜索后被重定向到首页或异常页。不要反复用脚本刷京东搜索页。

推荐流程：

1. 用普通浏览器打开京东并手动搜索商品。
2. 等商品列表显示，必要时向下滚动一下。
3. F12 打开 Console，执行：

```javascript
(() => {
  const html = document.documentElement.outerHTML;
  copy(html);
  console.log("已复制页面HTML，长度：", html.length);
})();
```

4. 保存剪贴板内容：

```powershell
New-Item -ItemType Directory -Force data\jd_search_html
Get-Clipboard -Raw | Set-Content -Path "data\jd_search_html\yuhua_huozhe.html" -Encoding UTF8
```

5. 导入：

```powershell
$env:CRAWLER_ENABLE_MYSQL="1"

.\.venv\Scripts\python.exe -m jobs.import_copied_search_html `
  --keyword "余华 活着" `
  --input data\jd_search_html\yuhua_huozhe.html `
  --limit 10
```

成功时重点看：

```text
rows      从 HTML 解析到的商品卡片数量
matched   通过关键词过滤的数量
imported  实际入库数量
mysql=1   已写入 MySQL
```

如果 `rows>0` 但 `matched=0`，通常是关键词太严格。比如京东书籍标题经常不包含 ISBN，`余华 活着 ISBN 9787530215593` 应改成 `余华 活着`。

### 淘宝：CDP 手动当前页采集

启动 Edge：

```powershell
.\.venv\Scripts\python.exe -m jobs.launch_debug_browser `
  --port 9223 `
  --use-default-user-data `
  --url https://www.taobao.com/
```

另开 PowerShell，运行采集命令：

```powershell
.\.venv\Scripts\python.exe -m jobs.browser_capture_search `
  --platform taobao `
  --keyword "维达 V2239 抽纸 3层130抽24包" `
  --cdp-url http://127.0.0.1:9223 `
  --pages 1 `
  --limit 10 `
  --timeout 60 `
  --manual-search-wait `
  --manual-search-only `
  --keep-open-on-failure
```

命令启动后，在 Edge 里手动搜索同一个关键词，确认商品列表可见后回终端按 Enter。淘宝首页搜索如果跳空白页，可以保留一个已经成功打开的搜索结果页，在结果页顶部搜索框里继续搜下一个商品。

## 当前验收商品

京东导入和最终查询建议用较短关键词。当前有效验收商品不包含南孚电池：

```text
余华 活着
维达 V2239 抽纸 24包
蓝月亮 深层洁净 洗衣液 3kg
云南白药 益优冰柠牙膏 145g
海飞丝 怡神冰凉 洗发水 750ml
多芬 深层营润 沐浴露 720g
晨光 K35 中性笔 0.5mm 12支
可口可乐 330ml 24罐
雀巢咖啡 1+2 原味 100条
```

相关文件：

```text
data\exact_product_keywords.txt
data\compare_keywords.txt
data\crawl_keywords_20.txt
data\taobao_priority_keywords_20.txt
data\jd_search_html\README.md
```

`data\taobao_priority_keywords_20.txt` 保留更完整的淘宝搜索词。文件名里的 `20` 是早期记录遗留，当前有效验收数据以前端测试导出包为准。

注意：部分关键词文件可能仍保留早期候选词，最终以前端测试导出包中的数据为准。

## 当前代码能力

已实现：

- 京东复制 HTML 导入：`jobs.import_copied_search_html`
- 京东/淘宝浏览器采集：`jobs.browser_capture_search`
- CDP 调试浏览器启动：`jobs.launch_debug_browser`
- 商品查询：`jobs.query_products`
- 测试数据导出/导入：`jobs.export_seed_data`、`jobs.import_seed_data`
- 清洗、去重、价格历史、失败日志入库
- 商品 URL 保留到 `platform_offers.product_url`，前端可以用它跳转到淘宝或京东购买
- 稳定验收商品分类规则已扩展到图书、纸品、衣物清洁、口腔护理、洗护沐浴、电池、文具、饮料、咖啡冲饮

## 查询和导出

查询某个商品：

```powershell
.\.venv\Scripts\python.exe -m jobs.query_products --keyword "维达 V2239 抽纸 24包" --platform all --page 1 --page-size 10
```

导出给前后端测试：

当前已生成最新测试包：

```text
output\test_exports\products_api_response.json
output\test_exports\products_list.json
output\test_exports\onebuy_seed_records_all.json
output\test_exports\platform_offers.csv
output\test_exports\price_history.csv
output\test_exports\category_summary.csv
output\onebuy_test_exports.zip
```

前端直接 mock 接口时优先用：

```text
output\test_exports\products_api_response.json
```

后端重新导入 MySQL 时使用：

```text
output\test_exports\onebuy_seed_records_all.json
```

重新导出后端 seed JSON：

```powershell
.\.venv\Scripts\python.exe -m jobs.export_seed_data `
  --platform all `
  --limit 1000 `
  --output output\test_exports\onebuy_seed_records_all.json
```

仓库里已有的旧 seed JSON 可能仍是早期数码类样例。当前交付应使用 `output\test_exports` 中的最新导出文件。

## 注意事项

- 不要把 `.env`、`browser_profiles/`、`output/` 提交。
- `data/jd_search_html/*.html` 已加入 `.gitignore`，避免提交大段复制 HTML。
- 采集时不实现验证码破解、登录绕过或高频请求。
- 如果目标站点提示访问异常、验证码或访问频繁，应停止自动化采集，使用 HTML 导入、本地缓存或 seed 数据保障验收和联调。

## 新对话继续时可以直接说

```text
请读取 onebuy_crawler/NEXT_CONVERSATION_HANDOFF.md，继续“一次买够”爬虫任务。
当前京东主路径已经切换为手动复制搜索结果 HTML 后本地导入；淘宝主路径是 CDP 手动搜索当前页采集。
当前数据库已完成手动价格清洗和一致性修复，最新前后端测试数据在 output\test_exports 和 output\onebuy_test_exports.zip。
```
