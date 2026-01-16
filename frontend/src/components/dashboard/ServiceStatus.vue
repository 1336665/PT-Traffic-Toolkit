<template>
  <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
    <div class="flex items-center space-x-3">
      <div
        class="w-2 h-2 rounded-full"
        :class="enabled ? 'bg-green-500' : 'bg-gray-400'"
      ></div>
      <span class="text-sm text-gray-700 dark:text-gray-300">{{ name }}</span>
    </div>
    <div class="flex items-center space-x-2">
      <span v-if="detail" class="text-xs text-gray-500 dark:text-gray-400">{{ detail }}</span>
      <span :class="enabled ? 'badge-success' : 'badge-gray'">
        {{ enabled ? 'Active' : 'Inactive' }}
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  name: {
    type: String,
    required: true,
  },
  enabled: {
    type: Boolean,
    default: false,
  },
  detail: {
    type: String,
    default: '',
  },
})
</script>
