<template>
  <div class="min-h-screen flex overflow-hidden">
    <!-- 左侧品牌区域 -->
    <div class="hidden lg:flex lg:w-1/2 relative overflow-hidden"
         style="background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%)">
      <!-- 动态粒子背景 -->
      <div class="absolute inset-0">
        <!-- 浮动光球 -->
        <div class="absolute w-[600px] h-[600px] rounded-full blur-[100px] animate-float-slow"
             style="background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%); top: -10%; left: -10%;"></div>
        <div class="absolute w-[400px] h-[400px] rounded-full blur-[80px] animate-float-medium"
             style="background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); bottom: 10%; right: -5%;"></div>
        <div class="absolute w-[300px] h-[300px] rounded-full blur-[60px] animate-float-fast"
             style="background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%); top: 40%; left: 30%;"></div>

        <!-- 网格背景 -->
        <div class="absolute inset-0 opacity-[0.07]"
             style="background-image: radial-gradient(circle at 1px 1px, white 1px, transparent 0); background-size: 50px 50px;"></div>

        <!-- 六边形装饰 -->
        <svg class="absolute inset-0 w-full h-full opacity-10" preserveAspectRatio="none">
          <pattern id="hexagons" width="50" height="43.4" patternUnits="userSpaceOnUse" patternTransform="scale(2)">
            <polygon points="25,0 50,14.4 50,38.4 25,52.8 0,38.4 0,14.4" fill="none" stroke="white" stroke-width="0.5"/>
          </pattern>
          <rect width="100%" height="100%" fill="url(#hexagons)" class="animate-pattern-move"/>
        </svg>
      </div>

      <!-- 内容 -->
      <div class="relative z-10 flex flex-col justify-center px-12 xl:px-20">
        <div class="mb-8">
          <!-- Logo 动画 -->
          <div class="relative group mb-6">
            <div class="absolute inset-0 w-20 h-20 rounded-2xl bg-white/30 blur-xl group-hover:blur-2xl transition-all duration-500 animate-pulse-slow"></div>
            <div class="relative w-20 h-20 rounded-2xl bg-white/20 backdrop-blur-xl flex items-center justify-center shadow-2xl shadow-black/20 border border-white/20 transform hover:scale-110 hover:rotate-3 transition-all duration-500">
              <span class="text-white text-3xl font-bold tracking-tight">PT</span>
            </div>
            <div class="absolute -bottom-1 -right-1 w-4 h-4 bg-cyan-400 rounded-full border-2 border-white shadow-lg shadow-cyan-500/50">
              <div class="absolute inset-0 rounded-full bg-cyan-400 animate-ping"></div>
            </div>
          </div>

          <!-- 标题动画 -->
          <h1 class="text-4xl xl:text-5xl font-bold text-white mb-4 leading-tight">
            <span class="inline-block animate-fade-in-up">欢迎使用</span>
            <span class="inline-block animate-fade-in-up animation-delay-100 bg-gradient-to-r from-white via-cyan-200 to-white bg-clip-text text-transparent"> PT Manager</span>
          </h1>
          <p class="text-xl text-white/80 max-w-md leading-relaxed animate-fade-in-up animation-delay-200">
            只需几步，即可开启您的智能 PT 管理之旅
          </p>
        </div>

        <!-- 设置步骤指示器 -->
        <div class="space-y-6 mt-8">
          <div class="flex items-center space-x-4 text-white/90 animate-fade-in-up animation-delay-300">
            <div class="relative">
              <div class="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center border-2 border-white/40 shadow-lg">
                <span class="text-lg font-bold">1</span>
              </div>
              <div class="absolute left-1/2 top-full w-0.5 h-8 bg-white/20 -translate-x-1/2"></div>
            </div>
            <div>
              <span class="font-semibold block">创建管理员账户</span>
              <p class="text-sm text-white/60">设置用户名和安全密码</p>
            </div>
          </div>

          <div class="flex items-center space-x-4 text-white/60 animate-fade-in-up animation-delay-400">
            <div class="relative">
              <div class="w-12 h-12 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center border border-white/20">
                <span class="text-lg font-medium">2</span>
              </div>
              <div class="absolute left-1/2 top-full w-0.5 h-8 bg-white/10 -translate-x-1/2"></div>
            </div>
            <div>
              <span class="font-medium block">添加下载器</span>
              <p class="text-sm text-white/40">连接您的 BT 客户端</p>
            </div>
          </div>

          <div class="flex items-center space-x-4 text-white/60 animate-fade-in-up animation-delay-500">
            <div class="w-12 h-12 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center border border-white/20">
              <span class="text-lg font-medium">3</span>
            </div>
            <div>
              <span class="font-medium block">配置自动化规则</span>
              <p class="text-sm text-white/40">开启智能管理功能</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部装饰 -->
      <div class="absolute bottom-0 left-0 right-0 h-32 overflow-hidden">
        <svg class="absolute bottom-0 w-full" viewBox="0 0 1440 120" preserveAspectRatio="none">
          <path class="animate-wave" fill="rgba(255,255,255,0.05)" d="M0,64 C360,128 720,0 1080,64 C1260,96 1350,96 1440,64 L1440,120 L0,120 Z"></path>
          <path class="animate-wave animation-delay-200" fill="rgba(255,255,255,0.03)" d="M0,96 C360,32 720,128 1080,64 C1260,32 1350,96 1440,64 L1440,120 L0,120 Z"></path>
        </svg>
      </div>
    </div>

    <!-- 右侧设置区域 -->
    <div class="flex-1 flex items-center justify-center bg-surface-50 dark:bg-surface-950 px-4 sm:px-6 lg:px-8 relative">
      <!-- 背景装饰 -->
      <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-40 -right-40 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl animate-float-slow"></div>
        <div class="absolute -bottom-40 -left-40 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-float-medium"></div>
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-teal-500/5 rounded-full blur-3xl animate-pulse-slow"></div>
      </div>

      <div class="max-w-md w-full relative">
        <!-- 移动端 Logo -->
        <div class="text-center mb-8 lg:hidden">
          <div class="relative inline-block">
            <div class="absolute inset-0 w-24 h-24 rounded-2xl bg-emerald-500/50 blur-xl animate-pulse-slow"></div>
            <div class="relative w-24 h-24 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-2xl shadow-emerald-500/40 border border-white/20 transform hover:scale-105 transition-transform"
                 style="background: linear-gradient(135deg, #10b981 0%, #059669 100%)">
              <span class="text-white text-4xl font-bold">PT</span>
            </div>
          </div>
          <h2 class="text-2xl font-bold text-surface-900 dark:text-white">PT Manager Pro</h2>
          <p class="mt-1 text-surface-600 dark:text-surface-400">私有种子站智能管理系统</p>
        </div>

        <!-- 设置卡片 - 3D 效果 -->
        <div class="group perspective-1000">
          <div class="bg-white/90 dark:bg-surface-800/90 backdrop-blur-2xl rounded-3xl shadow-2xl shadow-surface-900/10 dark:shadow-black/40 border border-surface-200/50 dark:border-surface-700/50 p-8 lg:p-10 transform transition-all duration-500 hover:shadow-3xl"
               :class="{ 'scale-[1.02]': isFormFocused }">

            <!-- 顶部装饰条 -->
            <div class="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-1 rounded-full bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 opacity-80"></div>

            <div class="mb-8">
              <h2 class="text-2xl font-bold text-surface-900 dark:text-white flex items-center gap-3">
                <span class="inline-block p-2 rounded-xl bg-gradient-to-br from-emerald-500/10 to-cyan-500/10">
                  <SparklesIcon class="w-6 h-6 text-emerald-500" />
                </span>
                初始化设置
              </h2>
              <p class="mt-2 text-surface-600 dark:text-surface-400">
                首次使用，请创建管理员账户
              </p>
            </div>

            <form @submit.prevent="handleSubmit" class="space-y-5">
              <!-- 用户名 - 动态边框 -->
              <div class="form-group relative">
                <label class="form-label flex items-center gap-2 text-surface-700 dark:text-surface-300">
                  <UserIcon class="w-4 h-4 text-emerald-500" />
                  用户名
                </label>
                <div class="relative group/input">
                  <div class="absolute -inset-0.5 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 rounded-xl opacity-0 group-focus-within/input:opacity-100 blur transition-opacity duration-300"></div>
                  <input
                    v-model="form.username"
                    type="text"
                    required
                    minlength="3"
                    class="relative form-input bg-white dark:bg-surface-900 focus:ring-0 border-surface-200 dark:border-surface-700 focus:border-transparent"
                    placeholder="请设置管理员用户名"
                    autocomplete="username"
                    @focus="isFormFocused = true"
                    @blur="isFormFocused = false"
                  />
                </div>
              </div>

              <!-- 密码 - 动态边框 -->
              <div class="form-group relative">
                <label class="form-label flex items-center gap-2 text-surface-700 dark:text-surface-300">
                  <LockClosedIcon class="w-4 h-4 text-emerald-500" />
                  密码
                </label>
                <div class="relative group/input">
                  <div class="absolute -inset-0.5 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 rounded-xl opacity-0 group-focus-within/input:opacity-100 blur transition-opacity duration-300"></div>
                  <input
                    v-model="form.password"
                    :type="showPassword ? 'text' : 'password'"
                    required
                    minlength="6"
                    class="relative form-input pr-12 bg-white dark:bg-surface-900 focus:ring-0 border-surface-200 dark:border-surface-700 focus:border-transparent"
                    placeholder="请设置密码（至少6位）"
                    autocomplete="new-password"
                    @focus="isFormFocused = true"
                    @blur="isFormFocused = false"
                  />
                  <button
                    type="button"
                    @click="showPassword = !showPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-surface-400 hover:text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-all duration-200 cursor-pointer"
                  >
                    <EyeIcon v-if="!showPassword" class="w-5 h-5" />
                    <EyeSlashIcon v-else class="w-5 h-5" />
                  </button>
                </div>
                <!-- 密码强度指示器 -->
                <div v-if="form.password" class="mt-2 flex items-center gap-2">
                  <div class="flex-1 h-1.5 rounded-full bg-surface-200 dark:bg-surface-700 overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-300"
                         :class="passwordStrengthClass"
                         :style="{ width: `${passwordStrength}%` }"></div>
                  </div>
                  <span class="text-xs" :class="passwordStrengthTextClass">{{ passwordStrengthText }}</span>
                </div>
              </div>

              <!-- 确认密码 - 动态边框 -->
              <div class="form-group relative">
                <label class="form-label flex items-center gap-2 text-surface-700 dark:text-surface-300">
                  <ShieldCheckIcon class="w-4 h-4 text-emerald-500" />
                  确认密码
                </label>
                <div class="relative group/input">
                  <div class="absolute -inset-0.5 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 rounded-xl opacity-0 group-focus-within/input:opacity-100 blur transition-opacity duration-300"></div>
                  <input
                    v-model="form.confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    required
                    class="relative form-input pr-12 bg-white dark:bg-surface-900 focus:ring-0 border-surface-200 dark:border-surface-700 focus:border-transparent"
                    placeholder="请再次输入密码"
                    autocomplete="new-password"
                    @focus="isFormFocused = true"
                    @blur="isFormFocused = false"
                  />
                  <button
                    type="button"
                    @click="showConfirmPassword = !showConfirmPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-surface-400 hover:text-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-all duration-200 cursor-pointer"
                  >
                    <EyeIcon v-if="!showConfirmPassword" class="w-5 h-5" />
                    <EyeSlashIcon v-else class="w-5 h-5" />
                  </button>
                </div>
                <!-- 密码匹配指示 -->
                <div v-if="form.confirmPassword" class="mt-2 flex items-center gap-2">
                  <CheckCircleIcon v-if="passwordsMatch" class="w-4 h-4 text-emerald-500" />
                  <XCircleIcon v-else class="w-4 h-4 text-red-500" />
                  <span class="text-xs" :class="passwordsMatch ? 'text-emerald-500' : 'text-red-500'">
                    {{ passwordsMatch ? '密码匹配' : '密码不匹配' }}
                  </span>
                </div>
              </div>

              <!-- 错误提示 -->
              <transition
                enter-active-class="transition ease-out duration-300"
                enter-from-class="transform opacity-0 scale-95 -translate-y-2"
                enter-to-class="transform opacity-100 scale-100 translate-y-0"
                leave-active-class="transition ease-in duration-200"
                leave-from-class="transform opacity-100 scale-100 translate-y-0"
                leave-to-class="transform opacity-0 scale-95 -translate-y-2"
              >
                <div v-if="error" class="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 backdrop-blur-sm">
                  <div class="flex items-start space-x-3">
                    <div class="p-1 rounded-lg bg-red-100 dark:bg-red-900/30">
                      <ExclamationCircleIcon class="w-5 h-5 text-red-500" />
                    </div>
                    <div>
                      <p class="text-red-700 dark:text-red-400 text-sm font-medium">初始化失败</p>
                      <p class="text-red-600 dark:text-red-400 text-sm mt-0.5">{{ error }}</p>
                    </div>
                  </div>
                </div>
              </transition>

              <!-- 提交按钮 - 高级动画 -->
              <button
                type="submit"
                :disabled="loading || !canSubmit"
                class="group relative w-full py-4 text-white font-semibold rounded-xl overflow-hidden transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-surface-800 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                <!-- 渐变背景 -->
                <div class="absolute inset-0 bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-500 bg-[length:200%_100%] animate-gradient-x"></div>

                <!-- 悬浮光效 -->
                <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
                </div>

                <!-- 按钮内容 -->
                <span class="relative flex items-center justify-center gap-2">
                  <template v-if="loading">
                    <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>创建中...</span>
                  </template>
                  <template v-else>
                    <RocketLaunchIcon class="w-5 h-5 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                    <span>创建账户并开始使用</span>
                  </template>
                </span>
              </button>

              <!-- 底部信息 -->
              <div class="flex items-center justify-center pt-4">
                <div class="flex items-center space-x-2 text-sm text-surface-500 dark:text-surface-400 px-4 py-2 rounded-full bg-surface-100/50 dark:bg-surface-800/50 backdrop-blur-sm">
                  <ShieldCheckIcon class="w-4 h-4 text-emerald-500 animate-pulse-slow" />
                  <span>数据本地存储，安全可靠</span>
                </div>
              </div>
            </form>
          </div>
        </div>

        <!-- 版本信息 -->
        <div class="text-center mt-6 text-sm text-surface-500 dark:text-surface-400">
          <p class="flex items-center justify-center gap-2">
            <span class="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            PT Manager Pro v1.0.0
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getToast } from '@/composables/useToast'
import {
  UserIcon,
  LockClosedIcon,
  EyeIcon,
  EyeSlashIcon,
  ExclamationCircleIcon,
  ShieldCheckIcon,
  SparklesIcon,
  RocketLaunchIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()
const toast = getToast()

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
})
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const isFormFocused = ref(false)

