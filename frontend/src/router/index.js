import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('@/views/Setup.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/components/layout/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
      },
      {
        path: 'downloaders',
        name: 'Downloaders',
        component: () => import('@/views/Downloaders.vue'),
      },
      {
        path: 'rss',
        name: 'RssManager',
        component: () => import('@/views/RssManager.vue'),
      },
      {
        path: 'delete-rules',
        name: 'DeleteRules',
        component: () => import('@/views/DeleteRules.vue'),
      },
      {
        path: 'speed-limit',
        name: 'SpeedLimit',
        component: () => import('@/views/SpeedLimit.vue'),
      },
      {
        path: 'u2-magic',
        name: 'U2Magic',
        component: () => import('@/views/U2Magic.vue'),
      },
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/views/Statistics.vue'),
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue'),
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
      },
      {
        path: 'netcup',
        name: 'NetcupMonitor',
        component: () => import('@/views/NetcupMonitor.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Check system initialization status
  if (!authStore.statusChecked) {
    await authStore.checkStatus()
  }

  // Redirect to setup if not initialized
  if (!authStore.initialized && to.name !== 'Setup') {
    return next({ name: 'Setup' })
  }

  // Redirect to login if not authenticated
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next({ name: 'Login' })
  }

  // Redirect to dashboard if already authenticated
  if ((to.name === 'Login' || to.name === 'Setup') && authStore.isAuthenticated) {
    return next({ name: 'Dashboard' })
  }

  next()
})

export default router
