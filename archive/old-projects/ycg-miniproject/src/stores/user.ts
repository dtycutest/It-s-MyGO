import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authApi, userApi } from '../api';
import { storage } from '../utils';
import type { User, LoginRequest } from '../api/types';

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(storage.getToken());
  const userInfo = ref<User | null>(null);
  const loading = ref(false);

  const isLoggedIn = computed(() => !!token.value);

  const setToken = (newToken: string) => {
    token.value = newToken;
    storage.setToken(newToken);
  };

  const login = async (data: LoginRequest) => {
    loading.value = true;
    try {
      const res = await authApi.login(data);
      setToken(res.data.access_token);
      storage.setRefreshToken(res.data.refresh_token);
      
      if (res.data.nick_name) {
        userInfo.value = {
          user_id: res.data.user_id,
          openid: res.data.openid,
          nick_name: res.data.nick_name,
          avatar_url: res.data.avatar_url || '',
          created_at: '',
          updated_at: '',
          vip_level: 0
        } as User;
      }
      
      return res;
    } finally {
      loading.value = false;
    }
  };

  const fetchUserInfo = async () => {
    try {
      const res = await userApi.getProfile();
      userInfo.value = res.data;
      return res;
    } catch (error) {
      console.error('获取用户信息失败:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('登出请求失败:', error);
    } finally {
      token.value = '';
      userInfo.value = null;
      storage.removeToken();
      storage.removeRefreshToken();
    }
  };

  const init = () => {
    const savedToken = storage.getToken();
    if (savedToken) {
      token.value = savedToken;
      // 如果有 token，可以尝试获取用户信息
      // fetchUserInfo().catch(() => {});
    }
  };

  return {
    token,
    userInfo,
    loading,
    isLoggedIn,
    setToken,
    login,
    fetchUserInfo,
    logout,
    init
  };
});
