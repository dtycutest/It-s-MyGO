# "一次买够"小程序 UI开发实现指南

## 📚 本指南概览

本指南配合"微信小程序UI设计方案.md"使用，提供从设计到代码实现的完整路径。

---

## 🎨 1. 颜色系统实现

### SCSS 变量定义

```scss
// src/styles/variables.scss

// ============ 颜色定义 ============
// 主色系
$primary-color: #FF6B35;        // 主色 - 橙红色
$primary-light: #FFD4B9;        // 主色浅
$primary-dark: #E55A26;         // 主色深

// 辅助色系
$secondary-color: #004E89;      // 辅助色 - 深蓝色
$secondary-light: #4A90C5;      // 辅助色浅
$secondary-dark: #002E54;       // 辅助色深

// 功能色系
$success-color: #50C878;        // 成功色 - 绿色
$warning-color: #FFB81C;        // 警告色 - 黄色
$danger-color: #E4405F;         // 危险色 - 红色

// 中立色系
$white: #FFFFFF;                // 纯白
$bg-primary: #F5F5F5;           // 主背景色
$bg-secondary: #FAFAFA;         // 次背景色
$border-color: #EEEEEE;         // 边框色
$text-dark: #333333;            // 深文本色
$text-normal: #666666;          // 普通文本色
$text-light: #999999;           // 浅文本色
$text-placeholder: #CCCCCC;     // 占位文本色

// ============ 特殊颜色 ============
$price-color: #FF6B35;          // 价格突出色 = 主色
$discount-color: #50C878;       // 优惠色 = 成功色
$new-color: #FFB81C;            // 新品色 = 警告色
```

### 颜色使用映射表

```scss
// 按钮
.btn-primary {
  background-color: $primary-color;
  &:active {
    background-color: $primary-dark;
  }
  &:disabled {
    background-color: $text-light;
  }
}

// 链接和高亮
a, .link {
  color: $secondary-color;
  &:active {
    color: $secondary-dark;
  }
}

// 标签和徽章
.tag-success { background: $success-color; }
.tag-warning { background: $warning-color; }
.tag-danger { background: $danger-color; }

// 背景和分割
.container {
  background-color: $white;
}
.section {
  background-color: $bg-primary;
  border-bottom: 1px solid $border-color;
}

// 文本
.text-primary { color: $text-dark; }
.text-secondary { color: $text-normal; }
.text-hint { color: $text-light; }
```

---

## 🔤 2. 字体系统实现

### 字体导入

```scss
// src/styles/fonts.scss

@font-face {
  font-family: 'PingFang SC';
  src: url('/assets/fonts/PingFangSC-Regular.ttf') format('truetype');
  font-weight: 400;
}

@font-face {
  font-family: 'PingFang SC';
  src: url('/assets/fonts/PingFangSC-Semibold.ttf') format('truetype');
  font-weight: 600;
}

@font-face {
  font-family: 'PingFang SC';
  src: url('/assets/fonts/PingFangSC-Bold.ttf') format('truetype');
  font-weight: 700;
}

// 应用全局字体
body {
  font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, 
               'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}
```

### 文字样式规范

```scss
// src/styles/typography.scss

// 标题
.h1, h1 {
  font-size: 28px;
  font-weight: 700;
  line-height: 32px;
  letter-spacing: -0.5px;
  color: $text-dark;
}

.h2, h2 {
  font-size: 20px;
  font-weight: 600;
  line-height: 24px;
  color: $text-dark;
}

.h3, h3 {
  font-size: 16px;
  font-weight: 600;
  line-height: 20px;
  color: $text-dark;
}

// 正文
.body, body {
  font-size: 14px;
  font-weight: 400;
  line-height: 20px;
  color: $text-dark;
}

// 小文本
.small {
  font-size: 12px;
  font-weight: 400;
  line-height: 18px;
  color: $text-light;
}

// 超小文本
.xs {
  font-size: 11px;
  font-weight: 400;
  line-height: 16px;
  color: $text-light;
}

// 价格专用
.price-normal {
  font-size: 14px;
  font-weight: 600;
  color: $price-color;
}

.price-large {
  font-size: 18px;
  font-weight: 700;
  color: $price-color;
}
```

