import { defineStore } from 'pinia';
import { ref } from 'vue';
import { productApi, searchApi, browseHistoryApi, analyticsApi } from '../api';
import type { Product, SearchParams, HotWord, Pagination } from '../api/types';

export const useProductStore = defineStore('product', () => {
  const searchResults = ref<Product[]>([]);
  const currentProduct = ref<Product | null>(null);
  const hotWords = ref<HotWord[]>([]);
  const loading = ref(false);
  const pagination = ref<Pagination>({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false
  });

  const searchProducts = async (params: SearchParams) => {
    loading.value = true;
    try {
      const res = await productApi.search(params);
      
      if (params.page === 1) {
        searchResults.value = res.data.list;
      } else {
        searchResults.value = [...searchResults.value, ...res.data.list];
      }
      
      pagination.value = res.data.pagination;
      
      // 上报搜索事件
      try {
        analyticsApi.track({
          event_type: 'search',
          timestamp: new Date().toISOString(),
          metadata: { keyword: params.keyword }
        });
      } catch (e) {
        console.error('上报搜索事件失败:', e);
      }
      
      return res;
    } finally {
      loading.value = false;
    }
  };

  const getProductDetail = async (product_id: string) => {
    loading.value = true;
    try {
      const res = await productApi.detail(product_id);
      currentProduct.value = res.data;
      
      // 添加浏览历史
      try {
        browseHistoryApi.add({ product_id });
        
        // 上报商品点击事件
        analyticsApi.track({
          event_type: 'product_click',
          product_id,
          timestamp: new Date().toISOString()
        });
      } catch (e) {
        console.error('添加浏览历史失败:', e);
      }
      
      return res;
    } finally {
      loading.value = false;
    }
  };

  const getHotWords = async (limit = 10) => {
    try {
      const res = await searchApi.hotWords(limit);
      hotWords.value = res.data;
      return res;
    } catch (error) {
      console.error('获取热搜词失败:', error);
      throw error;
    }
  };

  const clearSearchResults = () => {
    searchResults.value = [];
    pagination.value = {
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
      has_next: false,
      has_prev: false
    };
  };

  return {
    searchResults,
    currentProduct,
    hotWords,
    loading,
    pagination,
    searchProducts,
    getProductDetail,
    getHotWords,
    clearSearchResults
  };
});
