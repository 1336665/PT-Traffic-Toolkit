<template>
  <aside
    class="hidden lg:flex lg:flex-col h-full transition-all duration-300 ease-out relative flex-shrink-0"
    :class="[
      settingsStore.sidebarCollapsed ? 'w-20' : 'w-72',
      'bg-white/70 dark:bg-surface-900/70',
      'backdrop-blur-2xl backdrop-saturate-150',
      'border-r border-surface-200/60 dark:border-surface-700/40',
      'shadow-xl shadow-surface-900/5 dark:shadow-black/20'
    ]"
  >
    <!-- Gradient overlay for depth -->
    <div class="absolute inset-0 bg-gradient-to-b from-primary-500/[0.02] via-transparent to-purple-500/[0.02] pointer-events-none"></div>

    <!-- Logo -->
    <div class="relative h-16 flex items-center px-4 border-b border-surface-200/60 dark:border-surface-700/40">
      <div
        class="flex items-center transition-all duration-300"
        :class="settingsStore.sidebarCollapsed ? 'justify-center w-full' : 'space-x-3'"
      >
        <div class="relative group">
          <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-primary-500 to-purple-500 blur-lg opacity-50 group-hover:opacity-70 transition-opacity"></div>
          <div class="relative w-10 h-10 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/40 overflow-hidden transition-shadow group-hover:shadow-xl"
               style="background: var(--gradient-primary)">
            <span class="text-white font-bold text-lg">PT</span>
          </div>
          <div class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white dark:border-surface-900 shadow-sm shadow-emerald-500/50">
            <div class="absolute inset-0 rounded-full bg-emerald-400 animate-ping"></div>
          </div>
        </div>
        <transition
          enter-active-class="transition-all duration-300"
          enter-from-class="opacity-0 -translate-x-2"
          enter-to-class="opacity-100 translate-x-0"
          leave-active-class="transition-all duration-200"
          leave-from-class="opacity-100 translate-x-0"
          leave-to-class="opacity-0 -translate-x-2"
        >
          <div v-if="!settingsStore.sidebarCollapsed" class="flex flex-col">
            <span class="font-bold text-surface-900 dark:text-white tracking-tight">{{ settingsStore.siteName }}</span>
            <span class="text-xs text-surface-500 dark:text-surface-400">{{ settingsStore.siteDescription }}</span>
          </div>
        </transition>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto py-6 px-3 scrollbar-hide">
      <!-- 主导航 -->
      <div v-if="!settingsStore.sidebarCollapsed" class="mb-3 px-3">
        <p class="text-[10px] font-semibold text-surface-400 dark:text-surface-500 uppercase tracking-wider">主导航</p>
      </div>
      <ul class="space-y-1">
        <li v-for="item in mainNavItems" :key="item.path">
          <router-link :to="item.path" v-slot="{ isExactActive }" custom>
            <a
              :href="item.path"
              @click.prevent="$router.push(item.path)"
              class="group flex items-center px-3 py-2.5 rounded-xl transition-all duration-200 relative cursor-pointer hover:translate-x-1"
              :class="[
                isExactActive
                  ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400 shadow-sm'
                  : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100/80 dark:hover:bg-surface-800/60 hover:text-surface-900 dark:hover:text-white'
              ]"
              :title="settingsStore.sidebarCollapsed ? item.label : ''"
            >
              <div
                v-if="isExactActive"
                class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full"
                style="background: var(--gradient-primary)"
              ></div>
              <div
                class="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-xl transition-all duration-200 group-hover:shadow-md"
                :class="[
                  isExactActive
                    ? 'text-white shadow-lg shadow-primary-500/40'
                    : 'bg-surface-100/80 dark:bg-surface-800/80 group-hover:bg-surface-200 dark:group-hover:bg-surface-700 group-hover:shadow-md'
                ]"
                :style="isExactActive ? { background: 'var(--gradient-primary)' } : {}"
              >
                <component :is="item.icon" class="w-5 h-5" />
              </div>
              <transition
                enter-active-class="transition-all duration-200"
                enter-from-class="opacity-0"
                enter-to-class="opacity-100"
                leave-active-class="transition-all duration-150"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
              >
                <div v-if="!settingsStore.sidebarCollapsed" class="ml-3 flex-1 min-w-0">
                  <span class="font-medium text-sm">{{ item.label }}</span>
                </div>
              </transition>
            </a>
          </router-link>
        </li>
      </ul>

      <!-- 自动化功能 -->
      <div v-if="!settingsStore.sidebarCollapsed" class="mt-6 mb-3 px-3">
        <p class="text-[10px] font-semibold text-surface-400 dark:text-surface-500 uppercase tracking-wider">自动化功能</p>
      </div>
      <div v-else class="my-4 mx-3 border-t border-surface-200 dark:border-surface-700"></div>
      <ul class="space-y-1">
        <li v-for="item in automationNavItems" :key="item.path">
          <router-link :to="item.path" v-slot="{ isExactActive }" custom>
            <a
              :href="item.path"
              @click.prevent="$router.push(item.path)"
              class="group flex items-center px-3 py-2.5 rounded-xl transition-all duration-200 relative cursor-pointer hover:translate-x-1"
              :class="[
                isExactActive
                  ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400 shadow-sm'
                  : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100/80 dark:hover:bg-surface-800/60 hover:text-surface-900 dark:hover:text-white'
              ]"
              :title="settingsStore.sidebarCollapsed ? item.label : ''"
            >
              <div
                v-if="isExactActive"
                class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full"
                :style="{ background: item.gradient }"
              ></div>
              <div
                class="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-xl transition-colors duration-200"
                :class="[
                  isExactActive
                    ? `text-white shadow-lg ${item.shadow}`
                    : 'bg-surface-100 dark:bg-surface-800 group-hover:bg-surface-200 dark:group-hover:bg-surface-700'
                ]"
                :style="isExactActive ? { background: item.gradient } : {}"
              >
                <component :is="item.icon" class="w-5 h-5" />
              </div>
              <transition
                enter-active-class="transition-all duration-200"
                enter-from-class="opacity-0"
                enter-to-class="opacity-100"
                leave-active-class="transition-all duration-150"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
              >
                <div v-if="!settingsStore.sidebarCollapsed" class="ml-3 flex-1 min-w-0">
                  <span class="font-medium text-sm">{{ item.label }}</span>
                </div>
              </transition>
            </a>
          </router-link>
        </li>
      </ul>

      <!-- 系统 -->
      <div v-if="!settingsStore.sidebarCollapsed" class="mt-6 mb-3 px-3">
        <p class="text-[10px] font-semibold text-surface-400 dark:text-surface-500 uppercase tracking-wider">系统</p>
      </div>
      <div v-else class="my-4 mx-3 border-t border-surface-200 dark:border-surface-700"></div>
      <ul class="space-y-1">
        <li v-for="item in systemNavItems" :key="item.path">
          <router-link :to="item.path" v-slot="{ isExactActive }" custom>
            <a
              :href="item.path"
              @click.prevent="$router.push(item.path)"
              class="group flex items-center px-3 py-2.5 rounded-xl transition-all duration-200 relative cursor-pointer hover:translate-x-1"
              :class="[
                isExactActive
                  ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400 shadow-sm'
                  : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100/80 dark:hover:bg-surface-800/60 hover:text-surface-900 dark:hover:text-white'
              ]"
              :title="settingsStore.sidebarCollapsed ? item.label : ''"
            >
              <div
                v-if="isExactActive"
                class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full"
                style="background: var(--gradient-primary)"
              ></div>
              <div
                class="flex-shrink-0 flex items-center justify-center w-9 h-9 rounded-xl transition-all duration-200 group-hover:shadow-md"
                :class="[
                  isExactActive
                    ? 'text-white shadow-lg shadow-primary-500/40'
                    : 'bg-surface-100/80 dark:bg-surface-800/80 group-hover:bg-surface-200 dark:group-hover:bg-surface-700 group-hover:shadow-md'
                ]"
                :style="isExactActive ? { background: 'var(--gradient-primary)' } : {}"
              >
                <component :is="item.icon" class="w-5 h-5" />
              </div>
              <transition
                enter-active-class="transition-all duration-200"
                enter-from-class="opacity-0"
                enter-to-class="opacity-100"
                leave-active-class="transition-all duration-150"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
              >
                <div v-if="!settingsStore.sidebarCollapsed" class="ml-3 flex-1 min-w-0">
                  <span class="font-medium text-sm">{{ item.label }}</span>
                </div>
              </transition>
            </a>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- Bottom section -->
    <div class="p-4 border-t border-surface-200/80 dark:border-surface-700/50 space-y-3">
      <!-- 系统状态卡片 -->
      <transition
        enter-active-class="transition-all duration-300"
        enter-from-class="opacity-0 translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition-all duration-200"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-2"
      >
        <div
          v-if="!settingsStore.sidebarCollapsed"
          class="p-3 rounded-xl bg-gradient-to-br from-primary-500/10 via-purple-500/5 to-cyan-500/10 dark:from-primary-900/30 dark:via-purple-900/20 dark:to-cyan-900/30 border border-primary-500/10 dark:border-primary-500/20"
        >
          <div class="flex items-center space-x-2">
            <div class="relative">
              <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
              <div class="absolute inset-0 rounded-full bg-emerald-500 animate-ping opacity-75"></div>
            </div>
            <span class="text-xs font-medium text-surface-700 dark:text-surface-300">系统运行正常</span>
          </div>
          <p class="text-[10px] text-surface-500 dark:text-surface-400 mt-1.5 flex items-center">
            <span class="inline-block w-1 h-1 rounded-full bg-primary-500 mr-1.5"></span>
            v1.0.0 · 已运行 {{ settingsStore.formattedUptime }}
          </p>
        </div>
      </transition>

      <!-- Collapse button -->
      <button
        @click="settingsStore.toggleSidebar"
        class="w-full flex items-center justify-center px-3 py-2.5 text-surface-500 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-xl transition-all duration-200 group cursor-pointer"
        :title="settingsStore.sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <ChevronDoubleLeftIcon
          class="flex-shrink-0 w-5 h-5 transition-transform duration-300 group-hover:text-primary-500"
          :class="{ 'rotate-180': settingsStore.sidebarCollapsed }"
        />
        <transition
          enter-active-class="transition-all duration-200"
          enter-from-class="opacity-0 w-0"
          enter-to-class="opacity-100 w-auto"
          leave-active-class="transition-all duration-150"
          leave-from-class="opacity-100 w-auto"
          leave-to-class="opacity-0 w-0"
        >
          <span v-if="!settingsStore.sidebarCollapsed" class="ml-2 text-sm overflow-hidden whitespace-nowrap">收起侧边栏</span>
        </transition>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import {
  HomeIcon,
  ServerStackIcon,
  RssIcon,
  TrashIcon,
  BoltIcon,
  SparklesIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  ChevronDoubleLeftIcon,
  ChartBarIcon,
  SignalIcon,
} from '@heroicons/vue/24/outline'

