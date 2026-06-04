<script setup lang="ts">
import { ref, computed } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { useProductStore } from '../../stores/product';
import { useUserStore } from '../../stores/user';
import { favoriteApi, priceAlertApi } from '../../api';
import { mockPriceTrend, mockProductReviews } from '../../mock/data';
import PlatformBadge from '../../components/PlatformBadge.vue';
import PriceLabel from '../../components/PriceLabel.vue';

const productStore = useProductStore();
const userStore = useUserStore();

const productId = ref('');
const loading = ref(true);
const loadError = ref(false);

const currentProduct = computed(() => {
  return productStore.currentProduct || ({} as any);
});

const images = computed(() => {
  const p = currentProduct.value;
  return p.images && p.images.length > 0 ? p.images : [p.image_url || '/static/logo.png'];
});

const safeDiscount = computed(() => {
  const p = currentProduct.value;
  if (!p.max_price || !p.min_price || p.max_price <= 0) return '--';
  return Math.round(p.min_price / p.max_price * 100);
});

const priceTrend = computed(() => mockPriceTrend);
const reviews = computed(() => mockProductReviews);

const handleFavorite = async () => {
  if (!userStore.isLoggedIn) {
    uni.showModal({
      title: '提示',
      content: '收藏功能需要登录，是否前往登录？',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({ url: '/pages/login/login' });
        }
      }
    });
    return;
  }
  try {
    await favoriteApi.add({ product_id: productId.value });
    uni.showToast({ title: '收藏成功！', icon: 'success' });
  } catch {
    uni.showToast({ title: '收藏失败，请重试', icon: 'none' });
  }
};

const handleBuy = (platform: any) => {
  uni.showToast({ title: `即将前往 ${platform.platform_name}`, icon: 'none' });
};

const handleSetAlert = async () => {
  if (!userStore.isLoggedIn) {
    uni.showModal({
      title: '提示',
      content: '降价提醒功能需要登录，是否前往登录？',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({ url: '/pages/login/login' });
        }
      }
    });
    return;
  }
  try {
    const targetPrice = currentProduct.value.min_price ? currentProduct.value.min_price * 0.9 : 0;
    await priceAlertApi.create({
      product_id: productId.value,
      target_price: Math.round(targetPrice * 100) / 100
    });
    uni.showToast({ title: '降价提醒已设置！', icon: 'success' });
  } catch {
    uni.showToast({ title: '设置失败，请重试', icon: 'none' });
  }
};

onLoad(async (options: any) => {
  if (options.product_id) {
    productId.value = options.product_id;
    loading.value = true;
    loadError.value = false;
    try {
      await productStore.getProductDetail(options.product_id);
    } catch {
      loadError.value = true;
      console.error('获取商品详情失败');
      uni.showToast({ title: '加载失败，请重试', icon: 'none' });
    }
    loading.value = false;
  }
});
</script>

