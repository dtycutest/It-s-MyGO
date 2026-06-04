# 1. 系统体系架构

接入层：Nginx/API 网关（生产）或 Uvicorn（演示）接收 HTTPS 请求，转发至
FastAPI 服务。\
应用层：app/main.py 提供 RESTful
API，按认证、商品、用户、收藏、降价提醒、推荐、分析等业务分组。\
领域与数据层：app/schemas.py 定义统一数据模型；app/data.py
提供示例数据与查询能力；app/auth.py 负责令牌签发、校验、刷新。\
横切能力：统一响应（ApiResponse）、统一异常处理、鉴权依赖注入（Depends(get_current_user)）。

# 2. 系统功能结构（层次结构）

认证与安全模块：/auth/login、/auth/refresh、/auth/logout。\
商品与搜索模块：/products/search、/products/{product_id}、/products/categories。\
用户中心模块：/users/profile、/users/favorites\*、/users/price-alerts\*。\
行为与推荐模块：/users/browse-history\*、/users/search-records、/search/hot-words、/recommendations/personalized、/analytics/events。\
基础支撑模块：分页器 paginate、全局异常映射、统一 JSON 结构。

# 3. 系统用例时序图（顺序图）及说明

以\"用户搜索商品并查看详情\"为例（后端关键链路）：

![图形用户界面, 应用程序 AI
生成的内容可能不正确。](media/image1.png){width="6.0in"
height="4.320138888888889in"}

说明：\
1)
搜索请求进入后，先记录搜索词，再执行关键词过滤、条件筛选、排序与分页。\
2) 商品详情请求按 product_id 精确查询；若不存在返回业务错误码 404001。\
3) 两类接口均通过统一响应格式返回，便于前端统一解析。

# 4. 复杂功能算法设计（流程/伪码）

## 4.1 多条件商品搜索与排序算法

Input: keyword, category_id, min_price, max_price, platform, sort, page,
page_size\
Step1: results \<- products 中 title 包含 keyword 的集合\
Step2: 若有 category_id, 保留 category_id 匹配项\
Step3: 若有价格区间, 保留 min_price/max_price 落在范围内的项\
Step4: 若有 platform 过滤, 保留包含任一平台编码的商品\
Step5: 按 sort 执行排序(price_asc/price_desc/sales_desc/rating_desc)\
Step6: 根据 page/page_size 计算切片并生成 pagination\
Output: PaginatedResponse(list, pagination)

## 4.2 降价提醒触发判定算法（后台任务设计）

for alert in price_alerts where is_enabled = true:\
product = find_product(alert.product_id)\
if not product: continue\
current_price = min(平台价) 或 product.min_price\
if current_price \<= alert.target_price and alert.is_triggered ==
false:\
alert.is_triggered = true\
alert.triggered_at = now\
发送通知(站内信/订阅消息)\
alert.current_price = current_price\
alert.updated_at = now

# 5. 面向对象方法类图的详细设计

![图示 AI 生成的内容可能不正确。](media/image2.png){width="6.0in"
height="8.615972222222222in"}

设计说明：\
- schemas.py 中模型承担 DTO/领域实体双重角色，保证接口契约稳定。\
- TokenStore 为认证核心对象，负责令牌生命周期管理。\
- data.py 提供\"仓储式\"数据访问函数（如 find_product、record_search）。

# 6. 接口设计

## 6.1 统一约定

协议：HTTP/HTTPS + JSON。\
鉴权：Bearer Token（除登录、刷新、热搜等公开接口）。\
成功响应：{code: 0, message: \"ok\|业务提示\", data: \...}。\
失败响应：HTTP 状态码 + {code: 业务错误码, message: 错误说明, data:
null}。

## 6.2 代表性接口

  模块       接口                            方法       说明
  ---------- ------------------------------- ---------- --------------------------------
  认证       /auth/login                     POST       微信 code 登录并返回 TokenPair
  商品       /products/search                GET        多条件搜索 + 排序 + 分页
  商品       /products/{product_id}          GET        查询单商品详情
  收藏       /users/favorites                GET/POST   收藏列表与新增
  降价提醒   /users/price-alerts             GET/POST   提醒查询与创建
  推荐       /recommendations/personalized   GET        个性化推荐（示例）
  分析       /analytics/events               POST       用户行为上报

\> 完整字段结构以 openapi.json 与 app/schemas.py 为准。

# 7. 数据库物理设计

当前仓库为演示实现，使用内存数据结构（重启后重置）。若落地生产，建议
MySQL + Redis 物理设计如下：\
\
- MySQL
核心表：users、products、platform_prices、favorites、price_alerts、browse_history、search_records、analytics_events。\
- 关键索引：\
- products(title, category_id)（搜索）\
- platform_prices(product_id, platform_code,
updated_at)（比价与最新价）\
- favorites(user_id, product_id)（防重复收藏）\
- price_alerts(user_id, is_enabled, is_triggered)（提醒任务扫描）\
- Redis 使用建议：热搜词缓存、Token 黑名单、短期会话态、限流计数器。

# 8. UI（界面）设计

后端不直接渲染页面，但为前端界面提供稳定数据契约：\
\
- 首页搜索页：依赖 /products/search、/search/hot-words。\
- 商品详情页：依赖 /products/{product_id}，展示多平台价格与跳转链接。\
- 我的收藏/降价提醒页：依赖 /users/favorites\*、/users/price-alerts\*。\
- 个人中心页：依赖 /users/profile。\
- 行为埋点：页面交互通过 /analytics/events 回传，支撑推荐与运营分析。
