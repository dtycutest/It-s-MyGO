<script setup lang="ts">
import { ref, computed } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { useProductStore } from '../../stores/product';
import ProductCard from '../../components/ProductCard.vue';
import NoData from '../../components/NoData.vue';

const productStore = useProductStore();

const keyword = ref('');
const sortBy = ref<'default' | 'price_asc' | 'price_desc'>('default');
const priceRange = ref<'all' | '0-100' | '100-300' | '300+'>('all');
const loading = ref(true);

const searchResults = computed(() => {
  let results = productStore.searchResults;

  if (priceRange.value === '0-100') {
    results = results.filter(p => p.min_price <= 100);
  } else if (priceRange.value === '100-300') {
    results = results.filter(p => p.min_price > 100 && p.min_price <= 300);
  } else if (priceRange.value === '300+') {
    results = results.filter(p => p.min_price > 300);
  }

  if (sortBy.value === 'price_asc') {
    results = [...results].sort((a, b) => a.min_price - b.min_price);
  } else if (sortBy.value === 'price_desc') {
    results = [...results].sort((a, b) => b.min_price - a.min_price);
  }

  return results;
});

const handleProductClick = (productId: string) => {
  uni.navigateTo({
    url: `/pages/productDetail/productDetail?product_id=${productId}`
  });
};

const handleSortChange = (type: string) => {
  sortBy.value = type as any;
};

onLoad(async (options: any) => {
  if (options.keyword) {
    keyword.value = decodeURIComponent(options.keyword);
  }
  loading.value = true;
  try {
    await productStore.searchProducts({ keyword: keyword.value, page: 1, page_size: 50 });
  } catch {
    console.error('搜索失败');
    uni.showToast({ title: '搜索失败，请重试', icon: 'none' });
  }
  loading.value = false;
});
</script>

<template>
  <view class="page">
    <view class="search-bar">
      <text class="search-icon">🔍</text>
      <text class="search-text">{{ keyword || '搜索结果' }}</text>
    </view>

    <!-- 筛选栏 -->
    <view class="filter-bar">
      <view class="sort-tabs">
        <view
          :class="['sort-tab', { active: sortBy === 'default' }]"
          @click="handleSortChange('default')"
        >
          <text>综合</text>
        </view>
        <view
          :class="['sort-tab', { active: sortBy === 'price_asc' }]"
          @click="handleSortChange('price_asc')"
        >
          <text>价格↑</text>
        </view>
        <view
          :class="['sort-tab', { active: sortBy === 'price_desc' }]"
          @click="handleSortChange('price_desc')"
        >
          <text>价格↓</text>
        </view>
      </view>
      <view class="price-filters">
        <view
          :class="['filter-tag', { active: priceRange === 'all' }]"
          @click="priceRange = 'all'"
        >
          <text>全部</text>
        </view>
        <view
          :class="['filter-tag', { active: priceRange === '0-100' }]"
          @click="priceRange = '0-100'"
        >
          <text>0-100</text>
        </view>
        <view
          :class="['filter-tag', { active: priceRange === '100-300' }]"
          @click="priceRange = '100-300'"
        >
          <text>100-300</text>
        </view>
        <view
          :class="['filter-tag', { active: priceRange === '300+' }]"
          @click="priceRange = '300+'"
        >
          <text>300+</text>
        </view>
      </view>
    </view>

    <!-- 结果统计 -->
    <view class="result-info">
      <text v-if="searchResults.length > 0">
        找到 {{ searchResults.length }} 个关于「{{ keyword }}」的商品
      </text>
    </view>

    <!-- 商品列表 -->
    <view class="product-list">
      <NoData v-if="searchResults.length === 0" text="没有找到相关商品" icon="🔍" />
      <ProductCard
        v-for="product in searchResults"
        :key="product.product_id"
        :product="product"
        @click="handleProductClick"
      />
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.search-bar {
  background: linear-gradient(180deg, #FF6B35 0%, #E55A26 100%);
  padding: 20rpx 30rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.search-icon {
  font-size: 32rpx;
}

.search-text {
  flex: 1;
  font-size: 28rpx;
  color: white;
}

.filter-bar {
  background: white;
  padding: 0 30rpx;
}

.sort-tabs {
  display: flex;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.sort-tab {
  flex: 1;
  text-align: center;
  font-size: 26rpx;
  color: #666;
  position: relative;

  &.active {
    color: #FF6B35;
    font-weight: 600;

    &::after {
      content: '';
      position: absolute;
      bottom: -16rpx;
      left: 50%;
      transform: translateX(-50%);
      width: 40rpx;
      height: 4rpx;
      background: #FF6B35;
      border-radius: 2rpx;
    }
  }
}

.price-filters {
  display: flex;
  gap: 16rpx;
  padding: 16rpx 0;
}

.filter-tag {
  padding: 8rpx 24rpx;
  border-radius: 30rpx;
  background: #f5f5f5;
  font-size: 24rpx;
  color: #666;

  &.active {
    background: #FFF3E0;
    color: #FF6B35;
  }
}

.result-info {
  padding: 20rpx 30rpx;
  font-size: 24rpx;
  color: #999;
}

.product-list {
  padding: 0 24rpx 24rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
</style>