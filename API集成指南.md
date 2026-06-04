# "一次买够"小程序 API集成指南

## 一、API基础配置

### 1.1 HTTP请求工具封装

创建文件 `src/utils/request.js`：

```javascript
// HTTP请求基础配置和拦截器
import axios from 'axios'
import { getToken, setToken } from './auth'
import storage from './storage'

// API基础URL配置
const API_BASE_URL = process.env.VUE_APP_API_URL || 'https://api.ycg.com'
const API_VERSION = '/api/v1'
const FULL_API_URL = API_BASE_URL + API_VERSION

// 创建axios实例
const request = axios.create({
  baseURL: FULL_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加认证令牌
request.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一处理响应
request.interceptors.response.use(
  response => {
    const { data } = response
    
    // 检查业务错误码
    if (data.code === 0) {
      return data
    } else if (data.code === 401) {
      // Token过期，跳转到登录页
      clearAuth()
      uni.navigateTo({ url: '/pages/login/login' })
      return Promise.reject(new Error(data.message))
    } else {
      // 其他业务错误
      return Promise.reject(new Error(data.message || '请求失败'))
    }
  },
  error => {
    // 网络错误处理
    if (error.response) {
      switch (error.response.status) {
        case 400:
          console.error('参数错误')
          break
        case 401:
          console.error('未授权，请登录')
          break
        case 403:
          console.error('禁止访问')
          break
        case 404:
          console.error('资源不存在')
          break
        case 429:
          console.error('请求过于频繁')
          break
        case 500:
          console.error('服务器错误')
          break
        default:
          console.error('未知错误')
      }
    } else if (error.request) {
      console.error('网络连接错误')
    } else {
      console.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

// 防抖装饰器 - 防止重复请求
const requestMap = new Map()

export function debounceRequest(fn, delay = 500) {
  return async function(...args) {
    const key = fn.name + JSON.stringify(args)
    
    if (requestMap.has(key)) {
      return requestMap.get(key)
    }
    
    const promise = fn.apply(this, args)
    requestMap.set(key, promise)
    
    setTimeout(() => {
      requestMap.delete(key)
    }, delay)
    
    return promise
  }
}

export default request
```

### 1.2 环境配置

创建文件 `.env.example`：

```
# API配置
VUE_APP_API_URL=https://api.ycg.com
VUE_APP_API_TIMEOUT=30000

# 微信配置
VUE_APP_WECHAT_APPID=your_wechat_appid
VUE_APP_WECHAT_SECRET=your_wechat_secret

# 功能开关
VUE_APP_ENABLE_DEBUG=false
VUE_APP_ENABLE_ANALYTICS=true
```

创建文件 `.env.development`：

```
VUE_APP_API_URL=https://dev-api.ycg.com
VUE_APP_API_TIMEOUT=30000
VUE_APP_ENABLE_DEBUG=true
VUE_APP_ENABLE_ANALYTICS=false
```

创建文件 `.env.production`：

```
VUE_APP_API_URL=https://api.ycg.com
VUE_APP_API_TIMEOUT=30000
VUE_APP_ENABLE_DEBUG=false
VUE_APP_ENABLE_ANALYTICS=true
```

---

## 二、API管理模块

### 2.1 用户相关API

创建文件 `src/api/user.js`：

```javascript
import request, { debounceRequest } from '@/utils/request'

// 微信授权登录
export function wechatLogin(payload) {
  return request.post('/auth/wechat-login', {
    code: payload.code,
    encryptedData: payload.encryptedData,
    iv: payload.iv
  })
}

// 获取用户信息
export function getUserProfile() {
  return request.get('/user/profile')
}

// 更新用户信息
export function updateUserProfile(payload) {
  return request.put('/user/profile', payload)
}

// 账户登出
export function logout() {
  return request.post('/auth/logout')
}

// 刷新Token
export function refreshToken() {
  return request.post('/auth/refresh-token')
}

// 检验Token有效性
export function validateToken() {
  return request.get('/auth/validate-token')
}
```

