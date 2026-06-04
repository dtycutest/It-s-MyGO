import { mockProducts, mockHotWords, mockUser, mockFavorites, mockBrowseHistory, mockBanners, mockPriceAlerts, mockSearchRecords, mockPriceTrend, mockProductReviews } from './data';
import type {
  ApiResponse, PaginatedResponse,
  Product, HotWord, User, LoginResponse,
  Favorite, PriceAlert, BrowseHistory, SearchRecord
} from '../api/types';

const delay = (ms: number = 300) => new Promise(resolve => setTimeout(resolve, ms));

export const mockApi = {
  async authLogin(code: string): Promise<ApiResponse<LoginResponse>> {
    await delay(500);
    return {
      code: 0,
      message: 'success',
      data: {
        access_token: 'mock_access_token_' + Date.now(),
        refresh_token: 'mock_refresh_token_' + Date.now(),
        expires_in: 7200,
        user_id: 1,
        openid: 'mock_openid_123',
        nick_name: mockUser.nick_name,
        avatar_url: mockUser.avatar_url
      }
    };
  },

  async authLogout(): Promise<ApiResponse<null>> {
    await delay(200);
    return { code: 0, message: 'success', data: null };
  },

  async productSearch(params: {
    keyword: string;
    page?: number;
    page_size?: number;
  }): Promise<ApiResponse<PaginatedResponse<Product>>> {
    await delay(600);
    const page = params.page || 1;
    const pageSize = params.page_size || 20;
    
    let filteredProducts = [...mockProducts];
    
    if (params.keyword) {
      const kw = params.keyword.toLowerCase();
      filteredProducts = mockProducts.filter(p => 
        p.title.toLowerCase().includes(kw) || 
        p.category_name.includes(kw)
      );
    }
    
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const list = filteredProducts.slice(start, end);
    
    return {
      code: 0,
      message: 'success',
      data: {
        list,
        pagination: {
          page,
          page_size: pageSize,
          total: filteredProducts.length,
          total_pages: Math.ceil(filteredProducts.length / pageSize),
          has_next: end < filteredProducts.length,
          has_prev: page > 1
        }
      }
    };
  },

  async productDetail(productId: string): Promise<ApiResponse<Product>> {
    await delay(400);
    const product = mockProducts.find(p => p.product_id === productId) || mockProducts[0];
    return {
      code: 0,
      message: 'success',
      data: product
    };
  },

  async productCategories(parentId = 0): Promise<ApiResponse<any[]>> {
    await delay(200);
    return {
      code: 0,
      message: 'success',
      data: [
        { category_id: 1, name: '数码产品', parent_id: parentId },
        { category_id: 2, name: '服装', parent_id: parentId },
        { category_id: 3, name: '食品', parent_id: parentId },
        { category_id: 4, name: '家居', parent_id: parentId }
      ]
    };
  },

  async searchHotWords(limit = 10): Promise<ApiResponse<HotWord[]>> {
    await delay(300);
    return {
      code: 0,
      message: 'success',
      data: mockHotWords.slice(0, limit)
    };
  },

  async userGetProfile(): Promise<ApiResponse<User>> {
    await delay(300);
    return {
      code: 0,
      message: 'success',
      data: mockUser
    };
  },

  async userUpdateProfile(data: any): Promise<ApiResponse<User>> {
    await delay(300);
    return {
      code: 0,
      message: 'success',
      data: { ...mockUser, ...data }
    };
  },

  async favoriteList(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<Favorite>>> {
    await delay(300);
    return {
      code: 0,
      message: 'success',
      data: {
        list: mockFavorites,
        pagination: {
          page,
          page_size: pageSize,
          total: mockFavorites.length,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      }
    };
  },

  async favoriteAdd(data: { product_id: string; notes?: string }): Promise<ApiResponse<Favorite>> {
    await delay(300);
    const product = mockProducts.find(p => p.product_id === data.product_id) || mockProducts[0];
    const newFavorite: Favorite = {
      favorite_id: Date.now(),
      user_id: 1,
      product_id: data.product_id,
      product_title: product.title,
      product_image: product.image_url,
      product_min_price: product.min_price,
      notes: data.notes || '',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    return {
      code: 0,
      message: 'success',
      data: newFavorite
    };
  },

  async favoriteDelete(favoriteId: number): Promise<ApiResponse<null>> {
    await delay(300);
    return {
      code: 0,
      message: 'success',
      data: null
    };
  },

  async priceAlertList(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<PriceAlert>>> {
    await delay(300);
    return {
      code: 0,
      message: 'success',
      data: {
        list: mockPriceAlerts,
        pagination: {
          page,
          page_size: pageSize,
          total: mockPriceAlerts.length,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      }
    };
  },

  async browseHistoryList(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<BrowseHistory>>> {
    await delay(300);
    return {
      code: 0,
      message: 'success',
      data: {
        list: mockBrowseHistory,
        pagination: {
          page,
          page_size: pageSize,
          total: mockBrowseHistory.length,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      }
    };
  },

  async browseHistoryAdd(data: { product_id: string }): Promise<ApiResponse<null>> {
    await delay(200);
    return {
      code: 0,
      message: 'success',
      data: null
    };
  },

  async searchRecordList(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<SearchRecord>>> {
    await delay(300);
    return {
      code: 0,
      message: 'success',
      data: {
        list: mockSearchRecords,
        pagination: {
          page,
          page_size: pageSize,
          total: mockSearchRecords.length,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      }
    };
  },

  async recommendationPersonalized(page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<Product>>> {
    await delay(400);
    return {
      code: 0,
      message: 'success',
      data: {
        list: mockProducts.slice(0, pageSize),
        pagination: {
          page,
          page_size: pageSize,
          total: mockProducts.length,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      }
    };
  },

  async analyticsTrack(data: any): Promise<ApiResponse<null>> {
    await delay(100);
    console.log('[Analytics] Track event:', data);
    return {
      code: 0,
      message: 'success',
      data: null
    };
  },

  async getBanners(): Promise<ApiResponse<any[]>> {
    await delay(300);
    return {
      code: 0,
      message: 'success',
      data: mockBanners
    };
  },

  async getPriceTrend(productId: string): Promise<ApiResponse<any[]>> {
    await delay(400);
    return {
      code: 0,
      message: 'success',
      data: mockPriceTrend
    };
  },

  async getProductReviews(productId: string, page = 1, pageSize = 20): Promise<ApiResponse<PaginatedResponse<any>>> {
    await delay(300);
    const reviews = mockProductReviews;
    return {
      code: 0,
      message: 'success',
      data: {
        list: reviews,
        pagination: {
          page,
          page_size: pageSize,
          total: reviews.length,
          total_pages: 1,
          has_next: false,
          has_prev: false
        }
      }
    };
  },

  async searchRecordAdd(data: { keyword: string }): Promise<ApiResponse<null>> {
    await delay(200);
    return {
      code: 0,
      message: 'success',
      data: null
    };
  },

  async searchRecordClear(): Promise<ApiResponse<null>> {
    await delay(200);
    return {
      code: 0,
      message: 'success',
      data: null
    };
  }
};
