<template>
  <button
    ref="buttonRef"
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClass"
    :style="buttonStyle"
    @click="handleClick"
    @mousedown="handleMouseDown"
    @mouseup="handleMouseUp"
    @mouseleave="handleMouseUp"
  >
    <!-- Ripple effect container -->
    <span class="absolute inset-0 overflow-hidden rounded-inherit pointer-events-none">
      <transition
        enter-active-class="transition-transform duration-500 ease-out"
        enter-from-class="scale-0 opacity-100"
        enter-to-class="scale-100 opacity-0"
        leave-active-class="transition-opacity duration-200"
        leave-to-class="opacity-0"
      >
        <span
          v-if="showRipple"
          class="absolute rounded-full bg-white/30"
          :style="rippleStyle"
        ></span>
      </transition>
    </span>

    <!-- Loading state -->
    <template v-if="loading">
      <span class="flex items-center justify-center">
        <!-- Animated spinner -->
        <svg
          class="animate-spin h-4 w-4"
          :class="$slots.default ? 'mr-2' : ''"
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
        <span v-if="$slots.default" class="relative inline-flex items-center whitespace-nowrap">
          <slot />
        </span>
      </span>
    </template>

    <!-- Normal content -->
    <template v-else>
      <component
        v-if="icon"
        :is="icon"
        :class="[
          'w-4 h-4 transition-all duration-150',
          $slots.default ? '-ml-0.5 mr-2' : '',
          isPressed ? 'scale-90' : 'scale-100'
        ]"
      />
      <span class="relative inline-flex items-center whitespace-nowrap">
        <slot />
      </span>
    </template>

    <!-- Success overlay -->
    <transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 scale-50"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-200"
      leave-to-class="opacity-0 scale-50"
    >
      <span
        v-if="showSuccess"
        class="absolute inset-0 flex items-center justify-center rounded-inherit"
        :style="buttonStyle"
      >
        <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </span>
    </transition>
  </button>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'button',
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'danger', 'success', 'warning', 'ghost', 'link'].includes(value),
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

const emit = defineEmits(['click'])

const buttonRef = ref(null)
const isPressed = ref(false)
const showRipple = ref(false)
const showSuccess = ref(false)
const rippleStyle = ref({})

function handleMouseDown(e) {
  if (props.disabled || props.loading) return
  isPressed.value = true

  // Create ripple effect
  const button = buttonRef.value
  if (button) {
    const rect = button.getBoundingClientRect()
    const size = Math.max(rect.width, rect.height) * 2
    const x = e.clientX - rect.left - size / 2
    const y = e.clientY - rect.top - size / 2

    rippleStyle.value = {
      width: `${size}px`,
      height: `${size}px`,
      left: `${x}px`,
      top: `${y}px`,
    }
    showRipple.value = true

    setTimeout(() => {
      showRipple.value = false
    }, 500)
  }
}

function handleMouseUp() {
  isPressed.value = false
}

function handleClick(e) {
  if (props.disabled || props.loading) return
  emit('click', e)
}

// Expose method for external success feedback
function triggerSuccess() {
  showSuccess.value = true
  setTimeout(() => {
    showSuccess.value = false
  }, 1500)
}

defineExpose({ triggerSuccess })

