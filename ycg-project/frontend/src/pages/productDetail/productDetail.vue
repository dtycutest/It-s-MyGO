<script setup lang="ts">
import { ref, computed } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { useProductStore } from '../../stores/product';
import { useUserStore } from '../../stores/user';
import { favoriteApi, priceAlertApi, browseHistoryApi } from '../../api';
import PlatformBadge from '../../components/PlatformBadge.vue';
import PriceLabel from '../../components/PriceLabel.vue';

const productStore = useProductStore();
const userStore = useUserStore();

const productId = ref('')
const loading = ref(true)
const loadError = ref(false)
const imgErrors = ref<Record<number, boolean>>({});

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

const sortedPlatforms = computed(() => {
  const all = currentProduct.value.platforms || []
  // 按价格排序，展示所有平台报价（不合并，保留不同店铺的比价信息）
  return [...all].sort((a: any, b: any) => a.price - b.price)
});

const formatSalesVolume = (volume: number): string => {
  if (volume >= 100000000) return `${(volume / 100000000).toFixed(1)}亿+`;
  if (volume >= 10000) return `${(volume / 10000).toFixed(1)}万+`;
  if (volume >= 1000) return `${(volume / 1000).toFixed(1)}千+`;
  return `${volume}件`;
};

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
  if (platform.product_url) {
    uni.setClipboardData({
      data: platform.product_url,
      success: () => {
        uni.showToast({ title: '链接已复制，请在浏览器中打开', icon: 'none' });
      }
    });
  } else {
    uni.showToast({ title: '暂无购买链接', icon: 'none' });
  }
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
  const pid = options?.productId || options?.product_id
  if (pid) {
    productId.value = pid
    loading.value = true
    loadError.value = false
    try {
      await productStore.getProductDetail(pid)
      // 记录浏览历史（静默调用，未登录时忽略错误）
      browseHistoryApi.add({ product_id: pid }).catch(() => {})
    } catch {
      loadError.value = true
      console.error('获取商品详情失败')
    }
    loading.value = false
  } else {
    loading.value = false
    loadError.value = true
  }
})

