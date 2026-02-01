<template>
  <TransitionRoot appear :show="modelValue" as="template">
    <Dialog as="div" class="relative z-50" @close="close">
      <!-- Backdrop with enhanced blur and gradient -->
      <TransitionChild
        as="template"
        enter="ease-out duration-400"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-300"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-surface-950/60 dark:bg-black/70 backdrop-blur-md">
          <!-- Subtle gradient overlay -->
          <div class="absolute inset-0 bg-gradient-to-br from-primary-500/5 via-transparent to-purple-500/5"></div>
        </div>
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-end sm:items-center justify-center p-2 sm:p-4 text-center">
          <TransitionChild
            as="template"
            enter="ease-out duration-400"
            enter-from="opacity-0 scale-90 translate-y-8"
            enter-to="opacity-100 scale-100 translate-y-0"
            leave="ease-in duration-300"
            leave-from="opacity-100 scale-100 translate-y-0"
            leave-to="opacity-0 scale-90 translate-y-8"
          >
            <DialogPanel
              class="relative w-full transform text-left align-middle transition-all flex flex-col max-h-[85vh] sm:max-h-[90vh] group"
              :class="[sizeClass]"
            >
              <!-- Animated glow border -->
              <div v-if="glow" class="absolute -inset-[1px] rounded-2xl bg-gradient-to-r from-primary-500 via-purple-500 to-cyan-500 opacity-40 blur-sm animate-glow-pulse -z-10"></div>

              <!-- Main modal container -->
              <div class="relative rounded-2xl overflow-hidden flex flex-col min-h-0"
                   :class="[
                     glass
                       ? 'bg-white/80 dark:bg-surface-800/80 backdrop-blur-2xl backdrop-saturate-150'
                       : 'bg-white dark:bg-surface-800',
                     'shadow-2xl shadow-surface-900/20 dark:shadow-black/40',
                     'ring-1 ring-surface-200/50 dark:ring-surface-700/50'
                   ]">

                <!-- Decorative top gradient line -->
                <div v-if="accent" class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary-500 via-purple-500 to-cyan-500"></div>

                <!-- Floating decoration orbs -->
                <div v-if="decorative" class="absolute inset-0 overflow-hidden pointer-events-none">
                  <div class="absolute -top-20 -right-20 w-40 h-40 rounded-full blur-3xl" :class="decorativeOrbClass"></div>
                  <div class="absolute -bottom-10 -left-10 w-24 h-24 rounded-full blur-2xl" :class="decorativeOrbClass" style="opacity: 0.5;"></div>
                </div>

                <!-- Header -->
                <div class="relative flex-shrink-0 flex items-center justify-between px-6 py-4 border-b border-surface-200/80 dark:border-surface-700/50">
                  <div class="flex items-center space-x-3">
                    <div v-if="icon" class="p-2.5 rounded-xl transition-all duration-300 group-hover:scale-110" :class="iconBgClass">
                      <component :is="icon" class="w-5 h-5 transition-transform duration-300" :class="iconColorClass" />
                    </div>
                    <div>
                      <DialogTitle
                        as="h3"
                        class="text-lg font-semibold leading-6 text-surface-900 dark:text-white"
                      >
                        {{ title }}
                      </DialogTitle>
                      <p v-if="subtitle" class="text-sm text-surface-500 dark:text-surface-400 mt-0.5">
                        {{ subtitle }}
                      </p>
                    </div>
                  </div>
                  <button
                    @click="close"
                    class="p-2 rounded-xl text-surface-400 hover:text-surface-600 dark:hover:text-surface-200 hover:bg-surface-100 dark:hover:bg-surface-700 transition-all duration-200 hover:rotate-90 hover:scale-110"
                  >
                    <XMarkIcon class="h-5 w-5" />
                  </button>
                </div>

                <!-- Body -->
                <div class="relative flex-1 px-6 py-5 overflow-y-auto overscroll-contain" style="-webkit-overflow-scrolling: touch;">
                  <slot />
                </div>

                <!-- Footer -->
                <div v-if="$slots.footer" class="relative flex-shrink-0 flex justify-end gap-3 px-6 py-4 border-t border-surface-200/80 dark:border-surface-700/50 bg-surface-50/50 dark:bg-surface-900/30 rounded-b-2xl">
                  <slot name="footer" />
                </div>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { computed } from 'vue'
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionRoot,
  TransitionChild,
} from '@headlessui/vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
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
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'xl', '2xl', 'full'].includes(value),
  },
  glass: {
    type: Boolean,
    default: true,
  },
  glow: {
    type: Boolean,
    default: false,
  },
  accent: {
    type: Boolean,
    default: false,
  },
  decorative: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'close'])