---

## 📏 3. 间距系统实现

### 间距变量定义

```scss
// src/styles/spacing.scss

$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 12px;
$spacing-lg: 16px;
$spacing-xl: 24px;
$spacing-xxl: 32px;

// 生成工具类
@for $i from 1 through 10 {
  $value: $spacing-xs * $i;
  .m#{$i * 4} { margin: $value; }
  .mt#{$i * 4} { margin-top: $value; }
  .mr#{$i * 4} { margin-right: $value; }
  .mb#{$i * 4} { margin-bottom: $value; }
  .ml#{$i * 4} { margin-left: $value; }
  .mv#{$i * 4} { 
    margin-top: $value;
    margin-bottom: $value;
  }
  .mh#{$i * 4} {
    margin-left: $value;
    margin-right: $value;
  }
}

// 边距
@for $i from 1 through 10 {
  $value: $spacing-xs * $i;
  .p#{$i * 4} { padding: $value; }
  .pt#{$i * 4} { padding-top: $value; }
  .pr#{$i * 4} { padding-right: $value; }
  .pb#{$i * 4} { padding-bottom: $value; }
  .pl#{$i * 4} { padding-left: $value; }
  .pv#{$i * 4} {
    padding-top: $value;
    padding-bottom: $value;
  }
  .ph#{$i * 4} {
    padding-left: $value;
    padding-right: $value;
  }
}
```

---

## 🎯 4. 组件库核心实现

### 4.1 ProductCard 商品卡片

```vue
<!-- src/components/ProductCard.vue -->
<template>
  <view class="product-card">
    <!-- 商品图片 -->
    <view class="card-image">
      <image :src="product.image" mode="aspectFill" />
      <view v-if="product.isNew" class="badge badge-new">新</view>
      <view v-if="product.discount" class="badge badge-discount">特价</view>
    </view>
    
    <!-- 商品信息 -->
    <view class="card-info">
      <view class="product-title">{{ product.title }}</view>
      
      <!-- 评分 -->
      <view class="rating-row">
        <view class="rating">
          <text v-for="n in 5" :key="n" :class="n <= product.rating ? 'star-fill' : 'star-empty'">★</text>
        </view>
        <text class="rating-count">{{ product.ratingCount }}+</text>
      </view>
      
      <!-- 价格 -->
      <view class="price-row">
        <text class="price-min">¥{{ product.minPrice }}</text>
        <text class="price-range">- ¥{{ product.maxPrice }}</text>
      </view>
      
      <!-- 平台徽章 -->
      <view class="platforms-row">
        <view v-for="(platform, idx) in product.platforms.slice(0, 3)" :key="idx" class="platform-badge">
          {{ platform }}
        </view>
        <view v-if="product.platforms.length > 3" class="platform-more">
          +{{ product.platforms.length - 3 }}
        </view>
      </view>
      
      <!-- 操作按钮 -->
      <view class="action-row">
        <button class="btn-secondary" @click="handleFavorite">❤️ {{ isFavorited ? '已收藏' : '收藏' }}</button>
        <button class="btn-primary" @click="handleViewDetail">查看详情 →</button>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'ProductCard',
  props: {
    product: {
      type: Object,
      required: true,
      validator: (obj) => {
        return obj.image && obj.title && obj.minPrice;
      }
    }
  },
  data() {
    return {
      isFavorited: false
    };
  },
  methods: {
    handleFavorite() {
      this.isFavorited = !this.isFavorited;
      this.$emit('favorite', this.product.id);
    },
    handleViewDetail() {
      this.$emit('detail', this.product.id);
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/styles/variables.scss';

.product-card {
  position: relative;
  background: $white;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: $spacing-lg;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  
  &:active {
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  }
}

.card-image {
  position: relative;
  width: 100%;
  height: 200px;
  background: $bg-primary;
  
  image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .badge {
    position: absolute;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    color: $white;
    
    &.badge-new {
      top: $spacing-sm;
      right: $spacing-sm;
      background: $warning-color;
    }
    
    &.badge-discount {
      top: $spacing-sm;
      left: $spacing-sm;
      background: $danger-color;
    }
  }
}

.card-info {
  padding: $spacing-lg;
}

.product-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
  color: $text-dark;
  margin-bottom: $spacing-sm;
}

.rating-row {
  display: flex;
  align-items: center;
  margin-bottom: $spacing-sm;
  
  .rating {
    color: $warning-color;
    font-size: 12px;
    margin-right: $spacing-sm;
    
    .star-fill {
      color: $warning-color;
    }
    
    .star-empty {
      color: $border-color;
    }
  }
  
  .rating-count {
    font-size: 12px;
    color: $text-light;
  }
}

.price-row {
  display: flex;
  align-items: baseline;
  margin-bottom: $spacing-md;
  
  .price-min {
    font-size: 18px;
    font-weight: 700;
    color: $price-color;
    margin-right: $spacing-xs;
  }
  
  .price-range {
    font-size: 12px;
    color: $text-light;
  }
}

.platforms-row {
  display: flex;
  flex-wrap: wrap;
  gap: $spacing-xs;
  margin-bottom: $spacing-lg;
  
  .platform-badge {
    display: inline-block;
    padding: 2px 6px;
    background: $bg-primary;
    border-radius: 4px;
    font-size: 11px;
    color: $text-normal;
  }
  
  .platform-more {
    padding: 2px 6px;
    background: $bg-primary;
    border-radius: 4px;
    font-size: 11px;
    color: $secondary-color;
  }
}

.action-row {
  display: flex;
  gap: $spacing-sm;
  
  button {
    flex: 1;
    height: 36px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    
    &.btn-primary {
      background: $primary-color;
      color: $white;
      
      &:active {
        background: $primary-dark;
        transform: scale(0.98);
      }
    }
    
    &.btn-secondary {
      background: $bg-primary;
      color: $text-dark;
      border: 1px solid $border-color;
      
      &:active {
        background: $border-color;
      }
    }
  }
}
</style>
```

