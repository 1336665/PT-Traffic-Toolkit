<template>
  <div class="h-screen flex overflow-hidden bg-surface-50 dark:bg-surface-950">
    <!-- Animated background gradient -->
    <div class="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div class="absolute -top-1/2 -left-1/4 w-[800px] h-[800px] rounded-full bg-primary-500/5 dark:bg-primary-500/10 blur-3xl animate-blob"></div>
      <div class="absolute -bottom-1/2 -right-1/4 w-[600px] h-[600px] rounded-full bg-purple-500/5 dark:bg-purple-500/10 blur-3xl animate-blob animation-delay-2000"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full bg-cyan-500/3 dark:bg-cyan-500/5 blur-3xl animate-blob animation-delay-4000"></div>
    </div>

    <!-- Sidebar - fixed height with internal scroll -->
    <Sidebar />

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
      <!-- Header -->
      <Header />

      <!-- Page content - scrollable area with page transitions -->
      <main class="flex-1 overflow-y-auto p-4 lg:p-6 bg-surface-50/50 dark:bg-surface-950/50">
        <router-view v-slot="{ Component, route }">
          <transition
            :name="transitionName"
            mode="out-in"
            @before-enter="onBeforeEnter"
            @after-leave="onAfterLeave"
          >
            <div :key="route.path" class="page-container">
              <component :is="Component" />
            </div>
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const route = useRoute()
const transitionName = ref('page-fade')

// Track navigation direction for slide transitions
let previousPath = ''
watch(
  () => route.path,
  (newPath, oldPath) => {
    previousPath = oldPath || ''
    // Use fade for simplicity, can be extended for directional slides
    transitionName.value = 'page-fade'
  }
)

function onBeforeEnter(el) {
  el.style.willChange = 'opacity, transform'
}

function onAfterLeave(el) {
  el.style.willChange = ''
}
</script>

<style scoped>
/* Page fade transition */
.page-fade-enter-active {
  transition: opacity 0.3s ease-out, transform 0.3s ease-out;
}

.page-fade-leave-active {
  transition: opacity 0.2s ease-in, transform 0.2s ease-in;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.page-fade-enter-to,
.page-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}

/* Page slide transition */
.page-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.page-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.page-slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.page-slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* Page scale transition */
.page-scale-enter-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-scale-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-scale-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.page-scale-leave-to {
  opacity: 0;
  transform: scale(1.02);
}

/* Page container for smooth transitions */
.page-container {
  min-height: 100%;
}

/* Blob animation */
@keyframes blob {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -50px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

.animate-blob {
  animation: blob 20s infinite ease-in-out;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

.animation-delay-4000 {
  animation-delay: 4s;
}
</style>