const retryLoad = async () => {
  if (!productId.value) return
  loading.value = true
  loadError.value = false
  try {
    await productStore.getProductDetail(productId.value)
    // 记录浏览历史（静默调用，未登录时忽略错误）
    browseHistoryApi.add({ product_id: productId.value }).catch(() => {})
  } catch {
    loadError.value = true
    console.error('获取商品详情失败')
  }
  loading.value = false
}
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
      <text class="retry-text" @click="retryLoad">点击重试</text>
    </view>

    <template v-else>
    <!-- 图片轮播 -->
    <swiper v-if="images.length > 0" class="image-swiper" autoplay interval="4000" indicator-dots indicator-active-color="#FF6B35" circular>
      <swiper-item v-for="(img, idx) in images" :key="idx">
        <view v-if="imgErrors[idx]" class="image-error-placeholder">
          <text class="img-error-text">图片失效</text>
        </view>
        <image
          v-else
          class="product-image"
          :src="img"
          mode="aspectFit"
          @error="imgErrors[idx] = true"
        />
      </swiper-item>
    </swiper>

    <!-- 商品信息 -->
    <view class="info-section">
      <view class="price-header">
        <PriceLabel :price="currentProduct.min_price || 0" size="large" />
        <text v-if="currentProduct.max_price && currentProduct.max_price !== currentProduct.min_price" class="original-price">¥{{ currentProduct.max_price }}</text>
        <text v-if="safeDiscount !== '--' && safeDiscount < 100" class="discount-badge">{{ safeDiscount }}折</text>
      </view>
      <text class="product-title">{{ currentProduct.title || '商品信息加载中' }}</text>
      <view class="diff-tip">
        <text class="diff-tip-text">💡 最大差价 ¥{{ (currentProduct.price_diff || 0).toFixed(2) }}！去低价平台购买吧！</text>
      </view>
      <view v-if="currentProduct.description" class="desc-section">
        <text class="desc-label">商品描述</text>
        <text class="desc-text">{{ currentProduct.description }}</text>
      </view>
    </view>

    <!-- 平台比价 -->
    <view v-if="sortedPlatforms.length > 0" class="platform-section">
      <view class="section-header">
        <text class="section-title">📊 各平台比价</text>
        <text class="section-count">共{{ sortedPlatforms.length }}个平台</text>
      </view>
      <view class="platform-list">
        <view
          v-for="platform in sortedPlatforms"
          :key="platform.platform_id"
          class="platform-item"
          :class="{ best: platform.price === currentProduct.min_price }"
          @click="handleBuy(platform)"
        >
          <view class="platform-left">
            <view class="platform-name-row">
              <PlatformBadge :platform="platform.platform_name" />
              <text v-if="platform.price === currentProduct.min_price" class="best-tag">最优价</text>
              <text class="stock-tag" :class="platform.in_stock ? 'in-stock' : 'out-stock'">
                {{ platform.in_stock ? '有货' : '缺货' }}
              </text>
            </view>
            <view v-if="platform.seller_name" class="seller-info">
              <text class="seller-label">店铺</text>
              <text class="seller-name">{{ platform.seller_name }}</text>
              <text v-if="platform.seller_rating" class="rating">⭐ {{ platform.seller_rating }}</text>
            </view>
            <view class="sales-info">
              <text v-if="platform.sales_volume" class="sales-vol">已售 {{ formatSalesVolume(platform.sales_volume) }}</text>
              <text v-else-if="platform.stock_quantity" class="stock-qty">库存 {{ platform.stock_quantity }}件</text>
            </view>
          </view>
          <view class="platform-right">
            <view class="prices">
              <text class="cur-price">¥{{ platform.price }}</text>
              <text v-if="platform.original_price && platform.original_price !== platform.price" class="orig-price">¥{{ platform.original_price }}</text>
            </view>
            <view v-if="platform.original_price && platform.original_price !== platform.price" class="save-info">
              <text class="save-text">省 ¥{{ (platform.original_price - platform.price).toFixed(2) }}</text>
            </view>
            <view class="meta">
              <text v-if="platform.discount_rate != null" class="discount-tag">{{ platform.discount_rate }}折</text>
            </view>
            <view class="go-btn">去购买 →</view>
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

    <!-- 底部操作栏 -->
    <view class="bottom-bar">
      <view class="action-btn alert" @click="handleSetAlert">
        <text>🔔 降价提醒</text>
      </view>
      <view class="action-btn favorite" @click="handleFavorite">
        <text>⭐ 收藏</text>
      </view>
      <view class="action-btn buy" @click="sortedPlatforms.length > 0 && handleBuy(sortedPlatforms[0])">
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
  padding-bottom: 160rpx;
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
  max-height: 60vh;
  background: #f0f0f0;
}

.product-image {
  width: 100%;
  height: 100%;
}

.image-error-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
}

.img-error-text {
  font-size: 32rpx;
  color: #ccc;
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

.diff-tip-text {
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

.platform-section {
  background: white;
  margin-top: 20rpx;
  padding: 30rpx;
  padding-bottom: 50rpx;
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

.stock-tag {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;

  &.in-stock {
    background: #E8F5E9;
    color: #2E7D32;
  }

  &.out-stock {
    background: #FFEBEE;
    color: #C62828;
  }
}

.seller-info {
  font-size: 24rpx;
  color: #666;
  line-height: 1.6;
}

.seller-label {
  color: #999;
  margin-right: 8rpx;
}

.seller-name {
  color: #333;
  font-weight: 500;
}

.rating {
  margin-left: 12rpx;
  color: #FF9800;
}

.sales-info {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #aaa;
}

.platform-right {
  text-align: right;
}

.prices {
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 8rpx;
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

.save-info {
  text-align: right;
  margin-top: 2rpx;
}

.save-text {
  font-size: 22rpx;
  color: #E4405F;
  font-weight: 500;
}

.meta {
  display: flex;
  justify-content: flex-end;
  margin-top: 4rpx;
}

.discount-tag {
  font-size: 20rpx;
  color: #FF6B35;
  background: #FFF3E0;
  padding: 2rpx 10rpx;
  border-radius: 4rpx;
  font-weight: 500;
}

.go-btn {
  margin-top: 6rpx;
  text-align: right;
  font-size: 24rpx;
  color: #FF6B35;
  font-weight: 500;
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
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