### 4.2 PriceLabel 价格标签

```vue
<!-- src/components/PriceLabel.vue -->
<template>
  <view :class="['price-label', `price-${size}`, `type-${type}`]">
    <text class="currency">¥</text>
    <text class="amount">{{ price }}</text>
  </view>
</template>

<script>
export default {
  name: 'PriceLabel',
  props: {
    price: {
      type: [Number, String],
      required: true,
      validator: (val) => !isNaN(val)
    },
    size: {
      type: String,
      default: 'normal',
      validator: (val) => ['small', 'normal', 'large'].includes(val)
    },
    type: {
      type: String,
      default: 'primary',
      validator: (val) => ['primary', 'success', 'warning', 'danger'].includes(val)
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/styles/variables.scss';

.price-label {
  display: inline-flex;
  align-items: center;
  font-weight: 600;
  
  .currency {
    font-size: 0.85em;
    margin-right: 2px;
  }
  
  .amount {
    font-feature-settings: 'tnum';
  }
  
  // 尺寸变体
  &.price-small {
    font-size: 12px;
    
    .currency {
      font-size: 10px;
    }
  }
  
  &.price-normal {
    font-size: 14px;
  }
  
  &.price-large {
    font-size: 18px;
  }
  
  // 颜色变体
  &.type-primary {
    color: $price-color;
  }
  
  &.type-success {
    color: $success-color;
  }
  
  &.type-warning {
    color: $warning-color;
  }
  
  &.type-danger {
    color: $danger-color;
  }
}
</style>
```

### 4.3 PlatformBadge 平台徽章

