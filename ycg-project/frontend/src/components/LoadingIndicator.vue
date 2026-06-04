<script setup lang="ts">
defineProps<{
  text?: string;
}>();
</script>

<template>
  <view class="loading-container">
    <view class="loading-spinner" />
    <text class="loading-text">{{ text || '加载中...' }}</text>
  </view>
</template>

<style lang="scss" scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #f0f0f0;
  border-top-color: #FF6B35;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-top: 20rpx;
  font-size: 26rpx;
  color: #999;
}
</style>