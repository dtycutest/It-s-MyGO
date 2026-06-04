import { defineStore } from 'pinia';
import { ref } from 'vue';
import { favoriteApi } from '../api';
import type { Favorite } from '../api/types';

export const useFavoriteStore = defineStore('favorite', () => {
  const favorites = ref<Favorite[]>([]);
  const loading = ref(false);

  const fetchFavorites = async (page = 1, pageSize = 20) => {
    loading.value = true;
    try {
      const res = await favoriteApi.list(page, pageSize);
      favorites.value = res.data.list;
      return res;
    } finally {
      loading.value = false;
    }
  };

  const addFavorite = async (productId: string) => {
    const res = await favoriteApi.add({ product_id: productId });
    favorites.value.unshift(res.data);
    return res;
  };

  const removeFavorite = async (favoriteId: number) => {
    await favoriteApi.remove(favoriteId);
    favorites.value = favorites.value.filter(f => f.favorite_id !== favoriteId);
  };

  return { favorites, loading, fetchFavorites, addFavorite, removeFavorite };
});