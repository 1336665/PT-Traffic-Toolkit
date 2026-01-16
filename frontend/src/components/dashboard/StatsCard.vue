<template>
  <div :class="cardClass">
    <div class="flex items-center justify-between">
      <div class="flex-1 min-w-0">
        <p class="stats-label">{{ title }}</p>
        <p class="stats-value">{{ value }}</p>
        <div v-if="trend" class="flex items-center mt-1">
          <span
            class="text-xs font-medium"
            :class="trend > 0 ? 'text-green-500' : 'text-red-500'"
          >
            {{ trend > 0 ? '+' : '' }}{{ trend }}%
          </span>
          <span class="text-xs text-gray-400 ml-1">vs {{ trendPeriod }}</span>
        </div>
      </div>
      <div class="stats-icon">
        <component :is="iconComponent" class="w-6 h-6" />
      </div>
    </div>
    <!-- 装饰性渐变背景 -->
    <div class="absolute top-0 right-0 w-24 h-24 opacity-10 transform translate-x-8 -translate-y-8">
      <div :class="decorClass"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  ArrowUpIcon,
  ArrowDownIcon,
  BoltIcon,
  CircleStackIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  value: {
    type: String,
    required: true,
  },
  icon: {
    type: String,
    required: true,
  },
  color: {
    type: String,
    default: 'blue',
  },
  trend: {
    type: Number,
    default: null,
  },
  trendPeriod: {
    type: String,
    default: '昨日',
  },
})

const iconComponent = computed(() => {
  const icons = {
    ArrowUpIcon,
    ArrowDownIcon,
    BoltIcon,
    CircleStackIcon,
  }
  return icons[props.icon] || BoltIcon
})

const cardClass = computed(() => {
  const base = 'stats-card'
  const colorClass = {
    blue: 'stats-card-blue',
    green: 'stats-card-green',
    yellow: 'stats-card-yellow',
    purple: 'stats-card-purple',
    red: 'stats-card-red',
  }
  return `${base} ${colorClass[props.color] || colorClass.blue}`
})

const decorClass = computed(() => {
  const classes = {
    blue: 'w-full h-full rounded-full bg-blue-500',
    green: 'w-full h-full rounded-full bg-green-500',
    yellow: 'w-full h-full rounded-full bg-yellow-500',
    purple: 'w-full h-full rounded-full bg-purple-500',
    red: 'w-full h-full rounded-full bg-red-500',
  }
  return classes[props.color] || classes.blue
})
</script>