### 2.2 商品相关API

创建文件 `src/api/product.js`：

```javascript
import request, { debounceRequest } from '@/utils/request'

// 搜索商品 (带防抖)
const _searchProducts = async (keyword, params) => {
  return request.get('/products/search', {
    params: {
      keyword,
      ...params
    }
  })
}

export const searchProducts = debounceRequest(_searchProducts, 500)

// 获取热搜榜
export function getTrendingKeywords(limit = 10) {
  return request.get('/products/trends', {
    params: { limit }
  })
}

// 获取商品详情
export function getProductDetail(productId) {
  return request.get(`/products/${productId}`)
}

// 获取价格走势数据
export function getPriceHistory(productId, days = 30) {
  return request.get(`/products/${productId}/price-history`, {
    params: { days }
  })
}

// 获取分类列表
export function getCategories(level = 1) {
  return request.get('/categories', {
    params: { level }
  })
}

// 获取分类下的商品
export function getCategoryProducts(categoryId, params) {
  return request.get(`/categories/${categoryId}/products`, {
    params
  })
}
```

### 2.3 收藏相关API

创建文件 `src/api/favorite.js`：

```javascript
import request from '@/utils/request'

// 获取收藏列表
export function getFavorites(pageNum = 1, pageSize = 20) {
  return request.get('/favorites', {
    params: { pageNum, pageSize }
  })
}

// 添加到收藏
export function addFavorite(productId) {
  return request.post('/favorites', { productId })
}

// 取消收藏
export function removeFavorite(favoriteId) {
  return request.delete(`/favorites/${favoriteId}`)
}

// 批量取消收藏
export function removeFavoritesBatch(favoriteIds) {
  return request.post('/favorites/batch-remove', { favoriteIds })
}

// 检查商品是否已收藏
export function isFavorited(productId) {
  return request.get(`/favorites/check/${productId}`)
}
```

### 2.4 降价提醒API

创建文件 `src/api/alert.js`：

```javascript
import request from '@/utils/request'

// 获取降价提醒列表
export function getPriceAlerts(status = 'active') {
  return request.get('/price-alerts', {
    params: { status }
  })
}

// 创建降价提醒
export function createPriceAlert(payload) {
  return request.post('/price-alerts', {
    productId: payload.productId,
    targetPrice: payload.targetPrice,
    alertType: payload.alertType || 'price_drop'
  })
}

// 更新降价提醒
export function updatePriceAlert(alertId, payload) {
  return request.put(`/price-alerts/${alertId}`, payload)
}

// 删除降价提醒
export function deletePriceAlert(alertId) {
  return request.delete(`/price-alerts/${alertId}`)
}

// 启用/禁用降价提醒
export function togglePriceAlert(alertId, enabled) {
  return request.patch(`/price-alerts/${alertId}/toggle`, { enabled })
}
```

### 2.5 浏览历史API

创建文件 `src/api/history.js`：

```javascript
import request from '@/utils/request'

// 获取浏览历史
export function getHistory(pageNum = 1, pageSize = 20) {
  return request.get('/history', {
    params: { pageNum, pageSize }
  })
}

// 添加浏览记录
export function addHistory(productId, duration = 0) {
  return request.post('/history', {
    productId,
    duration
  })
}

// 删除单条历史
export function deleteHistory(historyId) {
  return request.delete(`/history/${historyId}`)
}

// 清空浏览历史
export function clearHistory() {
  return request.delete('/history')
}

// 获取历史统计
export function getHistoryStats() {
  return request.get('/history/stats')
}
```

---

## 三、API调用示例

### 3.1 搜索功能实现

