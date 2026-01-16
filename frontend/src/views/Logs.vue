<template>
  <div class="space-y-6">
    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
      <div class="stats-card stats-card-blue">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">总日志数</p>
            <p class="stats-value">{{ stats.total || 0 }}</p>
          </div>
          <div class="stats-icon">
            <DocumentTextIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-green">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">信息</p>
            <p class="stats-value">{{ stats.by_level?.INFO || 0 }}</p>
          </div>
          <div class="stats-icon">
            <InformationCircleIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-yellow">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">警告</p>
            <p class="stats-value">{{ stats.by_level?.WARNING || 0 }}</p>
          </div>
          <div class="stats-icon">
            <ExclamationTriangleIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-red">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">错误</p>
            <p class="stats-value">{{ stats.by_level?.ERROR || 0 }}</p>
          </div>
          <div class="stats-icon">
            <XCircleIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-purple">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">严重</p>
            <p class="stats-value">{{ stats.by_level?.CRITICAL || 0 }}</p>
          </div>
          <div class="stats-icon">
            <FireIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>

    <!-- 过滤器卡片 -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
              <FunnelIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">日志过滤</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">筛选并搜索日志记录</p>
            </div>
          </div>
          <div class="flex items-center space-x-3">
            <label class="flex items-center space-x-2 cursor-pointer">
              <div class="relative">
                <input
                  v-model="autoRefresh"
                  type="checkbox"
                  class="sr-only peer"
                />
                <div class="w-10 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-5 peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
              </div>
              <span class="text-sm text-gray-600 dark:text-gray-400">自动刷新</span>
            </label>
            <Button variant="secondary" size="sm" @click="loadLogs" :loading="loading">
              <ArrowPathIcon class="w-4 h-4" />
              刷新
            </Button>
            <Button variant="danger" size="sm" @click="showClearModal = true">
              <TrashIcon class="w-4 h-4" />
              清理
            </Button>
          </div>
        </div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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
        <div class="form-group lg:col-span-2">
          <label class="form-label">搜索</label>
          <div class="relative">
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
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
              <DocumentTextIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">日志记录</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                显示 {{ filteredLogs.length }} 条记录
                <span v-if="autoRefresh" class="text-green-500 ml-2">
                  <span class="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></span>
                  实时更新中
                </span>
              </p>
            </div>
          </div>
        </div>
      </template>

      <div v-if="loading" class="flex flex-col items-center justify-center py-16">
        <div class="w-12 h-12 rounded-full border-4 border-primary-200 border-t-primary-600 animate-spin"></div>
        <p class="mt-4 text-gray-500 dark:text-gray-400">加载日志中...</p>
      </div>

      <div v-else-if="filteredLogs.length === 0" class="empty-state py-16">
        <div class="empty-state-icon">
          <DocumentTextIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title">暂无日志记录</p>
        <p class="empty-state-description">系统运行时会自动记录日志</p>
      </div>

      <div v-else class="overflow-x-auto max-h-[600px] overflow-y-auto scrollbar-hide">
        <table class="data-table">
          <thead>
            <tr>
              <th class="w-44">时间</th>
              <th class="w-24">级别</th>
              <th class="w-28">模块</th>
              <th>消息内容</th>
            </tr>
          </thead>
          <tbody class="font-mono text-xs">
            <tr
              v-for="(log, idx) in filteredLogs"
              :key="idx"
              :class="getRowClass(log.level)"
            >
              <td class="text-gray-500 dark:text-gray-400">
                <div class="flex items-center space-x-2">
                  <ClockIcon class="w-3.5 h-3.5" />
                  <span>{{ formatTime(log.timestamp) }}</span>
                </div>
              </td>
              <td>
                <span :class="getLevelBadgeClass(log.level)">
                  <component :is="getLevelIcon(log.level)" class="w-3 h-3 mr-1" />
                  {{ getLevelText(log.level) }}
                </span>
              </td>
              <td>
                <span class="badge badge-gray">{{ getModuleText(log.module) }}</span>
              </td>
              <td class="text-gray-900 dark:text-white">
                <div class="max-w-2xl">
                  <p class="truncate" :title="log.message">{{ log.message }}</p>
                  <p v-if="log.details" class="text-gray-400 dark:text-gray-500 text-[10px] mt-1 truncate">
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
      <p class="text-gray-600 dark:text-gray-400">
        确定要清理日志吗？此操作将删除选定时间范围之前的所有日志记录。
      </p>
      <div class="mt-4">
        <label class="form-label">清理范围</label>
        <select v-model="clearHours" class="form-select">
          <option :value="1">1小时前的日志</option>
          <option :value="6">6小时前的日志</option>
          <option :value="24">24小时前的日志</option>
          <option :value="72">3天前的日志</option>
          <option :value="168">7天前的日志</option>
        </select>
      </div>
      <template #footer>
        <Button variant="secondary" @click="showClearModal = false">取消</Button>
        <Button variant="danger" @click="clearLogs" :loading="clearing">确认清理</Button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { logsApi } from '@/api'
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
  CheckCircleIcon,
  BugAntIcon,
} from '@heroicons/vue/24/outline'

dayjs.locale('zh-cn')

const logs = ref([])
const stats = ref({})
const loading = ref(false)
const clearing = ref(false)
const autoRefresh = ref(false)
const showClearModal = ref(false)
const clearHours = ref(24)
let refreshInterval = null

const filter = reactive({
  level: '',
  module: '',
  limit: 100,
  search: '',
})

const filteredLogs = computed(() => {
  let result = logs.value

  if (filter.search) {
    const searchLower = filter.search.toLowerCase()
    result = result.filter(log =>
      log.message.toLowerCase().includes(searchLower) ||
      (log.details && log.details.toLowerCase().includes(searchLower))
    )
  }

  return result
})

function formatTime(timestamp) {
  return dayjs(timestamp).format('MM-DD HH:mm:ss')
}

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

function getRowClass(level) {
  if (level === 'ERROR' || level === 'CRITICAL') {
    return 'bg-red-50/30 dark:bg-red-900/5 hover:bg-red-50/50 dark:hover:bg-red-900/10'
  }
  if (level === 'WARNING') {
    return 'bg-yellow-50/30 dark:bg-yellow-900/5 hover:bg-yellow-50/50 dark:hover:bg-yellow-900/10'
  }
  return ''
}

async function loadLogs() {
  loading.value = true
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
    logs.value = logsRes.data
    stats.value = statsRes.data
  } catch (error) {
    console.error('Failed to load logs:', error)
  } finally {
    loading.value = false
  }
}

async function clearLogs() {
  clearing.value = true
  try {
    await logsApi.clearLogs(clearHours.value)
    showClearModal.value = false
    loadLogs()
  } catch (error) {
    console.error('Failed to clear logs:', error)
  } finally {
    clearing.value = false
  }
}

watch([() => filter.level, () => filter.module, () => filter.limit], () => {
  loadLogs()
})

watch(autoRefresh, (value) => {
  if (value) {
    refreshInterval = setInterval(loadLogs, 5000)
  } else if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})

onMounted(() => {
  loadLogs()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>
