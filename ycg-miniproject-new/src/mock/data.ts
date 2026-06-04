﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿import type { Product, Platform, HotWord, Favorite, BrowseHistory, User, Category, PriceAlert, SearchRecord } from '../api/types';

export const mockPlatforms: Platform[] = [
  {
    platform_id: 1,
    platform_name: '淘宝',
    platform_code: 'taobao',
    price: 299,
    original_price: 399,
    discount_rate: 75,
    sales_volume: 1200,
    seller_name: '官方旗舰店',
    seller_rating: 4.8,
    product_url: '',
    in_stock: true,
    update_at: new Date().toISOString()
  },
  {
    platform_id: 2,
    platform_name: '京东',
    platform_code: 'jingdong',
    price: 319,
    original_price: 399,
    discount_rate: 80,
    sales_volume: 800,
    seller_name: '京东自营',
    seller_rating: 4.9,
    product_url: '',
    in_stock: true,
    update_at: new Date().toISOString()
  },
  {
    platform_id: 3,
    platform_name: '拼多多',
    platform_code: 'pinduoduo',
    price: 289,
    original_price: 399,
    discount_rate: 72,
    sales_volume: 2000,
    seller_name: '拼多多旗舰店',
    seller_rating: 4.6,
    product_url: '',
    in_stock: true,
    update_at: new Date().toISOString()
  }
];

