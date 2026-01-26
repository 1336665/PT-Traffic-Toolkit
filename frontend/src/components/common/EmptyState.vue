<template>
  <div class="empty-state py-16 px-6">
    <!-- Icon with Animation -->
    <div class="relative mb-6">
      <div
        class="w-24 h-24 mx-auto rounded-3xl flex items-center justify-center"
        :class="iconBgClass"
      >
        <component
          :is="icon"
          class="w-12 h-12 transition-transform duration-500 group-hover:scale-110"
          :class="iconColorClass"
        />
      </div>
      <!-- Decorative circles -->
      <div class="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-primary-200/50 dark:bg-primary-800/30 animate-pulse"></div>
      <div class="absolute -bottom-1 -left-3 w-4 h-4 rounded-full bg-cyan-200/50 dark:bg-cyan-800/30 animate-pulse" style="animation-delay: 0.5s"></div>
    </div>

    <!-- Title -->
    <h3 class="text-xl font-semibold text-surface-700 dark:text-surface-200 mb-3">
      {{ title }}
    </h3>

    <!-- Description -->
    <p class="text-surface-500 dark:text-surface-400 max-w-md mx-auto mb-8 leading-relaxed">
      {{ description }}
    </p>

    <!-- Action Button -->
    <div v-if="actionLabel" class="flex justify-center">
      <button
        @click="$emit('action')"
        class="inline-flex items-center space-x-2 px-6 py-3 rounded-xl font-medium text-white shadow-lg transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl click-effect"
        :style="{ background: 'var(--gradient-primary)' }"
      >
        <component v-if="actionIcon" :is="actionIcon" class="w-5 h-5" />
        <span>{{ actionLabel }}</span>
      </button>
    </div>

    <!-- Secondary Action -->
    <div v-if="secondaryLabel" class="mt-4">
      <button
        @click="$emit('secondary')"
        class="text-sm text-surface-500 dark:text-surface-400 hover:text-primary-500 dark:hover:text-primary-400 transition-colors"
      >
        {{ secondaryLabel }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FolderOpenIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  icon: {
    type: [Object, Function],
    default: () => FolderOpenIcon
  },
  title: {
    type: String,
    default: '暂无数据'
  },
  description: {
    type: String,
    default: '当前没有任何数据可显示'
  },
  actionLabel: {
    type: String,
    default: ''
  },
  actionIcon: {
    type: [Object, Function],
    default: null
  },
  secondaryLabel: {
    type: String,
    default: ''
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'success', 'warning', 'danger', 'info'].includes(value)
  }
})

defineEmits(['action', 'secondary'])

const iconBgClass = computed(() => {
  const variants = {
    primary: 'bg-primary-50 dark:bg-primary-900/20',
    success: 'bg-emerald-50 dark:bg-emerald-900/20',
    warning: 'bg-amber-50 dark:bg-amber-900/20',
    danger: 'bg-red-50 dark:bg-red-900/20',
    info: 'bg-blue-50 dark:bg-blue-900/20'
  }
  return variants[props.variant]
})

const iconColorClass = computed(() => {
  const variants = {
    primary: 'text-primary-400 dark:text-primary-500',
    success: 'text-emerald-400 dark:text-emerald-500',
    warning: 'text-amber-400 dark:text-amber-500',
    danger: 'text-red-400 dark:text-red-500',
    info: 'text-blue-400 dark:text-blue-500'
  }
  return variants[props.variant]
})
</script>
