<template>
  <view class="search-results-page">
    <view class="search-header">
      <view class="back-btn" @tap="goBack">
        <text class="back-arrow">←</text>
      </view>
      <view class="search-input-wrapper">
        <SearchBar
          v-model="searchText"
          placeholder="搜索商品"
          @search="doSearch"
        />
      </view>
    </view>

    <view class="filter-bar" v-if="results.length > 0">
      <text
        class="filter-item"
        :class="{ active: sortType === 'price_asc' }"
        @tap="setSort('price_asc')"
      >
        价格升序
      </text>
      <text
        class="filter-item"
        :class="{ active: sortType === 'price_desc' }"
        @tap="setSort('price_desc')"
      >
        价格降序
      </text>
      <text
        class="filter-item"
        :class="{ active: sortType === 'sales_desc' }"
        @tap="setSort('sales_desc')"
      >
        销量优先
      </text>
    </view>

    <scroll-view scroll-y class="results-scroll" @scrolltolower="loadMore">
      <view class="results-inner">
        <view class="result-count" v-if="results.length > 0">
          <text>共 {{ totalResults }} 个结果</text>
        </view>

        <view class="product-grid" v-if="results.length > 0">
          <view class="product-grid-item" v-for="product in results" :key="product.product_id">
            <ProductCard
              :product="product"
              @click="goDetail(product.product_id)"
            />
          </view>
        </view>

        <view class="empty-result" v-if="!loading && results.length === 0 && searched">
          <text class="empty-icon">&#128269;</text>
          <text class="empty-text">没有找到相关商品</text>
          <text class="empty-hint">请尝试其他关键词</text>
        </view>

        <view class="loading-more" v-if="loading">
          <text>加载中...</text>
        </view>

        <view class="no-more" v-if="!loading && results.length > 0 && results.length >= totalResults">
          <text>— 已加载全部结果 —</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import SearchBar from '@/components/SearchBar.vue'
import ProductCard from '@/components/ProductCard.vue'
import { api } from '@/api/index'

const searchText = ref('')
const currentKeyword = ref('')
const sortType = ref('price_asc')
const results = ref<any[]>([])
const totalResults = ref(0)
const loading = ref(false)
const searched = ref(false)
const currentPage = ref(1)
const pageSize = 20

onLoad((options: any) => {
  const keyword = options?.keyword || ''
  if (keyword) {
    searchText.value = decodeURIComponent(keyword)
    currentKeyword.value = searchText.value
    doSearch(searchText.value)
  }
})

const doSearch = (keyword?: string) => {
  const kw = (keyword || searchText.value || '').trim()
  if (!kw) return

  searchText.value = kw
  currentKeyword.value = kw
  currentPage.value = 1
  results.value = []
  searched.value = false
  fetchResults()
}

const fetchResults = async () => {
  loading.value = true
  try {
    const res = await api.searchProducts({
      keyword: currentKeyword.value,
      page: currentPage.value,
      page_size: pageSize,
      sort: sortType.value,
    })
    if (res.code === 0 && res.data) {
      if (currentPage.value === 1) {
        results.value = res.data.items || []
      } else {
        results.value = [...results.value, ...(res.data.items || [])]
      }
      totalResults.value = res.data.pagination?.total || 0
    }
    searched.value = true
  } catch (e) {
    console.error('搜索失败:', e)
  } finally {
    loading.value = false
  }
}

const setSort = (sort: string) => {
  if (sortType.value === sort) return
  sortType.value = sort
  currentPage.value = 1
  results.value = []
  fetchResults()
}

const loadMore = () => {
  if (loading.value || results.value.length >= totalResults.value) return
  currentPage.value++
  fetchResults()
}

const goBack = () => {
  uni.navigateBack()
}

const goDetail = (productId: string) => {
  uni.navigateTo({
    url: `/pages/productDetail/productDetail?productId=${productId}`,
  })
}
</script>

<style scoped>
.search-results-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.search-header {
  display: flex;
  align-items: center;
  background: #fff;
  padding: calc(var(--status-bar-height) + 44px) 16rpx 12rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.back-btn {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 8rpx;
}

.back-arrow {
  font-size: 36rpx;
  color: #333;
  font-weight: 300;
}

.search-input-wrapper {
  flex: 1;
}

.search-input-wrapper .search-bar-wrapper {
  padding: 0;
}

.filter-bar {
  display: flex;
  background: #fff;
  padding: 0 20rpx 16rpx;
  gap: 32rpx;
}

.filter-item {
  font-size: 26rpx;
  color: #666;
  padding: 8rpx 0;
  position: relative;
}

.filter-item.active {
  color: #ff6b35;
  font-weight: 600;
}

.filter-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 24rpx;
  height: 4rpx;
  background: #ff6b35;
  border-radius: 2rpx;
}

.results-scroll {
  flex: 1;
}

.results-inner {
  padding: 20rpx;
}

.result-count {
  padding: 8rpx 0 16rpx;
}

.result-count text {
  font-size: 24rpx;
  color: #999;
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

.empty-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 0;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  font-size: 30rpx;
  color: #666;
  margin-bottom: 12rpx;
}

.empty-hint {
  font-size: 24rpx;
  color: #999;
}

.loading-more,
.no-more {
  text-align: center;
  padding: 32rpx 0;
  font-size: 24rpx;
  color: #999;
}
</style>