const settingsStore = useSettingsStore()

// Start uptime polling on mount
onMounted(() => {
  settingsStore.startUptimePolling()
})

onUnmounted(() => {
  settingsStore.stopUptimePolling()
})

// 主导航
const mainNavItems = [
  { label: '仪表盘', path: '/', icon: HomeIcon },
  { label: '下载器', path: '/downloaders', icon: ServerStackIcon },
  { label: '数据统计', path: '/statistics', icon: ChartBarIcon },
]

// 自动化功能
const automationNavItems = [
  {
    label: 'RSS 订阅',
    path: '/rss',
    icon: RssIcon,
    gradient: 'linear-gradient(135deg, #f97316 0%, #fb923c 100%)',
    shadow: 'shadow-orange-500/30'
  },
  {
    label: '删种规则',
    path: '/delete-rules',
    icon: TrashIcon,
    gradient: 'linear-gradient(135deg, #ef4444 0%, #f87171 100%)',
    shadow: 'shadow-red-500/30'
  },
  {
    label: '动态限速',
    path: '/speed-limit',
    icon: BoltIcon,
    gradient: 'linear-gradient(135deg, #eab308 0%, #facc15 100%)',
    shadow: 'shadow-yellow-500/30'
  },
  {
    label: 'U2 追魔',
    path: '/u2-magic',
    icon: SparklesIcon,
    gradient: 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)',
    shadow: 'shadow-pink-500/30'
  },
  {
    label: 'Netcup 监控',
    path: '/netcup',
    icon: SignalIcon,
    gradient: 'linear-gradient(135deg, #14b8a6 0%, #22d3ee 100%)',
    shadow: 'shadow-teal-500/30'
  },
]

