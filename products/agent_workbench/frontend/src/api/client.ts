/**
 * Axios HTTP 客户端
 *
 * 功能：
 * - 自动注入 JWT Token
 * - 401 响应自动跳转登录页
 * - 统一错误处理
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// API 基础地址（开发环境使用代理，生产环境使用实际地址）
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Token 存储键名
const TOKEN_KEY = 'agent_token';
const REFRESH_TOKEN_KEY = 'agent_refresh_token';

// 创建 Axios 实例
export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 获取 Token
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

// 设置 Token
export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

// 获取 Refresh Token
export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

// 设置 Refresh Token
export const setRefreshToken = (token: string): void => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
};

// 清除 Token
export const clearTokens = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

// 请求拦截器：自动注入 JWT Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：处理 401 和其他错误
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config;

    // 401 未授权：清除 Token 并跳转登录页
    if (error.response?.status === 401) {
      clearTokens();
      // 触发登录跳转（通过自定义事件，让 React 组件处理）
      window.dispatchEvent(new CustomEvent('auth:logout'));
      return Promise.reject(error);
    }

    // 403 禁止访问
    if (error.response?.status === 403) {
      console.error('权限不足:', error.response.data);
    }

    // 500 服务器错误
    if (error.response?.status === 500) {
      console.error('服务器错误:', error.response.data);
    }

    return Promise.reject(error);
  }
);

// 导出类型
export type { AxiosError, AxiosInstance };
