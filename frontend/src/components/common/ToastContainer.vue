<template>
  <Teleport to="body">
    <TransitionGroup
      name="toast"
      tag="div"
      class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none max-w-[90vw] sm:max-w-sm"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="[
          'pointer-events-auto w-full shadow-lg rounded-xl overflow-hidden',
          'transform transition-all duration-300',
          toastClasses[toast.type]
        ]"
      >
        <div class="p-3 sm:p-4 flex items-start gap-3">
          <component
            :is="toastIcons[toast.type]"
            class="w-5 h-5 flex-shrink-0 mt-0.5"
          />
          <div class="flex-1 min-w-0">
            <p v-if="toast.title" class="font-medium text-sm">{{ toast.title }}</p>
            <p :class="['text-sm break-words', toast.title ? 'mt-1 opacity-90' : '']">{{ toast.message }}</p>
          </div>
          <button
            @click="removeToast(toast.id)"
            class="flex-shrink-0 p-1 rounded-lg hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
          >
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>
        <!-- Progress bar -->
        <div
          v-if="toast.duration > 0"
          class="h-1 bg-black/10 dark:bg-white/10"
        >
          <div
            class="h-full bg-current opacity-30 transition-all ease-linear"
            :style="{ width: `${toast.progress}%` }"
          />
        </div>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup>
import { getToast } from '@/composables/useToast'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const { toasts, removeToast } = getToast()

const toastClasses = {
  success: 'bg-green-50 dark:bg-green-900/90 text-green-800 dark:text-green-100 border border-green-200 dark:border-green-700',
  error: 'bg-red-50 dark:bg-red-900/90 text-red-800 dark:text-red-100 border border-red-200 dark:border-red-700',
  warning: 'bg-yellow-50 dark:bg-yellow-900/90 text-yellow-800 dark:text-yellow-100 border border-yellow-200 dark:border-yellow-700',
  info: 'bg-blue-50 dark:bg-blue-900/90 text-blue-800 dark:text-blue-100 border border-blue-200 dark:border-blue-700',
}

const toastIcons = {
  success: CheckCircleIcon,
  error: ExclamationCircleIcon,
  warning: ExclamationTriangleIcon,
  info: InformationCircleIcon,
}
</script>

<style scoped>
.toast-enter-active {
  animation: toast-in 0.3s ease-out;
}

.toast-leave-active {
  animation: toast-out 0.2s ease-in forwards;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}
</style>
