<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useFavoriteStore } from '../../stores/favorite';
import { useUserStore } from '../../stores/user';
import { favoriteApi } from '../../api';
import NoData from '../../components/NoData.vue';
import ProductCard from '../../components/ProductCard.vue';
import LoadingIndicator from '../../components/LoadingIndicator.vue';

const favoriteStore = useFavoriteStore();
const userStore = useUserStore();

const favorites = ref<any[]>([]);
const loading = ref(true);

const loadFavorites = async () => {
  if (!userStore.isLoggedIn) {
    uni.showModal({
      title: '提示',
      content: '收藏功能需要登录，是否前往登录？',
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
    await favoriteStore.fetchFavorites();
    favorites.value = favoriteStore.favorites;
  } catch {
    console.error('加载收藏失败');
  }
  loading.value = false;
};

const handleProductClick = (productId: string) => {
  uni.navigateTo({ url: `/pages/productDetail/productDetail?product_id=${productId}` });
};

const handleDeleteFavorite = (item: any) => {
  uni.showModal({
    title: '提示',
    content: '确定取消收藏吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await favoriteApi.remove(item.favorite_id);
          favorites.value = favorites.value.filter(f => f.favorite_id !== item.favorite_id);
          uni.showToast({ title: '已取消收藏', icon: 'success' });
        } catch {
          uni.showToast({ title: '取消收藏失败', icon: 'none' });
        }
      }
    }
  });
};

onMounted(() => { loadFavorites(); });
</script>

<template>
  <view class="page">
    <view class="header">
      <text class="header-title">我的收藏</text>
    </view>

    <LoadingIndicator v-if="loading" text="加载中..." />
    <NoData v-else-if="favorites.length === 0" text="还没有收藏任何商品" icon="⭐" />
    <view v-else class="favorites-list">
      <view
        v-for="item in favorites"
        :key="item.favorite_id"
        class="favorite-item"
      >
        <view class="item-content" @click="handleProductClick(item.product_id)">
          <image
            class="item-image"
            :src="item.product_image || '/static/logo.png'"
            mode="aspectFill"
          />
          <view class="item-info">
            <text class="item-title">{{ item.product_title || '商品名加载中' }}</text>
            <text class="item-price">{{ item.product_min_price ? '¥' + item.product_min_price : '' }}</text>
            <text class="item-note">{{ item.notes || '' }}</text>
          </view>
        </view>
        <view class="item-delete" @click="handleDeleteFavorite(item)">
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

.favorites-list {
  padding: 20rpx 24rpx;
}

.favorite-item {
  background: white;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 16rpx;
  display: flex;
  align-items: center;
}

.item-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.item-image {
  width: 140rpx;
  height: 140rpx;
  border-radius: 12rpx;
  background: #f0f0f0;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  overflow: hidden;
}

.item-title {
  font-size: 28rpx;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 8rpx;
}

.item-price {
  font-size: 30rpx;
  font-weight: 600;
  color: #FF6B35;
}

.item-note {
  font-size: 22rpx;
  color: #999;
  margin-top: 4rpx;
}

.item-delete {
  padding: 16rpx;
  font-size: 32rpx;
}
</style>