<template>
  <view class="page">
    <!-- 加载中 -->
    <view v-if="loading" class="loading-container">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 加载失败 -->
    <view v-else-if="loadError" class="error-container">
      <text>加载失败</text>
      <text class="retry-text" @click="onLoad({ product_id: productId } as any)">点击重试</text>
    </view>

    <template v-else>
    <!-- 图片轮播 -->
    <swiper v-if="images.length > 0" class="image-swiper" autoplay interval="4000" indicator-dots indicator-active-color="#FF6B35" circular>
      <swiper-item v-for="(img, idx) in images" :key="idx">
        <image class="product-image" :src="img" mode="aspectFill" />
      </swiper-item>
    </swiper>

    <!-- 商品信息 -->
    <view class="info-section">
      <view class="price-header">
        <PriceLabel :price="currentProduct.min_price || 0" size="large" />
        <text v-if="currentProduct.max_price" class="original-price">¥{{ currentProduct.max_price }}</text>
        <text class="discount-badge">{{ safeDiscount }}{{ safeDiscount !== '--' ? '折' : '' }}</text>
      </view>
      <text class="product-title">{{ currentProduct.title || '商品信息加载中' }}</text>
      <view v-if="currentProduct.price_diff" class="diff-tip">
        <text>💡 最大差价 ¥{{ currentProduct.price_diff }}！去低价平台购买吧！</text>
      </view>
      <view v-if="currentProduct.description" class="desc-section">
        <text class="desc-label">商品描述</text>
        <text class="desc-text">{{ currentProduct.description }}</text>
      </view>
    </view>

    <!-- 价格走势 -->
    <view class="trend-section">
      <view class="section-header">
        <text class="section-title">📈 近7天价格走势</text>
      </view>
      <view class="trend-chart">
        <view v-for="point in priceTrend" :key="point.date" class="trend-bar-wrapper">
          <view
            class="trend-bar"
            :style="{ height: (point.price / 350 * 100) + '%' }"
          />
          <text class="trend-price">¥{{ point.price }}</text>
          <text class="trend-date">{{ point.date.slice(5) }}</text>
        </view>
      </view>
    </view>

    <!-- 平台比价 -->
    <view v-if="currentProduct.platforms && currentProduct.platforms.length > 0" class="platform-section">
      <view class="section-header">
        <text class="section-title">📊 各平台比价</text>
        <text class="section-count">共{{ currentProduct.platforms.length }}个平台</text>
      </view>
      <view class="platform-list">
        <view
          v-for="platform in currentProduct.platforms"
          :key="platform.platform_id"
          class="platform-item"
          :class="{ best: platform.platform_name === currentProduct.best_platform }"
          @click="handleBuy(platform)"
        >
          <view class="platform-left">
            <view class="platform-name-row">
              <PlatformBadge :platform="platform.platform_name" />
              <text v-if="platform.platform_name === currentProduct.best_platform" class="best-tag">最优价</text>
            </view>
            <view v-if="platform.seller_name" class="seller-info">
              <text>{{ platform.seller_name }}</text>
              <text v-if="platform.seller_rating" class="rating">⭐ {{ platform.seller_rating }}</text>
            </view>
          </view>
          <view class="platform-right">
            <view class="prices">
              <text class="cur-price">¥{{ platform.price }}</text>
              <text v-if="platform.original_price" class="orig-price">¥{{ platform.original_price }}</text>
            </view>
            <view class="meta">
              <text v-if="platform.discount_rate != null">{{ platform.discount_rate }}折</text>
              <text v-if="platform.sales_volume">已售 {{ platform.sales_volume }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 无平台数据 -->
    <view v-else class="platform-section">
      <view class="section-header">
        <text class="section-title">📊 各平台比价</text>
      </view>
      <text class="no-data-hint">暂无平台报价数据</text>
    </view>

    <!-- 商品评价 -->
    <view class="review-section">
      <view class="section-header">
        <text class="section-title">💬 用户评价</text>
      </view>
      <view v-for="review in reviews" :key="review.review_id" class="review-item">
        <view class="review-header">
          <text class="review-user">{{ review.user_name }}</text>
          <view class="review-stars">
            <text v-for="n in review.rating" :key="n">⭐</text>
          </view>
        </view>
        <text class="review-content">{{ review.content }}</text>
        <text class="review-time">{{ review.created_at }}</text>
      </view>
    </view>

    <!-- 底部操作栏 -->
    <view class="bottom-bar">
      <view class="action-btn alert" @click="handleSetAlert">
        <text>🔔 降价提醒</text>
      </view>
      <view class="action-btn favorite" @click="handleFavorite">
        <text>⭐ 收藏</text>
      </view>
      <view class="action-btn buy" @click="currentProduct.platforms && currentProduct.platforms.length > 0 && handleBuy(currentProduct.platforms[0])">
        <text>🛒 立即购买</text>
      </view>
    </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 120rpx;
}

.loading-container,
.error-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 28rpx;
}

.retry-text {
  margin-top: 20rpx;
  color: #FF6B35;
  text-decoration: underline;
}

