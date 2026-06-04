import { mockApi } from '../mock';
import request from '../utils/request';
import type {
  ApiResponse, PaginatedResponse,
  Product, SearchParams, Category, HotWord,
  User, LoginRequest, LoginResponse, UpdateUserRequest,
  Favorite, AddFavoriteRequest, UpdateFavoriteRequest,
  PriceAlert, CreatePriceAlertRequest, UpdatePriceAlertRequest,
  BrowseHistory, AddBrowseHistoryRequest,
  SearchRecord,
  TrackEventRequest,
} from './types';

// 是否使用 Mock 数据（开发时设为 true）
const USE_MOCK = false;

// ============ 认证 API ============
export const authApi = {
  login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    if (USE_MOCK) {
      return mockApi.authLogin(data.code);
    }
    return request.post('/auth/login', data);
  },
  
  refresh(refresh_token: string): Promise<ApiResponse<{ access_token: string; refresh_token: string; expires_in: number }>> {
    if (USE_MOCK) {
      return mockApi.authLogin('').then(res => ({
        ...res,
        data: {
          access_token: res.data.access_token,
          refresh_token: res.data.refresh_token,
          expires_in: res.data.expires_in
        }
      }));
    }
    return request.post('/auth/refresh', { refresh_token });
  },
  
  logout(): Promise<ApiResponse<null>> {
    if (USE_MOCK) {
      return mockApi.authLogout();
    }
    return request.post('/auth/logout');
  }
};

// ============ 商品 API ============
export const productApi = {
  search(params: SearchParams): Promise<ApiResponse<PaginatedResponse<Product>>> {
    if (USE_MOCK) {
      return mockApi.productSearch(params);
    }
    return request.get('/products/search', { params });
  },
  
  detail(product_id: string): Promise<ApiResponse<Product>> {
    if (USE_MOCK) {
      return mockApi.productDetail(product_id);
    }
    return request.get(`/products/${product_id}`);
  },
  
  categories(parent_id = 0): Promise<ApiResponse<Category[]>> {
    if (USE_MOCK) {
      return mockApi.productCategories(parent_id);
    }
    return request.get('/products/categories', { params: { parent_id } });
  }
};

// ============ 搜索 API ============
export const searchApi = {
  hotWords(limit = 10): Promise<ApiResponse<HotWord[]>> {
    if (USE_MOCK) {
      return mockApi.searchHotWords(limit);
    }
    return request.get('/search/hot-words', { params: { limit } });
  }
};

// ============ 用户 API ============
export const userApi = {
  getProfile(): Promise<ApiResponse<User>> {
    if (USE_MOCK) {
      return mockApi.userGetProfile();
    }
    return request.get('/users/profile');
  },
  
  updateProfile(data: UpdateUserRequest): Promise<ApiResponse<User>> {
    if (USE_MOCK) {
      return mockApi.userUpdateProfile(data);
    }
    return request.put('/users/profile', data);
  }
};

// ============ 收藏 API ============
export const favoriteApi = {
  list(page = 1, page_size = 20): Promise<ApiResponse<PaginatedResponse<Favorite>>> {
    if (USE_MOCK) {
      return mockApi.favoriteList(page, page_size);
    }
    return request.get('/users/favorites', { params: { page, page_size } });
  },
  
  add(data: AddFavoriteRequest): Promise<ApiResponse<Favorite>> {
    if (USE_MOCK) {
      return mockApi.favoriteAdd(data);
    }
    return request.post('/users/favorites', data);
  },
  
  update(favorite_id: number, data: UpdateFavoriteRequest): Promise<ApiResponse<Favorite>> {
    if (USE_MOCK) {
      return mockApi.favoriteAdd({ product_id: String(favorite_id), ...data });
    }
    return request.put(`/users/favorites/${favorite_id}`, data);
  },
  
  remove(favorite_id: number): Promise<ApiResponse<null>> {
    if (USE_MOCK) {
      return mockApi.favoriteDelete(favorite_id);
    }
    return request.delete(`/users/favorites/${favorite_id}`);
  }
};