```javascript
// pages/searchResults/searchResults.vue
import { searchProducts } from '@/api/product'
import { addHistory } from '@/api/history'

export default {
  data() {
    return {
      keyword: '',
      products: [],
      pageNum: 1,
      pageSize: 20,
      hasMore: true,
      loading: false,
      filters: {
        priceMin: null,
        priceMax: null,
        platforms: [],
        rating: 0
      }
    }
  },
  
  methods: {
    // 执行搜索
    async handleSearch() {
      if (!this.keyword.trim()) {
        this.$toast.warning('请输入搜索关键词')
        return
      }
      
      this.pageNum = 1
      this.products = []
      this.loading = true
      
      try {
        const response = await searchProducts(
          this.keyword,
          {
            pageNum: this.pageNum,
            pageSize: this.pageSize,
            ...this.filters
          }
        )
        
        this.products = response.data.list
        this.hasMore = this.pageNum < response.data.totalPages
        this.$toast.success('搜索完成')
        
      } catch (error) {
        this.$toast.error(error.message || '搜索失败')
      } finally {
        this.loading = false
      }
    },
    
    // 加载更多
    async handleLoadMore() {
      if (!this.hasMore || this.loading) return
      
      this.pageNum++
      this.loading = true
      
      try {
        const response = await searchProducts(
          this.keyword,
          {
            pageNum: this.pageNum,
            pageSize: this.pageSize,
            ...this.filters
          }
        )
        
        this.products = [...this.products, ...response.data.list]
        this.hasMore = this.pageNum < response.data.totalPages
        
      } catch (error) {
        this.pageNum-- // 失败时回退页码
        this.$toast.error(error.message || '加载失败')
      } finally {
        this.loading = false
      }
    },
    
    // 查看商品详情
    async handleProductTap(product) {
      // 添加浏览记录
      try {
        await addHistory(product.productId)
      } catch (error) {
        console.warn('添加浏览记录失败:', error)
      }
      
      // 跳转详情页
      uni.navigateTo({
        url: `/pages/productDetail/productDetail?id=${product.productId}`
      })
    }
  }
}
```

### 3.2 商品详情页实现

```javascript
// pages/productDetail/productDetail.vue
import { getProductDetail, getPriceHistory } from '@/api/product'
import { addFavorite, removeFavorite, isFavorited } from '@/api/favorite'
import { createPriceAlert } from '@/api/alert'

export default {
  data() {
    return {
      productId: '',
      product: null,
      priceHistory: [],
      isCollected: false,
      loading: true,
      alertModalVisible: false
    }
  },
  
  onLoad(options) {
    this.productId = options.id
    this.loadProductDetail()
    this.checkFavoriteStatus()
  },
  
  methods: {
    // 加载商品详情
    async loadProductDetail() {
      try {
        const response = await getProductDetail(this.productId)
        this.product = response.data
        
        // 加载价格历史
        await this.loadPriceHistory()
        
      } catch (error) {
        this.$toast.error(error.message || '加载失败')
        setTimeout(() => uni.navigateBack(), 2000)
      } finally {
        this.loading = false
      }
    },
    
    // 加载价格走势
    async loadPriceHistory() {
      try {
        const response = await getPriceHistory(this.productId, 30)
        this.priceHistory = response.data.priceData
      } catch (error) {
        console.warn('加载价格历史失败:', error)
      }
    },
    
    // 检查是否已收藏
    async checkFavoriteStatus() {
      try {
        const response = await isFavorited(this.productId)
        this.isCollected = response.data.favorited
      } catch (error) {
        console.warn('检查收藏状态失败:', error)
      }
    },
    
    // 收藏/取消收藏
    async handleCollect() {
      try {
        if (this.isCollected) {
          // 取消收藏
          await removeFavorite(this.product.favoriteId)
          this.isCollected = false
          this.$toast.success('已取消收藏')
        } else {
          // 添加收藏
          const response = await addFavorite(this.productId)
          this.isCollected = true
          this.product.favoriteId = response.data.favoriteId
          this.$toast.success('已收藏')
        }
      } catch (error) {
        this.$toast.error(error.message || '操作失败')
      }
    },
    
    // 设置降价提醒
    async handleSetAlert(targetPrice) {
      try {
        await createPriceAlert({
          productId: this.productId,
          targetPrice,
          alertType: 'specific_price'
        })
        this.$toast.success('已设置降价提醒')
        this.alertModalVisible = false
      } catch (error) {
        this.$toast.error(error.message || '设置失败')
      }
    },
    
    // 跳转购买
    handleBuy(offerUrl) {
      uni.openURL({ url: offerUrl })
    }
  }
}
```