```vue
<!-- src/components/PlatformBadge.vue -->
<template>
  <view :class="['platform-badge', `platform-${platform.toLowerCase()}`]">
    <image :src="platformIcon" class="badge-icon" />
    <text class="badge-text">{{ platform }}</text>
  </view>
</template>

<script>
export default {
  name: 'PlatformBadge',
  props: {
    platform: {
      type: String,
      required: true,
      validator: (val) => {
        return ['淘宝', '京东', '拼多多', '亚马逊', '苏宁', '其他'].includes(val);
      }
    },
    size: {
      type: String,
      default: 'normal',
      validator: (val) => ['small', 'normal', 'large'].includes(val)
    }
  },
  computed: {
    platformIcon() {
      const icons = {
        '淘宝': '/assets/icons/taobao.png',
        '京东': '/assets/icons/jingdong.png',
        '拼多多': '/assets/icons/pinduoduo.png',
        '亚马逊': '/assets/icons/amazon.png',
        '苏宁': '/assets/icons/suning.png',
        '其他': '/assets/icons/default.png'
      };
      return icons[this.platform] || icons['其他'];
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/styles/variables.scss';

.platform-badge {
  display: inline-flex;
  align-items: center;
  gap: $spacing-xs;
  padding: 4px 8px;
  border-radius: 4px;
  background: $bg-primary;
  font-size: 12px;
  font-weight: 600;
  
  .badge-icon {
    width: 16px;
    height: 16px;
    border-radius: 2px;
  }
  
  .badge-text {
    color: $text-dark;
  }
  
  // 平台特色色
  &.platform-淘宝 {
    background: #FFF7E6;
    color: #E1640F;
  }
  
  &.platform-京东 {
    background: #E8F5FF;
    color: #0052CC;
  }
  
  &.platform-拼多多 {
    background: #FFE8E8;
    color: #E82E2E;
  }
}
</style>
```

---

## 📲 5. 页面实现框架

### 首页实现结构

```vue
<!-- src/pages/index/index.vue -->
<template>
  <view class="index-page">
    <!-- 搜索栏 -->
    <SearchBar @search="handleSearch" />
    
    <!-- 分类导航 -->
    <CategoryNav @select="handleCategory" />
    
    <!-- Banner 轮播 -->
    <swiper 
      class="banner" 
      autoplay 
      interval="3000" 
      indicator-dots
      indicator-active-color="#FF6B35"
    >
      <swiper-item v-for="(banner, idx) in banners" :key="idx">
        <image :src="banner.image" />
      </swiper-item>
    </swiper>
    
    <!-- 热搜榜 -->
    <MoreHeader title="🔥 热搜榜" />
    <view class="hot-search-list">
      <view 
        v-for="(word, idx) in hotWords" 
        :key="idx" 
        class="hot-item"
        @click="handleHotWordClick(word)"
      >
        <text class="rank">[{{ idx + 1 }}]</text>
        <text class="word">{{ word.name }}</text>
        <text class="heat">{{ word.count }}k热</text>
      </view>
    </view>
    
    <!-- 推荐商品 -->
    <MoreHeader title="推荐好物" />
    <scroll-view class="recommend-scroll" scroll-x>
      <ProductCard 
        v-for="product in recommendProducts" 
        :key="product.id"
        :product="product"
        @detail="handleProductDetail"
      />
    </scroll-view>
    
    <!-- 加载更多 -->
    <LoadingIndicator v-if="isLoading" />
  </view>
</template>

<script>
import SearchBar from '@/components/SearchBar.vue';
import CategoryNav from '@/components/CategoryNav.vue';
import ProductCard from '@/components/ProductCard.vue';
import MoreHeader from '@/components/MoreHeader.vue';
import LoadingIndicator from '@/components/LoadingIndicator.vue';

export default {
  components: {
    SearchBar,
    CategoryNav,
    ProductCard,
    MoreHeader,
    LoadingIndicator
  },
  data() {
    return {
      banners: [],
      hotWords: [],
      recommendProducts: [],
      isLoading: false
    };
  },
  onLoad() {
    this.loadBanners();
    this.loadHotWords();
    this.loadRecommendProducts();
  },
  methods: {
    async loadBanners() {
      try {
        const res = await uni.request({
          url: 'https://api.ycg.com/api/v1/banners',
          method: 'GET'
        });
        if (res.data.code === 0) {
          this.banners = res.data.data;
        }
      } catch (error) {
        console.error('加载 Banner 失败:', error);
      }
    },
    async loadHotWords() {
      try {
        const res = await uni.request({
          url: 'https://api.ycg.com/api/v1/search/hot-words?limit=6',
          method: 'GET'
        });
        if (res.data.code === 0) {
          this.hotWords = res.data.data;
        }
      } catch (error) {
        console.error('加载热搜词失败:', error);
      }
    },
    async loadRecommendProducts() {
      this.isLoading = true;
      try {
        const res = await uni.request({
          url: 'https://api.ycg.com/api/v1/recommendations/personalized?page=1&page_size=10',
          method: 'GET',
          header: {
            'Authorization': `Bearer ${this.$store.state.user.token}`
          }
        });
        if (res.data.code === 0) {
          this.recommendProducts = res.data.data.list;
        }
      } catch (error) {
        console.error('加载推荐商品失败:', error);
      } finally {
        this.isLoading = false;
      }
    },
    handleSearch(keyword) {
      uni.navigateTo({
        url: `/pages/searchResults/searchResults?keyword=${keyword}`
      });
    },
    handleCategory(categoryId) {
      uni.navigateTo({
        url: `/pages/searchResults/searchResults?categoryId=${categoryId}`
      });
    },
    handleHotWordClick(word) {
      this.handleSearch(word.name);
    },
    handleProductDetail(productId) {
      uni.navigateTo({
        url: `/pages/productDetail/productDetail?id=${productId}`
      });
    }
  }
};
</script>

<style scoped lang="scss">
@import '@/styles/variables.scss';

.index-page {
  background: $bg-primary;
  min-height: 100vh;
}

.banner {
  width: 100%;
  height: 180px;
  background: $white;
  margin-bottom: $spacing-lg;
  
  swiper-item {
    width: 100%;
    height: 180px;
    
    image {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
}

.hot-search-list {
  background: $white;
  padding: $spacing-lg;
  
  .hot-item {
    display: flex;
    align-items: center;
    padding: $spacing-md 0;
    border-bottom: 1px solid $border-color;
    
    &:last-child {
      border-bottom: none;
    }
    
    .rank {
      width: 30px;
      font-weight: 700;
      color: $primary-color;
    }
    
    .word {
      flex: 1;
      font-size: 14px;
      color: $text-dark;
    }
    
    .heat {
      font-size: 12px;
      color: $text-light;
    }
  }
}

.recommend-scroll {
  white-space: nowrap;
  padding: $spacing-lg;
  background: $white;
}
```

