import axios from 'axios';
import type { ApiResponse } from '@/types';

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
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
    const msg = error.response?.data?.message || error.message || '网络异常';
    return Promise.reject(new Error(msg));
  },
);

export default request;
