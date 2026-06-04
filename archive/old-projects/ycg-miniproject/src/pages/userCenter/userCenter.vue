<script setup lang="ts">
import { ref, onMounted } from 'vue';

console.log('[DEBUG] 用户中心 setup 开始');
const isLoggedIn = ref(false);

onMounted(() => {
  console.log('[DEBUG] 用户中心 onMounted');
});

const toggleLogin = () => {
  isLoggedIn.value = !isLoggedIn.value;
  uni.showToast({
    title: isLoggedIn.value ? '已登录' : '已退出',
    icon: 'success'
  });
};
</script>

<template>
  <view style="min-height: 100vh; background: #f5f5f5;">
    <!-- 头部 -->
    <view style="background: linear-gradient(180deg, #FF6B35 0%, #E55A26 100%); padding: 80rpx 40rpx 50rpx;">
      <view style="display: flex; align-items: center;">
        <view style="width: 100rpx; height: 100rpx; background: white; border-radius: 50rpx; display: flex; align-items: center; justify-content: center; font-size: 40rpx;">
          {{ isLoggedIn ? '测' : '👤' }}
        </view>
        <view style="margin-left: 30rpx;">
          <text style="font-size: 32rpx; color: white; font-weight: 600; display: block;">
            {{ isLoggedIn ? '测试用户' : '未登录' }}
          </text>
          <text style="font-size: 24rpx; color: rgba(255,255,255,0.8); display: block; margin-top: 10rpx;">
            这是一个简化的用户中心页面
          </text>
        </view>
      </view>
    </view>

    <!-- 测试按钮 -->
    <view style="padding: 40rpx;">
      <button 
        style="width: 100%; background: #3498db; color: white; padding: 30rpx; border-radius: 16rpx; border: none; font-size: 28rpx;"
        @click="toggleLogin"
      >
        {{ isLoggedIn ? '退出登录' : '点击登录' }}
      </button>
    </view>

    <!-- 菜单项 -->
    <view style="background: white; margin: 0 24rpx; border-radius: 24rpx; overflow: hidden;">
      <view style="display: flex; align-items: center; padding: 35rpx; border-bottom: 1rpx solid #eee;">
        <text style="font-size: 36rpx; margin-right: 24rpx;">⭐</text>
        <text style="flex: 1; font-size: 28rpx;">我的收藏</text>
        <text style="font-size: 32rpx; color: #ccc;">›</text>
      </view>
      <view style="display: flex; align-items: center; padding: 35rpx;">
        <text style="font-size: 36rpx; margin-right: 24rpx;">📋</text>
        <text style="flex: 1; font-size: 28rpx;">浏览历史</text>
        <text style="font-size: 32rpx; color: #ccc;">›</text>
      </view>
    </view>

    <!-- 底部测试 -->
    <view style="margin-top: 50rpx; text-align: center;">
      <text style="font-size: 24rpx; color: #999;">页面渲染正常 ✅</text>
    </view>
  </view>
</template>
