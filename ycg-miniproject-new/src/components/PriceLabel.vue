<script setup lang="ts">
defineProps<{
  price: number;
  size?: 'small' | 'normal' | 'large';
  type?: 'primary' | 'success' | 'warning' | 'danger';
}>();
</script>

<template>
  <view :class="['price-label', `size-${size || 'normal'}`, `type-${type || 'primary'}`]">
    <text class="currency">¥</text>
    <text class="amount">{{ price }}</text>
  </view>
</template>

<style lang="scss" scoped>
.price-label {
  display: inline-flex;
  align-items: baseline;
  font-weight: 600;

  .currency {
    font-size: 0.8em;
    margin-right: 2rpx;
  }
}

.size-small {
  font-size: 24rpx;
}

.size-normal {
  font-size: 32rpx;
}

.size-large {
  font-size: 48rpx;
}

.type-primary {
  color: #FF6B35;
}

.type-success {
  color: #50C878;
}

.type-warning {
  color: #FFB81C;
}

.type-danger {
  color: #E4405F;
}
</style>