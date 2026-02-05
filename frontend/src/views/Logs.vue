<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/30">
          <DocumentTextIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">系统日志</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">查看和管理系统运行日志</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <label class="flex items-center space-x-2 cursor-pointer select-none">
          <div class="relative">
            <input v-model="autoRefresh" type="checkbox" class="sr-only peer" />
            <div class="w-10 h-5 bg-surface-200 peer-focus:outline-none rounded-full peer dark:bg-surface-700 peer-checked:after:translate-x-5 peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-surface-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-surface-600 peer-checked:bg-primary-600"></div>
          </div>
          <span class="text-sm text-surface-600 dark:text-surface-400">自动刷新</span>
        </label>
        <Button variant="secondary" size="sm" @click="handleRefresh" :loading="refreshing">
          <ArrowPathIcon class="w-4 h-4" />
          刷新
        </Button>
        <Button variant="danger" size="sm" @click="showClearModal = true">
          <TrashIcon class="w-4 h-4" />
          清理
        </Button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
      <!-- 总日志数 -->
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20 border border-blue-200/50 dark:border-blue-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-blue-500/10 dark:bg-blue-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-blue-600/70 dark:text-blue-400/70 uppercase tracking-wide">总日志数</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ stats.total || 0 }}</p>
          </div>
          <div class="p-3 rounded-xl bg-blue-500/20 dark:bg-blue-500/30">
            <DocumentTextIcon class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </div>

      <!-- 信息 -->
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-green-500/10 to-emerald-500/10 dark:from-green-500/20 dark:to-emerald-500/20 border border-green-200/50 dark:border-green-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-green-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-green-500/10 dark:bg-green-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-green-600/70 dark:text-green-400/70 uppercase tracking-wide">信息</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ stats.by_level?.INFO || 0 }}</p>
          </div>
          <div class="p-3 rounded-xl bg-green-500/20 dark:bg-green-500/30">
            <InformationCircleIcon class="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
        </div>
      </div>

      <!-- 警告 -->
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-yellow-500/10 to-amber-500/10 dark:from-yellow-500/20 dark:to-amber-500/20 border border-yellow-200/50 dark:border-yellow-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-yellow-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-yellow-500/10 dark:bg-yellow-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-yellow-600/70 dark:text-yellow-400/70 uppercase tracking-wide">警告</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ stats.by_level?.WARNING || 0 }}</p>
          </div>
          <div class="p-3 rounded-xl bg-yellow-500/20 dark:bg-yellow-500/30">
            <ExclamationTriangleIcon class="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
          </div>
        </div>
      </div>

      <!-- 错误 -->
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-red-500/10 to-rose-500/10 dark:from-red-500/20 dark:to-rose-500/20 border border-red-200/50 dark:border-red-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-red-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-red-500/10 dark:bg-red-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-red-600/70 dark:text-red-400/70 uppercase tracking-wide">错误</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ stats.by_level?.ERROR || 0 }}</p>
          </div>
          <div class="p-3 rounded-xl bg-red-500/20 dark:bg-red-500/30">
            <XCircleIcon class="w-6 h-6 text-red-600 dark:text-red-400" />
          </div>
        </div>
      </div>

      <!-- 严重 -->
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-500/20 dark:to-pink-500/20 border border-purple-200/50 dark:border-purple-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-purple-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-purple-500/10 dark:bg-purple-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-purple-600/70 dark:text-purple-400/70 uppercase tracking-wide">严重</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ stats.by_level?.CRITICAL || 0 }}</p>
          </div>
          <div class="p-3 rounded-xl bg-purple-500/20 dark:bg-purple-500/30">
            <FireIcon class="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
      </div>
    </div>

    <!-- 过滤器 -->
    <Card>
      <template #header>
        <div class="flex items-center space-x-3">
          <div class="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
            <FunnelIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h3 class="font-semibold text-surface-900 dark:text-white">日志过滤</h3>
            <p class="text-xs text-surface-500 dark:text-surface-400">筛选并搜索日志记录</p>
          </div>
        </div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="form-group">
          <label class="form-label">日志级别</label>
          <select v-model="filter.level" class="form-select">
            <option value="">全部级别</option>
            <option value="DEBUG">调试</option>
            <option value="INFO">信息</option>
            <option value="WARNING">警告</option>
            <option value="ERROR">错误</option>
            <option value="CRITICAL">严重</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">模块</label>
          <select v-model="filter.module" class="form-select">
            <option value="">全部模块</option>
            <option value="rss">RSS订阅</option>
            <option value="delete">删种规则</option>
            <option value="speed_limit">动态限速</option>
            <option value="u2_magic">U2追魔</option>
            <option value="downloader">下载器</option>
            <option value="auth">认证</option>
            <option value="system">系统</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">显示数量</label>
          <select v-model="filter.limit" class="form-select">
            <option :value="100">最近 100 条</option>
            <option :value="500">最近 500 条</option>
            <option :value="1000">最近 1000 条</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">搜索</label>
          <div class="relative">
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
            <input
              v-model="filter.search"
              type="text"
              class="form-input pl-10"
              placeholder="搜索日志内容..."
            />
          </div>
        </div>
      </div>
    </Card>

    <!-- 日志列表 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <QueueListIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">日志记录</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">
                显示 {{ displayLogs.length }} 条记录
                <span v-if="autoRefresh" class="text-green-500 ml-2">
                  <span class="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></span>
                  实时更新中
                </span>
              </p>
            </div>
          </div>
        </div>
      </template>

      <!-- 初始加载状态 -->
      <div v-if="initialLoading" class="flex flex-col items-center justify-center py-16">
        <div class="w-12 h-12 rounded-full border-4 border-primary-200 border-t-primary-600 animate-spin"></div>
        <p class="mt-4 text-surface-500 dark:text-surface-400">加载日志中...</p>
      </div>

      <!-- 空状态 - 只有在非加载状态且确实没有日志时显示 -->
      <div v-else-if="!initialLoading && displayLogs.length === 0" class="empty-state py-16">
        <div class="empty-state-icon">
          <DocumentTextIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title">暂无日志记录</p>
        <p class="empty-state-description">
          {{ filter.module || filter.level ? '当前筛选条件下没有日志记录' : '系统运行时会自动记录日志' }}
        </p>
      </div>

      <!-- 日志表格 -->
      <div v-else class="relative overflow-x-auto max-h-[600px] overflow-y-auto">
        <!-- Loading overlay during refresh -->
        <transition
          enter-active-class="transition-opacity duration-200"
          enter-from-class="opacity-0"
          enter-to-class="opacity-100"
          leave-active-class="transition-opacity duration-200"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div v-if="refreshing" class="absolute inset-0 z-20 flex items-center justify-center bg-white/60 dark:bg-surface-800/60 backdrop-blur-sm">
            <div class="flex flex-col items-center">
              <div class="w-10 h-10 rounded-full border-3 border-primary-200 border-t-primary-600 animate-spin"></div>
              <p class="mt-3 text-sm text-surface-500 dark:text-surface-400">刷新中...</p>
            </div>
          </div>
        </transition>
        <table class="data-table">
          <thead class="sticky top-0 z-10">
            <tr>
              <th class="w-44">时间</th>
              <th class="w-24">级别</th>
              <th class="w-28">模块</th>
              <th>消息内容</th>
            </tr>
          </thead>
          <tbody class="font-mono text-xs">
            <tr
              v-for="(log, idx) in displayLogs"
              :key="log.id || idx"
              :class="getRowClass(log.level)"
              class="transition-colors"
            >
              <td class="text-surface-500 dark:text-surface-400">
                <div class="flex items-center space-x-2">
                  <ClockIcon class="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{{ formatLogTime(log.timestamp) }}</span>
                </div>
              </td>
              <td>
                <span :class="getLevelBadgeClass(log.level)" class="inline-flex items-center">
                  <component :is="getLevelIcon(log.level)" class="w-3 h-3 mr-1" />
                  {{ getLevelText(log.level) }}
                </span>
              </td>
              <td>
                <span class="badge badge-gray">{{ getModuleText(log.module) }}</span>
              </td>
              <td class="text-surface-900 dark:text-white">
                <div class="max-w-2xl">
                  <p class="truncate" :title="log.message">{{ log.message }}</p>
                  <p v-if="log.details" class="text-surface-400 dark:text-surface-500 text-[10px] mt-1 truncate" :title="log.details">
                    {{ log.details }}
                  </p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- 清理日志确认对话框 -->
    <Modal v-model="showClearModal" title="清理日志">
      <div class="space-y-4">
        <div class="flex items-start space-x-3 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
          <ExclamationTriangleIcon class="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p class="text-amber-700 dark:text-amber-400 text-sm font-medium">注意</p>
            <p class="text-amber-600 dark:text-amber-400 text-sm mt-0.5">此操作将永久删除选定时间范围之前的所有日志记录，无法恢复。</p>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">清理范围</label>
          <select v-model="clearHours" class="form-select">
            <option :value="1">1小时前的日志</option>
            <option :value="6">6小时前的日志</option>
            <option :value="24">24小时前的日志</option>
            <option :value="72">3天前的日志</option>
            <option :value="168">7天前的日志</option>
          </select>
        </div>
      </div>
      <template #footer>
        <Button variant="secondary" @click="showClearModal = false">取消</Button>
        <Button variant="danger" @click="clearLogs" :loading="clearing">
          <TrashIcon class="w-4 h-4" />
          确认清理
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { logsApi } from '@/api'
import { formatTime } from '@/utils/format'
import { getToast } from '@/composables/useToast'
import { useRealtime } from '@/services/realtime'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import {
  ArrowPathIcon,
  DocumentTextIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  FireIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  TrashIcon,
  BugAntIcon,
  QueueListIcon,
} from '@heroicons/vue/24/outline'

