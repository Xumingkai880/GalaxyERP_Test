import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',        // 经 vite proxy 转发到 http://127.0.0.1:8000/api
  timeout: 60000,         // Selenium 执行可能较慢，超时设 60s
})

// 响应拦截：统一处理错误
http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

/* -------- 用例接口 -------- */
export const caseApi = {
  list: ()              => http.get('/case/list'),
  get: (id)             => http.get(`/case/${id}`),
  create: (data)        => http.post('/case/create', data),
  update: (id, data)    => http.put(`/case/${id}`, data),
  remove: (id)          => http.delete(`/case/${id}`),
}

/* -------- 任务接口 -------- */
export const taskApi = {
  run: (data)   => http.post('/task/run', data),
  get: (id)     => http.get(`/task/${id}`),
  list: ()      => http.get('/task/list/all'),
  clear: ()     => http.delete('/task/clear'),
}