const buttonClass = computed(() => {
  const base = [
    'relative inline-flex items-center justify-center gap-2',
    'font-semibold transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-surface-900',
    'cursor-pointer select-none overflow-hidden',
  ]

  // Size classes
  const sizes = {
    sm: 'px-3 py-1.5 text-xs rounded-lg',
    md: 'px-4 py-2.5 text-sm rounded-xl',
    lg: 'px-6 py-3 text-base rounded-xl',
    icon: 'p-2.5 rounded-xl',
  }

  // Variant classes with enhanced effects
  const variants = {
    primary: [
      'text-white',
      'shadow-lg shadow-primary-500/25',
      'hover:shadow-xl hover:shadow-primary-500/40',
      'hover:-translate-y-0.5',
      'focus:ring-primary-500',
      'active:translate-y-0 active:shadow-md',
      'hover:brightness-110',
    ].join(' '),
    secondary: [
      'border border-surface-200 dark:border-surface-600',
      'text-surface-700 dark:text-surface-200',
      'bg-white dark:bg-surface-800',
      'hover:bg-surface-50 dark:hover:bg-surface-700',
      'hover:border-surface-300 dark:hover:border-surface-500',
      'hover:shadow-md',
      'active:bg-surface-100 dark:active:bg-surface-600',
      'focus:ring-surface-400',
    ].join(' '),
    danger: [
      'text-white',
      'shadow-lg shadow-red-500/25',
      'hover:shadow-xl hover:shadow-red-500/40',
      'hover:-translate-y-0.5',
      'focus:ring-red-500',
      'active:translate-y-0 active:shadow-md',
      'hover:brightness-110',
    ].join(' '),
    success: [
      'text-white',
      'shadow-lg shadow-emerald-500/25',
      'hover:shadow-xl hover:shadow-emerald-500/40',
      'hover:-translate-y-0.5',
      'focus:ring-emerald-500',
      'active:translate-y-0 active:shadow-md',
      'hover:brightness-110',
    ].join(' '),
    warning: [
      'text-white',
      'shadow-lg shadow-amber-500/25',
      'hover:shadow-xl hover:shadow-amber-500/40',
      'hover:-translate-y-0.5',
      'focus:ring-amber-500',
      'active:translate-y-0 active:shadow-md',
      'hover:brightness-110',
    ].join(' '),
    ghost: [
      'text-surface-600 dark:text-surface-300',
      'hover:bg-surface-100 dark:hover:bg-surface-700',
      'hover:text-surface-900 dark:hover:text-white',
      'active:bg-surface-200 dark:active:bg-surface-600',
      'focus:ring-surface-400',
    ].join(' '),
    link: [
      'text-primary-600 dark:text-primary-400',
      'hover:text-primary-700 dark:hover:text-primary-300',
      'underline-offset-4 hover:underline',
      'focus:ring-primary-500',
    ].join(' '),
  }

  const disabledClass = 'disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none disabled:transform-none disabled:hover:translate-y-0'
  const roundedClass = props.rounded ? '!rounded-full' : ''
  const loadingClass = props.loading ? 'cursor-wait' : ''

  return [
    ...base,
    sizes[props.size],
    variants[props.variant],
    disabledClass,
    roundedClass,
    loadingClass,
  ].join(' ')
})

// For gradient backgrounds
const buttonStyle = computed(() => {
  const gradientVariants = ['primary', 'danger', 'success', 'warning']
  if (gradientVariants.includes(props.variant)) {
    const gradients = {
      primary: 'var(--gradient-primary)',
      danger: 'var(--gradient-danger)',
      success: 'var(--gradient-success)',
      warning: 'var(--gradient-warning)',
    }
    return { background: gradients[props.variant] }
  }
  return {}
})
</script>

<style scoped>
.rounded-inherit {
  border-radius: inherit;
}

@keyframes ripple {
  to {
    transform: scale(1);
    opacity: 0;
  }
}

/* Enhanced hover glow effect */
button:not(:disabled):hover {
  filter: brightness(1.05);
}

/* Pulse animation for loading state */
@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 0 0 currentColor;
  }
  50% {
    box-shadow: 0 0 10px 2px currentColor;
  }
}

button[data-loading="true"] {
  animation: pulse-glow 2s ease-in-out infinite;
}

/* Scale bounce on click */
@keyframes click-bounce {
  0% { transform: scale(1); }
  50% { transform: scale(0.95); }
  100% { transform: scale(1); }
}

button:active:not(:disabled) {
  animation: click-bounce 0.15s ease-out;
}

/* Shine effect on hover */
button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.5s ease;
  pointer-events: none;
}

button:hover:not(:disabled)::before {
  left: 100%;
}
</style>
