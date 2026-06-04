<script setup lang="ts">
import { useUserStore } from '../../stores/user';

const userStore = useUserStore();

const handleWeixinLogin = async () => {
  try {
    // 第一步：调用微信登录获取临时 code
    const loginRes = await uni.login({ provider: 'weixin' });
    if (!loginRes.code) {
      uni.showToast({ title: '获取微信授权失败', icon: 'none' });
      return;
    }
    const code = loginRes.code;

    // 第二步：获取用户基本信息（昵称、头像等）
    let rawData = '{}';
    let signature = 'weixin_signature';

    try {
      const profileRes = await uni.getUserProfile({
        desc: '用于完善用户资料',
      });
      if (profileRes.rawData) {
        rawData = JSON.stringify(profileRes.rawData);
      }
      if (profileRes.signature) {
        signature = profileRes.signature;
      }
    } catch (e: any) {
      // 用户拒绝授权个人信息，仍可使用 code 登录
      console.log('用户拒绝个人信息授权，使用基础登录');
    }

    // 第三步：将 code 和用户信息发送到后端
    await userStore.login({
      code,
      raw_data: rawData,
      signature,
    });

    uni.showToast({ title: '登录成功', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 500);
  } catch (error: any) {
    console.error('微信登录失败:', error);
    const errMsg = error?.errMsg || error?.message || '';
    if (errMsg.includes('cancel')) {
      uni.showToast({ title: '已取消登录', icon: 'none' });
    } else if (errMsg.includes('not support') || errMsg.includes('not exist')) {
      uni.showToast({ title: '请在微信小程序中使用微信登录', icon: 'none' });
    } else {
      uni.showToast({ title: '登录失败，请重试', icon: 'none' });
    }
  }
};

const handleMockLogin = async () => {
  try {
    await userStore.login({
      code: 'mock_dev_code',
      raw_data: JSON.stringify({ nickName: '测试用户', gender: 1 }),
      signature: 'mock_dev_signature',
    });

    uni.showToast({ title: '模拟登录成功', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 500);
  } catch (error) {
    console.error('模拟登录失败:', error);
    uni.showToast({ title: '登录失败，请重试', icon: 'none' });
  }
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
      <!-- #ifdef MP-WEIXIN -->
      <button class="login-btn weixin" @click="handleWeixinLogin">
        <text class="btn-icon">💚</text>
        微信一键登录
      </button>
      <!-- #endif -->
      <!-- #ifndef MP-WEIXIN -->
      <button class="login-btn weixin-disabled" disabled>
        <text class="btn-icon">💚</text>
        请在微信小程序中登录
      </button>
      <!-- #endif -->
      
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

.weixin-disabled {
  background-color: #a0d8b5;
  color: rgba(255, 255, 255, 0.7);
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
