<template>
  <div :class="cardClasses" class="group/card">
    <!-- Animated border gradient (for glow effect) -->
    <div v-if="glow" class="absolute -inset-[1px] rounded-2xl bg-gradient-to-r from-primary-500 via-purple-500 to-cyan-500 opacity-0 group-hover/card:opacity-30 blur-sm transition-opacity duration-500 -z-10"></div>

    <!-- Shine effect overlay -->
    <div v-if="shine || hover" class="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">
      <div class="card-shine-effect"></div>
    </div>

    <!-- Gradient top border -->
    <div v-if="gradientBorder" class="absolute top-0 left-0 right-0 h-1 rounded-t-2xl overflow-hidden">
      <div class="w-full h-full animate-gradient-x" :style="{ background: gradientBorderColor, backgroundSize: '200% 100%' }"></div>
    </div>

    <!-- Floating decoration orbs -->
    <div v-if="decorative" class="absolute inset-0 overflow-hidden rounded-2xl pointer-events-none">
      <div class="absolute -top-20 -right-20 w-40 h-40 rounded-full blur-3xl transition-transform duration-700 group-hover/card:scale-150" :class="decorativeOrbClass"></div>
      <div class="absolute -bottom-10 -left-10 w-24 h-24 rounded-full blur-2xl transition-transform duration-700 group-hover/card:scale-125" :class="decorativeOrbClass" style="opacity: 0.5;"></div>
    </div>

    <!-- Header -->
    <div v-if="$slots.header || title" class="relative px-5 py-4 border-b border-surface-200/60 dark:border-surface-700/40">
      <slot name="header">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div v-if="icon" class="p-2.5 rounded-xl transition-all duration-300 group-hover/card:scale-110 group-hover/card:shadow-lg" :class="iconBgClass">
              <component :is="icon" class="w-5 h-5 transition-transform duration-300" :class="iconColorClass" />
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
    <div v-if="$slots.footer" class="relative px-5 py-4 border-t border-surface-200/60 dark:border-surface-700/40 bg-surface-50/50 dark:bg-surface-800/30 rounded-b-2xl">
      <slot name="footer" />
    </div>

    <!-- Bottom gradient line (subtle) -->
    <div v-if="!$slots.footer && accent" class="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary-500/30 to-transparent"></div>
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
    default: 'linear-gradient(90deg, var(--color-primary-500), var(--color-purple-500), var(--color-cyan-500), var(--color-primary-500))',
  },
  decorative: {
    type: Boolean,
    default: false,
  },
  accent: {
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

const cardClasses = computed(() => {
  const base = [
    'relative overflow-hidden rounded-2xl',
    'transition-all duration-300 ease-out',
  ]

  if (props.glass) {
    base.push(
      'bg-white/70 dark:bg-surface-800/70',
      'backdrop-blur-2xl backdrop-saturate-150',
      'border border-white/50 dark:border-surface-700/50',
      'shadow-xl shadow-surface-900/10 dark:shadow-black/30'
    )
  } else {
    base.push(
      'bg-white/95 dark:bg-surface-800/95',
      'backdrop-blur-xl',
      'border border-surface-200/80 dark:border-surface-700/50',
      'shadow-lg shadow-surface-900/5 dark:shadow-black/20'
    )
  }

  if (props.hover) {
    base.push(
      'cursor-pointer',
      'hover:shadow-2xl hover:shadow-surface-900/15 dark:hover:shadow-black/50',
      'hover:border-surface-300 dark:hover:border-surface-600',
      'hover:-translate-y-1.5',
      'hover:bg-white dark:hover:bg-surface-800',
      'active:translate-y-0 active:shadow-lg active:scale-[0.99]'
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
    primary: 'bg-gradient-to-br from-primary-100 to-primary-200/50 dark:from-primary-900/50 dark:to-primary-800/30 shadow-sm shadow-primary-500/20',
    blue: 'bg-gradient-to-br from-blue-100 to-blue-200/50 dark:from-blue-900/50 dark:to-blue-800/30 shadow-sm shadow-blue-500/20',
    green: 'bg-gradient-to-br from-emerald-100 to-emerald-200/50 dark:from-emerald-900/50 dark:to-emerald-800/30 shadow-sm shadow-emerald-500/20',
    yellow: 'bg-gradient-to-br from-amber-100 to-amber-200/50 dark:from-amber-900/50 dark:to-amber-800/30 shadow-sm shadow-amber-500/20',
    purple: 'bg-gradient-to-br from-purple-100 to-purple-200/50 dark:from-purple-900/50 dark:to-purple-800/30 shadow-sm shadow-purple-500/20',
    red: 'bg-gradient-to-br from-red-100 to-red-200/50 dark:from-red-900/50 dark:to-red-800/30 shadow-sm shadow-red-500/20',
    cyan: 'bg-gradient-to-br from-cyan-100 to-cyan-200/50 dark:from-cyan-900/50 dark:to-cyan-800/30 shadow-sm shadow-cyan-500/20',
    pink: 'bg-gradient-to-br from-pink-100 to-pink-200/50 dark:from-pink-900/50 dark:to-pink-800/30 shadow-sm shadow-pink-500/20',
    orange: 'bg-gradient-to-br from-orange-100 to-orange-200/50 dark:from-orange-900/50 dark:to-orange-800/30 shadow-sm shadow-orange-500/20',
    gray: 'bg-gradient-to-br from-surface-100 to-surface-200/50 dark:from-surface-700 dark:to-surface-600/50 shadow-sm',
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

const decorativeOrbClass = computed(() => {
  const classes = {
    primary: 'bg-primary-500/10 dark:bg-primary-500/20',
    blue: 'bg-blue-500/10 dark:bg-blue-500/20',
    green: 'bg-emerald-500/10 dark:bg-emerald-500/20',
    yellow: 'bg-amber-500/10 dark:bg-amber-500/20',
    purple: 'bg-purple-500/10 dark:bg-purple-500/20',
    red: 'bg-red-500/10 dark:bg-red-500/20',
    cyan: 'bg-cyan-500/10 dark:bg-cyan-500/20',
    pink: 'bg-pink-500/10 dark:bg-pink-500/20',
    orange: 'bg-orange-500/10 dark:bg-orange-500/20',
    gray: 'bg-surface-500/10 dark:bg-surface-500/20',
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
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.6s ease;
}

.group\/card:hover .card-shine-effect {
  left: 100%;
}

.card-glow-effect {
  position: relative;
}

.card-glow-effect::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-purple-500), var(--color-cyan-500));
  opacity: 0;
  z-index: -1;
  transition: opacity 0.4s ease;
  filter: blur(8px);
}

.card-glow-effect:hover::before {
  opacity: 0.25;
}

@keyframes gradient-x {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.animate-gradient-x {
  animation: gradient-x 3s linear infinite;
}
</style>
