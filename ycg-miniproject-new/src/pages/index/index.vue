<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { mockBanners } from '../../mock/data';
import { useProductStore } from '../../stores/product';
import { productApi } from '../../api';
import SearchBar from '../../components/SearchBar.vue';
import ProductCard from '../../components/ProductCard.vue';
import MoreHeader from '../../components/MoreHeader.vue';
import LoadingIndicator from '../../components/LoadingIndicator.vue';

const productStore = useProductStore();

const searchKeyword = ref('');
const hotWords = ref<any[]>([]);
const banners = ref<any[]>([]);
const categories = ref<any[]>([]);
const products = ref<any[]>([]);
const loading = ref(true);

onMounted(async () => {
  banners.value = mockBanners;

  try {
    const catRes = await productApi.getCategories();
    categories.value = catRes.data || [];
  } catch {
    categories.value = [];
  }

  try {
    const hotRes = await productStore.getHotWords(10);
    hotWords.value = hotRes.data || [];
  } catch {
    hotWords.value = [];
  }

  try {
    const prodRes = await productStore.searchProducts({ keyword: '', page: 1, page_size: 20 });
    products.value = prodRes.data?.list || [];
  } catch {
    products.value = [];
  }

  loading.value = false;
});

const handleSearch = (keyword: string) => {
  uni.navigateTo({
    url: `/pages/searchResults/searchResults?keyword=${encodeURIComponent(keyword)}`
  });
};

const handleHotWordClick = (keyword: string) => {
  handleSearch(keyword);
};

const handleProductClick = (productId: string) => {
  uni.navigateTo({
    url: `/pages/productDetail/productDetail?product_id=${productId}`
  });
};

const handleBannerClick = (banner: any) => {
  if (banner.link_type === 'product') {
    handleProductClick(banner.link_value);
  } else if (banner.link_type === 'search') {
    handleSearch(banner.link_value);
  }
};

const handleCategoryClick = (category: any) => {
  uni.navigateTo({
    url: `/pages/searchResults/searchResults?keyword=${encodeURIComponent(category.name)}`
  });
};
</script>

<template>
  <view class="page">
    <SearchBar v-model="searchKeyword" @search="handleSearch" />

    <!-- Banner 轮播 -->
    <view class="banner-section">
      <swiper class="banner-swiper" autoplay interval="3000" indicator-dots indicator-active-color="#FF6B35" circular>
        <swiper-item v-for="banner in banners" :key="banner.id" @click="handleBannerClick(banner)">
          <image class="banner-image" :src="banner.image_url" mode="aspectFill" />
        </swiper-item>
      </swiper>
    </view>

    <!-- 分类导航 -->
    <view class="category-section">
      <scroll-view class="category-scroll" scroll-x enable-flex>
        <view
          v-for="cat in categories"
          :key="cat.category_id"
          class="category-item"
          @click="handleCategoryClick(cat)"
        >
          <view class="category-icon-box">📦</view>
          <text class="category-name">{{ cat.name }}</text>
        </view>
      </scroll-view>
    </view>

    <!-- 热搜榜 -->
    <view class="section">
      <MoreHeader title="🔥 热搜榜" />
      <view class="hot-words">
        <view
          v-for="(word, index) in hotWords"
          :key="index"
          class="hot-word"
          @click="handleHotWordClick(word.keyword)"
        >
          <text :class="index < 3 ? 'hot-rank-top' : 'hot-rank'">{{ index + 1 }}</text>
          <text class="hot-keyword">{{ word.keyword }}</text>
          <text class="hot-count">{{ word.count }}热度</text>
        </view>
      </view>
    </view>

    <!-- 推荐商品 -->
    <view class="section">
      <MoreHeader title="🛒 为你推荐" />
      <LoadingIndicator v-if="loading" />
      <view v-else class="product-grid">
        <ProductCard
          v-for="product in products"
          :key="product.product_id"
          :product="product"
          @click="handleProductClick"
        />
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 20rpx;
}

.banner-section {
  margin: 20rpx 24rpx;
}

.banner-swiper {
  width: 100%;
  height: 300rpx;
  border-radius: 16rpx;
  overflow: hidden;
}

.banner-image {
  width: 100%;
  height: 100%;
}

.category-section {
  background: white;
  margin: 0 24rpx;
  border-radius: 16rpx;
  padding: 20rpx 0;
}

.category-scroll {
  white-space: nowrap;
  display: flex;
}

.category-item {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding: 0 28rpx;
}

.category-icon-box {
  width: 80rpx;
  height: 80rpx;
  background: #f5f5f5;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  margin-bottom: 8rpx;
}

.category-name {
  font-size: 22rpx;
  color: #666;
}

.section {
  margin: 24rpx;
}

.hot-words {
  background: white;
  border-radius: 16rpx;
  padding: 16rpx 24rpx;
}

.hot-word {
  display: flex;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f5f5f5;

  &:last-child {
    border-bottom: none;
  }
}

.hot-rank {
  width: 40rpx;
  font-size: 24rpx;
  color: #999;
  text-align: center;
  margin-right: 16rpx;
}

.hot-rank-top {
  width: 40rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #FF6B35;
  text-align: center;
  margin-right: 16rpx;
}

.hot-keyword {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.hot-count {
  font-size: 22rpx;
  color: #bbb;
}

.product-grid {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
</style>