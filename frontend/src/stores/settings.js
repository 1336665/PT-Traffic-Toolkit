import { defineStore } from 'pinia'
import { ref, watch, computed } from 'vue'
import { systemApi, settingsApi } from '@/api'

export const useSettingsStore = defineStore('settings', () => {
  const darkMode = ref(localStorage.getItem('darkMode') === 'true')
  const sidebarCollapsed = ref(localStorage.getItem('sidebarCollapsed') === 'true')
  const uptimeSeconds = ref(0)
  const systemStatus = ref('healthy')
  let uptimeInterval = null

  // Site settings
  const siteName = ref(localStorage.getItem('siteName') || 'PT Manager')
  const siteDescription = ref(localStorage.getItem('siteDescription') || 'PT 流量管理工具')

  // Watch for dark mode changes
  watch(darkMode, (value) => {
    localStorage.setItem('darkMode', value)
    if (value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, { immediate: true })

  // Watch for sidebar changes
  watch(sidebarCollapsed, (value) => {
    localStorage.setItem('sidebarCollapsed', value)
  })

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  // Format uptime as human readable string
  const formattedUptime = computed(() => {
    const seconds = uptimeSeconds.value
    if (seconds < 60) return `${seconds}秒`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时`
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    return `${days}天${hours}小时`
  })

  async function fetchSystemHealth() {
    try {
      const response = await systemApi.getHealth()
      uptimeSeconds.value = response.data.uptime_seconds || 0
      systemStatus.value = response.data.status || 'healthy'
    } catch (error) {
      console.error('Failed to fetch system health:', error)
      systemStatus.value = 'error'
    }
  }

  function startUptimePolling() {
    // Fetch immediately
    fetchSystemHealth()
    // Then fetch every 60 seconds
    if (uptimeInterval) clearInterval(uptimeInterval)
    uptimeInterval = setInterval(() => {
      fetchSystemHealth()
    }, 60000)
  }

  function stopUptimePolling() {
    if (uptimeInterval) {
      clearInterval(uptimeInterval)
      uptimeInterval = null
    }
  }

  async function fetchSiteSettings() {
    try {
      const response = await settingsApi.getSite()
      siteName.value = response.data.site_name || 'PT Manager'
      siteDescription.value = response.data.site_description || 'PT 流量管理工具'
      // Cache in localStorage
      localStorage.setItem('siteName', siteName.value)
      localStorage.setItem('siteDescription', siteDescription.value)
      // Update document title
      document.title = siteName.value
    } catch (error) {
      console.error('Failed to fetch site settings:', error)
    }
  }

  async function fetchSiteSettingsPublic() {
    try {
      const response = await settingsApi.getSitePublic()
      siteName.value = response.data.site_name || 'PT Manager'
      siteDescription.value = response.data.site_description || 'PT 流量管理工具'
      localStorage.setItem('siteName', siteName.value)
      localStorage.setItem('siteDescription', siteDescription.value)
      document.title = siteName.value
    } catch (error) {
      console.error('Failed to fetch site settings:', error)
    }
  }

  return {
    darkMode,
    sidebarCollapsed,
    uptimeSeconds,
    systemStatus,
    formattedUptime,
    siteName,
    siteDescription,
    toggleDarkMode,
    toggleSidebar,
    fetchSystemHealth,
    startUptimePolling,
    stopUptimePolling,
    fetchSiteSettings,
    fetchSiteSettingsPublic,
  }
})
