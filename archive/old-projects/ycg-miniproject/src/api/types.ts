// ============ 基础类型 ============
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse<T> {
  list: T[];
  pagination: Pagination;
}

// ============ 平台相关 ============
export type PlatformCode = 'taobao' | 'jingdong' | 'pinduoduo' | 'amazon' | 'other';
export type PlatformName = '淘宝' | '京东' | '拼多多' | '亚马逊' | '其他';

export interface Platform {
  platform_id: number;
  platform_name: PlatformName;
  platform_code: PlatformCode;
  price: number;
  original_price?: number;
  discount_rate?: number;
  sales_volume?: number;
  seller_name?: string;
  seller_rating?: number;
  seller_id?: string;
  product_url: string;
  in_stock: boolean;
  stock_quantity?: number;
  update_at: string;
}

// ============ 商品相关 ============
export interface Product {
  product_id: string;
  title: string;
  category_id: number;
  category_name: string;
  image_url: string;
  images?: string[];
  platforms: Platform[];
  min_price: number;
  max_price: number;
  price_diff: number;
  best_platform: string;
  description?: string;
  specs?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface SearchParams {
  keyword: string;
  page?: number;
  page_size?: number;
  category_id?: number;
  min_price?: number;
  max_price?: number;
  platform?: string;
  sort?: 'price_asc' | 'price_desc' | 'sales_desc' | 'rating_desc';
}

export interface Category {
  category_id: number;
  name: string;
  parent_id: number;
  children?: Category[];
}

export interface HotWord {
  keyword: string;
  count: number;
  rank: number;
}

// ============ 用户相关 ============
export interface User {
  user_id: number;
  openid: string;
  nick_name: string;
  avatar_url: string;
  gender?: number;
  province?: string;
  city?: string;
  created_at: string;
  updated_at: string;
  vip_level: number;
  vip_expire_at?: string;
}

export interface LoginRequest {
  code: string;
  raw_data: string;
  signature: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user_id: number;
  openid: string;
  nick_name?: string;
  avatar_url?: string;
}

export interface UpdateUserRequest {
  nick_name?: string;
  avatar_url?: string;
  gender?: number;
}

// ============ 收藏相关 ============
export interface Favorite {
  favorite_id: number;
  user_id: number;
  product_id: string;
  product_title: string;
  product_image: string;
  product_min_price: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface AddFavoriteRequest {
  product_id: string;
  notes?: string;
}

export interface UpdateFavoriteRequest {
  notes: string;
}

// ============ 降价提醒相关 ============
export interface PriceAlert {
  alert_id: number;
  user_id: number;
  product_id: string;
  product_title: string;
  target_price: number;
  current_price: number;
  is_triggered: boolean;
  triggered_at?: string;
  is_enabled: boolean;
  platform_filter?: string[];
  created_at: string;
  updated_at: string;
}

export interface CreatePriceAlertRequest {
  product_id: string;
  target_price: number;
  platform_filter?: string[];
}

export interface UpdatePriceAlertRequest {
  target_price?: number;
  is_enabled?: boolean;
}

// ============ 浏览历史 ============
export interface BrowseHistory {
  history_id: number;
  user_id: number;
  product_id: string;
  product_title: string;
  product_image: string;
  viewed_at: string;
}

export interface AddBrowseHistoryRequest {
  product_id: string;
}

// ============ 搜索记录 ============
export interface SearchRecord {
  record_id: number;
  user_id: number;
  keyword: string;
  search_count: number;
  created_at: string;
  updated_at: string;
}

// ============ 事件上报 ============
export type EventType = 'search' | 'product_click' | 'add_favorite' | 'remove_favorite' | 'alert_set' | 'purchase_redirect';

export interface TrackEventRequest {
  event_type: EventType;
  product_id?: string;
  platform?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}