const toast = getToast()

// 状态
const logs = ref([])
const stats = ref({})
const initialLoading = ref(true)  // 初始加载状态
const refreshing = ref(false)     // 刷新按钮状态
const clearing = ref(false)
const autoRefresh = ref(true)
const showClearModal = ref(false)
const clearHours = ref(24)
const realtime = useRealtime()
const unsubscribeHandlers = []

// 过滤器
const filter = reactive({
  level: '',
  module: '',
  limit: 100,
  search: '',
})

// 计算属性：显示的日志（本地搜索过滤）
const displayLogs = computed(() => {
  let result = logs.value || []

  // 确保是数组
  if (!Array.isArray(result)) {
    console.warn('logs.value is not an array:', result)
    return []
  }

  // 本地搜索过滤
  if (filter.search) {
    const searchLower = filter.search.toLowerCase()
    result = result.filter(log =>
      (log.message && log.message.toLowerCase().includes(searchLower)) ||
      (log.details && log.details.toLowerCase().includes(searchLower))
    )
  }

  return result
})

// 格式化时间
function formatLogTime(timestamp) {
  return formatTime(timestamp, 'MM-DD HH:mm:ss')
}

// 级别文本
function getLevelText(level) {
  const texts = {
    DEBUG: '调试',
    INFO: '信息',
    WARNING: '警告',
    ERROR: '错误',
    CRITICAL: '严重',
  }
  return texts[level] || level
}