// 密码强度计算
const passwordStrength = computed(() => {
  const pwd = form.password
  if (!pwd) return 0
  let strength = 0
  if (pwd.length >= 6) strength += 25
  if (pwd.length >= 8) strength += 15
  if (/[a-z]/.test(pwd)) strength += 15
  if (/[A-Z]/.test(pwd)) strength += 15
  if (/[0-9]/.test(pwd)) strength += 15
  if (/[^a-zA-Z0-9]/.test(pwd)) strength += 15
  return Math.min(strength, 100)
})

const passwordStrengthClass = computed(() => {
  const strength = passwordStrength.value
  if (strength < 40) return 'bg-red-500'
  if (strength < 70) return 'bg-yellow-500'
  return 'bg-emerald-500'
})

const passwordStrengthTextClass = computed(() => {
  const strength = passwordStrength.value
  if (strength < 40) return 'text-red-500'
  if (strength < 70) return 'text-yellow-500'
  return 'text-emerald-500'
})

const passwordStrengthText = computed(() => {
  const strength = passwordStrength.value
  if (strength < 40) return '弱'
  if (strength < 70) return '中'
  return '强'
})

const passwordsMatch = computed(() => {
  return form.password && form.confirmPassword && form.password === form.confirmPassword
})

const canSubmit = computed(() => {
  return form.username.length >= 3 && form.password.length >= 6 && passwordsMatch.value
})

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
    toast.success('账户创建成功')
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || '初始化失败，请检查后端服务是否正常运行'
    toast.error('初始化失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 动画关键帧 */
@keyframes float-slow {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  33% { transform: translate(30px, -30px) rotate(5deg); }
  66% { transform: translate(-20px, 20px) rotate(-5deg); }
}

@keyframes float-medium {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-40px, 30px); }
}

