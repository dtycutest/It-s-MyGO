const TOKEN_KEY = 'ycg_token';
const REFRESH_TOKEN_KEY = 'ycg_refresh_token';

export const storage = {
  setToken(token: string) {
    try {
      uni.setStorageSync(TOKEN_KEY, token);
    } catch (error) {
      console.error('保存 token 失败:', error);
    }
  },

  getToken(): string {
    try {
      return uni.getStorageSync(TOKEN_KEY) || '';
    } catch (error) {
      console.error('获取 token 失败:', error);
      return '';
    }
  },

  removeToken() {
    try {
      uni.removeStorageSync(TOKEN_KEY);
    } catch (error) {
      console.error('删除 token 失败:', error);
    }
  },

  setRefreshToken(token: string) {
    try {
      uni.setStorageSync(REFRESH_TOKEN_KEY, token);
    } catch (error) {
      console.error('保存 refresh token 失败:', error);
    }
  },

  getRefreshToken(): string {
    try {
      return uni.getStorageSync(REFRESH_TOKEN_KEY) || '';
    } catch (error) {
      console.error('获取 refresh token 失败:', error);
      return '';
    }
  },

  removeRefreshToken() {
    try {
      uni.removeStorageSync(REFRESH_TOKEN_KEY);
    } catch (error) {
      console.error('删除 refresh token 失败:', error);
    }
  },

  set(key: string, value: any) {
    try {
      uni.setStorageSync(key, value);
    } catch (error) {
      console.error(`保存 ${key} 失败:`, error);
    }
  },

  get<T = any>(key: string): T | null {
    try {
      const value = uni.getStorageSync(key);
      return value !== '' ? value : null;
    } catch (error) {
      console.error(`获取 ${key} 失败:`, error);
      return null;
    }
  },

  remove(key: string) {
    try {
      uni.removeStorageSync(key);
    } catch (error) {
      console.error(`删除 ${key} 失败:`, error);
    }
  },

  clear() {
    try {
      uni.clearStorageSync();
    } catch (error) {
      console.error('清空存储失败:', error);
    }
  }
};