// 模块文本
function getModuleText(module) {
  const texts = {
    rss: 'RSS',
    delete: '删种',
    speed_limit: '限速',
    u2_magic: 'U2',
    downloader: '下载器',
    auth: '认证',
    system: '系统',
  }
  return texts[module] || module
}

// 级别图标
function getLevelIcon(level) {
  const icons = {
    DEBUG: BugAntIcon,
    INFO: InformationCircleIcon,
    WARNING: ExclamationTriangleIcon,
    ERROR: XCircleIcon,
    CRITICAL: FireIcon,
  }
  return icons[level] || InformationCircleIcon
}

// 级别徽章样式
function getLevelBadgeClass(level) {
  const classes = {
    DEBUG: 'badge badge-gray',
    INFO: 'badge badge-info',
    WARNING: 'badge badge-warning',
    ERROR: 'badge badge-danger',
    CRITICAL: 'badge bg-red-600 text-white dark:bg-red-500',
  }
  return classes[level] || classes.INFO
}

// 行样式
function getRowClass(level) {
  if (level === 'ERROR' || level === 'CRITICAL') {
    return 'bg-red-50/50 dark:bg-red-900/10 hover:bg-red-100/50 dark:hover:bg-red-900/20'
  }
  if (level === 'WARNING') {
    return 'bg-yellow-50/50 dark:bg-yellow-900/10 hover:bg-yellow-100/50 dark:hover:bg-yellow-900/20'
  }
  return 'hover:bg-surface-50 dark:hover:bg-surface-800/50'
}

