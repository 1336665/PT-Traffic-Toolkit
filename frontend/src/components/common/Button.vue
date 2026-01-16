<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClass"
  >
    <!-- Loading spinner -->
    <svg
      v-if="loading"
      class="animate-spin -ml-1 mr-2 h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      ></circle>
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
    <!-- Icon slot -->
    <component
      v-if="icon && !loading"
      :is="icon"
      :class="['w-4 h-4', $slots.default ? '-ml-0.5 mr-2' : '']"
    />
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'button',
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'danger', 'success', 'ghost', 'link'].includes(value),
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'icon'].includes(value),
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  icon: {
    type: [Object, Function],
    default: null,
  },
  rounded: {
    type: Boolean,
    default: false,
  },
})

const buttonClass = computed(() => {
  const base = [
    'inline-flex items-center justify-center gap-2',
    'font-medium transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-900',
  ]

  // Size classes
  const sizes = {
    sm: 'px-3 py-1.5 text-xs rounded-md',
    md: 'px-4 py-2.5 text-sm rounded-lg',
    lg: 'px-6 py-3 text-base rounded-xl',
    icon: 'p-2 rounded-lg',
  }

  // Variant classes with modern gradients
  const variants = {
    primary: [
      'text-white',
      'bg-gradient-to-r from-primary-600 to-primary-500',
      'hover:from-primary-700 hover:to-primary-600',
      'shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40',
      'focus:ring-primary-500',
      'active:scale-[0.98]',
    ].join(' '),
    secondary: [
      'border border-gray-300 dark:border-gray-600',
      'text-gray-700 dark:text-gray-200',
      'bg-white dark:bg-gray-800',
      'hover:bg-gray-50 dark:hover:bg-gray-700',
      'focus:ring-gray-400',
    ].join(' '),
    danger: [
      'text-white',
      'bg-gradient-to-r from-red-600 to-red-500',
      'hover:from-red-700 hover:to-red-600',
      'shadow-lg shadow-red-500/25 hover:shadow-red-500/40',
      'focus:ring-red-500',
      'active:scale-[0.98]',
    ].join(' '),
    success: [
      'text-white',
      'bg-gradient-to-r from-green-600 to-green-500',
      'hover:from-green-700 hover:to-green-600',
      'shadow-lg shadow-green-500/25 hover:shadow-green-500/40',
      'focus:ring-green-500',
      'active:scale-[0.98]',
    ].join(' '),
    ghost: [
      'text-gray-600 dark:text-gray-300',
      'hover:bg-gray-100 dark:hover:bg-gray-700',
      'focus:ring-gray-400',
    ].join(' '),
    link: [
      'text-primary-600 dark:text-primary-400',
      'hover:text-primary-700 dark:hover:text-primary-300',
      'underline-offset-4 hover:underline',
      'focus:ring-primary-500',
    ].join(' '),
  }

  const disabledClass = 'disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none'
  const roundedClass = props.rounded ? '!rounded-full' : ''

  return [
    ...base,
    sizes[props.size],
    variants[props.variant],
    disabledClass,
    roundedClass,
  ].join(' ')
})
</script>
