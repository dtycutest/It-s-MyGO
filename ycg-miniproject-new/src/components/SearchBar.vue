<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  placeholder?: string;
  modelValue?: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'search', keyword: string): void;
  (e: 'focus'): void;
}>();

const keyword = ref(props.modelValue || '');

const handleConfirm = () => {
  const kw = keyword.value.trim();
  if (!kw) {
    uni.showToast({ title: '请输入搜索内容', icon: 'none' });
    return;
  }
  emit('search', kw);
};

const handleFocus = () => {
  emit('focus');
};
</script>

<template>
  <view class="search-container">
    <view class="search-box">
      <text class="search-icon">🔍</text>
      <input
        class="search-input"
        v-model="keyword"
        :placeholder="placeholder || '搜索商品'"
        placeholder-class="search-placeholder"
        confirm-type="search"
        @confirm="handleConfirm"
        @focus="handleFocus"
      />
    </view>
  </view>
</template>

<style lang="scss" scoped>
.search-container {
  background: linear-gradient(180deg, #FF6B35 0%, #E55A26 100%);
  padding: 20rpx 30rpx;
}

.search-box {
  background: white;
  border-radius: 50rpx;
  padding: 15rpx 30rpx;
  display: flex;
  align-items: center;
}

.search-icon {
  font-size: 32rpx;
  margin-right: 15rpx;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
  height: 50rpx;
}

.search-placeholder {
  color: #999;
}
</style>