import axios from 'axios';
import type { ApiResponse } from '@/types';

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// 请求拦截：自动附加 Bearer Token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截：统一处理业务错误
request.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse<unknown>;
    if (data.code && data.code !== 200) {
      return Promise.reject(new Error(data.message || '请求失败'));
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      const role = window.location.pathname.startsWith('/hr') ? 'hr' : 'candidate';
      window.location.href = role === 'hr' ? '/hr/login' : '/';
      return Promise.reject(new Error('登录已过期，请重新登录'));
    }
    const msg = error.response?.data?.message || error.message || '网络异常';
    return Promise.reject(new Error(msg));
  },
);

export default request;