@keyframes float-fast {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(20px, -20px) scale(1.1); }
}

@keyframes pulse-slow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes gradient-x {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes wave {
  0% { transform: translateX(0); }
  50% { transform: translateX(-25px); }
  100% { transform: translateX(0); }
}

@keyframes pattern-move {
  0% { transform: translateX(0) translateY(0); }
  100% { transform: translateX(50px) translateY(43.4px); }
}

/* 动画类 */
.animate-float-slow { animation: float-slow 20s ease-in-out infinite; }
.animate-float-medium { animation: float-medium 15s ease-in-out infinite; }
.animate-float-fast { animation: float-fast 10s ease-in-out infinite; }
.animate-pulse-slow { animation: pulse-slow 4s ease-in-out infinite; }
.animate-fade-in-up { animation: fade-in-up 0.6s ease-out forwards; }
.animate-gradient-x { animation: gradient-x 3s ease infinite; }
.animate-wave { animation: wave 8s ease-in-out infinite; }
.animate-pattern-move { animation: pattern-move 20s linear infinite; }

/* 延迟类 */
.animation-delay-100 { animation-delay: 100ms; }
.animation-delay-200 { animation-delay: 200ms; }
.animation-delay-300 { animation-delay: 300ms; }
.animation-delay-400 { animation-delay: 400ms; }
.animation-delay-500 { animation-delay: 500ms; }

/* 3D 透视 */
.perspective-1000 { perspective: 1000px; }
.shadow-3xl { box-shadow: 0 35px 60px -15px rgba(0, 0, 0, 0.3); }
</style>
