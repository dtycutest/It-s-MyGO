import { storage } from './storage';
import type { ApiResponse } from '../api/types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// 错误码映射
const ERROR_MESSAGES: Record<number, string> = {
  400001: '参数缺失',
  400002: '参数类型错误',
  400003: '参数值范围错误',
  401001: '未登录，请先登录',
  401002: '登录已过期，请重新登录',
  401003: '登录无效，请重新登录',
  401004: '签名验证失败',
  403001: '无访问权限',
  403002: '资源禁止访问',
  404001: '用户不存在',
  404002: '商品不存在',
  429001: '搜索请求过于频繁',
  429002: 'API调用过于频繁',
  500001: '服务器错误',
  500002: '第三方服务异常',
  500003: '数据服务异常',
};

// 显示错误提示
function showError(message: string) {
  uni.showToast({
    title: message,
    icon: 'none',
    duration: 2000
  });
}

interface RequestConfig {
  header?: Record<string, string>;
  data?: any;
  params?: any;
  [key: string]: any;
}

const request = {
  async get<T = any>(url: string, config?: RequestConfig): Promise<T> {
    return this._request<T>('GET', url, { ...config, method: 'GET' });
  },

  async post<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this._request<T>('POST', url, { ...config, data });
  },

  async put<T = any>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this._request<T>('PUT', url, { ...config, data });
  },

  async delete<T = any>(url: string, config?: RequestConfig): Promise<T> {
    return this._request<T>('DELETE', url, { ...config, method: 'DELETE' });
  },

  async _request<T>(method: string, url: string, config: RequestConfig = {}): Promise<T> {
    const token = storage.getToken();
    const header: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Client-Version': '1.0.0',
      'X-Client-Platform': 'miniapp',
      ...config.header
    };

    if (token) {
      header['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await uni.request({
        url: BASE_URL + url,
        method: method as any,
        header,
        data: config.data || config.params,
        timeout: 30000
      });

      const response = res.data as ApiResponse<T>;

      if (response.code === 0) {
        return response as any;
      } else {
        const errorCode = response.code;
        const errorMessage = ERROR_MESSAGES[errorCode] || response.message || '请求失败';

        if (errorCode >= 401001 && errorCode <= 401004) {
          const hadToken = !!storage.getToken();
          storage.removeToken();
          storage.removeRefreshToken();
          if (hadToken) {
            showError(errorMessage);
            uni.navigateTo({
              url: '/pages/login/login'
            });
          }
          return Promise.reject(new Error(errorMessage));
        }

        showError(errorMessage);
        return Promise.reject(new Error(errorMessage));
      }
    } catch (error) {
      console.error('请求失败:', error);
      showError('网络请求失败，请检查网络');
      return Promise.reject(error);
    }
  }
};

export default request;
