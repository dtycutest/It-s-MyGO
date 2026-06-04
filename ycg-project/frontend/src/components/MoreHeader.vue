<script setup lang="ts">
defineProps<{
  title: string;
}>();

defineEmits<{
  (e: 'more'): void;
}>();
</script>

<template>
  <view class="more-header">
    <text class="more-title">{{ title }}</text>
    <view class="more-action" @click="$emit('more')">
      <text class="more-text">更多</text>
      <text class="more-arrow">›</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.more-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 30rpx;
}

.more-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.more-action {
  display: flex;
  align-items: center;
}

.more-text {
  font-size: 26rpx;
  color: #999;
}

.more-arrow {
  font-size: 36rpx;
  color: #999;
  margin-left: 4rpx;
}
</style>