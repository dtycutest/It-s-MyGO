<template>
  <view class="test-page">
    <view class="test-container">
      <text class="test-title">✅ 测试页面</text>
      <text class="test-text">如果你能看到这句话，说明页面渲染正常！</text>
      <view class="test-box">
        <text class="test-box-text">测试内容 1</text>
      </view>
      <view class="test-box">
        <text class="test-box-text">测试内容 2</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
console.log('测试页面已加载！');
</script>

<style lang="scss" scoped>
.test-page {
  padding: 40rpx;
  background-color: #f0f0f0;
  min-height: 100vh;
}

.test-container {
  background-color: white;
  padding: 40rpx;
  border-radius: 16rpx;
}

.test-title {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 30rpx;
}

.test-text {
  font-size: 32rpx;
  color: #666;
  display: block;
  margin-bottom: 30rpx;
}

.test-box {
  background-color: #FF6B35;
  padding: 30rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}

.test-box-text {
  color: white;
  font-size: 28rpx;
}
</style>
