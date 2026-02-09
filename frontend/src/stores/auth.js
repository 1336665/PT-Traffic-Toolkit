import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(null)
  const initialized = ref(false)
  const statusChecked = ref(false)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  async function checkStatus() {
    try {
      const response = await authApi.getStatus()
      initialized.value = response.data.initialized
      statusChecked.value = true
    } catch (error) {
      console.error('Failed to check system status:', error)
      statusChecked.value = true
    }
  }

  async function setup(username, password) {
    loading.value = true
    try {
      const response = await authApi.setup({ username, password })
      token.value = response.data.access_token
      localStorage.setItem('token', token.value)
      initialized.value = true
      // Don't await fetchUser - let it happen in background
      fetchUser().catch(() => {})
    } finally {
      loading.value = false
    }
  }

  async function login(username, password) {
    loading.value = true
    try {
      const response = await authApi.login({ username, password })
      token.value = response.data.access_token
      localStorage.setItem('token', token.value)
      // Don't await fetchUser - redirect immediately and fetch in background
      fetchUser().catch(() => {})
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const response = await authApi.getMe()
      user.value = response.data
    } catch (error) {
      console.error('Failed to fetch user:', error)
      // Only logout if it's an auth error
      if (error.response?.status === 401) {
        logout()
      }
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  // Initialize user if token exists (background)
  if (token.value) {
    fetchUser().catch(() => {})
  }

  return {
    token,
    user,
    initialized,
    statusChecked,
    isAuthenticated,
    loading,
    checkStatus,
    setup,
    login,
    fetchUser,
    logout,
  }
})
