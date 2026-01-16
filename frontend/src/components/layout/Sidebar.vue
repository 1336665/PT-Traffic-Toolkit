<template>
  <aside
    class="hidden lg:flex lg:flex-col transition-all duration-300 ease-in-out"
    :class="[
      settingsStore.sidebarCollapsed ? 'w-20' : 'w-72',
      'bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800',
      'border-r border-gray-200/80 dark:border-gray-700/50'
    ]"
  >
    <!-- Logo -->
    <div class="h-16 flex items-center px-4 border-b border-gray-200/80 dark:border-gray-700/50">
      <div
        class="flex items-center transition-all duration-300"
        :class="settingsStore.sidebarCollapsed ? 'justify-center w-full' : 'space-x-3'"
      >
        <div class="relative">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/30">
            <span class="text-white font-bold text-lg">PT</span>
          </div>
          <!-- 在线状态指示器 -->
          <div class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white dark:border-gray-800"></div>
        </div>
        <div v-if="!settingsStore.sidebarCollapsed" class="flex flex-col">
          <span class="font-bold text-gray-900 dark:text-white tracking-tight">Manager Pro</span>
          <span class="text-xs text-gray-500 dark:text-gray-400">PT 管理系统</span>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto py-6 px-3 scrollbar-hide">
      <div v-if="!settingsStore.sidebarCollapsed" class="mb-4 px-3">
        <p class="text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">导航菜单</p>
      </div>
      <ul class="space-y-1.5">
        <li v-for="item in navItems" :key="item.path">
          <router-link
            :to="item.path"
            v-slot="{ isActive }"
            custom
          >
            <a
              :href="item.path"
              @click.prevent="$router.push(item.path)"
              class="group flex items-center px-3 py-2.5 rounded-xl transition-all duration-200 relative"
              :class="[
                isActive
                  ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/50 hover:text-gray-900 dark:hover:text-white'
              ]"
            >
              <!-- 活跃指示器 -->
              <div
                v-if="isActive"
                class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full bg-primary-500"
              ></div>
              <div
                class="flex items-center justify-center w-9 h-9 rounded-lg transition-colors"
                :class="[
                  isActive
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-gray-100 dark:bg-gray-700/50 group-hover:bg-gray-200 dark:group-hover:bg-gray-600'
                ]"
              >
                <component :is="item.icon" class="h-5 w-5" />
              </div>
              <div v-if="!settingsStore.sidebarCollapsed" class="ml-3 flex-1 min-w-0">
                <span class="font-medium text-sm">{{ $t(item.labelKey) }}</span>
                <p v-if="item.badge" class="text-[10px] text-gray-400 dark:text-gray-500">{{ item.badge }}</p>
              </div>
              <!-- 徽章 -->
              <div
                v-if="item.count && !settingsStore.sidebarCollapsed"
                class="ml-auto px-2 py-0.5 rounded-full text-xs font-medium"
                :class="[
                  isActive
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
                ]"
              >
                {{ item.count }}
              </div>
            </a>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- Bottom section -->
    <div class="p-4 border-t border-gray-200/80 dark:border-gray-700/50 space-y-3">
      <!-- 系统状态卡片 -->
      <div
        v-if="!settingsStore.sidebarCollapsed"
        class="p-3 rounded-xl bg-gradient-to-br from-primary-500/10 to-purple-500/10 dark:from-primary-900/20 dark:to-purple-900/20"
      >
        <div class="flex items-center space-x-2">
          <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
          <span class="text-xs font-medium text-gray-700 dark:text-gray-300">系统运行正常</span>
        </div>
      </div>

      <!-- Collapse button -->
      <button
        @click="settingsStore.toggleSidebar"
        class="w-full flex items-center justify-center px-3 py-2.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/50 rounded-xl transition-all duration-200"
      >
        <ChevronDoubleLeftIcon
          class="h-5 w-5 transition-transform duration-300"
          :class="{ 'rotate-180': settingsStore.sidebarCollapsed }"
        />
        <span v-if="!settingsStore.sidebarCollapsed" class="ml-2 text-sm">收起侧边栏</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { inject } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import {
  HomeIcon,
  ServerIcon,
  RssIcon,
  TrashIcon,
  BoltIcon,
  SparklesIcon,
  DocumentTextIcon,
  ChevronDoubleLeftIcon,
} from '@heroicons/vue/24/outline'

const $t = inject('t')
const settingsStore = useSettingsStore()

const navItems = [
  { labelKey: 'nav.dashboard', path: '/', icon: HomeIcon },
  { labelKey: 'nav.downloaders', path: '/downloaders', icon: ServerIcon },
  { labelKey: 'nav.rss', path: '/rss', icon: RssIcon },
  { labelKey: 'nav.deleteRules', path: '/delete-rules', icon: TrashIcon },
  { labelKey: 'nav.speedLimit', path: '/speed-limit', icon: BoltIcon },
  { labelKey: 'nav.u2Magic', path: '/u2-magic', icon: SparklesIcon },
  { labelKey: 'nav.logs', path: '/logs', icon: DocumentTextIcon },
]
</script>
