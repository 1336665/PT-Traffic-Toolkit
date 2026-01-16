<template>
  <router-view />
</template>

<script setup>
import { useSettingsStore } from '@/stores/settings'

// Initialize settings store to apply dark mode
const settingsStore = useSettingsStore()
</script>