export const mockProducts: Product[] = [
  {
    product_id: 'prod_001',
    title: '无线蓝牙耳机入耳式降噪运动跑步超长续航',
    category_id: 1,
    category_name: '数码产品',
    image_url: '/static/logo.png',
    images: [
      '/static/logo.png',
      '/static/logo.png'
    ],
    platforms: [...mockPlatforms],
    min_price: 289,
    max_price: 319,
    price_diff: 30,
    best_platform: '拼多多',
    description: '高品质无线蓝牙耳机，支持主动降噪，续航30小时。',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    product_id: 'prod_002',
    title: '智能手表多功能健康监测心率血氧运动',
    category_id: 1,
    category_name: '数码产品',
    image_url: '/static/logo.png',
    images: [],
    platforms: [
      { ...mockPlatforms[0], price: 599, original_price: 799 },
      { ...mockPlatforms[1], price: 579, original_price: 799 },
      { ...mockPlatforms[2], price: 559, original_price: 799 }
    ],
    min_price: 559,
    max_price: 599,
    price_diff: 40,
    best_platform: '拼多多',
    description: '智能手表，支持心率、血氧、睡眠监测。',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    product_id: 'prod_003',
    title: '便携式充电宝20000毫安大容量快充移动电源',
    category_id: 1,
    category_name: '数码产品',
    image_url: '/static/logo.png',
    images: [],
    platforms: [
      { ...mockPlatforms[0], price: 99, original_price: 159 },
      { ...mockPlatforms[1], price: 89, original_price: 159 },
      { ...mockPlatforms[2], price: 79, original_price: 159 }
    ],
    min_price: 79,
    max_price: 99,
    price_diff: 20,
    best_platform: '拼多多',
    description: '20000毫安大容量，支持多设备快充。',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    product_id: 'prod_004',
    title: '纯棉T恤男士夏季圆领纯色百搭打底衫',
    category_id: 2,
    category_name: '服装',
    image_url: '/static/logo.png',
    images: [],
    platforms: [
      { ...mockPlatforms[0], price: 49, original_price: 99 },
      { ...mockPlatforms[1], price: 59, original_price: 99 },
      { ...mockPlatforms[2], price: 39, original_price: 99 }
    ],
    min_price: 39,
    max_price: 59,
    price_diff: 20,
    best_platform: '拼多多',
    description: '100%纯棉面料，舒适透气，多色可选。',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    product_id: 'prod_005',
    title: '运动鞋男士透气跑步鞋减震轻便休闲鞋',
    category_id: 2,
    category_name: '服装',
    image_url: '/static/logo.png',
    images: [],
    platforms: [
      { ...mockPlatforms[0], price: 199, original_price: 399 },
      { ...mockPlatforms[1], price: 219, original_price: 399 },
      { ...mockPlatforms[2], price: 179, original_price: 399 }
    ],
    min_price: 179,
    max_price: 219,
    price_diff: 40,
    best_platform: '拼多多',
    description: '轻便透气，减震设计，适合日常和运动穿着。',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const mockHotWords: HotWord[] = [
  { keyword: '手机', count: 12345, rank: 1 },
  { keyword: '蓝牙耳机', count: 9876, rank: 2 },
  { keyword: 'T恤', count: 8765, rank: 3 },
  { keyword: '运动鞋', count: 7654, rank: 4 },
  { keyword: '充电宝', count: 6543, rank: 5 },
  { keyword: '智能手表', count: 5432, rank: 6 },
  { keyword: '笔记本', count: 4321, rank: 7 },
  { keyword: '键盘', count: 3210, rank: 8 }
];

export const mockUser: User = {
  user_id: 1,
  openid: 'mock_openid_123',
  nick_name: '测试用户',
  avatar_url: '',
  gender: 1,
  province: '广东',
  city: '深圳',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  vip_level: 0
};

export const mockFavorites: Favorite[] = [
  {
    favorite_id: 1,
    user_id: 1,
    product_id: mockProducts[0].product_id,
    product_title: mockProducts[0].title,
    product_image: mockProducts[0].image_url,
    product_min_price: mockProducts[0].min_price,
    notes: '',
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    favorite_id: 2,
    user_id: 1,
    product_id: mockProducts[1].product_id,
    product_title: mockProducts[1].title,
    product_image: mockProducts[1].image_url,
    product_min_price: mockProducts[1].min_price,
    notes: '',
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const mockBrowseHistory: BrowseHistory[] = mockProducts.slice(0, 3).map((product, index) => ({
  history_id: index + 1,
  user_id: 1,
  product_id: product.product_id,
  product_title: product.title,
  product_image: product.image_url,
  viewed_at: new Date(Date.now() - index * 24 * 60 * 60 * 1000).toISOString()
}));

export const mockBanners = [
  { id: 1, image_url: '/static/logo.png', link_type: 'product', link_value: 'prod_001' },
  { id: 2, image_url: '/static/logo.png', link_type: 'product', link_value: 'prod_002' },
  { id: 3, image_url: '/static/logo.png', link_type: 'search', link_value: '手机' }
];

export const mockCategories: Category[] = [
  { category_id: 1, name: '数码产品', parent_id: 0 },
  { category_id: 2, name: '服装鞋帽', parent_id: 0 },
  { category_id: 3, name: '食品饮料', parent_id: 0 },
  { category_id: 4, name: '家居用品', parent_id: 0 },
  { category_id: 5, name: '美妆护肤', parent_id: 0 },
  { category_id: 6, name: '图书文具', parent_id: 0 }
];

export const mockPriceAlerts: PriceAlert[] = [
  { alert_id: 1, user_id: 1, product_id: 'prod_001', product_title: '无线蓝牙耳机入耳式降噪运动跑步超长续航', target_price: 250, current_price: 289, is_triggered: false, is_enabled: true, created_at: new Date(Date.now() - 5 * 86400000).toISOString(), updated_at: new Date().toISOString() },
  { alert_id: 2, user_id: 1, product_id: 'prod_002', product_title: '智能手表多功能健康监测心率血氧运动', target_price: 500, current_price: 559, is_triggered: false, is_enabled: true, created_at: new Date(Date.now() - 3 * 86400000).toISOString(), updated_at: new Date().toISOString() },
  { alert_id: 3, user_id: 1, product_id: 'prod_005', product_title: '运动鞋男士透气跑步鞋减震轻便休闲鞋', target_price: 150, current_price: 179, is_triggered: false, is_enabled: true, created_at: new Date(Date.now() - 7 * 86400000).toISOString(), updated_at: new Date().toISOString() }
];

export const mockSearchRecords: SearchRecord[] = [
  { record_id: 1, user_id: 1, keyword: '蓝牙耳机', search_count: 5, created_at: new Date(Date.now() - 7 * 86400000).toISOString(), updated_at: new Date().toISOString() },
  { record_id: 2, user_id: 1, keyword: '手机', search_count: 3, created_at: new Date(Date.now() - 5 * 86400000).toISOString(), updated_at: new Date().toISOString() },
  { record_id: 3, user_id: 1, keyword: '运动鞋', search_count: 2, created_at: new Date(Date.now() - 2 * 86400000).toISOString(), updated_at: new Date().toISOString() }
];

export const mockPriceTrend = [
  { date: '2026-04-20', price: 319 },
  { date: '2026-04-21', price: 309 },
  { date: '2026-04-22', price: 299 },
  { date: '2026-04-23', price: 305 },
  { date: '2026-04-24', price: 295 },
  { date: '2026-04-25', price: 289 },
  { date: '2026-04-26', price: 289 }
];

export const mockProductReviews = [
  { review_id: 1, user_name: '小明', rating: 5, content: '非常好用，比价功能很实用！', created_at: new Date(Date.now() - 2 * 86400000).toISOString() },
  { review_id: 2, user_name: '小红', rating: 4, content: '质量不错，物流很快。', created_at: new Date(Date.now() - 5 * 86400000).toISOString() },
  { review_id: 3, user_name: '张三', rating: 5, content: '性价比很高，推荐购买。', created_at: new Date(Date.now() - 7 * 86400000).toISOString() }
];
