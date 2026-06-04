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
    history.value = res.data?.list || [];
  } catch {
    console.error('加载浏览历史失败');
  }
  loading.value = false;
};

const handleProductClick = (productId: string) => {
  uni.navigateTo({ url: `/pages/productDetail/productDetail?product_id=${productId}` });
};

const handleClear = () => {
  uni.showModal({
    title: '提示',
    content: '确定清空浏览历史吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await browseHistoryApi.clear();
        } catch {
          console.error('清空失败');
        }
        history.value = [];
        uni.showToast({ title: '已清空', icon: 'success' });
      }
    }
  });
};

onMounted(() => { loadHistory(); });
</script>

<template>
  <view class="page">
    <view v-if="history.length > 0" class="header-bar">
      <view class="clear-btn" @click="handleClear">
        <text>🗑️ 清空</text>
      </view>
    </view>
    <LoadingIndicator v-if="loading" />
    <template v-else>
      <NoData v-if="history.length === 0" text="暂无浏览历史" icon="👀" />
      <view v-else class="history-list">
        <view v-for="item in history" :key="item.history_id" class="history-item" @click="handleProductClick(item.product_id)">
          <image class="item-image" :src="item.product_image || '/static/logo.png'" mode="aspectFill" />
          <view class="item-info">
            <text class="item-title">{{ item.product_title }}</text>
            <text class="item-time">浏览于 {{ item.viewed_at }}</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
.page { min-height: 100vh; background: #f5f5f5; }
.header-bar { display: flex; justify-content: flex-end; padding: 16rpx 30rpx; background: white; }
.clear-btn { font-size: 26rpx; color: #999; }
.history-list { padding: 0 24rpx 24rpx; display: flex; flex-direction: column; gap: 20rpx; }
.history-item { background: white; border-radius: 16rpx; padding: 20rpx; display: flex; align-items: center; }
.item-image { width: 160rpx; height: 160rpx; border-radius: 8rpx; flex-shrink: 0; margin-right: 20rpx; }
.item-info { flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
.item-title { font-size: 26rpx; color: #333; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.item-time { font-size: 22rpx; color: #999; }
</style>