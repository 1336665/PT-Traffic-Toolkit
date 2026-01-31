<template>
  <router-view />
  <ToastContainer />
</template>

<script setup>
import { onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import ToastContainer from '@/components/common/ToastContainer.vue'

// Initialize settings store to apply dark mode
const settingsStore = useSettingsStore()

// Fetch site settings on app startup
onMounted(() => {
  settingsStore.fetchSiteSettingsPublic()
})
</script>
