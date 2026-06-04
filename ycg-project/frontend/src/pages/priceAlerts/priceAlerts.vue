<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { usePriceAlertStore } from '../../stores/priceAlert';
import { useUserStore } from '../../stores/user';
import { priceAlertApi } from '../../api';
import NoData from '../../components/NoData.vue';
import LoadingIndicator from '../../components/LoadingIndicator.vue';

const alertStore = usePriceAlertStore();
const userStore = useUserStore();
const loading = ref(true);
const alerts = ref<any[]>([]);

const loadAlerts = async () => {
  if (!userStore.isLoggedIn) {
    uni.showModal({
      title: '提示',
      content: '降价提醒功能需要登录，是否前往登录？',
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
    await alertStore.fetchAlerts();
    alerts.value = alertStore.alerts;
  } catch {
    console.error('加载降价提醒失败');
  }
  loading.value = false;
};

const handleProductClick = (productId: string) => {
  uni.navigateTo({ url: `/pages/productDetail/productDetail?product_id=${productId}` });
};

const handleDelete = (alert: any) => {
  uni.showModal({
    title: '提示',
    content: '确定删除此降价提醒吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await priceAlertApi.delete(alert.alert_id);
          alerts.value = alerts.value.filter(a => a.alert_id !== alert.alert_id);
          uni.showToast({ title: '已删除', icon: 'success' });
        } catch {
          uni.showToast({ title: '删除失败', icon: 'none' });
        }
      }
    }
  });
};

onMounted(() => { loadAlerts(); });
</script>

<template>
  <view class="page">
    <view class="header">
      <text class="header-title">降价提醒</text>
    </view>

    <LoadingIndicator v-if="loading" text="加载中..." />
    <NoData v-else-if="alerts.length === 0" text="还没有设置降价提醒" icon="🔔" />
    <view v-else class="alert-list">
      <view
        v-for="alert in alerts"
        :key="alert.alert_id"
        class="alert-item"
        @click="handleProductClick(alert.product_id)"
      >
        <image
          class="alert-image"
          :src="alert.product_image || '/static/logo.png'"
          mode="aspectFill"
        />
        <view class="alert-info">
          <text class="alert-title">{{ alert.product_title || '商品' }}</text>
          <view class="alert-price-row">
            <text class="alert-target">目标价: ¥{{ alert.target_price }}</text>
            <text v-if="alert.current_price" class="alert-current">当前价: ¥{{ alert.current_price }}</text>
          </view>
          <view class="alert-status">
            <text v-if="alert.is_triggered" class="triggered">已触发降价</text>
            <text v-else-if="alert.is_enabled" class="enabled">监控中</text>
            <text v-else class="disabled">已暂停</text>
          </view>
        </view>
        <view class="alert-delete" @click.stop="handleDelete(alert)">
          <text>🗑</text>
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
}

.header-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.alert-list {
  padding: 20rpx 24rpx;
}

.alert-item {
  background: white;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 16rpx;
  display: flex;
  align-items: center;
}

.alert-image {
  width: 120rpx;
  height: 120rpx;
  border-radius: 12rpx;
  background: #f0f0f0;
  flex-shrink: 0;
  margin-right: 20rpx;
}

.alert-info {
  flex: 1;
  overflow: hidden;
}

.alert-title {
  font-size: 28rpx;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 8rpx;
}

.alert-price-row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 8rpx;
}

.alert-target {
  font-size: 24rpx;
  color: #FF6B35;
  font-weight: 600;
}

.alert-current {
  font-size: 24rpx;
  color: #999;
}

.alert-status {
  font-size: 22rpx;
}

.triggered {
  color: #E4405F;
  font-weight: 600;
}

.enabled {
  color: #4CAF50;
}

.disabled {
  color: #999;
}

.alert-delete {
  padding: 16rpx;
  font-size: 32rpx;
}
</style>