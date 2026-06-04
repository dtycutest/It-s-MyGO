<script setup lang="ts">
import { ref } from 'vue';
import type { Product } from '../api/types';

const props = defineProps<{
  product: Product;
}>();

const emit = defineEmits<{
  (e: 'click', productId: string): void;
}>();

const imgError = ref(false);

const handleClick = () => {
  emit('click', props.product.product_id);
};

const onImageError = () => {
  imgError.value = true;
};
</script>

<template>
  <view class="product-card" @click="handleClick">
    <view v-if="imgError" class="card-image card-image-error">
      <text class="img-error-text">图片失效</text>
    </view>
    <image
      v-else
      class="card-image"
      :src="product.image_url || ''"
      mode="aspectFill"
      @error="onImageError"
    />
    <view class="card-body">
      <text class="card-title">{{ product.title }}</text>
      <view class="card-price-row">
        <text class="card-min-price">¥{{ product.min_price }}</text>
        <text class="card-diff">差价¥{{ (product.price_diff || 0).toFixed(2) }}</text>
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
  height: 280rpx;
  background: #f0f0f0;
}

.card-image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
}

.img-error-text {
  font-size: 24rpx;
  color: #ccc;
}

.card-body {
  padding: 16rpx;
}

.card-title {
  font-size: 26rpx;
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
  flex-wrap: wrap;
  margin-top: 8rpx;
}

.card-min-price {
  font-size: 32rpx;
  font-weight: 700;
  color: #FF6B35;
}

.card-diff {
  font-size: 22rpx;
  color: #E4405F;
  margin-left: 8rpx;
}

.card-footer {
  margin-top: 4rpx;
}

.card-platform {
  font-size: 20rpx;
  color: #999;
}
</style>