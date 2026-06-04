<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  platform: string;
  size?: 'small' | 'normal';
}>();

const platformColor = computed(() => {
  const map: Record<string, string> = {
    '淘宝': '#FFF7E6',
    '京东': '#E8F5FF',
    '拼多多': '#FFE8E8',
  };
  return map[props.platform] || '#f5f5f5';
});

const platformTextColor = computed(() => {
  const map: Record<string, string> = {
    '淘宝': '#E1640F',
    '京东': '#0052CC',
    '拼多多': '#E82E2E',
  };
  return map[props.platform] || '#666';
});
</script>

<template>
  <view
    :class="['platform-badge', `badge-${size || 'normal'}`]"
    :style="{ background: platformColor, color: platformTextColor }"
  >
    <text>{{ platform }}</text>
  </view>
</template>

<style lang="scss" scoped>
.platform-badge {
  display: inline-flex;
  align-items: center;
  border-radius: 6rpx;
  font-weight: 500;
}

.badge-small {
  padding: 4rpx 12rpx;
  font-size: 20rpx;
}

.badge-normal {
  padding: 6rpx 16rpx;
  font-size: 24rpx;
}
</style>