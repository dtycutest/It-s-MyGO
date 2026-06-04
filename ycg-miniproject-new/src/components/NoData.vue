<script setup lang="ts">
defineProps<{
  text?: string;
  icon?: string;
}>();
</script>

<template>
  <view class="no-data">
    <text class="no-data-icon">{{ icon || '📭' }}</text>
    <text class="no-data-text">{{ text || '暂无数据' }}</text>
  </view>
</template>

<style lang="scss" scoped>
.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 60rpx;
}

.no-data-icon {
  font-size: 100rpx;
  margin-bottom: 24rpx;
}

.no-data-text {
  font-size: 28rpx;
  color: #999;
}
</style>