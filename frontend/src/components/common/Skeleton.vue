<template>
  <div :class="skeletonClasses" :style="skeletonStyle"></div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'text',
    validator: (value) => ['text', 'circle', 'card', 'avatar', 'button', 'image'].includes(value)
  },
  width: {
    type: [String, Number],
    default: null
  },
  height: {
    type: [String, Number],
    default: null
  },
  rounded: {
    type: String,
    default: 'md',
    validator: (value) => ['none', 'sm', 'md', 'lg', 'xl', '2xl', 'full'].includes(value)
  },
  animated: {
    type: Boolean,
    default: true
  }
})

const skeletonClasses = computed(() => {
  const baseClasses = [
    'bg-surface-200 dark:bg-surface-700',
    props.animated ? 'skeleton' : ''
  ]

  const roundedClasses = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    full: 'rounded-full'
  }

  const typeClasses = {
    text: 'h-4 rounded-md',
    circle: 'rounded-full',
    card: 'rounded-2xl',
    avatar: 'rounded-xl',
    button: 'h-10 rounded-xl',
    image: 'rounded-xl'
  }

  return [
    ...baseClasses,
    props.type === 'circle' || props.type === 'avatar' ? '' : roundedClasses[props.rounded],
    typeClasses[props.type]
  ].filter(Boolean).join(' ')
})

const skeletonStyle = computed(() => {
  const style = {}

  if (props.width) {
    style.width = typeof props.width === 'number' ? `${props.width}px` : props.width
  }

  if (props.height) {
    style.height = typeof props.height === 'number' ? `${props.height}px` : props.height
  }

  // Default sizes based on type
  if (!props.width && !props.height) {
    switch (props.type) {
      case 'circle':
        style.width = '48px'
        style.height = '48px'
        break
      case 'avatar':
        style.width = '40px'
        style.height = '40px'
        break
      case 'card':
        style.width = '100%'
        style.height = '200px'
        break
      case 'image':
        style.width = '100%'
        style.height = '150px'
        break
      case 'button':
        style.width = '100px'
        break
      case 'text':
      default:
        style.width = '100%'
        break
    }
  }

  return style
})
</script>
