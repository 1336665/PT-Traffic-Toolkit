<template>
  <div class="min-h-screen flex">
    <!-- 左侧品牌区域 -->
    <div class="hidden lg:flex lg:w-1/2 relative overflow-hidden"
         style="background: var(--gradient-primary)">
      <!-- 装饰背景 -->
      <div class="absolute inset-0">
        <div class="absolute top-0 left-0 w-[500px] h-[500px] bg-white/5 rounded-full -translate-x-1/2 -translate-y-1/2 blur-3xl"></div>
        <div class="absolute bottom-0 right-0 w-[400px] h-[400px] bg-white/5 rounded-full translate-x-1/3 translate-y-1/3 blur-3xl"></div>
        <div class="absolute top-1/2 left-1/2 w-[300px] h-[300px] bg-white/5 rounded-full -translate-x-1/2 -translate-y-1/2 blur-2xl"></div>
        <!-- 网格背景 -->
        <div class="absolute inset-0 opacity-10"
             style="background-image: radial-gradient(circle at 1px 1px, white 1px, transparent 0); background-size: 40px 40px;"></div>
      </div>

      <!-- 内容 -->
      <div class="relative z-10 flex flex-col justify-center px-12 xl:px-20">
        <div class="mb-8">
          <div class="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center mb-6 shadow-lg">
            <span class="text-white text-2xl font-bold">PT</span>
          </div>
          <h1 class="text-4xl xl:text-5xl font-bold text-white mb-4 leading-tight">
            PT Manager Pro
          </h1>
          <p class="text-xl text-white/80 max-w-md leading-relaxed">
            私有种子站智能管理系统，让资源管理更简单高效
          </p>
        </div>

        <!-- 功能特点 -->
        <div class="space-y-4 mt-8">
          <div class="flex items-center space-x-4 text-white/90 group">
            <div class="w-12 h-12 rounded-xl bg-white/10 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/20 transition-colors">
              <ServerStackIcon class="w-6 h-6" />
            </div>
            <div>
              <span class="font-medium">多下载器统一管理</span>
              <p class="text-sm text-white/60">支持 qBittorrent、Transmission、Deluge</p>
            </div>
          </div>
          <div class="flex items-center space-x-4 text-white/90 group">
            <div class="w-12 h-12 rounded-xl bg-white/10 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/20 transition-colors">
              <RssIcon class="w-6 h-6" />
            </div>
            <div>
              <span class="font-medium">智能 RSS 订阅推送</span>
              <p class="text-sm text-white/60">自动抓取免费种子</p>
            </div>
          </div>
          <div class="flex items-center space-x-4 text-white/90 group">
            <div class="w-12 h-12 rounded-xl bg-white/10 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/20 transition-colors">
              <TrashIcon class="w-6 h-6" />
            </div>
            <div>
              <span class="font-medium">自动化删种规则</span>
              <p class="text-sm text-white/60">智能清理无用种子</p>
            </div>
          </div>
          <div class="flex items-center space-x-4 text-white/90 group">
            <div class="w-12 h-12 rounded-xl bg-white/10 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/20 transition-colors">
              <BoltIcon class="w-6 h-6" />
            </div>
            <div>
              <span class="font-medium">动态限速调控</span>
              <p class="text-sm text-white/60">PID 算法精准控制</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录区域 -->
    <div class="flex-1 flex items-center justify-center bg-surface-50 dark:bg-surface-950 px-4 sm:px-6 lg:px-8 relative">
      <!-- 背景装饰 -->
      <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/10 rounded-full blur-3xl"></div>
        <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      <div class="max-w-md w-full relative">
        <!-- 移动端 Logo -->
        <div class="text-center mb-8 lg:hidden">
          <div class="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-2xl shadow-primary-500/30"
               style="background: var(--gradient-primary)">
            <span class="text-white text-3xl font-bold">PT</span>
          </div>
          <h2 class="text-2xl font-bold text-surface-900 dark:text-white">PT Manager Pro</h2>
          <p class="mt-1 text-surface-600 dark:text-surface-400">私有种子站智能管理系统</p>
        </div>

        <!-- 登录卡片 -->
        <div class="bg-white/90 dark:bg-surface-800/90 backdrop-blur-xl rounded-2xl shadow-xl shadow-surface-900/10 dark:shadow-black/30 border border-surface-200/50 dark:border-surface-700/50 p-8 lg:p-10">
          <div class="mb-8">
            <h2 class="text-2xl font-bold text-surface-900 dark:text-white">
              欢迎回来
            </h2>
            <p class="mt-2 text-surface-600 dark:text-surface-400">
              请输入您的账户信息登录系统
            </p>
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-6">
            <!-- 用户名 -->
            <div class="form-group">
              <label class="form-label flex items-center gap-2">
                <UserIcon class="w-4 h-4 text-surface-400" />
                用户名
              </label>
              <input
                v-model="form.username"
                type="text"
                required
                class="form-input"
                placeholder="请输入用户名"
                autocomplete="username"
              />
            </div>

            <!-- 密码 -->
            <div class="form-group">
              <label class="form-label flex items-center gap-2">
                <LockClosedIcon class="w-4 h-4 text-surface-400" />
                密码
              </label>
              <div class="relative">
                <input
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  class="form-input pr-12"
                  placeholder="请输入密码"
                  autocomplete="current-password"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors cursor-pointer"
                >
                  <EyeIcon v-if="!showPassword" class="w-5 h-5" />
                  <EyeSlashIcon v-else class="w-5 h-5" />
                </button>
              </div>
            </div>

            <!-- 错误提示 -->
            <transition
              enter-active-class="transition ease-out duration-200"
              enter-from-class="transform opacity-0 -translate-y-2"
              enter-to-class="transform opacity-100 translate-y-0"
              leave-active-class="transition ease-in duration-150"
              leave-from-class="transform opacity-100 translate-y-0"
              leave-to-class="transform opacity-0 -translate-y-2"
            >
              <div v-if="error" class="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50">
                <div class="flex items-start space-x-3">
                  <ExclamationCircleIcon class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p class="text-red-700 dark:text-red-400 text-sm font-medium">登录失败</p>
                    <p class="text-red-600 dark:text-red-400 text-sm mt-0.5">{{ error }}</p>
                  </div>
                </div>
              </div>
            </transition>

            <!-- 登录按钮 -->
            <button
              type="submit"
              :disabled="loading"
              class="group w-full py-3.5 text-white font-semibold rounded-xl shadow-lg shadow-primary-500/30 hover:shadow-xl hover:shadow-primary-500/50 hover:-translate-y-0.5 active:translate-y-0 active:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-surface-800 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 flex items-center justify-center gap-2 cursor-pointer overflow-hidden relative"
              style="background: var(--gradient-primary)"
            >
              <!-- Loading state -->
              <template v-if="loading">
                <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>登录中...</span>
              </template>
              <!-- Normal state -->
              <template v-else>
                <ArrowRightOnRectangleIcon class="w-5 h-5 transition-transform group-hover:translate-x-0.5" />
                <span>登录系统</span>
              </template>
              <!-- Shine effect on hover -->
              <span class="absolute inset-0 overflow-hidden rounded-xl pointer-events-none">
                <span class="absolute top-0 -left-full w-1/2 h-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:left-full transition-all duration-700"></span>
              </span>
            </button>

            <!-- 底部信息 -->
            <div class="flex items-center justify-center pt-4">
              <div class="flex items-center space-x-2 text-sm text-surface-500 dark:text-surface-400">
                <ShieldCheckIcon class="w-4 h-4 text-emerald-500" />
                <span>安全加密传输</span>
              </div>
            </div>
          </form>
        </div>

        <!-- 版本信息 -->
        <div class="text-center mt-6 text-sm text-surface-500 dark:text-surface-400">
          <p>PT Manager Pro v1.0.0</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  UserIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ExclamationCircleIcon,
  ArrowRightOnRectangleIcon,
  ShieldCheckIcon,
  ServerStackIcon,
  RssIcon,
  TrashIcon,
  BoltIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: '',
})
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

async function handleSubmit() {
  loading.value = true
  error.value = ''

  try {
    await authStore.login(form.username, form.password)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || '用户名或密码错误'
  } finally {
    loading.value = false
  }
}
</script>