// 系统
const systemNavItems = [
  { label: '系统日志', path: '/logs', icon: DocumentTextIcon },
  { label: '系统设置', path: '/settings', icon: Cog6ToothIcon },
]
</script>

<style scoped>
/* Nav item hover effects */
.group:hover .nav-icon {
  animation: nav-icon-bounce 0.4s ease;
}

@keyframes nav-icon-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

/* Stagger animation for nav items */
nav ul li {
  animation: nav-slide-in 0.4s ease-out both;
}

nav ul li:nth-child(1) { animation-delay: 0.05s; }
nav ul li:nth-child(2) { animation-delay: 0.1s; }
nav ul li:nth-child(3) { animation-delay: 0.15s; }
nav ul li:nth-child(4) { animation-delay: 0.2s; }
nav ul li:nth-child(5) { animation-delay: 0.25s; }
nav ul li:nth-child(6) { animation-delay: 0.3s; }
nav ul li:nth-child(7) { animation-delay: 0.35s; }
nav ul li:nth-child(8) { animation-delay: 0.4s; }

@keyframes nav-slide-in {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Active indicator glow pulse */
.group a div[style*="gradient"] {
  position: relative;
}

.group a div[style*="gradient"]::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  opacity: 0;
  animation: active-pulse 2s ease-in-out infinite;
}

@keyframes active-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4);
    opacity: 0.5;
  }
  50% {
    box-shadow: 0 0 12px 4px rgba(99, 102, 241, 0.3);
    opacity: 0.8;
  }
}

/* Sidebar collapse/expand smooth transition */
aside {
  will-change: width;
}

/* Logo hover effect */
.group:hover > div:first-child {
  filter: brightness(1.1);
}

/* Navigation link underline effect on hover */
.group a::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--gradient-primary);
  transition: all 0.3s ease;
  transform: translateX(-50%);
  border-radius: 1px;
}

.group a:hover::before {
  width: 80%;
}

/* Icon container shine effect */
.group a > div:first-of-type {
  position: relative;
  overflow: hidden;
}

.group a > div:first-of-type::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  transition: left 0.5s ease;
}

.group a:hover > div:first-of-type::before {
  left: 100%;
}
</style>
