<template>
  <view class="search-bar-wrapper">
    <view class="search-bar">
      <view class="search-icon">
        <text class="search-icon-text">&#xe627;</text>
      </view>
      <input
        class="search-input"
        type="text"
        :value="modelValue"
        :placeholder="placeholder"
        confirm-type="search"
        :maxlength="100"
        @input="onInput"
        @confirm="onConfirm"
      />
      <view class="search-btn" @tap="onSearch">
        <text class="search-btn-text">搜索</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
  }>(),
  {
    placeholder: '搜索商品',
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'search', keyword: string): void
}>()

const onInput = (e: any) => {
  emit('update:modelValue', e.detail.value)
}

const onConfirm = (e: any) => {
  const keyword = e.detail.value || props.modelValue
  if (keyword.trim()) {
    emit('search', keyword.trim())
  }
}

const onSearch = () => {
  if (props.modelValue.trim()) {
    emit('search', props.modelValue.trim())
  }
}
</script>

<style scoped>
.search-bar-wrapper {
  padding: 16rpx 20rpx;
  background: #fff;
}

.search-bar {
  display: flex;
  align-items: center;
  height: 72rpx;
  background: #f5f5f5;
  border-radius: 36rpx;
  padding: 0 8rpx 0 24rpx;
}

.search-icon {
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12rpx;
}

.search-icon-text {
  font-size: 32rpx;
  color: #999;
}

.search-input {
  flex: 1;
  height: 100%;
  font-size: 28rpx;
  color: #333;
}

.search-btn {
  height: 60rpx;
  padding: 0 32rpx;
  background: linear-gradient(135deg, #ff6b35, #ff4500);
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.search-btn-text {
  font-size: 26rpx;
  color: #fff;
  font-weight: 500;
}
</style>