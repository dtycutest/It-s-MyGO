# "一次买够"网购比价平台系统设计说明书

1.  ## 系统体系架构 

    1.  ### 数据采集与处理模块架构设计

数据采集与处理模块位于系统整体架构中的数据层，负责从外部电商平台获取原始商品数据，并经过清洗、去重与结构化处理后存储至数据库，为后端业务服务提供数据支撑。

该模块在系统中的数据流关系如下：

-   上游：电商平台（淘宝、京东等）

-   本模块：数据采集 → 数据清洗 → 数据聚合 → 数据入库

-   下游：商品服务模块（提供比价API）

2.  ## 系统功能结构 

    1.  ### 数据采集与处理模块功能划分

本模块采用分层设计思想，将功能划分为多个子模块：

-   爬虫采集子模块

    -   多平台数据抓取

    -   请求调度

    -   反爬机制处理

-   数据清洗子模块

    -   数据格式标准化

    -   异常数据过滤

    -   字段补全

-   数据去重与聚合子模块

    -   商品匹配

    -   相似度计算

    -   数据融合

-   数据入库子模块

    -   商品数据新增

    -   平台数据更新

    -   数据持久化

-   调度与监控子模块

    -   定时任务执行

    -   日志记录

    -   异常处理

3.  ## 系统用例时序图（顺序图）及说明 

    1.  ### 用例：商品数据采集与入库

**时序描述**

1.  调度器触发爬虫任务

2.  爬虫向目标电商平台发送请求

3.  平台返回商品页面数据

4.  爬虫解析页面并提取商品信息

5.  数据进入清洗模块进行标准化处理

6.  执行商品去重与匹配

7.  数据写入数据库

8.  返回任务执行结果

```{=html}
<!-- -->
```
4.  ## 复杂功能算法设计

    1.  ### 商品匹配算法

**设计思路**

针对不同平台商品名称不统一的问题，采用基于文本相似度的匹配算法，实现商品聚合。

**伪代码**

  ---------------------------------------------------------------
  function matchProduct(newProduct, productList):\
  for product in productList:\
  similarity = calcSimilarity(newProduct.title, product.title)\
  if similarity \> THRESHOLD:\
  return product.id\
  return NULL

  ---------------------------------------------------------------

### 数据入库更新算法（Upsert）

**设计思路**

保证数据唯一性，同时支持价格更新。

**伪代码**

  --------------------------------------
  function saveProduct(product):\
  if product exists:\
  update platform price\
  recalculate min_price and max_price\
  else:\
  insert new product

  --------------------------------------

## 面向对象类图设计

**核心类设计**

系统采用面向对象设计方法，将数据采集模块抽象为以下核心类：

-   Crawler（爬虫控制类）

-   ProductItem（商品数据模型）

-   DataCleaner（数据清洗类）

-   ProductMatcher（商品匹配类）

-   DatabaseService（数据库服务类）

**类关系说明**

-   Crawler 负责数据抓取

-   DataCleaner 负责数据预处理

-   ProductMatcher 负责商品匹配

-   DatabaseService 负责数据持久化

## 接口设计（模块内部接口）

本模块主要提供内部处理接口，包括：

-   clean(data) → cleaned_data

-   match(product) → product_id

-   save(product) → success/fail

接口用于模块间数据传递，不直接对外提供HTTP服务。

## 数据库物理设计

**商品表（product）**

  **字段**     **类型**   **说明**
  ------------ ---------- --------------
  product_id   varchar    商品唯一标识
  title        varchar    商品名称
  min_price    double     最低价格
  max_price    double     最高价格

**平台表（platform）**

  **字段**       **类型**   **说明**
  -------------- ---------- ----------
  platform_id    int        平台编号
  product_id     varchar    商品ID
  price          double     当前价格
  sales_volume   int        销量
  product_url    varchar    商品链接
