<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useProductStore } from '../../stores/product';
import type { OnLoadOptions } from '@dcloudio/types';
import { mockProducts } from '../../mock/data';

console.log('搜索结果页面 script setup 开始');

const productStore = useProductStore();
const keyword = ref('');
const localProducts = ref<any[]>([]);

const loadMore = () => {
  console.log('loadMore 被调用');
  if (productStore.pagination.has_next && !productStore.loading) {
    productStore.searchProducts({
      keyword: keyword.value,
      page: productStore.pagination.page + 1
    });
  }
};

const goToDetail = (product_id: string) => {
  console.log('goToDetail 被调用, product_id:', product_id);
  uni.navigateTo({
    url: `/pages/productDetail/productDetail?product_id=${product_id}`
  });
};

const loadResults = async (kw: string) => {
  console.log('loadResults 被调用, kw:', kw);
  if (kw) {
    // 先设置本地 mock 数据
    localProducts.value = mockProducts.filter(p => 
      p.title.includes(kw) || p.category_name.includes(kw)
    );
    console.log('本地搜索结果:', localProducts.value);
    
    // 再尝试调用 store
    try {
      await productStore.searchProducts({
        keyword: kw,
        page: 1
      });
      console.log('store 搜索结果:', productStore.searchResults);
    } catch (error) {
      console.error('store 搜索失败:', error);
    }
  }
};

onLoad((options: OnLoadOptions) => {
  console.log('搜索结果页面 onLoad, options:', options);
  if (options.keyword) {
    keyword.value = decodeURIComponent(options.keyword);
    loadResults(keyword.value);
  }
});
</script>

<template>
  <view class="page">
    <!-- 调试信息 -->
    <view class="debug-section">
      <text class="debug-title">🔍 搜索结果调试</text>
      <text class="debug-text">关键词: {{ keyword }}</text>
      <text class="debug-text">store 结果数: {{ productStore.searchResults.length }}</text>
      <text class="debug-text">本地结果数: {{ localProducts.length }}</text>
    </view>

    <view v-if="keyword" class="keyword-bar">
      <text>关键词：</text>
      <text class="keyword">{{ keyword }}</text>
    </view>

    <view v-if="(productStore.loading || localProducts.length === 0) && productStore.searchResults.length === 0 && localProducts.length === 0" class="loading-container">
      <text class="loading-text">搜索中...</text>
    </view>

    <view v-else-if="productStore.searchResults.length === 0 && localProducts.length === 0" class="empty-container">
      <view class="empty-icon">🔍</view>
      <text class="empty-text">没有找到相关商品</text>
    </view>

    <scroll-view 
      v-else 
      class="product-list-scroll" 
      scroll-y 
      @scrolltolower="loadMore"
    >
      <view class="product-list">
        <!-- 优先用 store 的数据，没有的话用本地的 -->
        <view 
          v-for="item in (productStore.searchResults.length > 0 ? productStore.searchResults : localProducts)" 
          :key="item.product_id"
          class="product-card"
          @click="goToDetail(item.product_id)"
        >
          <image :src="item.image_url" class="product-image" mode="aspectFill" />
          <view class="product-info">
            <text class="product-title">{{ item.title }}</text>
            <view class="product-price-row">
              <text class="product-price">¥{{ item.min_price }}</text>
              <text class="price-tag">起</text>
            </view>
            <view class="platforms">
              <view 
                v-for="plat in item.platforms.slice(0, 3)" 
                :key="plat.platform_id"
                class="platform-tag"
              >
                <text>{{ plat.platform_name }}</text>
              </view>
            </view>
          </view>
        </view>

        <view v-if="productStore.pagination.has_next" class="load-more">
          <text>{{ productStore.loading ? '加载中...' : '加载更多' }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 32rpx;
}

.debug-section {
  background-color: #e8f4fd;
  border: 2rpx solid #3498db;
  padding: 30rpx;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
}

.debug-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #2c3e50;
  display: block;
  margin-bottom: 15rpx;
}

.debug-text {
  font-size: 26rpx;
  color: #34495e;
  display: block;
  margin-bottom: 8rpx;
}

.keyword-bar {
  background-color: white;
  padding: 24rpx 32rpx;
  border-radius: 16rpx;
  margin-bottom: 32rpx;
  font-size: 28rpx;
  color: #666;
}

.keyword {
  color: #FF6B35;
  font-weight: 600;
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 160rpx;
}

.loading-text {
  color: #999;
  font-size: 28rpx;
}

.empty-icon {
  font-size: 96rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  color: #999;
  font-size: 28rpx;
}

.product-list-scroll {
  height: calc(100vh - 200rpx);
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.product-card {
  display: flex;
  background-color: white;
  border-radius: 24rpx;
  padding: 32rpx;
}

.product-image {
  width: 200rpx;
  height: 200rpx;
  border-radius: 16rpx;
  background-color: #f8f8f8;
  flex-shrink: 0;
}

.product-info {
  flex: 1;
  margin-left: 32rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.product-title {
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
  margin-bottom: 16rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-price-row {
  display: flex;
  align-items: baseline;
  margin-bottom: 16rpx;
}

.product-price {
  font-size: 40rpx;
  font-weight: 700;
  color: #FF6B35;
}

.price-tag {
  font-size: 24rpx;
  color: #999;
  margin-left: 8rpx;
}

.platforms {
  display: flex;
  gap: 12rpx;
  flex-wrap: wrap;
}

.platform-tag {
  background-color: #f8f8f8;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
}

.platform-tag text {
  font-size: 22rpx;
  color: #999;
}

.load-more {
  text-align: center;
  padding: 32rpx;
}

.load-more text {
  color: #999;
  font-size: 28rpx;
}
</style>
