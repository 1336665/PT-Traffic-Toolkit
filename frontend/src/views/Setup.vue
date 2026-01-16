<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
    <div class="max-w-md w-full">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 rounded-xl bg-primary-600 flex items-center justify-center mx-auto mb-4">
          <span class="text-white text-2xl font-bold">PT</span>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ $t('auth.welcomeTitle') }}</h2>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">{{ $t('auth.setupDesc') }}</p>
      </div>

      <!-- Form -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        <form @submit.prevent="handleSubmit">
          <div class="space-y-4">
            <div>
              <label class="form-label">{{ $t('auth.username') }}</label>
              <input
                v-model="form.username"
                type="text"
                required
                minlength="3"
                class="form-input"
                :placeholder="$t('auth.chooseUsername')"
              />
            </div>

            <div>
              <label class="form-label">{{ $t('auth.password') }}</label>
              <input
                v-model="form.password"
                type="password"
                required
                minlength="6"
                class="form-input"
                :placeholder="$t('auth.createPassword')"
              />
            </div>

            <div>
              <label class="form-label">{{ $t('auth.confirmPassword') }}</label>
              <input
                v-model="form.confirmPassword"
                type="password"
                required
                class="form-input"
                :placeholder="$t('auth.confirmPassword')"
              />
            </div>

            <div v-if="error" class="p-3 rounded-md bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
              {{ error }}
            </div>

            <Button
              type="submit"
              variant="primary"
              class="w-full"
              :loading="loading"
            >
              {{ $t('auth.createAccount') }}
            </Button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Button from '@/components/common/Button.vue'

const $t = inject('t')
const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
})
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  if (form.password !== form.confirmPassword) {
    error.value = $t('auth.passwordMismatch')
    return
  }

  loading.value = true
  error.value = ''

  try {
    await authStore.setup(form.username, form.password)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || $t('auth.setupFailed')
  } finally {
    loading.value = false
  }
}
</script>
