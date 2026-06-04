<template>
  <view class="home-page">
    <view class="search-section">
      <SearchBar
        v-model="searchKeyword"
        placeholder="搜索商品"
        @search="goSearch"
      />
    </view>

    <scroll-view scroll-y class="content-scroll">
      <view class="content-inner">
        <view class="hot-words-section" v-if="hotWords.length > 0">
          <view class="section-title">
            <text class="title-text">热门搜索</text>
          </view>
          <view class="hot-words-list">
            <text
              v-for="(word, index) in hotWords"
              :key="index"
              class="hot-word-tag"
              :class="{ 'hot-word-1': index === 0, 'hot-word-2': index === 1, 'hot-word-3': index === 2 }"
              @tap="onHotWordClick(word.keyword || '')"
            >
              {{ word.keyword || '' }}
            </text>
          </view>
        </view>

        <view class="recommend-section">
          <view class="section-title">
            <text class="title-text">为你推荐</text>
            <text class="refresh-tip" @tap="refreshRecommend">换一批</text>
          </view>
          <view class="product-grid">
            <view class="product-grid-item" v-for="product in recommendProducts" :key="product.product_id">
              <ProductCard
                :product="product"
                @click="goDetail(product.product_id)"
              />
            </view>
          </view>
          <view class="load-more" v-if="recommendProducts.length === 0">
            <text>加载中...</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import SearchBar from '@/components/SearchBar.vue'
import ProductCard from '@/components/ProductCard.vue'
import { api } from '@/api/index'

const searchKeyword = ref('')
const hotWords = ref<{ keyword: string; count: number }[]>([])
const recommendProducts = ref<any[]>([])

const fetchHotWords = async () => {
  try {
    const res = await api.getHotWords()
    if (res.code === 0 && res.data) {
      hotWords.value = res.data as any[]
    }
  } catch (e) {
    console.error('获取热搜词失败:', e)
  }
}

const fetchRecommend = async () => {
  try {
    const res = await api.getRecommendProducts(1, 20)
    if (res.code === 0 && res.data) {
      recommendProducts.value = res.data.items || []
    }
  } catch (e) {
    console.error('获取推荐失败:', e)
  }
}

const refreshRecommend = () => {
  fetchRecommend()
}

const goSearch = (keyword: string) => {
  if (!keyword.trim()) return
  uni.navigateTo({
    url: `/pages/searchResults/searchResults?keyword=${encodeURIComponent(keyword.trim())}`,
  })
}

const onHotWordClick = (keyword: string) => {
  if (!keyword || !keyword.trim()) return
  uni.navigateTo({
    url: `/pages/searchResults/searchResults?keyword=${encodeURIComponent(keyword.trim())}`,
  })
}

const goDetail = (productId: string) => {
  uni.navigateTo({
    url: `/pages/productDetail/productDetail?productId=${productId}`,
  })
}

const onRefresh = () => {
  fetchHotWords()
  fetchRecommend()
}

onMounted(() => {
  fetchHotWords()
  fetchRecommend()
})
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.search-section {
  background: linear-gradient(135deg, #ff6b35, #ff4500);
  padding: calc(var(--status-bar-height) + 44px) 0 20rpx;
}

.search-section .search-bar-wrapper {
  background: transparent;
}

.content-scroll {
  flex: 1;
}

.content-inner {
  padding: 20rpx;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8rpx 16rpx;
}

.title-text {
  font-size: 32rpx;
  font-weight: 700;
  color: #333;
  position: relative;
  padding-left: 28rpx;
}

.title-text::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 6rpx;
  height: 28rpx;
  background: linear-gradient(180deg, #ff6b35, #ff4500);
  border-radius: 3rpx;
}

.refresh-tip {
  font-size: 24rpx;
  color: #ff6b35;
  padding: 8rpx 16rpx;
}

.hot-words-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
}

.hot-words-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.hot-word-tag {
  display: inline-block;
  padding: 10rpx 24rpx;
  background: #f5f5f5;
  border-radius: 28rpx;
  font-size: 26rpx;
  color: #666;
}

.hot-word-1,
.hot-word-2,
.hot-word-3 {
  color: #ff6b35;
  font-weight: 600;
  background: #fff5f0;
}

.recommend-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 20rpx;
}

.product-grid {
  display: flex;
  flex-wrap: wrap;
}

.product-grid-item {
  width: 50%;
  box-sizing: border-box;
  padding: 8rpx;
}

.load-more {
  text-align: center;
  padding: 40rpx 0;
  color: #999;
  font-size: 26rpx;
}
</style>