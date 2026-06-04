<script setup lang="ts">
import { ref, computed } from 'vue';
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
      favorites.value = favRes.data?.list || [];
    } catch { /* ignore */ }
    try {
      const histRes = await browseHistoryApi.list();
      history.value = histRes.data?.list || [];
    } catch { /* ignore */ }
    try {
      const alertRes = await priceAlertApi.list();
      alertCount.value = alertRes.data?.pagination?.total || alertRes.data?.list?.length || 0;
    } catch { /* ignore */ }
  }
};

const handleLogin = () => {
  uni.navigateTo({ url: '/pages/login/login' });
};

const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: async (res) => {
      if (res.confirm) {
        await userStore.logout();
        uni.showToast({ title: '已退出登录', icon: 'success' });
      }
    }
  });
};

const handleNavigate = (url: string) => {
  uni.navigateTo({ url });
};

const handleProductClick = (productId: string) => {
  uni.navigateTo({ url: `/pages/productDetail/productDetail?product_id=${productId}` });
};

userStore.init().then(() => loadData());
</script>

<template>
  <view class="page">
    <!-- 用户信息头部 -->
    <view class="header">
      <template v-if="isLoggedIn">
        <view class="user-row">
          <view class="avatar">👤</view>
          <view class="info">
            <text class="name">{{ currentUser.nick_name || '测试用户' }}</text>
            <text class="uid">ID: {{ currentUser.user_id }}</text>
          </view>
          <view class="logout-btn" @click="handleLogout">
            <text>退出</text>
          </view>
        </view>
      </template>
      <template v-else>
        <view class="login-tip" @click="handleLogin">
          <view class="avatar">👤</view>
          <text class="login-text">点击登录</text>
        </view>
      </template>

      <!-- 统计卡片 -->
      <view class="stats-row">
        <view class="stat-card" @click="handleNavigate('/pages/favorites/favorites')">
          <text class="stat-num">{{ stats.favorites }}</text>
          <text class="stat-label">收藏</text>
        </view>
        <view class="stat-card" @click="handleNavigate('/pages/history/history')">
          <text class="stat-num">{{ stats.history }}</text>
          <text class="stat-label">足迹</text>
        </view>
        <view class="stat-card" @click="handleNavigate('/pages/priceAlerts/priceAlerts')">
          <text class="stat-num">{{ stats.alerts }}</text>
          <text class="stat-label">降价提醒</text>
        </view>
      </view>
    </view>

    <!-- 功能菜单 -->
    <view class="menu-section">
      <view class="menu-item" @click="handleNavigate('/pages/favorites/favorites')">
        <text class="menu-icon">⭐</text>
        <text class="menu-text">我的收藏</text>
        <text class="menu-count">{{ stats.favorites }}</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="handleNavigate('/pages/history/history')">
        <text class="menu-icon">👀</text>
        <text class="menu-text">浏览历史</text>
        <text class="menu-count">{{ stats.history }}</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="handleNavigate('/pages/priceAlerts/priceAlerts')">
        <text class="menu-icon">🔔</text>
        <text class="menu-text">降价提醒</text>
        <text class="menu-count">{{ stats.alerts }}</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- 最近收藏 -->
    <view v-if="favorites.length > 0" class="preview-section">
      <view class="section-header">
        <text class="section-title">⭐ 最近收藏</text>
        <text class="section-more" @click="handleNavigate('/pages/favorites/favorites')">全部 ›</text>
      </view>
      <view class="mini-list">
        <view
          v-for="item in favorites"
          :key="item.favorite_id"
          class="mini-item"
          @click="handleProductClick(item.product_id)"
        >
          <image class="mini-image" :src="item.product_image" mode="aspectFill" />
          <text class="mini-title">{{ item.product_title }}</text>
          <text class="mini-price">¥{{ item.product_min_price }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background: linear-gradient(180deg, #FF6B35 0%, #E55A26 100%);
  padding: 40rpx 30rpx 30rpx;
}

.user-row {
  display: flex;
  align-items: center;
}

.avatar {
  width: 120rpx;
  height: 120rpx;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 60rpx;
  margin-right: 24rpx;
}

.info {
  flex: 1;
}

.name {
  font-size: 36rpx;
  font-weight: 600;
  color: white;
  display: block;
  margin-bottom: 8rpx;
}

.uid {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
}

.logout-btn {
  padding: 12rpx 24rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 30rpx;
  font-size: 24rpx;
  color: white;
}

.login-tip {
  display: flex;
  align-items: center;
}

.login-text {
  font-size: 32rpx;
  font-weight: 600;
  color: white;
}

.stats-row {
  display: flex;
  margin-top: 36rpx;
}

.stat-card {
  flex: 1;
  text-align: center;
}

.stat-num {
  font-size: 40rpx;
  font-weight: 700;
  color: white;
  display: block;
}

.stat-label {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4rpx;
}

.menu-section {
  background: white;
  margin-top: 20rpx;
}

.menu-item {
  padding: 30rpx;
  display: flex;
  align-items: center;
  border-bottom: 1rpx solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }
}

.menu-icon {
  font-size: 36rpx;
  margin-right: 20rpx;
}

.menu-text {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.menu-count {
  font-size: 24rpx;
  color: #FF6B35;
  font-weight: 600;
  margin-right: 10rpx;
}

.menu-arrow {
  font-size: 40rpx;
  color: #ccc;
}

.preview-section {
  background: white;
  margin-top: 20rpx;
  padding: 0 30rpx 30rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30rpx 0;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.section-more {
  font-size: 26rpx;
  color: #FF6B35;
}

.mini-list {
  display: flex;
  gap: 20rpx;
}

.mini-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.mini-image {
  width: 100%;
  height: 200rpx;
  border-radius: 8rpx;
  background: #f0f0f0;
}

.mini-title {
  font-size: 22rpx;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.mini-price {
  font-size: 26rpx;
  font-weight: 700;
  color: #FF6B35;
}
</style>