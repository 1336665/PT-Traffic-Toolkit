<template>
  <header class="h-16 bg-white/80 dark:bg-surface-900/80 backdrop-blur-xl border-b border-surface-200/80 dark:border-surface-700/50 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-40">
    <!-- Left side -->
    <div class="flex items-center space-x-4">
      <!-- Mobile menu button -->
      <button
        class="lg:hidden p-2 rounded-xl text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors cursor-pointer"
        @click="mobileMenuOpen = true"
      >
        <Bars3Icon class="h-6 w-6" />
      </button>

      <!-- Breadcrumb / Page title -->
      <div class="flex items-center space-x-2">
        <div class="hidden sm:flex items-center text-sm">
          <HomeIcon class="w-4 h-4 text-surface-400" />
          <ChevronRightIcon class="w-4 h-4 text-surface-300 mx-1" />
        </div>
        <h1 class="text-lg font-bold text-surface-900 dark:text-white">
          {{ currentPageTitle }}
        </h1>
      </div>
    </div>

    <!-- Right side -->
    <div class="flex items-center space-x-2">
      <!-- 搜索按钮 -->
      <button
        class="hidden sm:flex p-2.5 rounded-xl text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors cursor-pointer"
      >
        <MagnifyingGlassIcon class="h-5 w-5" />
      </button>

      <!-- 通知按钮 -->
      <div class="relative">
        <button
          class="relative p-2.5 rounded-xl text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors cursor-pointer"
          @click="toggleNotifications"
        >
          <BellIcon class="h-5 w-5" />
          <!-- 通知红点 -->
          <span
            v-if="errorCount > 0"
            class="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white dark:ring-surface-900"
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
            class="fixed inset-x-4 top-16 sm:absolute sm:inset-x-auto sm:left-auto sm:right-0 sm:mt-2 sm:w-80 rounded-2xl bg-white dark:bg-surface-800 shadow-xl shadow-surface-900/10 dark:shadow-black/30 ring-1 ring-surface-200/50 dark:ring-surface-700/50 z-50 overflow-hidden"
          >
            <div class="px-4 py-3 border-b border-surface-100 dark:border-surface-700 bg-surface-50/50 dark:bg-surface-800/50">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <div class="p-1.5 rounded-lg bg-red-100 dark:bg-red-900/30">
                    <ExclamationTriangleIcon class="w-4 h-4 text-red-500" />
                  </div>
                  <span class="text-sm font-semibold text-surface-900 dark:text-white">错误通知</span>
                </div>
                <button
                  class="text-xs text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 cursor-pointer"
                  @click="toggleNotifications"
                >
                  关闭
                </button>
              </div>
              <p class="text-xs text-surface-500 dark:text-surface-400 mt-1">
                最近 24 小时错误：<span class="font-medium text-red-500">{{ errorCount }}</span>
              </p>
            </div>
            <div class="max-h-72 overflow-y-auto">
              <div v-if="loadingErrors" class="p-4 text-sm text-surface-500 text-center">
                <div class="spinner mx-auto mb-2"></div>
                加载中...
              </div>
              <div v-else-if="errorLogs.length === 0" class="p-8 text-center">
                <CheckCircleIcon class="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                <p class="text-sm text-surface-500">暂无错误信息</p>
              </div>
              <ul v-else class="divide-y divide-surface-100 dark:divide-surface-700">
                <li v-for="log in errorLogs" :key="log.id" class="px-4 py-3 hover:bg-surface-50 dark:hover:bg-surface-700/50 transition-colors">
                  <p class="text-sm font-medium text-surface-900 dark:text-white truncate">
                    {{ log.message }}
                  </p>
                  <p class="text-xs text-surface-500 dark:text-surface-400 mt-1 flex items-center">
                    <ClockIcon class="w-3 h-3 mr-1" />
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
        class="p-2.5 rounded-xl text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-all duration-200 cursor-pointer"
      >
        <SunIcon v-if="settingsStore.darkMode" class="h-5 w-5 text-amber-500" />
        <MoonIcon v-else class="h-5 w-5" />
      </button>

      <!-- Divider -->
      <div class="hidden sm:block w-px h-8 bg-surface-200 dark:bg-surface-700"></div>

      <!-- User menu -->
      <Menu as="div" class="relative">
        <MenuButton class="flex items-center space-x-3 p-1.5 pr-3 rounded-xl hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors cursor-pointer">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/20 overflow-hidden"
               style="background: var(--gradient-primary)">
            <span class="text-white text-sm font-bold">
              {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
            </span>
          </div>
          <div class="hidden sm:flex flex-col items-start">
            <span class="text-sm font-medium text-surface-700 dark:text-surface-200">
              {{ authStore.user?.username || 'User' }}
            </span>
            <span class="text-xs text-surface-500 dark:text-surface-400">管理员</span>
          </div>
          <ChevronDownIcon class="hidden sm:block h-4 w-4 text-surface-400" />
        </MenuButton>

        <transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="transform opacity-0 scale-95 -translate-y-2"
          enter-to-class="transform opacity-100 scale-100 translate-y-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="transform opacity-100 scale-100 translate-y-0"
          leave-to-class="transform opacity-0 scale-95 -translate-y-2"
        >
          <MenuItems class="absolute right-0 mt-2 w-56 origin-top-right bg-white dark:bg-surface-800 rounded-2xl shadow-xl shadow-surface-900/10 dark:shadow-black/30 ring-1 ring-surface-200/50 dark:ring-surface-700/50 focus:outline-none z-50 p-1.5 overflow-hidden">
            <div class="px-3 py-2.5 border-b border-surface-100 dark:border-surface-700 mb-1.5">
              <p class="text-sm font-medium text-surface-900 dark:text-white">{{ authStore.user?.username }}</p>
              <p class="text-xs text-surface-500 dark:text-surface-400">admin@ptmanager.local</p>
            </div>
            <MenuItem v-slot="{ active }">
              <button
                @click="goToSettings('profile')"
                class="w-full flex items-center space-x-2 px-3 py-2.5 text-sm rounded-xl transition-colors cursor-pointer"
                :class="[
                  active ? 'bg-surface-100 dark:bg-surface-700' : '',
                  'text-surface-700 dark:text-surface-300'
                ]"
              >
                <UserCircleIcon class="w-4 h-4" />
                <span>个人设置</span>
              </button>
            </MenuItem>
            <MenuItem v-slot="{ active }">
              <button
                @click="goToSettings('system')"
                class="w-full flex items-center space-x-2 px-3 py-2.5 text-sm rounded-xl transition-colors cursor-pointer"
                :class="[
                  active ? 'bg-surface-100 dark:bg-surface-700' : '',
                  'text-surface-700 dark:text-surface-300'
                ]"
              >
                <Cog6ToothIcon class="w-4 h-4" />
                <span>系统设置</span>
              </button>
            </MenuItem>
            <div class="border-t border-surface-100 dark:border-surface-700 mt-1.5 pt-1.5">
              <MenuItem v-slot="{ active }">
                <button
                  @click="showLogoutConfirm = true"
                  class="w-full flex items-center space-x-2 px-3 py-2.5 text-sm rounded-xl transition-colors cursor-pointer"
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
        <div class="fixed inset-0 bg-surface-900/80 backdrop-blur-sm" />
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
                <button type="button" class="-m-2.5 p-2.5 cursor-pointer" @click="mobileMenuOpen = false">
                  <XMarkIcon class="h-6 w-6 text-white" />
                </button>
              </div>
            </TransitionChild>

            <div class="flex grow flex-col overflow-y-auto bg-white dark:bg-surface-900 px-6 pb-4">
              <div class="flex h-16 shrink-0 items-center">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30 overflow-hidden"
                       style="background: var(--gradient-primary)">
                    <span class="text-white font-bold text-lg">PT</span>
                  </div>
                  <div>
                    <span class="font-bold text-surface-900 dark:text-white">Manager Pro</span>
                    <p class="text-xs text-surface-500 dark:text-surface-400">PT 管理系统</p>
                  </div>
                </div>
              </div>
              <nav class="flex flex-1 flex-col mt-6">
                <ul role="list" class="flex flex-1 flex-col gap-y-2">
                  <li v-for="item in navItems" :key="item.path">
                    <router-link
                      :to="item.path"
                      @click="mobileMenuOpen = false"
                      class="group flex items-center gap-x-3 rounded-xl p-3 text-sm font-medium transition-colors"
                      :class="[
                        $route.path === item.path
                          ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400'
                          : 'text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800'
                      ]"
                    >
                      <div
                        class="flex items-center justify-center w-9 h-9 rounded-xl transition-colors"
                        :class="[
                          $route.path === item.path
                            ? 'text-white shadow-lg shadow-primary-500/30'
                            : 'bg-surface-100 dark:bg-surface-800 group-hover:bg-surface-200 dark:group-hover:bg-surface-700'
                        ]"
                        :style="$route.path === item.path ? { background: 'var(--gradient-primary)' } : {}"
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

  <!-- 退出确认对话框 -->
  <TransitionRoot appear :show="showLogoutConfirm" as="template">
    <Dialog as="div" @close="showLogoutConfirm = false" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-surface-900/60 dark:bg-black/70 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full max-w-sm transform overflow-hidden rounded-2xl bg-white dark:bg-surface-800 p-6 text-left align-middle shadow-2xl transition-all">
              <div class="flex items-center justify-center w-14 h-14 mx-auto rounded-2xl bg-red-100 dark:bg-red-900/30 mb-4">
                <ArrowRightOnRectangleIcon class="w-7 h-7 text-red-600 dark:text-red-400" />
              </div>
              <DialogTitle as="h3" class="text-lg font-semibold text-center text-surface-900 dark:text-white">
                确认退出登录
              </DialogTitle>
              <div class="mt-2">
                <p class="text-sm text-center text-surface-500 dark:text-surface-400">
                  您确定要退出登录吗？退出后需要重新输入账号密码。
                </p>
              </div>

              <div class="mt-6 flex space-x-3">
                <button
                  type="button"
                  class="flex-1 btn-secondary cursor-pointer"
                  @click="showLogoutConfirm = false"
                >
                  取消
                </button>
                <button
                  type="button"
                  class="flex-1 btn-danger cursor-pointer"
                  @click="confirmLogout"
                >
                  确认退出
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import {
  Dialog,
  DialogPanel,
  DialogTitle,
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
  ChartBarIcon,
  XMarkIcon,
  BellIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { logsApi } from '@/api'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const mobileMenuOpen = ref(false)
const notificationOpen = ref(false)
const showLogoutConfirm = ref(false)
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
  { name: '数据统计', path: '/statistics', icon: ChartBarIcon },
  { name: '系统日志', path: '/logs', icon: DocumentTextIcon },
  { name: '系统设置', path: '/settings', icon: Cog6ToothIcon },
]

const currentPageTitle = computed(() => {
  const item = navItems.find(i => i.path === route.path)
  return item?.name || 'PT Manager'
})

function goToSettings(tab) {
  router.push({ path: '/settings', query: { tab } })
}

function confirmLogout() {
  showLogoutConfirm.value = false
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
