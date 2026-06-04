<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useUserStore } from '../../stores/user';
import { favoriteApi, browseHistoryApi, priceAlertApi } from '../../api';
import NoData from '../../components/NoData.vue';

const userStore = useUserStore();
const favorites = ref<any[]>([]);
const history = ref<any[]>([]);
const alertCount = ref(0);

const currentUser = computed(() => userStore.userInfo || { nick_name: '未登录', user_id: 0 });
const isLoggedIn = computed(() => userStore.isLoggedIn);

const stats = computed(() => ({
  favorites: favorites.value.length,
  history: history.value.length,
  alerts: alertCount.value
}));

const loadData = async () => {
  if (isLoggedIn.value) {
    try {
      const favRes = await favoriteApi.list();
      favorites.value = favRes.data?.items || [];
    } catch (e) { console.error('[userCenter] 加载收藏失败:', e); }
    try {
      const histRes = await browseHistoryApi.list();
      history.value = histRes.data?.items || [];
    } catch (e) { console.error('[userCenter] 加载历史失败:', e); }
    try {
      const alertRes = await priceAlertApi.list();
      alertCount.value = alertRes.data?.pagination?.total || alertRes.data?.items?.length || 0;
    } catch (e) { console.error('[userCenter] 加载提醒失败:', e); }
  }
};

const goLogin = () => {
  uni.navigateTo({ url: '/pages/login/login' });
};

const goTo = (url: string) => {
  if (!isLoggedIn.value) {
    uni.showModal({
      title: '提示',
      content: '此功能需要登录，是否前往登录？',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({ url: '/pages/login/login' });
        }
      }
    });
    return;
  }
  uni.navigateTo({ url });
};

const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定退出登录吗？',
    success: async (res) => {
      if (res.confirm) {
        await userStore.logout();
        favorites.value = [];
        history.value = [];
        alertCount.value = 0;
        uni.showToast({ title: '已退出登录', icon: 'none' });
      }
    }
  });
};

onMounted(() => { loadData(); });
onShow(() => { loadData(); });

// 登录状态变化时自动重新加载
watch(isLoggedIn, (val) => {
  if (val) {
    loadData();
  }
});
</script>

<template>
  <view class="page">
    <view class="user-header">
      <view class="avatar">
        <text class="avatar-text">{{ currentUser.nick_name ? currentUser.nick_name.slice(0, 1) : '?' }}</text>
      </view>
      <view class="user-name-wrap">
        <text class="user-name">{{ currentUser.nick_name || '未登录' }}</text>
        <text v-if="currentUser.vip_level" class="vip-tag">VIP {{ currentUser.vip_level }}</text>
      </view>
      <text v-if="!isLoggedIn" class="login-btn" @click="goLogin">点击登录</text>
      <text v-else class="logout-btn" @click="handleLogout">退出</text>
    </view>

    <view class="stats">
      <view class="stat-item" @click="goTo('/pages/favorites/favorites')">
        <text class="stat-num">{{ stats.favorites }}</text>
        <text class="stat-label">收藏</text>
      </view>
      <view class="stat-item" @click="goTo('/pages/history/history')">
        <text class="stat-num">{{ stats.history }}</text>
        <text class="stat-label">足迹</text>
      </view>
      <view class="stat-item" @click="goTo('/pages/priceAlerts/priceAlerts')">
        <text class="stat-num">{{ stats.alerts }}</text>
        <text class="stat-label">提醒</text>
      </view>
    </view>

    <view class="menu-list">
      <view class="menu-item" @click="goTo('/pages/favorites/favorites')">
        <text>⭐ 我的收藏</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="goTo('/pages/history/history')">
        <text>📋 浏览历史</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="goTo('/pages/priceAlerts/priceAlerts')">
        <text>🔔 降价提醒</text>
        <text class="arrow">›</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #f5f5f5;
}

.user-header {
  background: linear-gradient(135deg, #FF6B35 0%, #FF8C5A 100%);
  padding: 60rpx 30rpx 40rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4rpx solid rgba(255, 255, 255, 0.5);
}

.avatar-text {
  font-size: 44rpx;
  color: white;
  font-weight: 700;
}

.user-name-wrap {
  flex: 1;
}

.user-name {
  font-size: 34rpx;
  color: white;
  font-weight: 600;
}

.vip-tag {
  font-size: 20rpx;
  background: gold;
  color: #333;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  margin-left: 12rpx;
  font-weight: 600;
}

.login-btn, .logout-btn {
  font-size: 26rpx;
  color: white;
  padding: 10rpx 24rpx;
  border: 2rpx solid white;
  border-radius: 30rpx;
}

.stats {
  background: white;
  margin: -30rpx 24rpx 20rpx;
  border-radius: 16rpx;
  padding: 30rpx 0;
  display: flex;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.08);
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.stat-num {
  font-size: 40rpx;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 24rpx;
  color: #999;
}

.menu-list {
  background: white;
  margin: 0 24rpx;
  border-radius: 16rpx;
}

.menu-item {
  padding: 30rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1rpx solid #f5f5f5;
  font-size: 28rpx;
  color: #333;
}

.menu-item:last-child {
  border-bottom: none;
}

.arrow {
  font-size: 32rpx;
  color: #ccc;
}
</style>