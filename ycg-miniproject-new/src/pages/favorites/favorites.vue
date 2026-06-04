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
    <LoadingIndicator v-if="loading" />
    <template v-else>
      <NoData v-if="favorites.length === 0" text="还没有收藏商品" icon="⭐" />
      <view v-else class="favorite-list">
        <view v-for="item in favorites" :key="item.favorite_id" class="favorite-item">
          <view class="item-main" @click="handleProductClick(item.product_id)">
            <image class="item-image" :src="item.product_image" mode="aspectFill" />
            <view class="item-info">
              <text class="item-title">{{ item.product_title }}</text>
              <text class="item-price">¥{{ item.product_min_price }}</text>
            </view>
          </view>
          <view class="item-delete" @click="handleDeleteFavorite(item)">
            <text>🗑️</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
.page { min-height: 100vh; background: #f5f5f5; }
.favorite-list { padding: 24rpx; display: flex; flex-direction: column; gap: 20rpx; }
.favorite-item { background: white; border-radius: 16rpx; padding: 20rpx; display: flex; align-items: center; }
.item-main { flex: 1; display: flex; align-items: center; }
.item-image { width: 160rpx; height: 160rpx; border-radius: 8rpx; flex-shrink: 0; margin-right: 20rpx; }
.item-info { flex: 1; display: flex; flex-direction: column; justify-content: space-between; }
.item-title { font-size: 26rpx; color: #333; line-height: 1.4; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.item-price { font-size: 32rpx; font-weight: 700; color: #FF6B35; }
.item-delete { padding: 20rpx; font-size: 36rpx; }
</style>