<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-gray-100 to-gray-200 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 px-4">
    <!-- 背景装饰 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/10 rounded-full blur-3xl"></div>
      <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
    </div>

    <div class="max-w-md w-full relative">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="relative inline-block">
          <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center mx-auto mb-4 shadow-2xl shadow-primary-500/30 transform hover:scale-105 transition-transform">
            <span class="text-white text-3xl font-bold">PT</span>
          </div>
          <div class="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-4 border-white dark:border-gray-900 animate-pulse"></div>
        </div>
        <h2 class="text-3xl font-bold text-gray-900 dark:text-white mt-4">PT Manager Pro</h2>
        <p class="mt-2 text-gray-600 dark:text-gray-400">私有种子站智能管理系统</p>
      </div>

      <!-- Form -->
      <div class="card-glass p-8">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <div class="form-group">
            <label class="form-label">
              <UserIcon class="w-4 h-4 inline mr-1" />
              用户名
            </label>
            <div class="relative">
              <input
                v-model="form.username"
                type="text"
                required
                class="form-input pl-10"
                placeholder="请输入用户名"
                autocomplete="username"
              />
              <UserIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">
              <LockClosedIcon class="w-4 h-4 inline mr-1" />
              密码
            </label>
            <div class="relative">
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                required
                class="form-input pl-10 pr-10"
                placeholder="请输入密码"
                autocomplete="current-password"
              />
              <LockClosedIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <EyeIcon v-if="!showPassword" class="w-5 h-5" />
                <EyeSlashIcon v-else class="w-5 h-5" />
              </button>
            </div>
          </div>

          <div v-if="error" class="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-start space-x-3">
            <ExclamationCircleIcon class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p class="text-red-700 dark:text-red-400 text-sm font-medium">登录失败</p>
              <p class="text-red-600 dark:text-red-400 text-sm mt-1">{{ error }}</p>
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            class="w-full py-3"
            :loading="loading"
          >
            <ArrowRightOnRectangleIcon v-if="!loading" class="w-5 h-5 mr-2" />
            登录系统
          </Button>

          <div class="flex items-center justify-center space-x-4 pt-4 border-t border-gray-200/50 dark:border-gray-700/50">
            <div class="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
              <ShieldCheckIcon class="w-4 h-4" />
              <span>安全加密传输</span>
            </div>
          </div>
        </form>
      </div>

      <!-- 底部信息 -->
      <div class="text-center mt-6 text-sm text-gray-500 dark:text-gray-400">
        <p>PT Manager Pro v1.0.0</p>
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
  ArrowRightOnRectangleIcon,
  ShieldCheckIcon,
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
