<script setup lang="ts">
import { useUserStore } from '../../stores/user';

const userStore = useUserStore();

const handleWeixinLogin = async () => {
  try {
    await userStore.login({
      code: 'mock_code',
      raw_data: '',
      signature: ''
    });
    
    uni.showToast({ title: '登录成功', icon: 'success' });
    uni.navigateBack();
  } catch (error) {
    console.error('登录失败:', error);
    uni.showToast({ title: '登录失败，请重试', icon: 'none' });
  }
};

const handleMockLogin = async () => {
  // 模拟登录，仅用于开发测试
  await userStore.login({
    code: 'mock_code',
    raw_data: '',
    signature: ''
  });
  
  uni.showToast({ title: '登录成功', icon: 'success' });
  uni.navigateBack();
};
</script>

<template>
  <view class="page">
    
    <view class="logo-section">
      <view class="logo">🛒</view>
      <text class="app-name">一次买够</text>
      <text class="app-desc">全网比价，一次买够</text>
    </view>

    <view class="login-section">
      <button class="login-btn weixin" @click="handleWeixinLogin">
        <text class="btn-icon">💚</text>
        微信一键登录
      </button>
      
      <text class="login-tips">
        登录即表示同意用户协议和隐私政策
      </text>
      
      <button class="dev-tips" @click="handleMockLogin">
        (开发测试) 点击这里模拟登录
      </button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
  padding: 40rpx;
}

.logo-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.logo {
  font-size: 128rpx;
  margin-bottom: 32rpx;
}

.app-name {
  font-size: 48rpx;
  font-weight: 700;
  color: #333;
  display: block;
  margin-bottom: 16rpx;
}

.app-desc {
  font-size: 28rpx;
  color: #999;
  display: block;
}

.login-section {
  padding-bottom: 80rpx;
}

.login-btn {
  width: 100%;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  line-height: 1;
}

.login-btn::after {
  border: none;
}

.btn-icon {
  margin-right: 16rpx;
  font-size: 40rpx;
}

.weixin {
  background-color: #07C160;
  color: white;
}

.login-tips {
  text-align: center;
  font-size: 24rpx;
  color: #999;
  margin-top: 40rpx;
  display: block;
}

.dev-tips {
  display: block;
  width: 100%;
  text-align: center;
  font-size: 26rpx;
  color: #FF6B35;
  margin-top: 32rpx;
  background: none;
  border: none;
  padding: 16rpx;
  line-height: 1;
}

.dev-tips::after {
  border: none;
}
</style>