### 3.3 用户中心实现

```javascript
// pages/userCenter/userCenter.vue
import { getUserProfile, logout } from '@/api/user'
import { clearAuth } from '@/utils/auth'

export default {
  data() {
    return {
      userInfo: null,
      loading: true
    }
  },
  
  onLoad() {
    this.loadUserProfile()
  },
  
  onShow() {
    // 每次显示时刷新用户信息
    this.loadUserProfile()
  },
  
  methods: {
    // 加载用户信息
    async loadUserProfile() {
      try {
        const response = await getUserProfile()
        this.userInfo = response.data
      } catch (error) {
        this.$toast.error(error.message || '加载失败')
      } finally {
        this.loading = false
      }
    },
    
    // 用户登出
    async handleLogout() {
      uni.showModal({
        title: '确认登出',
        content: '确定要登出账号吗？',
        success: async (res) => {
          if (res.confirm) {
            try {
              await logout()
              clearAuth()
              this.$toast.success('已登出')
              uni.redirectTo({ url: '/pages/login/login' })
            } catch (error) {
              // 即使登出失败，也清除本地缓存
              clearAuth()
              uni.redirectTo({ url: '/pages/login/login' })
            }
          }
        }
      })
    },
    
    // 跳转到收藏页
    handleNavigateToFavorites() {
      uni.navigateTo({
        url: '/pages/favorites/favorites'
      })
    },
    
    // 跳转到降价提醒
    handleNavigateToAlerts() {
      uni.navigateTo({
        url: '/pages/priceAlerts/priceAlerts'
      })
    }
  }
}
```

---

## 四、错误处理最佳实践

### 4.1 统一错误处理

创建文件 `src/utils/errorHandler.js`：

```javascript
// 错误类型定义
export const ErrorType = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  PARAMETER_ERROR: 'PARAMETER_ERROR',
  UNAUTHORIZED_ERROR: 'UNAUTHORIZED_ERROR',
  FORBIDDEN_ERROR: 'FORBIDDEN_ERROR',
  NOT_FOUND_ERROR: 'NOT_FOUND_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  BUSINESS_ERROR: 'BUSINESS_ERROR'
}

// 错误处理器
export function handleError(error, context) {
  let errorType = ErrorType.BUSINESS_ERROR
  let errorMessage = '操作失败，请稍后重试'
  let errorCode = -1
  
  if (error.response) {
    // 服务器响应了错误状态码
    const status = error.response.status
    const data = error.response.data
    
    errorCode = data.code || status
    errorMessage = data.message || errorMessage
    
    switch (status) {
      case 400:
        errorType = ErrorType.PARAMETER_ERROR
        errorMessage = '请求参数错误'
        break
      case 401:
        errorType = ErrorType.UNAUTHORIZED_ERROR
        errorMessage = '请重新登录'
        break
      case 403:
        errorType = ErrorType.FORBIDDEN_ERROR
        errorMessage = '您没有权限进行此操作'
        break
      case 404:
        errorType = ErrorType.NOT_FOUND_ERROR
        errorMessage = '请求的资源不存在'
        break
      case 500:
      case 502:
      case 503:
      case 504:
        errorType = ErrorType.SERVER_ERROR
        errorMessage = '服务器错误，请稍后重试'
        break
    }
  } else if (error.request) {
    // 有请求但没有收到响应
    errorType = ErrorType.NETWORK_ERROR
    errorMessage = '网络连接失败，请检查网络设置'
  } else {
    // 其他错误
    errorMessage = error.message || '未知错误'
  }
  
  return {
    errorType,
    errorCode,
    errorMessage,
    originalError: error
  }
}

// 根据错误类型进行不同处理
export function processError(errorInfo, context) {
  const { errorType, errorMessage } = errorInfo
  
  // 显示错误提示
  if (context && context.$toast) {
    context.$toast.error(errorMessage)
  } else {
    console.error(errorMessage)
  }
  
  // 针对特定错误类型的处理
  switch (errorType) {
    case ErrorType.UNAUTHORIZED_ERROR:
      // 跳转到登录页
      setTimeout(() => {
        uni.redirectTo({ url: '/pages/login/login' })
      }, 500)
      break
      
    case ErrorType.NETWORK_ERROR:
      // 可以显示重试按钮等
      break
      
    case ErrorType.SERVER_ERROR:
      // 可以记录日志上报
      console.error('Server error:', errorInfo)
      break
  }
}
```

