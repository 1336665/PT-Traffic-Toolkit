import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dashboardApi } from '@/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref({
    total_upload_speed: 0,
    total_download_speed: 0,
    total_uploaded: 0,
    total_downloaded: 0,
    active_torrents: 0,
    seeding_torrents: 0,
    downloading_torrents: 0,
    total_torrents: 0,
    total_size: 0,
    free_space: 0,
  })

  const timeline = ref([])
  const downloadersStatus = ref([])
  const servicesStatus = ref({})
  const recentActivity = ref({})
  const loading = ref(false)

  async function fetchStats() {
    try {
      const response = await dashboardApi.getStats()
      stats.value = response.data
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  async function fetchTimeline(limit = 50) {
    try {
      const response = await dashboardApi.getTimeline(limit)
      timeline.value = response.data
    } catch (error) {
      console.error('Failed to fetch timeline:', error)
    }
  }

  async function fetchDownloadersStatus() {
    try {
      const response = await dashboardApi.getDownloadersStatus()
      downloadersStatus.value = response.data
    } catch (error) {
      console.error('Failed to fetch downloaders status:', error)
    }
  }

  async function fetchServicesStatus() {
    try {
      const response = await dashboardApi.getServicesStatus()
      servicesStatus.value = response.data
    } catch (error) {
      console.error('Failed to fetch services status:', error)
    }
  }

  async function fetchRecentActivity(hours = 24) {
    try {
      const response = await dashboardApi.getRecentActivity(hours)
      recentActivity.value = response.data
    } catch (error) {
      console.error('Failed to fetch recent activity:', error)
    }
  }

  function setStats(data) {
    stats.value = data
  }

  function setDownloadersStatus(data) {
    downloadersStatus.value = data
  }

  function setServicesStatus(data) {
    servicesStatus.value = data
  }

  async function fetchAll() {
    loading.value = true
    await Promise.all([
      fetchStats(),
      fetchTimeline(),
      fetchDownloadersStatus(),
      fetchServicesStatus(),
      fetchRecentActivity(),
    ])
    loading.value = false
  }

  return {
    stats,
    timeline,
    downloadersStatus,
    servicesStatus,
    recentActivity,
    loading,
    fetchStats,
    fetchTimeline,
    fetchDownloadersStatus,
    fetchServicesStatus,
    fetchRecentActivity,
    fetchAll,
    setStats,
    setDownloadersStatus,
    setServicesStatus,
  }
})