---

## 🔌 6. API 集成示例

### 创建 API 模块

```javascript
// src/api/product.js

import request from '@/utils/request';

// 搜索商品
export function searchProducts(params) {
  return request({
    url: '/products/search',
    method: 'GET',
    data: {
      keyword: params.keyword,
      page: params.page || 1,
      page_size: params.pageSize || 20,
      category_id: params.categoryId || null,
      min_price: params.minPrice || null,
      max_price: params.maxPrice || null,
      platform: params.platform || null,
      sort: params.sort || 'price_asc'
    }
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
    data: { limit }
  });
}

// 获取商品分类
export function getCategories(parentId = 0) {
  return request({
    url: '/products/categories',
    method: 'GET',
    data: { parent_id: parentId }
  });
}
```

---

## 🎬 7. 动画实现

### Transition 动画

```vue
<template>
  <transition name="slide-up" @enter="onEnter">
    <view v-if="show" class="modal-content">
      <!-- 内容 -->
    </view>
  </transition>
</template>

<script>
export default {
  methods: {
    onEnter(el) {
      // GSAP 或自定义动画
      if (process.client) {
        gsap.from(el, {
          y: 100,
          opacity: 0,
          duration: 0.3,
          ease: 'power2.out'
        });
      }
    }
  }
};
</script>

<style scoped lang="scss">
.slide-up-enter-active {
  animation: slideUp 0.3s ease-out;
}

.slide-up-leave-active {
  animation: slideUp 0.3s ease-in reverse;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
```

---

## 📦 8. 组件库文件结构建议