### 4.2 在组件中使用错误处理

```javascript
import { handleError, processError } from '@/utils/errorHandler'

export default {
  methods: {
    async handleSearch() {
      try {
        const response = await searchProducts(this.keyword, this.filters)
        this.products = response.data.list
      } catch (error) {
        const errorInfo = handleError(error, this)
        processError(errorInfo, this)
        
        // 可以根据错误类型做特殊处理
        if (errorInfo.errorType === ErrorType.PARAMETER_ERROR) {
          // 清空搜索条件
          this.filters = {}
        }
      }
    }
  }
}
```

---

## 五、数据缓存策略

### 5.1 本地存储工具

创建文件 `src/utils/storage.js`：

```javascript
// 本地存储管理工具
class StorageManager {
  constructor() {
    this.prefix = 'ycg_'
  }
  
  // 设置存储
  setItem(key, value, ttl = null) {
    const data = {
      value,
      timestamp: Date.now(),
      ttl // 生存时间（毫秒），null表示永久存储
    }
    
    try {
      uni.setStorageSync(this.prefix + key, JSON.stringify(data))
    } catch (error) {
      console.error('存储失败:', error)
    }
  }
  
  // 获取存储
  getItem(key) {
    try {
      const data = uni.getStorageSync(this.prefix + key)
      if (!data) return null
      
      const parsed = JSON.parse(data)
      
      // 检查是否过期
      if (parsed.ttl) {
        const age = Date.now() - parsed.timestamp
        if (age > parsed.ttl) {
          this.removeItem(key)
          return null
        }
      }
      
      return parsed.value
    } catch (error) {
      console.error('读取存储失败:', error)
      return null
    }
  }
  
  // 删除存储
  removeItem(key) {
    try {
      uni.removeStorageSync(this.prefix + key)
    } catch (error) {
      console.error('删除存储失败:', error)
    }
  }
  
  // 清空所有存储
  clear() {
    try {
      uni.clearStorageSync()
    } catch (error) {
      console.error('清空存储失败:', error)
    }
  }
}

export default new StorageManager()
```

### 5.2 API响应缓存

```javascript
// 修改request.js中的响应拦截器

const cacheMap = new Map()

// 响应拦截器
request.interceptors.response.use(
  response => {
    const { config, data } = response
    
    // 缓存GET请求的成功响应
    if (config.method === 'get' && config.cache !== false) {
      const cacheKey = config.url + JSON.stringify(config.params)
      const cacheDuration = config.cacheDuration || 5 * 60 * 1000 // 默认5分钟
      
      cacheMap.set(cacheKey, {
        data,
        timestamp: Date.now(),
        duration: cacheDuration
      })
    }
    
    return data
  }
  // ... 其他拦截器代码
)

// 使用缓存
export function getCachedRequest(url, params, cacheDuration = 5 * 60 * 1000) {
  const cacheKey = url + JSON.stringify(params)
  const cached = cacheMap.get(cacheKey)
  
  if (cached) {
    const age = Date.now() - cached.timestamp
    if (age < cached.duration) {
      return Promise.resolve(cached.data)
    }
  }
  
  return request.get(url, { params, cache: true, cacheDuration })
}
```

---

## 六、API超时处理