const sizeClass = computed(() => {
  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    full: 'max-w-4xl',
  }
  return sizes[props.size]
})

const iconBgClass = computed(() => {
  const classes = {
    primary: 'bg-gradient-to-br from-primary-100 to-primary-200/50 dark:from-primary-900/50 dark:to-primary-800/30 shadow-sm shadow-primary-500/20',
    blue: 'bg-gradient-to-br from-blue-100 to-blue-200/50 dark:from-blue-900/50 dark:to-blue-800/30 shadow-sm shadow-blue-500/20',
    green: 'bg-gradient-to-br from-emerald-100 to-emerald-200/50 dark:from-emerald-900/50 dark:to-emerald-800/30 shadow-sm shadow-emerald-500/20',
    yellow: 'bg-gradient-to-br from-amber-100 to-amber-200/50 dark:from-amber-900/50 dark:to-amber-800/30 shadow-sm shadow-amber-500/20',
    red: 'bg-gradient-to-br from-red-100 to-red-200/50 dark:from-red-900/50 dark:to-red-800/30 shadow-sm shadow-red-500/20',
    purple: 'bg-gradient-to-br from-purple-100 to-purple-200/50 dark:from-purple-900/50 dark:to-purple-800/30 shadow-sm shadow-purple-500/20',
    cyan: 'bg-gradient-to-br from-cyan-100 to-cyan-200/50 dark:from-cyan-900/50 dark:to-cyan-800/30 shadow-sm shadow-cyan-500/20',
    surface: 'bg-gradient-to-br from-surface-100 to-surface-200/50 dark:from-surface-700 dark:to-surface-600/50 shadow-sm',
  }
  return classes[props.iconColor] || classes.blue
})

const iconColorClass = computed(() => {
  const classes = {
    primary: 'text-primary-600 dark:text-primary-400',
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-emerald-600 dark:text-emerald-400',
    yellow: 'text-amber-600 dark:text-amber-400',
    red: 'text-red-600 dark:text-red-400',
    purple: 'text-purple-600 dark:text-purple-400',
    cyan: 'text-cyan-600 dark:text-cyan-400',
    surface: 'text-surface-600 dark:text-surface-400',
  }
  return classes[props.iconColor] || classes.blue
})

const decorativeOrbClass = computed(() => {
  const classes = {
    primary: 'bg-primary-500/10 dark:bg-primary-500/20',
    blue: 'bg-blue-500/10 dark:bg-blue-500/20',
    green: 'bg-emerald-500/10 dark:bg-emerald-500/20',
    yellow: 'bg-amber-500/10 dark:bg-amber-500/20',
    red: 'bg-red-500/10 dark:bg-red-500/20',
    purple: 'bg-purple-500/10 dark:bg-purple-500/20',
    cyan: 'bg-cyan-500/10 dark:bg-cyan-500/20',
    surface: 'bg-surface-500/10 dark:bg-surface-500/20',
  }
  return classes[props.iconColor] || classes.blue
})

function close() {
  emit('update:modelValue', false)
  emit('close')
}
</script>

<style scoped>
@keyframes glow-pulse {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.6;
  }
}

.animate-glow-pulse {
  animation: glow-pulse 2s ease-in-out infinite;
}
</style>
