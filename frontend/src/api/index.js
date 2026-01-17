import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
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

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  getStatus: () => api.get('/auth/status'),
  setup: (data) => api.post('/auth/setup', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  changePassword: (oldPassword, newPassword) =>
    api.post('/auth/change-password', null, {
      params: { old_password: oldPassword, new_password: newPassword },
    }),
}

// Dashboard API
export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
  getTimeline: (limit = 50) => api.get('/dashboard/timeline', { params: { limit } }),
  getDownloadersStatus: () => api.get('/dashboard/downloaders-status'),
  getServicesStatus: () => api.get('/dashboard/services-status'),
  getRecentActivity: (hours = 24) =>
    api.get('/dashboard/recent-activity', { params: { hours } }),
}

// Downloaders API
export const downloadersApi = {
  getAll: () => api.get('/downloaders'),
  get: (id) => api.get(`/downloaders/${id}`),
  create: (data) => api.post('/downloaders', data),
  update: (id, data) => api.put(`/downloaders/${id}`, data),
  delete: (id) => api.delete(`/downloaders/${id}`),
  test: (id) => api.post(`/downloaders/${id}/test`),
  getStatus: (id) => api.get(`/downloaders/${id}/status`),
  getTorrents: (id) => api.get(`/downloaders/${id}/torrents`),
  pauseTorrent: (downloaderId, hash) =>
    api.post(`/downloaders/${downloaderId}/torrents/${hash}/pause`),
  resumeTorrent: (downloaderId, hash) =>
    api.post(`/downloaders/${downloaderId}/torrents/${hash}/resume`),
  deleteTorrent: (downloaderId, hash, deleteFiles = false) =>
    api.delete(`/downloaders/${downloaderId}/torrents/${hash}`, {
      params: { delete_files: deleteFiles },
    }),
  reannounceTorrent: (downloaderId, hash) =>
    api.post(`/downloaders/${downloaderId}/torrents/${hash}/reannounce`),
}

// RSS API
export const rssApi = {
  getFeeds: () => api.get('/rss/feeds'),
  getFeed: (id) => api.get(`/rss/feeds/${id}`),
  createFeed: (data) => api.post('/rss/feeds', data),
  updateFeed: (id, data) => api.put(`/rss/feeds/${id}`, data),
  deleteFeed: (id) => api.delete(`/rss/feeds/${id}`),
  fetchFeed: (id) => api.post(`/rss/feeds/${id}/fetch`),
  resetFeed: (id) => api.post(`/rss/feeds/${id}/reset`),
  getRecords: (params) => api.get('/rss/records', { params }),
  deleteRecord: (id) => api.delete(`/rss/records/${id}`),
}

// Delete Rules API
export const deleteRulesApi = {
  getAll: () => api.get('/delete-rules'),
  get: (id) => api.get(`/delete-rules/${id}`),
  create: (data) => api.post('/delete-rules', data),
  update: (id, data) => api.put(`/delete-rules/${id}`, data),
  delete: (id) => api.delete(`/delete-rules/${id}`),
  run: (id) => api.post(`/delete-rules/${id}/run`),
  preview: (id) => api.post(`/delete-rules/${id}/preview`),
  getRecords: (params) => api.get('/delete-rules/records/all', { params }),
  getInterval: () => api.get('/delete-rules/interval'),
  updateInterval: (seconds) => api.put('/delete-rules/interval', { seconds }),
}

// Speed Limit API
export const speedLimitApi = {
  getConfig: () => api.get('/speed-limit/config'),
  updateConfig: (data) => api.put('/speed-limit/config', data),
  getSites: () => api.get('/speed-limit/sites'),
  getSite: (id) => api.get(`/speed-limit/sites/${id}`),
  createSite: (data) => api.post('/speed-limit/sites', data),
  updateSite: (id, data) => api.put(`/speed-limit/sites/${id}`, data),
  deleteSite: (id) => api.delete(`/speed-limit/sites/${id}`),
  getStatus: () => api.get('/speed-limit/status'),
  apply: () => api.post('/speed-limit/apply'),
  clear: () => api.post('/speed-limit/clear'),
  getRecords: (params) => api.get('/speed-limit/records', { params }),
}

// U2 Magic API
export const u2MagicApi = {
  getConfig: () => api.get('/u2-magic/config'),
  updateConfig: (data) => api.put('/u2-magic/config', data),
  fetch: () => api.post('/u2-magic/fetch'),
  getRecords: (params) => api.get('/u2-magic/records', { params }),
  deleteRecord: (id) => api.delete(`/u2-magic/records/${id}`),
}

// Logs API
export const logsApi = {
  getLogs: (params) => api.get('/logs', { params }),
  clearLogs: (beforeHours = 24) => api.delete('/logs', { params: { before_hours: beforeHours } }),
  getStats: (hours = 24) => api.get('/logs/stats', { params: { hours } }),
}

export default api