### 6.1 超时配置和重试

```javascript
// request.js中的超时和重试配置

let retryCount = {}

request.interceptors.response.use(
  response => response,
  error => {
    if (!error.config) {
      return Promise.reject(error)
    }
    
    const { url, method } = error.config
    const key = `${method}_${url}`
    
    // 只重试GET请求
    if (method !== 'get') {
      return Promise.reject(error)
    }
    
    // 最多重试3次
    if (!retryCount[key]) {
      retryCount[key] = 0
    }
    
    if (retryCount[key] < 3) {
      retryCount[key]++
      
      // 延迟后重试
      return new Promise(resolve => {
        setTimeout(() => {
          resolve(request(error.config))
        }, 1000 * retryCount[key])
      })
    }
    
    // 清除重试计数
    delete retryCount[key]
    
    return Promise.reject(error)
  }
)
```

---

## 七、API监控和日志

### 7.1 API调用日志

```javascript
// utils/apiLogger.js

class APILogger {
  // 记录API请求
  logRequest(config) {
    if (process.env.VUE_APP_ENABLE_DEBUG) {
      console.group(`📤 API Request: ${config.method?.toUpperCase()} ${config.url}`)
      console.log('Headers:', config.headers)
      console.log('Params:', config.params)
      console.log('Data:', config.data)
      console.groupEnd()
    }
  }
  
  // 记录API响应
  logResponse(config, response) {
    if (process.env.VUE_APP_ENABLE_DEBUG) {
      console.group(`📥 API Response: ${config.method?.toUpperCase()} ${config.url}`)
      console.log('Status:', response.status)
      console.log('Data:', response.data)
      console.groupEnd()
    }
  }
  
  // 记录API错误
  logError(config, error) {
    console.group(`❌ API Error: ${config.method?.toUpperCase()} ${config.url}`)
    console.error('Error:', error.message)
    if (error.response) {
      console.error('Response:', error.response.data)
    }
    console.groupEnd()
  }
}

export default new APILogger()
```

在request.js中使用：

```javascript
import apiLogger from '@/utils/apiLogger'

request.interceptors.request.use(config => {
  apiLogger.logRequest(config)
  return config
})

request.interceptors.response.use(
  response => {
    apiLogger.logResponse(response.config, response)
    return response.data
  },
  error => {
    apiLogger.logError(error.config, error)
    return Promise.reject(error)
  }
)
```

---

## 八、常见问题和解决方案

### 8.1 CORS跨域问题

**问题描述**：小程序请求服务器时出现跨域错误

**解决方案**：
1. 在服务器配置CORS响应头：

```javascript
// Django/Python示例
from django.http import HttpResponse

def cors_middleware(get_response):
  def middleware(request):
    response = get_response(request)
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response
  return middleware
```

2. 或使用nginx代理

### 8.2 Token过期处理

**问题描述**：Token过期导致请求失败

**解决方案**：在响应拦截器中自动刷新Token

```javascript
// 响应拦截器中的Token刷新逻辑
if (data.code === 401) {
  // 尝试刷新Token
  try {
    const newTokenResponse = await request.post('/auth/refresh-token')
    setToken(newTokenResponse.data.token)
    
    // 重新发送原请求
    return request(config)
  } catch (refreshError) {
    // 刷新失败，跳转登录
    clearAuth()
    uni.redirectTo({ url: '/pages/login/login' })
  }
}
```

### 8.3 大数据列表加载缓慢

**问题描述**：渲染大量商品列表时性能不佳

**解决方案**：
1. 使用虚拟滚动列表
2. 分页加载
3. 图片懒加载
4. 使用CDN加速图片加载

---

## 总结

这份指南覆盖了API集成的全面内容，包括：
✅ HTTP请求工具封装  
✅ 所有主要模块的API方法  
✅ 错误处理和数据缓存  
✅ 性能优化建议  
✅ 常见问题解决方案  

开发团队可以按照本指南快速集成后端API，保证代码规范性和可维护性。
