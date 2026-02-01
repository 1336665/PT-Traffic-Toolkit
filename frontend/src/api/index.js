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
      // Avoid redirect loop: don't redirect if already on login page
      const currentPath = window.location.pathname
      if (currentPath !== '/login' && currentPath !== '/setup') {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
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
    api.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    }),
}

// System API
export const systemApi = {
  getHealth: () => api.get('/health'),
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
  getAllStatus: () => api.get('/downloaders/status/all'),
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
  testFeed: (id) => api.post(`/rss/feeds/${id}/test`),
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

// Statistics API
export const statisticsApi = {
  getOverview: () => api.get('/statistics/overview'),
  getDownloaderStats: () => api.get('/statistics/downloaders'),
  getTrend: (params) => api.get('/statistics/trend', { params }),
  getPeriodStats: (params) => api.get('/statistics/period', { params }),
  getDeleteSummary: (days = 30) => api.get('/statistics/delete-summary', { params: { days } }),
  getRssSummary: (days = 30) => api.get('/statistics/rss-summary', { params: { days } }),
}

// Settings API
export const settingsApi = {
  getTelegram: () => api.get('/settings/telegram'),
  updateTelegram: (data) => api.put('/settings/telegram', data),
  testTelegram: () => api.post('/settings/telegram/test'),
  getNotifications: () => api.get('/settings/notifications'),
  updateNotifications: (data) => api.put('/settings/notifications', data),
  getSite: () => api.get('/settings/site'),
  updateSite: (data) => api.put('/settings/site', data),
  getSitePublic: () => api.get('/settings/site/public'),
}

// Netcup Monitor API
export const netcupApi = {
  getConfig: () => api.get('/netcup/config'),
  updateConfig: (data) => api.put('/netcup/config', data),
  // Accounts
  getAccounts: () => api.get('/netcup/accounts'),
  getAccount: (id) => api.get(`/netcup/accounts/${id}`),
  createAccount: (data) => api.post('/netcup/accounts', data),
  updateAccount: (id, data) => api.put(`/netcup/accounts/${id}`, data),
  deleteAccount: (id) => api.delete(`/netcup/accounts/${id}`),
  testAccount: (id) => api.post(`/netcup/accounts/${id}/test`),
  getAccountServers: (id) => api.get(`/netcup/accounts/${id}/servers`),
  // Servers
  getServers: () => api.get('/netcup/servers'),
  getServer: (id) => api.get(`/netcup/servers/${id}`),
  createServer: (data) => api.post('/netcup/servers', data),
  updateServer: (id, data) => api.put(`/netcup/servers/${id}`, data),
  deleteServer: (id) => api.delete(`/netcup/servers/${id}`),
  testServer: (id) => api.post(`/netcup/servers/${id}/test`),
  // Status & Records
  getStatus: () => api.get('/netcup/status'),
  getServerStatus: (id) => api.get(`/netcup/status/${id}`),
  check: () => api.post('/netcup/check'),
  getRecords: (params) => api.get('/netcup/records', { params }),
  getStatistics: (serverId = null) => api.get('/netcup/statistics', { params: { server_id: serverId } }),
}

export default api