.no-data-hint {
  display: block;
  text-align: center;
  color: #999;
  font-size: 26rpx;
  padding: 40rpx 0;
}

.image-swiper {
  width: 100%;
  height: 750rpx;
  background: white;
}

.product-image {
  width: 100%;
  height: 100%;
}

.info-section {
  background: white;
  padding: 30rpx;
}

.price-header {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.original-price {
  font-size: 26rpx;
  color: #999;
  text-decoration: line-through;
}

.discount-badge {
  background: #E4405F;
  color: white;
  font-size: 20rpx;
  padding: 4rpx 10rpx;
  border-radius: 4rpx;
}

.product-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  line-height: 1.5;
  display: block;
  margin-bottom: 20rpx;
}

.diff-tip {
  background: #FFF3E0;
  padding: 16rpx 20rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}

.diff-tip text {
  font-size: 24rpx;
  color: #FF6B35;
}

.desc-section {
  padding-top: 20rpx;
  border-top: 1rpx solid #eee;
}

.desc-label {
  font-size: 26rpx;
  color: #666;
  font-weight: 600;
  display: block;
  margin-bottom: 10rpx;
}

.desc-text {
  font-size: 26rpx;
  color: #999;
  line-height: 1.6;
}

.trend-section {
  background: white;
  margin-top: 20rpx;
  padding: 30rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.section-count {
  font-size: 24rpx;
  color: #999;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 240rpx;
  padding-top: 40rpx;
}

.trend-bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
  justify-content: flex-end;
}

.trend-bar {
  width: 32rpx;
  background: linear-gradient(to top, #FF6B35, #FFD4B9);
  border-radius: 6rpx 6rpx 0 0;
  min-height: 20rpx;
}

.trend-price {
  font-size: 18rpx;
  color: #FF6B35;
  font-weight: 600;
  margin-top: 4rpx;
}

.trend-date {
  font-size: 18rpx;
  color: #ccc;
  margin-top: 4rpx;
}

.platform-section {
  background: white;
  margin-top: 20rpx;
  padding: 30rpx;
}

.platform-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.platform-item {
  background: #f8f8f8;
  padding: 24rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;

  &.best {
    background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%);
    border: 2rpx solid #FF6B35;
  }
}

.platform-left {
  flex: 1;
}

.platform-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 8rpx;
}

.best-tag {
  background: #FF6B35;
  color: white;
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
}

.seller-info {
  font-size: 22rpx;
  color: #999;
}

.rating {
  margin-left: 12rpx;
}

.platform-right {
  text-align: right;
}

.prices {
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 8rpx;
  margin-bottom: 6rpx;
}

.cur-price {
  font-size: 34rpx;
  font-weight: 700;
  color: #FF6B35;
}

.orig-price {
  font-size: 22rpx;
  color: #999;
  text-decoration: line-through;
}

.meta {
  display: flex;
  gap: 16rpx;
  justify-content: flex-end;
  font-size: 20rpx;
  color: #bbb;
}

.review-section {
  background: white;
  margin-top: 20rpx;
  padding: 30rpx;
}

.review-item {
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }
}

.review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.review-user {
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
}

.review-stars {
  font-size: 24rpx;
}

.review-content {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
  display: block;
  margin-bottom: 8rpx;
}

.review-time {
  font-size: 22rpx;
  color: #ccc;
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 20rpx 30rpx;
  display: flex;
  gap: 16rpx;
  border-top: 1rpx solid #eee;
  box-shadow: 0 -4rpx 12rpx rgba(0, 0, 0, 0.06);
}

.action-btn {
  padding: 20rpx 0;
  text-align: center;
  border-radius: 50rpx;
  font-size: 26rpx;
  font-weight: 600;

  &.alert {
    background: #f5f5f5;
    color: #666;
    flex: 1;
  }

  &.favorite {
    background: #FFF3E0;
    color: #FF6B35;
    flex: 1;
  }

  &.buy {
    background: linear-gradient(135deg, #FF6B35 0%, #E55A26 100%);
    color: white;
    flex: 1.5;
  }
}
</style>