```
src/
├── components/
│   ├── base/
│   │   ├── Button.vue            # 按钮
│   │   ├── Input.vue             # 输入框
│   │   ├── Modal.vue             # 弹窗
│   │   ├── TabBar.vue            # 标签栏
│   │   └── Loading.vue           # 加载动画
│   │
│   ├── business/
│   │   ├── ProductCard.vue       # 商品卡片
│   │   ├── PriceLabel.vue        # 价格标签
│   │   ├── PlatformBadge.vue     # 平台徽章
│   │   ├── SearchBar.vue         # 搜索栏
│   │   ├── FilterPanel.vue       # 筛选面板
│   │   ├── PriceChart.vue        # 价格走势
│   │   └── ImageSwiper.vue       # 图片轮播
│   │
│   └── shared/
│       ├── NoData.vue            # 空状态
│       ├── ErrorState.vue        # 错误状态
│       └── MoreHeader.vue        # 更多标题
│
├── pages/
│   ├── index/
│   │   └── index.vue
│   ├── searchResults/
│   │   └── searchResults.vue
│   ├── productDetail/
│   │   └── productDetail.vue
│   ├── userCenter/
│   │   └── userCenter.vue
│   ├── favorites/
│   │   └── favorites.vue
│   ├── history/
│   │   └── history.vue
│   ├── priceAlerts/
│   │   └── priceAlerts.vue
│   ├── category/
│   │   └── category.vue
│   ├── search/
│   │   └── search.vue
│   ├── comparison/
│   │   └── comparison.vue
│   └── login/
│       └── login.vue
│
├── store/                         # Pinia 状态管理
│   ├── modules/
│   │   ├── user.js
│   │   ├── product.js
│   │   ├── favorite.js
│   │   └── search.js
│   └── index.js
│
├── api/                          # API 模块
│   ├── user.js
│   ├── product.js
│   ├── favorite.js
│   ├── alert.js
│   └── analytics.js
│
├── utils/                        # 工具函数
│   ├── request.js               # HTTP 请求封装
│   ├── storage.js               # 本地存储
│   ├── auth.js                  # 认证工具
│   ├── format.js                # 格式化工具
│   └── validate.js              # 数据验证
│
└── styles/                       # 样式
    ├── variables.scss            # 颜色、间距变量
    ├── typography.scss           # 字体规范
    ├── mixins.scss               # SCSS 混入
    └── common.scss               # 全局样式
```

---

## ✅ 实现检查清单

### 设计实现步骤

- [ ] **第1周** - 搭建项目框架和组件库基础
  - [ ] 创建 uni-app 项目
  - [ ] 配置 SCSS 变量和全局样式
  - [ ] 实现基础组件 (Button、Input、Modal 等)
  
- [ ] **第2周** - 实现业务组件
  - [ ] ProductCard、PriceLabel、PlatformBadge...
  - [ ] SearchBar、FilterPanel
  - [ ] ImageSwiper、PriceChart
  
- [ ] **第3周** - 首页开发
  - [ ] 搜索栏、分类导航
  - [ ] Banner 轮播、热搜榜
  - [ ] 推荐商品列表
  
- [ ] **第4周** - 搜索和结果页
  - [ ] 搜索页面和搜索历史
  - [ ] 搜索结果页布局
  - [ ] 筛选和排序功能
  
- [ ] **第5周** - 商品详情页
  - [ ] 图片轮播和基本信息
  - [ ] 价格对比表和走势图
  - [ ] 评价和供货商信息
  
- [ ] **第6周** - 用户功能页
  - [ ] 我的收藏、浏览历史
  - [ ] 降价提醒、商品对比
  - [ ] 用户中心和登录
  
- [ ] **第7周** - 调试和优化
  - [ ] 页面间导航测试
  - [ ] API 集成测试
  - [ ] 性能优化和加载速度
  
- [ ] **第8周** - 上线前冲刺
  - [ ] 完整功能测试
  - [ ] 真机测试 (多机型)
  - [ ] 修复 Bug，发布版本

### 质量检查

- [ ] 所有文本都是中文，且符合产品风格
- [ ] 所有图片都已优化，大小 < 100KB
- [ ] 所有转跳都正确，无死链接
- [ ] 响应式布局适配各种屏幕尺寸
- [ ] 深色模式支持 (可选)
- [ ] 无障碍性满足标准 (WCAG 2.1)
- [ ] 加载性能达到目标 (首屏 < 2s)

---

## 🚀 上线建议

1. **灰度发布** - 先发布 10% 用户，收集反馈
2. **监控告警** - 部署性能监控和错误追踪
3. **引导用户** - 发版说明和功能指引
4. **持续迭代** - 根据用户反馈快速迭代优化

---

**最后更新**：2024年3月24日  
**版本**：1.0  
**适用于**："一次买够"微信小程序前端  
