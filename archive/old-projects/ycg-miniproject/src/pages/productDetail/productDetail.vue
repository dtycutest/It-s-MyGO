<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useProductStore } from '../../stores/product';
import { useUserStore } from '../../stores/user';
import { favoriteApi, analyticsApi } from '../../api';
import type { OnLoadOptions } from '@dcloudio/types';
import { mockProducts } from '../../mock/data';

console.log('商品详情页面 script setup 开始');

const productStore = useProductStore();
const userStore = useUserStore();
const localProduct = ref<any>(null);

const addToFavorite = async () => {
  console.log('addToFavorite 被调用');
  if (!userStore.isLoggedIn) {
    uni.navigateTo({
      url: '/pages/login/login'
    });
    return;
  }

  const product = productStore.currentProduct || localProduct.value;
  if (!product) return;

  try {
    await favoriteApi.add({
      product_id: product.product_id
    });
    
    uni.showToast({ title: '已添加收藏', icon: 'success' });
    
    analyticsApi.track({
      event_type: 'add_favorite',
      product_id: product.product_id,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('添加收藏失败:', error);
    uni.showToast({ title: '添加收藏失败', icon: 'none' });
  }
};

const loadDetail = async (product_id: string) => {
  console.log('loadDetail 被调用, product_id:', product_id);
  if (product_id) {
    // 先设置本地 mock 数据
    localProduct.value = mockProducts.find(p => p.product_id === product_id) || mockProducts[0];
    console.log('本地商品数据:', localProduct.value);
    
    // 再尝试调用 store
    try {
      await productStore.getProductDetail(product_id);
      console.log('store 商品数据:', productStore.currentProduct);
    } catch (error) {
      console.error('store 加载失败:', error);
    }
  }
};

onLoad((options: OnLoadOptions) => {
  console.log('商品详情页面 onLoad, options:', options);
  if (options.product_id) {
    loadDetail(options.product_id);
  }
});
</script>

<template>
  <view class="page">
    <!-- 调试信息 -->
    <view class="debug-section">
      <text class="debug-title">🔍 商品详情调试</text>
      <text class="debug-text">store 有数据: {{ !!productStore.currentProduct }}</text>
      <text class="debug-text">本地有数据: {{ !!localProduct }}</text>
    </view>

    <view v-if="productStore.loading && !localProduct" class="loading-container">
      <text class="loading-text">加载中...</text>
    </view>

    <template v-else-if="productStore.currentProduct || localProduct">
      <view v-if="productStore.currentProduct || localProduct">
        <image 
          :src="(productStore.currentProduct || localProduct).image_url" 
          class="product-image" 
          mode="aspectFill" 
        />
        
        <view class="product-info">
          <text class="product-title">{{ (productStore.currentProduct || localProduct).title }}</text>
          
          <view class="price-section">
            <view class="price-row">
              <text class="price-label">全网最低价</text>
              <text class="min-price">¥{{ (productStore.currentProduct || localProduct).min_price }}</text>
            </view>
            <text class="price-range">
              价格区间: ¥{{ (productStore.currentProduct || localProduct).min_price }} - ¥{{ (productStore.currentProduct || localProduct).max_price }}
            </text>
            <text class="best-platform">
              最佳平台: {{ (productStore.currentProduct || localProduct).best_platform }}
            </text>
          </view>
          
          <view class="platforms-section">
            <text class="section-title">各平台比价</text>
            <view class="platform-list">
              <view 
                v-for="plat in (productStore.currentProduct || localProduct).platforms" 
                :key="plat.platform_id"
                class="platform-item"
              >
                <text class="platform-name">{{ plat.platform_name }}</text>
                <text class="platform-price">¥{{ plat.price }}</text>
                <button class="platform-action">去购买</button>
              </view>
            </view>
          </view>
        </view>
        
        <view class="bottom-actions">
          <button class="action-btn collect" @click="addToFavorite">
            ⭐ 收藏
          </button>
          <button class="action-btn buy">
            立即购买
          </button>
        </view>
      </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 160rpx;
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

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 200rpx;
}

.product-image {
  width: 100%;
  height: 600rpx;
  background-color: #f8f8f8;
}

.product-info {
  background-color: white;
  padding: 40rpx;
}

.product-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #333;
  line-height: 1.5;
  display: block;
  margin-bottom: 40rpx;
}

.price-section {
  padding: 40rpx;
  background-color: #f8f8f8;
  border-radius: 24rpx;
  margin-bottom: 40rpx;
}

.price-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.price-label {
  font-size: 28rpx;
  color: #666;
}

.min-price {
  font-size: 56rpx;
  font-weight: 700;
  color: #FF6B35;
}

.price-range,
.best-platform {
  font-size: 26rpx;
  color: #999;
  display: block;
  margin-top: 12rpx;
}

.platforms-section {
  margin-top: 40rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 32rpx;
}

.platform-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.platform-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx;
  background-color: #f8f8f8;
  border-radius: 16rpx;
}

.platform-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.platform-price {
  font-size: 36rpx;
  font-weight: 600;
  color: #FF6B35;
}

.platform-action {
  font-size: 26rpx;
  padding: 12rpx 32rpx;
  background-color: #FF6B35;
  color: white;
  border: none;
  border-radius: 32rpx;
  line-height: 1;
  height: auto;
}

.platform-action::after {
  border: none;
}

.bottom-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  padding: 24rpx 40rpx;
  background-color: white;
  border-top: 1px solid #eee;
  gap: 32rpx;
}

.action-btn {
  flex: 1;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 44rpx;
  font-size: 30rpx;
  font-weight: 600;
  border: none;
  line-height: 1;
}

.action-btn::after {
  border: none;
}

.collect {
  background-color: #f8f8f8;
  color: #333;
}

.buy {
  background-color: #FF6B35;
  color: white;
}
</style>
