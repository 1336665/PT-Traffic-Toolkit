<template>
  <div :class="['card', hover ? 'card-hover' : '', cardClass]">
    <!-- Header -->
    <div v-if="$slots.header || title" class="px-5 py-4 border-b border-gray-200 dark:border-gray-700/50">
      <slot name="header">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div v-if="icon" class="p-2 rounded-lg" :class="iconBgClass">
              <component :is="icon" class="w-5 h-5" :class="iconColorClass" />
            </div>
            <div>
              <h3 class="text-base font-semibold text-gray-900 dark:text-white">{{ title }}</h3>
              <p v-if="subtitle" class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ subtitle }}</p>
            </div>
          </div>
          <slot name="action" />
        </div>
      </slot>
    </div>

    <!-- Body -->
    <div :class="[padding ? 'p-5' : '', bodyClass]">
      <slot />
    </div>

    <!-- Footer -->
    <div v-if="$slots.footer" class="px-5 py-4 border-t border-gray-200 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/50">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  icon: {
    type: [Object, Function],
    default: null,
  },
  iconColor: {
    type: String,
    default: 'blue',
  },
  padding: {
    type: Boolean,
    default: true,
  },
  hover: {
    type: Boolean,
    default: false,
  },
  cardClass: {
    type: String,
    default: '',
  },
  bodyClass: {
    type: String,
    default: '',
  },
})

const iconBgClass = computed(() => {
  const classes = {
    blue: 'bg-blue-100 dark:bg-blue-900/30',
    green: 'bg-green-100 dark:bg-green-900/30',
    yellow: 'bg-yellow-100 dark:bg-yellow-900/30',
    purple: 'bg-purple-100 dark:bg-purple-900/30',
    red: 'bg-red-100 dark:bg-red-900/30',
    gray: 'bg-gray-100 dark:bg-gray-700',
  }
  return classes[props.iconColor] || classes.blue
})

const iconColorClass = computed(() => {
  const classes = {
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-green-600 dark:text-green-400',
    yellow: 'text-yellow-600 dark:text-yellow-400',
    purple: 'text-purple-600 dark:text-purple-400',
    red: 'text-red-600 dark:text-red-400',
    gray: 'text-gray-600 dark:text-gray-400',
  }
  return classes[props.iconColor] || classes.blue
})
</script>
