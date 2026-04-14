import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      // 只在JWT认证失败时跳转登录页（detail为"Not authenticated"或"无效的认证令牌"）
      if (status === 401 && (data.detail === 'Not authenticated' || data.detail === '无效的认证令牌')) {
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        window.location.href = '/login'
      } else if (status === 401) {
        // 其他401错误（如店铺登录失败）正常显示错误信息
        ElMessage.error(data.detail || data.message || '请求失败')
      } else {
        ElMessage.error(data.detail || data.message || '请求失败')
      }
    }
    return Promise.reject(error)
  }
)

export default api
