import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const darkMode = ref(localStorage.getItem('darkMode') === 'true')
  const sidebarCollapsed = ref(localStorage.getItem('sidebarCollapsed') === 'true')

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

  return {
    darkMode,
    sidebarCollapsed,
    toggleDarkMode,
    toggleSidebar,
  }
})
