<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { browseHistoryApi } from '../../api';
import { useUserStore } from '../../stores/user';
import NoData from '../../components/NoData.vue';
import LoadingIndicator from '../../components/LoadingIndicator.vue';

const userStore = useUserStore();
const history = ref<any[]>([]);
const loading = ref(true);

const loadHistory = async () => {
  if (!userStore.isLoggedIn) {
    uni.showModal({
      title: '提示',
      content: '浏览历史功能需要登录，是否前往登录？',
      success: (res) => {
        if (res.confirm) {
          uni.navigateTo({ url: '/pages/login/login' });
        }
      }
    });
    loading.value = false;
    return;
  }
  loading.value = true;
  try {
    const res = await browseHistoryApi.list();
    history.value = res.data?.items || [];
  } catch {
    console.error('加载浏览历史失败');
  }
  loading.value = false;
};

const handleProductClick = (productId: string) => {
  uni.navigateTo({ url: `/pages/productDetail/productDetail?product_id=${productId}` });
};

const handleClearAll = () => {
  uni.showModal({
    title: '提示',
    content: '确定清空所有浏览记录吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await browseHistoryApi.clear();
          history.value = [];
          uni.showToast({ title: '已清空', icon: 'success' });
        } catch {
          uni.showToast({ title: '清空失败', icon: 'none' });
        }
      }
    }
  });
};

const formatViewTime = (utcStr: string): string => {
  if (!utcStr) return '';
  try {
    const d = new Date(utcStr);
    if (isNaN(d.getTime())) return utcStr;
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    const days = Math.floor(hours / 24);
    if (days === 1) return '昨天';
    if (days < 7) return `${days}天前`;
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hour = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${month}-${day} ${hour}:${min}`;
  } catch {
    return utcStr;
  }
};

onMounted(() => { loadHistory(); });
</script>

<template>
  <view class="page">
    <view class="header">
      <text class="header-title">浏览历史</text>
      <text v-if="history.length > 0" class="clear-btn" @click="handleClearAll">清空</text>
    </view>

    <LoadingIndicator v-if="loading" text="加载中..." />
    <NoData v-else-if="history.length === 0" text="还没有浏览记录" icon="📋" />
    <view v-else class="history-list">
      <view
        v-for="item in history"
        :key="item.history_id"
        class="history-item"
        @click="handleProductClick(item.product_id)"
      >
        <image
          class="history-image"
          :src="item.product_image || '/static/logo.png'"
          mode="aspectFill"
        />
        <view class="history-info">
          <text class="history-title">{{ item.product_title || '商品' }}</text>
          <text class="history-time">{{ formatViewTime(item.viewed_at) }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  background: white;
  padding: 24rpx 30rpx;
  border-bottom: 1rpx solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.clear-btn {
  font-size: 26rpx;
  color: #FF6B35;
}

.history-list {
  padding: 20rpx 24rpx;
}

.history-item {
  background: white;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 12rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.history-image {
  width: 120rpx;
  height: 120rpx;
  border-radius: 12rpx;
  background: #f0f0f0;
  flex-shrink: 0;
}

.history-info {
  flex: 1;
  overflow: hidden;
}

.history-title {
  font-size: 28rpx;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 8rpx;
}

.history-time {
  font-size: 22rpx;
  color: #bbb;
}
</style>