// 加载日志
async function loadLogs() {
  try {
    const params = {
      limit: filter.limit,
      ...(filter.level && { level: filter.level }),
      ...(filter.module && { module: filter.module }),
    }

    const [logsRes, statsRes] = await Promise.all([
      logsApi.getLogs(params),
      logsApi.getStats(24),
    ])

    // 处理日志数据 - 兼容不同的 API 响应格式
    const logsData = logsRes.data
    if (Array.isArray(logsData)) {
      logs.value = logsData
    } else if (logsData && Array.isArray(logsData.items)) {
      logs.value = logsData.items
    } else if (logsData && Array.isArray(logsData.logs)) {
      logs.value = logsData.logs
    } else {
      logs.value = []
    }

    // 处理统计数据
    stats.value = statsRes.data || {}

  } catch (error) {
    console.error('Failed to load logs:', error)
    logs.value = []
  }
}

// 手动刷新
async function handleRefresh() {
  refreshing.value = true
  try {
    await loadLogs()
    toast.success('日志已刷新')
  } catch (error) {
    toast.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

// 清理日志
async function clearLogs() {
  clearing.value = true
  try {
    await logsApi.clearLogs(clearHours.value)
    showClearModal.value = false
    await loadLogs()
    toast.success('日志清理成功')
  } catch (error) {
    console.error('Failed to clear logs:', error)
    toast.error('清理失败')
  } finally {
    clearing.value = false
  }
}

// 监听过滤器变化 - 使用防抖
let filterDebounceTimer = null
watch(
  [() => filter.level, () => filter.module, () => filter.limit],
  () => {
    if (filterDebounceTimer) {
      clearTimeout(filterDebounceTimer)
    }
    filterDebounceTimer = setTimeout(() => {
      loadLogs()
    }, 150)
  }
)

// 初始化
onMounted(async () => {
  initialLoading.value = true
  await loadLogs()
  initialLoading.value = false
  realtime.connect()
  unsubscribeHandlers.push(
    realtime.subscribe('logs', (newLogs) => {
      if (!autoRefresh.value || !Array.isArray(newLogs)) return
      const filtered = newLogs.filter(log => {
        if (filter.level && log.level !== filter.level) return false
        if (filter.module && log.module !== filter.module) return false
        return true
      })
      if (filtered.length === 0) return
      logs.value = [...filtered.reverse(), ...logs.value].slice(0, filter.limit)
    })
  )
})

// 清理
onUnmounted(() => {
  if (filterDebounceTimer) {
    clearTimeout(filterDebounceTimer)
  }
  unsubscribeHandlers.forEach((unsubscribe) => unsubscribe())
})
</script>

<style scoped>
/* Stagger animation for stat cards */
.grid > * {
  animation: fadeInUp 0.4s ease-out both;
}

.grid > *:nth-child(1) { animation-delay: 0ms; }
.grid > *:nth-child(2) { animation-delay: 50ms; }
.grid > *:nth-child(3) { animation-delay: 100ms; }
.grid > *:nth-child(4) { animation-delay: 150ms; }
.grid > *:nth-child(5) { animation-delay: 200ms; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Table row animation */
.data-table tbody tr {
  animation: tableRowIn 0.3s ease-out both;
}

.data-table tbody tr:nth-child(1) { animation-delay: 0.02s; }
.data-table tbody tr:nth-child(2) { animation-delay: 0.04s; }
.data-table tbody tr:nth-child(3) { animation-delay: 0.06s; }
.data-table tbody tr:nth-child(4) { animation-delay: 0.08s; }
.data-table tbody tr:nth-child(5) { animation-delay: 0.1s; }

@keyframes tableRowIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Enhanced hover effect for table rows */
.data-table tbody tr {
  transition: all 0.2s ease;
}

.data-table tbody tr:hover {
  transform: translateX(2px);
}

/* Pulse animation for auto-refresh indicator */
@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.animate-pulse {
  animation: pulse-dot 1.5s ease-in-out infinite;
}
</style>
