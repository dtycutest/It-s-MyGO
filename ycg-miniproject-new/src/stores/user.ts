import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authApi, userApi } from '../api';
import { storage } from '../utils';
import type { User, LoginRequest } from '../api/types';

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(storage.getToken());
  const refreshToken = ref<string>(storage.getRefreshToken());
  const userInfo = ref<User | null>(null);
  const loading = ref(false);

  const isLoggedIn = computed(() => !!token.value);

  const setToken = (accessToken: string, refreshTokenValue?: string) => {
    token.value = accessToken;
    storage.setToken(accessToken);
    if (refreshTokenValue) {
      refreshToken.value = refreshTokenValue;
      storage.setRefreshToken(refreshTokenValue);
    }
  };

  const login = async (data: LoginRequest) => {
    loading.value = true;
    try {
      const res = await authApi.login(data);
      const loginData = res.data;
      setToken(loginData.access_token, loginData.refresh_token);

      try {
        const profileRes = await userApi.getProfile();
        userInfo.value = profileRes.data;
      } catch {
        userInfo.value = {
          user_id: loginData.user_id,
          openid: loginData.openid,
          nick_name: '微信用户',
          avatar_url: '',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          vip_level: 0,
        };
      }

      return { success: true };
    } catch (error) {
      console.error('[userStore] 登录失败:', error);
      return { success: false, error };
    } finally {
      loading.value = false;
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('[userStore] 登出请求失败:', error);
    } finally {
      token.value = '';
      refreshToken.value = '';
      userInfo.value = null;
      storage.removeToken();
      storage.removeRefreshToken();
    }
  };

  const init = async () => {
    const savedToken = storage.getToken();
    if (savedToken) {
      token.value = savedToken;
      refreshToken.value = storage.getRefreshToken();
      try {
        const profileRes = await userApi.getProfile();
        userInfo.value = profileRes.data;
      } catch {
        token.value = '';
        refreshToken.value = '';
        storage.removeToken();
        storage.removeRefreshToken();
      }
    }
  };

  return {
    token,
    refreshToken,
    userInfo,
    loading,
    isLoggedIn,
    setToken,
    login,
    logout,
    init,
  };
});