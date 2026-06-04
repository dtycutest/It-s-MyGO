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
    <LoadingIndicator v-if="loading" />
    <template v-else>
      <NoData v-if="alerts.length === 0" text="暂无降价提醒" icon="🔔" />
      <view v-else class="alert-list">
        <view v-for="alert in alerts" :key="alert.alert_id" class="alert-item">
          <view class="item-main" @click="handleProductClick(alert.product_id)">
            <image class="item-image" :src="alert.product_image || '/static/logo.png'" mode="aspectFill" />
            <view class="item-info">
              <text class="item-title">{{ alert.product_title }}</text>
              <view class="price-info">
                <text class="current-price">现价 ¥{{ alert.current_price }}</text>
                <text class="target-price">目标价 ¥{{ alert.target_price }}</text>
              </view>
              <view class="status-row">
                <view class="status-tag" :class="alert.current_price <= alert.target_price ? 'tag-done' : 'tag-pending'">
                  <text>{{ alert.current_price <= alert.target_price ? '✅ 已触发' : '⏳ 等待降价' }}</text>
                </view>
                <text class="create-time">设置于 {{ alert.created_at }}</text>
              </view>
            </view>
          </view>
          <view class="item-delete" @click="handleDelete(alert)">
            <text>🗑️</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
.page { min-height: 100vh; background: #f5f5f5; }
.alert-list { padding: 24rpx; display: flex; flex-direction: column; gap: 20rpx; }
.alert-item { background: white; border-radius: 16rpx; padding: 20rpx; display: flex; align-items: center; }
.item-main { flex: 1; display: flex; align-items: center; }
.item-image { width: 160rpx; height: 160rpx; border-radius: 8rpx; flex-shrink: 0; margin-right: 20rpx; }
.item-info { flex: 1; display: flex; flex-direction: column; gap: 10rpx; }
.item-title { font-size: 26rpx; color: #333; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.price-info { display: flex; gap: 20rpx; }
.current-price { font-size: 28rpx; font-weight: 700; color: #FF6B35; }
.target-price { font-size: 24rpx; color: #999; }
.status-row { display: flex; align-items: center; justify-content: space-between; }
.status-tag { padding: 4rpx 12rpx; border-radius: 8rpx; font-size: 20rpx; }
.tag-done { background: #E8F5E9; color: #50C878; }
.tag-pending { background: #FFF3E0; color: #FF6B35; }
.create-time { font-size: 20rpx; color: #999; }
.item-delete { padding: 20rpx; font-size: 36rpx; }
</style>