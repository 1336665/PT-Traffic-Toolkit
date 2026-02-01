<template>
  <div class="space-y-4">
    <!-- Stats Cards Skeleton -->
    <div v-if="type === 'stats'" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="i in 4" :key="i" class="rounded-2xl p-4 bg-surface-100 dark:bg-surface-800/50 border border-surface-200/50 dark:border-surface-700/50">
        <div class="flex items-center justify-between">
          <div class="space-y-2 flex-1">
            <div class="skeleton h-3 w-16 rounded"></div>
            <div class="skeleton h-8 w-24 rounded"></div>
          </div>
          <div class="skeleton w-12 h-12 rounded-xl"></div>
        </div>
      </div>
    </div>

    <!-- Table Skeleton -->
    <div v-else-if="type === 'table'" class="card">
      <div class="px-5 py-4 border-b border-surface-200/80 dark:border-surface-700/50">
        <div class="skeleton h-5 w-32 rounded"></div>
      </div>
      <div class="p-5 space-y-4">
        <div v-for="i in rows" :key="i" class="flex items-center space-x-4">
          <div class="skeleton h-10 w-10 rounded-lg"></div>
          <div class="flex-1 space-y-2">
            <div class="skeleton h-4 rounded" :style="{ width: `${60 + Math.random() * 30}%` }"></div>
            <div class="skeleton h-3 w-24 rounded"></div>
          </div>
          <div class="skeleton h-6 w-16 rounded-full"></div>
        </div>
      </div>
    </div>

    <!-- Card Skeleton -->
    <div v-else-if="type === 'card'" class="card">
      <div class="px-5 py-4 border-b border-surface-200/80 dark:border-surface-700/50">
        <div class="flex items-center space-x-3">
          <div class="skeleton w-10 h-10 rounded-xl"></div>
          <div class="space-y-2">
            <div class="skeleton h-4 w-28 rounded"></div>
            <div class="skeleton h-3 w-20 rounded"></div>
          </div>
        </div>
      </div>
      <div class="p-5 space-y-3">
        <div class="skeleton h-4 w-full rounded"></div>
        <div class="skeleton h-4 w-4/5 rounded"></div>
        <div class="skeleton h-4 w-3/5 rounded"></div>
      </div>
    </div>

    <!-- Grid Skeleton -->
    <div v-else-if="type === 'grid'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="card p-5 space-y-4">
        <div class="flex items-center space-x-3">
          <div class="skeleton w-12 h-12 rounded-xl"></div>
          <div class="flex-1 space-y-2">
            <div class="skeleton h-4 w-3/4 rounded"></div>
            <div class="skeleton h-3 w-1/2 rounded"></div>
          </div>
        </div>
        <div class="space-y-2">
          <div class="skeleton h-3 w-full rounded"></div>
          <div class="skeleton h-3 w-5/6 rounded"></div>
        </div>
        <div class="flex space-x-2">
          <div class="skeleton h-8 w-20 rounded-lg"></div>
          <div class="skeleton h-8 w-20 rounded-lg"></div>
        </div>
      </div>
    </div>

    <!-- Chart Skeleton -->
    <div v-else-if="type === 'chart'" class="card p-5">
      <div class="flex items-center justify-between mb-6">
        <div class="space-y-2">
          <div class="skeleton h-5 w-32 rounded"></div>
          <div class="skeleton h-3 w-24 rounded"></div>
        </div>
        <div class="skeleton h-8 w-24 rounded-lg"></div>
      </div>
      <div class="skeleton h-64 w-full rounded-xl"></div>
    </div>

    <!-- List Skeleton -->
    <div v-else-if="type === 'list'" class="space-y-3">
      <div v-for="i in rows" :key="i" class="flex items-center space-x-4 p-3 rounded-xl bg-surface-50 dark:bg-surface-800/50">
        <div class="skeleton w-10 h-10 rounded-full"></div>
        <div class="flex-1 space-y-2">
          <div class="skeleton h-4 rounded" :style="{ width: `${50 + Math.random() * 40}%` }"></div>
          <div class="skeleton h-3 w-1/3 rounded"></div>
        </div>
      </div>
    </div>

    <!-- Default/Text Skeleton -->
    <div v-else class="space-y-3">
      <div v-for="i in rows" :key="i" class="skeleton h-4 rounded" :style="{ width: `${60 + Math.random() * 35}%` }"></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'text',
    validator: (value) => ['stats', 'table', 'card', 'grid', 'chart', 'list', 'text'].includes(value)
  },
  rows: {
    type: Number,
    default: 5
  }
})
</script>
