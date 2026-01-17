<template>
  <header class="h-16 bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg border-b border-gray-200/80 dark:border-gray-700/50 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-40">
    <!-- Left side -->
    <div class="flex items-center space-x-4">
      <!-- Mobile menu button -->
      <button
        class="lg:hidden p-2 rounded-xl text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        @click="mobileMenuOpen = true"
      >
        <Bars3Icon class="h-6 w-6" />
      </button>

      <!-- Breadcrumb / Page title -->
      <div class="flex items-center space-x-2">
        <div class="hidden sm:flex items-center text-sm">
          <HomeIcon class="w-4 h-4 text-gray-400" />
          <ChevronRightIcon class="w-4 h-4 text-gray-300 mx-1" />
        </div>
        <h1 class="text-lg font-bold text-gray-900 dark:text-white">
          {{ currentPageTitle }}
        </h1>
      </div>
    </div>

    <!-- Right side -->
    <div class="flex items-center space-x-2">
      <!-- 搜索按钮（可选） -->
      <button
        class="hidden sm:flex p-2.5 rounded-xl text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        <MagnifyingGlassIcon class="h-5 w-5" />
      </button>

      <!-- 通知按钮 -->
      <div class="relative">
        <button
          class="relative p-2.5 rounded-xl text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          @click="toggleNotifications"
        >
          <BellIcon class="h-5 w-5" />
          <!-- 通知红点 -->
          <span
            v-if="errorCount > 0"
            class="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"
          ></span>
        </button>
        <transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="transform opacity-0 scale-95 -translate-y-2"
          enter-to-class="transform opacity-100 scale-100 translate-y-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="transform opacity-100 scale-100 translate-y-0"
          leave-to-class="transform opacity-0 scale-95 -translate-y-2"
        >
          <div
            v-if="notificationOpen"
            class="absolute right-0 mt-2 w-80 rounded-xl bg-white dark:bg-gray-800 shadow-xl ring-1 ring-black/5 dark:ring-white/10 z-50"
          >
            <div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
              <div class="flex items-center justify-between">
                <span class="text-sm font-semibold text-gray-900 dark:text-white">错误通知</span>
                <button
                  class="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  @click="toggleNotifications"
                >
                  关闭
                </button>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                最近 24 小时错误：{{ errorCount }}
              </p>
            </div>
            <div class="max-h-72 overflow-y-auto">
              <div v-if="loadingErrors" class="p-4 text-sm text-gray-500">加载中...</div>
              <div v-else-if="errorLogs.length === 0" class="p-4 text-sm text-gray-500">
                暂无错误信息
              </div>
              <ul v-else class="divide-y divide-gray-100 dark:divide-gray-700">
                <li v-for="log in errorLogs" :key="log.id" class="px-4 py-3">
                  <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {{ log.message }}
                  </p>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {{ formatLogTime(log.timestamp) }} · {{ log.module }}
                  </p>
                </li>
              </ul>
            </div>
          </div>
        </transition>
      </div>

      <!-- Dark mode toggle -->
      <button
        @click="settingsStore.toggleDarkMode"
        class="p-2.5 rounded-xl text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        <SunIcon v-if="settingsStore.darkMode" class="h-5 w-5 text-yellow-500" />
        <MoonIcon v-else class="h-5 w-5" />
      </button>

      <!-- Divider -->
      <div class="hidden sm:block w-px h-8 bg-gray-200 dark:bg-gray-700"></div>

      <!-- User menu -->
      <Menu as="div" class="relative">
        <MenuButton class="flex items-center space-x-3 p-1.5 pr-3 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/20">
            <span class="text-white text-sm font-bold">
              {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
            </span>
          </div>
          <div class="hidden sm:flex flex-col items-start">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-200">
              {{ authStore.user?.username || 'User' }}
            </span>
            <span class="text-xs text-gray-500 dark:text-gray-400">管理员</span>
          </div>
          <ChevronDownIcon class="hidden sm:block h-4 w-4 text-gray-400" />
        </MenuButton>

        <transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="transform opacity-0 scale-95 -translate-y-2"
          enter-to-class="transform opacity-100 scale-100 translate-y-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="transform opacity-100 scale-100 translate-y-0"
          leave-to-class="transform opacity-0 scale-95 -translate-y-2"
        >
          <MenuItems class="absolute right-0 mt-2 w-56 origin-top-right bg-white dark:bg-gray-800 rounded-xl shadow-xl ring-1 ring-black/5 dark:ring-white/10 focus:outline-none z-50 p-1">
            <div class="px-3 py-2 border-b border-gray-100 dark:border-gray-700 mb-1">
              <p class="text-sm font-medium text-gray-900 dark:text-white">{{ authStore.user?.username }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">admin@ptmanager.local</p>
            </div>
            <MenuItem v-slot="{ active }">
              <button
                class="w-full flex items-center space-x-2 px-3 py-2 text-sm rounded-lg"
                :class="[
                  active ? 'bg-gray-100 dark:bg-gray-700' : '',
                  'text-gray-700 dark:text-gray-300'
                ]"
              >
                <UserCircleIcon class="w-4 h-4" />
                <span>个人设置</span>
              </button>
            </MenuItem>
            <MenuItem v-slot="{ active }">
              <button
                class="w-full flex items-center space-x-2 px-3 py-2 text-sm rounded-lg"
                :class="[
                  active ? 'bg-gray-100 dark:bg-gray-700' : '',
                  'text-gray-700 dark:text-gray-300'
                ]"
              >
                <Cog6ToothIcon class="w-4 h-4" />
                <span>系统设置</span>
              </button>
            </MenuItem>
            <div class="border-t border-gray-100 dark:border-gray-700 mt-1 pt-1">
              <MenuItem v-slot="{ active }">
                <button
                  @click="logout"
                  class="w-full flex items-center space-x-2 px-3 py-2 text-sm rounded-lg"
                  :class="[
                    active ? 'bg-red-50 dark:bg-red-900/20' : '',
                    'text-red-600 dark:text-red-400'
                  ]"
                >
                  <ArrowRightOnRectangleIcon class="w-4 h-4" />
                  <span>退出登录</span>
                </button>
              </MenuItem>
            </div>
          </MenuItems>
        </transition>
      </Menu>
    </div>
  </header>

  <!-- Mobile menu -->
  <TransitionRoot as="template" :show="mobileMenuOpen">
    <Dialog as="div" class="relative z-50 lg:hidden" @close="mobileMenuOpen = false">
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-300"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-gray-900/80 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 flex">
        <TransitionChild
          as="template"
          enter="transition ease-in-out duration-300 transform"
          enter-from="-translate-x-full"
          enter-to="translate-x-0"
          leave="transition ease-in-out duration-300 transform"
          leave-from="translate-x-0"
          leave-to="-translate-x-full"
        >
          <DialogPanel class="relative mr-16 flex w-full max-w-xs flex-1">
            <!-- Close button -->
            <TransitionChild
              as="template"
              enter="ease-in-out duration-300"
              enter-from="opacity-0"
              enter-to="opacity-100"
              leave="ease-in-out duration-300"
              leave-from="opacity-100"
              leave-to="opacity-0"
            >
              <div class="absolute left-full top-0 flex w-16 justify-center pt-5">
                <button type="button" class="-m-2.5 p-2.5" @click="mobileMenuOpen = false">
                  <XMarkIcon class="h-6 w-6 text-white" />
                </button>
              </div>
            </TransitionChild>

            <div class="flex grow flex-col overflow-y-auto bg-white dark:bg-gray-800 px-6 pb-4">
              <div class="flex h-16 shrink-0 items-center">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/30">
                    <span class="text-white font-bold text-lg">PT</span>
                  </div>
                  <div>
                    <span class="font-bold text-gray-900 dark:text-white">Manager Pro</span>
                    <p class="text-xs text-gray-500 dark:text-gray-400">PT 管理系统</p>
                  </div>
                </div>
              </div>
              <nav class="flex flex-1 flex-col mt-6">
                <ul role="list" class="flex flex-1 flex-col gap-y-2">
                  <li v-for="item in navItems" :key="item.path">
                    <router-link
                      :to="item.path"
                      @click="mobileMenuOpen = false"
                      class="group flex items-center gap-x-3 rounded-xl p-3 text-sm font-medium"
                      :class="[
                        $route.path === item.path
                          ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                      ]"
                    >
                      <div
                        class="flex items-center justify-center w-9 h-9 rounded-lg"
                        :class="[
                          $route.path === item.path
                            ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/30'
                            : 'bg-gray-100 dark:bg-gray-700 group-hover:bg-gray-200 dark:group-hover:bg-gray-600'
                        ]"
                      >
                        <component :is="item.icon" class="h-5 w-5 shrink-0" />
                      </div>
                      {{ item.name }}
                    </router-link>
                  </li>
                </ul>
              </nav>
            </div>
          </DialogPanel>
        </TransitionChild>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { ref, computed, inject, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import {
  Dialog,
  DialogPanel,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import {
  Bars3Icon,
  SunIcon,
  MoonIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  HomeIcon,
  ServerIcon,
  RssIcon,
  TrashIcon,
  BoltIcon,
  SparklesIcon,
  DocumentTextIcon,
  XMarkIcon,
  BellIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { logsApi } from '@/api'

const $t = inject('t')
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const mobileMenuOpen = ref(false)
const notificationOpen = ref(false)
const errorLogs = ref([])
const loadingErrors = ref(false)
const errorCount = ref(0)
let errorIntervalId

const navItems = [
  { name: '仪表盘', path: '/', icon: HomeIcon },
  { name: '下载器', path: '/downloaders', icon: ServerIcon },
  { name: 'RSS订阅', path: '/rss', icon: RssIcon },
  { name: '删种规则', path: '/delete-rules', icon: TrashIcon },
  { name: '动态限速', path: '/speed-limit', icon: BoltIcon },
  { name: 'U2追魔', path: '/u2-magic', icon: SparklesIcon },
  { name: '系统日志', path: '/logs', icon: DocumentTextIcon },
]

const currentPageTitle = computed(() => {
  const item = navItems.find(i => i.path === route.path)
  return item?.name || 'PT Manager'
})

function logout() {
  authStore.logout()
  router.push('/login')
}

function formatLogTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const pad = (value) => String(value).padStart(2, '0')
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

async function loadErrorStats() {
  try {
    const response = await logsApi.getStats(24)
    errorCount.value = response.data?.by_level?.ERROR || 0
  } catch (error) {
    console.error('Failed to load error stats:', error)
  }
}

async function loadErrorLogs() {
  loadingErrors.value = true
  try {
    const response = await logsApi.getLogs({ level: 'ERROR', limit: 10 })
    errorLogs.value = response.data || []
  } catch (error) {
    console.error('Failed to load error logs:', error)
  } finally {
    loadingErrors.value = false
  }
}

async function toggleNotifications() {
  notificationOpen.value = !notificationOpen.value
  if (notificationOpen.value) {
    await loadErrorLogs()
    await loadErrorStats()
  }
}

onMounted(() => {
  loadErrorStats()
  errorIntervalId = setInterval(loadErrorStats, 60000)
})

onUnmounted(() => {
  if (errorIntervalId) {
    clearInterval(errorIntervalId)
  }
})
</script>