// ============ 降价提醒 API ============
export const priceAlertApi = {
  list(page = 1, page_size = 20, status: 'all' | 'triggered' | 'untriggered' = 'all'): Promise<ApiResponse<PaginatedResponse<PriceAlert>>> {
    if (USE_MOCK) {
      return mockApi.priceAlertList(page, page_size);
    }
    return request.get('/users/price-alerts', { params: { page, page_size, status } });
  },
  
  create(data: CreatePriceAlertRequest): Promise<ApiResponse<PriceAlert>> {
    if (USE_MOCK) {
      return mockApi.priceAlertList(1, 1).then(res => ({
        ...res,
        data: res.data.items[0] || {} as PriceAlert
      }));
    }
    return request.post('/users/price-alerts', data);
  },
  
  update(alert_id: number, data: UpdatePriceAlertRequest): Promise<ApiResponse<PriceAlert>> {
    if (USE_MOCK) {
      return mockApi.priceAlertList(1, 1).then(res => ({
        ...res,
        data: { ...res.data.items[0], ...data } as PriceAlert
      }));
    }
    return request.put(`/users/price-alerts/${alert_id}`, data);
  },
  
  delete(alert_id: number): Promise<ApiResponse<null>> {
    if (USE_MOCK) {
      return mockApi.favoriteDelete(alert_id);
    }
    return request.delete(`/users/price-alerts/${alert_id}`);
  }
};

// ============ 浏览历史 API ============
export const browseHistoryApi = {
  list(page = 1, page_size = 20): Promise<ApiResponse<PaginatedResponse<BrowseHistory>>> {
    if (USE_MOCK) {
      return mockApi.browseHistoryList(page, page_size);
    }
    return request.get('/users/browse-history', { params: { page, page_size } });
  },
  
  add(data: AddBrowseHistoryRequest): Promise<ApiResponse<null>> {
    if (USE_MOCK) {
      return mockApi.browseHistoryAdd(data);
    }
    return request.post('/users/browse-history', data);
  },
  
  clear(): Promise<ApiResponse<null>> {
    if (USE_MOCK) {
      return mockApi.favoriteDelete(0);
    }
    return request.delete('/users/browse-history');
  }
};

// ============ 搜索记录 API ============
export const searchRecordApi = {
  list(page = 1, page_size = 20): Promise<ApiResponse<PaginatedResponse<SearchRecord>>> {
    if (USE_MOCK) {
      return mockApi.searchRecordList(page, page_size);
    }
    return request.get('/users/search-records', { params: { page, page_size } });
  }
};

// ============ 推荐 API ============
export const recommendationApi = {
  personalized(page = 1, page_size = 20): Promise<ApiResponse<PaginatedResponse<Product>>> {
    if (USE_MOCK) {
      return mockApi.recommendationPersonalized(page, page_size);
    }
    return request.get('/recommendations/personalized', { params: { page, page_size } });
  }
};

// ============ 分析 API ============
export const analyticsApi = {
  track(data: TrackEventRequest): Promise<ApiResponse<null>> {
    if (USE_MOCK) {
      return mockApi.analyticsTrack(data);
    }
    return request.post('/analytics/events', data);
  }
};

// ============ 统一导出 ============
export const api = {
  login: authApi.login,
  refresh: authApi.refresh,
  logout: authApi.logout,
  searchProducts: productApi.search,
  getProductDetail: productApi.detail,
  getCategories: productApi.categories,
  getHotWords: searchApi.hotWords,
  getRecommendProducts: recommendationApi.personalized,
  getUserProfile: userApi.getProfile,
  updateUserProfile: userApi.updateProfile,
  getFavorites: favoriteApi.list,
  addFavorite: favoriteApi.add,
  updateFavorite: favoriteApi.update,
  removeFavorite: favoriteApi.remove,
  getPriceAlerts: priceAlertApi.list,
  createPriceAlert: priceAlertApi.create,
  updatePriceAlert: priceAlertApi.update,
  deletePriceAlert: priceAlertApi.delete,
  getBrowseHistory: browseHistoryApi.list,
  addBrowseHistory: browseHistoryApi.add,
  clearBrowseHistory: browseHistoryApi.clear,
  getSearchRecords: searchRecordApi.list,
  trackEvent: analyticsApi.track,
};
