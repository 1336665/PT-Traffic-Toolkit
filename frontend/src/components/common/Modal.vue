<template>
  <TransitionRoot appear :show="modelValue" as="template">
    <Dialog as="div" class="relative z-50" @close="close">
      <TransitionChild
        as="template"
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild
            as="template"
            enter="ease-out duration-300"
            enter-from="opacity-0 scale-95 translate-y-4"
            enter-to="opacity-100 scale-100 translate-y-0"
            leave="ease-in duration-200"
            leave-from="opacity-100 scale-100 translate-y-0"
            leave-to="opacity-0 scale-95 translate-y-4"
          >
            <DialogPanel
              class="w-full transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 text-left align-middle shadow-2xl transition-all"
              :class="[sizeClass]"
            >
              <!-- Header -->
              <div class="flex items-center justify-between px-6 py-5 border-b border-gray-200/80 dark:border-gray-700/50">
                <div class="flex items-center space-x-3">
                  <div v-if="icon" class="p-2 rounded-xl" :class="iconBgClass">
                    <component :is="icon" class="w-5 h-5" :class="iconColorClass" />
                  </div>
                  <div>
                    <DialogTitle
                      as="h3"
                      class="text-lg font-semibold leading-6 text-gray-900 dark:text-white"
                    >
                      {{ title }}
                    </DialogTitle>
                    <p v-if="subtitle" class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                      {{ subtitle }}
                    </p>
                  </div>
                </div>
                <button
                  @click="close"
                  class="p-2 rounded-xl text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <XMarkIcon class="h-5 w-5" />
                </button>
              </div>

              <!-- Body -->
              <div class="px-6 py-5 max-h-[70vh] overflow-y-auto">
                <slot />
              </div>

              <!-- Footer -->
              <div v-if="$slots.footer" class="flex justify-end gap-3 px-6 py-4 border-t border-gray-200/80 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/50">
                <slot name="footer" />
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
    blue: 'bg-blue-100 dark:bg-blue-900/30',
    green: 'bg-green-100 dark:bg-green-900/30',
    yellow: 'bg-yellow-100 dark:bg-yellow-900/30',
    red: 'bg-red-100 dark:bg-red-900/30',
    purple: 'bg-purple-100 dark:bg-purple-900/30',
    gray: 'bg-gray-100 dark:bg-gray-700',
  }
  return classes[props.iconColor] || classes.blue
})

const iconColorClass = computed(() => {
  const classes = {
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-green-600 dark:text-green-400',
    yellow: 'text-yellow-600 dark:text-yellow-400',
    red: 'text-red-600 dark:text-red-400',
    purple: 'text-purple-600 dark:text-purple-400',
    gray: 'text-gray-600 dark:text-gray-400',
  }
  return classes[props.iconColor] || classes.blue
})

function close() {
  emit('update:modelValue', false)
  emit('close')
}
</script>
