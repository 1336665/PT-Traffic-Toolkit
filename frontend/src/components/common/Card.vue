<template>
  <div :class="cardClasses">
    <!-- Shine effect overlay -->
    <div v-if="shine" class="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">
      <div class="card-shine-effect"></div>
    </div>

    <!-- Gradient top border -->
    <div v-if="gradientBorder" class="absolute top-0 left-0 right-0 h-1 rounded-t-2xl overflow-hidden">
      <div class="w-full h-full" :style="{ background: gradientBorderColor }"></div>
    </div>

    <!-- Header -->
    <div v-if="$slots.header || title" class="relative px-5 py-4 border-b border-surface-200/60 dark:border-surface-700/40">
      <slot name="header">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div v-if="icon" class="p-2.5 rounded-xl transition-all duration-200 group-hover:scale-105" :class="iconBgClass">
              <component :is="icon" class="w-5 h-5" :class="iconColorClass" />
            </div>
            <div>
              <h3 class="text-base font-semibold text-surface-900 dark:text-white">{{ title }}</h3>
              <p v-if="subtitle" class="text-xs text-surface-500 dark:text-surface-400 mt-0.5">{{ subtitle }}</p>
            </div>
          </div>
          <slot name="action" />
        </div>
      </slot>
    </div>

    <!-- Body -->
    <div :class="[padding ? 'p-5' : '', bodyClass, 'relative']">
      <slot />
    </div>

    <!-- Footer -->
    <div v-if="$slots.footer" class="relative px-5 py-4 border-t border-surface-200/60 dark:border-surface-700/40 bg-surface-50/30 dark:bg-surface-800/30 rounded-b-2xl">
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
    default: 'primary',
  },
  padding: {
    type: Boolean,
    default: true,
  },
  hover: {
    type: Boolean,
    default: false,
  },
  glass: {
    type: Boolean,
    default: false,
  },
  glow: {
    type: Boolean,
    default: false,
  },
  shine: {
    type: Boolean,
    default: false,
  },
  gradientBorder: {
    type: Boolean,
    default: false,
  },
  gradientBorderColor: {
    type: String,
    default: 'var(--gradient-primary)',
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

const cardClasses = computed(() => {
  const base = [
    'relative overflow-hidden rounded-2xl',
    'transition-all duration-300',
  ]

  if (props.glass) {
    base.push(
      'bg-white/60 dark:bg-surface-800/60',
      'backdrop-blur-2xl backdrop-saturate-150',
      'border border-white/40 dark:border-surface-700/40',
      'shadow-xl shadow-surface-900/10 dark:shadow-black/30'
    )
  } else {
    base.push(
      'bg-white/90 dark:bg-surface-800/90',
      'backdrop-blur-xl',
      'border border-surface-200/60 dark:border-surface-700/40',
      'shadow-lg shadow-surface-900/5 dark:shadow-black/20'
    )
  }

  if (props.hover) {
    base.push(
      'cursor-pointer',
      'hover:shadow-xl hover:shadow-surface-900/10 dark:hover:shadow-black/40',
      'hover:border-surface-300/80 dark:hover:border-surface-600/60',
      'hover:-translate-y-1',
      'active:translate-y-0 active:shadow-lg'
    )
  }

  if (props.glow) {
    base.push('card-glow-effect')
  }

  if (props.cardClass) {
    base.push(props.cardClass)
  }

  return base.join(' ')
})

const iconBgClass = computed(() => {
  const classes = {
    primary: 'bg-primary-100/80 dark:bg-primary-900/40 shadow-sm shadow-primary-500/10',
    blue: 'bg-blue-100/80 dark:bg-blue-900/40 shadow-sm shadow-blue-500/10',
    green: 'bg-emerald-100/80 dark:bg-emerald-900/40 shadow-sm shadow-emerald-500/10',
    yellow: 'bg-amber-100/80 dark:bg-amber-900/40 shadow-sm shadow-amber-500/10',
    purple: 'bg-purple-100/80 dark:bg-purple-900/40 shadow-sm shadow-purple-500/10',
    red: 'bg-red-100/80 dark:bg-red-900/40 shadow-sm shadow-red-500/10',
    cyan: 'bg-cyan-100/80 dark:bg-cyan-900/40 shadow-sm shadow-cyan-500/10',
    pink: 'bg-pink-100/80 dark:bg-pink-900/40 shadow-sm shadow-pink-500/10',
    orange: 'bg-orange-100/80 dark:bg-orange-900/40 shadow-sm shadow-orange-500/10',
    gray: 'bg-surface-100/80 dark:bg-surface-700/80 shadow-sm',
  }
  return classes[props.iconColor] || classes.primary
})

const iconColorClass = computed(() => {
  const classes = {
    primary: 'text-primary-600 dark:text-primary-400',
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-emerald-600 dark:text-emerald-400',
    yellow: 'text-amber-600 dark:text-amber-400',
    purple: 'text-purple-600 dark:text-purple-400',
    red: 'text-red-600 dark:text-red-400',
    cyan: 'text-cyan-600 dark:text-cyan-400',
    pink: 'text-pink-600 dark:text-pink-400',
    orange: 'text-orange-600 dark:text-orange-400',
    gray: 'text-surface-600 dark:text-surface-400',
  }
  return classes[props.iconColor] || classes.primary
})
</script>

<style scoped>
.card-shine-effect {
  position: absolute;
  top: 0;
  left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.15),
    transparent
  );
  transition: left 0.7s ease;
}

.group:hover .card-shine-effect,
div:hover > .card-shine-effect {
  left: 100%;
}

.card-glow-effect {
  position: relative;
}

.card-glow-effect::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  background: var(--gradient-primary);
  opacity: 0;
  z-index: -1;
  transition: opacity 0.3s ease;
}

.card-glow-effect:hover::before {
  opacity: 0.15;
}
</style>
