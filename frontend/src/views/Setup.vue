<template>
  <div class="min-h-screen flex">
    <!-- 左侧品牌区域 -->
    <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 relative overflow-hidden">
      <!-- 装饰背景 -->
      <div class="absolute inset-0">
        <div class="absolute top-0 left-0 w-96 h-96 bg-white/5 rounded-full -translate-x-1/2 -translate-y-1/2"></div>
        <div class="absolute bottom-0 right-0 w-80 h-80 bg-white/5 rounded-full translate-x-1/3 translate-y-1/3"></div>
        <div class="absolute top-1/2 left-1/2 w-64 h-64 bg-white/5 rounded-full -translate-x-1/2 -translate-y-1/2"></div>
      </div>

      <!-- 内容 -->
      <div class="relative z-10 flex flex-col justify-center px-12 xl:px-20">
        <div class="mb-8">
          <div class="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center mb-6">
            <span class="text-white text-2xl font-bold">PT</span>
          </div>
          <h1 class="text-4xl xl:text-5xl font-bold text-white mb-4">
            PT Manager Pro
          </h1>
          <p class="text-xl text-white/80 max-w-md">
            私有种子站智能管理系统，让资源管理更简单高效
          </p>
        </div>

        <!-- 功能特点 -->
        <div class="space-y-4 mt-8">
          <div class="flex items-center space-x-3 text-white/90">
            <div class="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
              <ServerStackIcon class="w-5 h-5" />
            </div>
            <span>多下载器统一管理</span>
          </div>
          <div class="flex items-center space-x-3 text-white/90">
            <div class="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
              <RssIcon class="w-5 h-5" />
            </div>
            <span>智能 RSS 订阅推送</span>
          </div>
          <div class="flex items-center space-x-3 text-white/90">
            <div class="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
              <TrashIcon class="w-5 h-5" />
            </div>
            <span>自动化删种规则</span>
          </div>
          <div class="flex items-center space-x-3 text-white/90">
            <div class="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
              <BoltIcon class="w-5 h-5" />
            </div>
            <span>动态限速调控</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧设置区域 -->
    <div class="flex-1 flex items-center justify-center bg-surface-50 dark:bg-surface-900 px-4 sm:px-6 lg:px-8">
      <!-- 移动端背景装饰 -->
      <div class="absolute inset-0 lg:hidden overflow-hidden pointer-events-none">
        <div class="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/10 rounded-full blur-3xl"></div>
        <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      <div class="max-w-md w-full relative">
        <!-- 移动端 Logo -->
        <div class="text-center mb-8 lg:hidden">
          <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center mx-auto mb-4 shadow-2xl shadow-primary-500/30">
            <span class="text-white text-3xl font-bold">PT</span>
          </div>
          <h2 class="text-2xl font-bold text-surface-900 dark:text-white">PT Manager Pro</h2>
          <p class="mt-1 text-surface-600 dark:text-surface-400">私有种子站智能管理系统</p>
        </div>

        <!-- 设置卡片 -->
        <div class="bg-white dark:bg-surface-800 rounded-2xl shadow-xl shadow-surface-200/50 dark:shadow-surface-900/50 p-8 lg:p-10">
          <div class="mb-8">
            <div class="flex items-center space-x-3 mb-2">
              <div class="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
                <SparklesIcon class="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <h2 class="text-2xl font-bold text-surface-900 dark:text-white">
                初始化设置
              </h2>
            </div>
            <p class="mt-2 text-surface-600 dark:text-surface-400">
              首次使用，请创建管理员账户
            </p>
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-5">
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
                minlength="3"
                class="form-input"
                placeholder="请设置管理员用户名"
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
                  minlength="6"
                  class="form-input pr-12"
                  placeholder="请设置密码（至少6位）"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors"
                >
                  <EyeIcon v-if="!showPassword" class="w-5 h-5" />
                  <EyeSlashIcon v-else class="w-5 h-5" />
                </button>
              </div>
            </div>

            <!-- 确认密码 -->
            <div class="form-group">
              <label class="form-label flex items-center gap-2">
                <ShieldCheckIcon class="w-4 h-4 text-surface-400" />
                确认密码
              </label>
              <div class="relative">
                <input
                  v-model="form.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  required
                  class="form-input pr-12"
                  placeholder="请再次输入密码"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  @click="showConfirmPassword = !showConfirmPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-lg text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors"
                >
                  <EyeIcon v-if="!showConfirmPassword" class="w-5 h-5" />
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
              <div v-if="error" class="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                <div class="flex items-start space-x-3">
                  <ExclamationCircleIcon class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p class="text-red-700 dark:text-red-400 text-sm font-medium">初始化失败</p>
                    <p class="text-red-600 dark:text-red-400 text-sm mt-0.5">{{ error }}</p>
                  </div>
                </div>
              </div>
            </transition>

            <!-- 提交按钮 -->
            <Button
              type="submit"
              variant="primary"
              class="w-full py-3"
              :loading="loading"
            >
              <RocketLaunchIcon v-if="!loading" class="w-5 h-5" />
              创建账户并开始使用
            </Button>

            <!-- 底部信息 -->
            <div class="flex items-center justify-center pt-4">
              <div class="flex items-center space-x-2 text-sm text-surface-500 dark:text-surface-400">
                <ShieldCheckIcon class="w-4 h-4" />
                <span>数据本地存储，安全可靠</span>
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
import Button from '@/components/common/Button.vue'
import {
  UserIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ExclamationCircleIcon,
  ShieldCheckIcon,
  SparklesIcon,
  RocketLaunchIcon,
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
  confirmPassword: '',
})
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

async function handleSubmit() {
  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }

  if (form.password.length < 6) {
    error.value = '密码至少需要6位字符'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await authStore.setup(form.username, form.password)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || '初始化失败，请检查后端服务是否正常运行'
  } finally {
    loading.value = false
  }
}
</script>
