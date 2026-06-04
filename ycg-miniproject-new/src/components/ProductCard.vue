<script setup lang="ts">
import type { Product } from '../api/types';

const props = defineProps<{
  product: Product;
}>();

const emit = defineEmits<{
  (e: 'click', productId: string): void;
}>();

const handleClick = () => {
  emit('click', props.product.product_id);
};
</script>

<template>
  <view class="product-card" @click="handleClick">
    <image class="card-image" :src="product.image_url || '/static/logo.png'" mode="aspectFill" />
    <view class="card-body">
      <text class="card-title">{{ product.title }}</text>
      <view class="card-price-row">
        <text class="card-min-price">¥{{ product.min_price }}</text>
        <text class="card-diff">差价¥{{ product.price_diff }}</text>
      </view>
      <view class="card-footer">
        <text class="card-platform">最优价: {{ product.best_platform }}</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.product-card {
  background: white;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.card-image {
  width: 100%;
  height: 360rpx;
  background: #f0f0f0;
}

.card-body {
  padding: 20rpx 24rpx;
}

.card-title {
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.card-price-row {
  display: flex;
  align-items: baseline;
  margin-top: 12rpx;
}

.card-min-price {
  font-size: 36rpx;
  font-weight: 700;
  color: #FF6B35;
}

.card-diff {
  font-size: 24rpx;
  color: #E4405F;
  margin-left: 12rpx;
}

.card-footer {
  margin-top: 8rpx;
}

.card-platform {
  font-size: 22rpx;
  color: #999;
}
</style>