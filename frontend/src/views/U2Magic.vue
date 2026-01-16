<template>
  <div class="space-y-6">
    <!-- Stats Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="stats-card stats-card-purple">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">发现魔法</p>
            <p class="stats-value">{{ stats.total }}</p>
          </div>
          <div class="stats-icon">
            <SparklesIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-green">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">已下载</p>
            <p class="stats-value">{{ stats.downloaded }}</p>
          </div>
          <div class="stats-icon">
            <ArrowDownTrayIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-yellow">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">已跳过</p>
            <p class="stats-value">{{ stats.skipped }}</p>
          </div>
          <div class="stats-icon">
            <ForwardIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-blue">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">下载体积</p>
            <p class="stats-value text-lg">{{ formatSize(stats.totalSize) }}</p>
          </div>
          <div class="stats-icon">
            <CircleStackIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>

    <!-- Configuration Card -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20">
        <div class="flex items-center space-x-3">
          <div class="p-2.5 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg shadow-purple-500/30">
            <SparklesIcon class="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900 dark:text-white">U2 追魔配置</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">自动追踪并下载U2魔法种子</p>
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <span class="text-sm font-medium" :class="config.enabled ? 'text-green-600 dark:text-green-400' : 'text-gray-500'">
            {{ config.enabled ? '运行中' : '已停止' }}
          </span>
          <button
            @click="toggleEnabled"
            :class="[
              'relative inline-flex h-7 w-12 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2',
              config.enabled ? 'bg-gradient-to-r from-purple-500 to-pink-500' : 'bg-gray-200 dark:bg-gray-600'
            ]"
          >
            <span
              :class="[
                'pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out',
                config.enabled ? 'translate-x-5' : 'translate-x-0'
              ]"
            />
          </button>
        </div>
      </div>

      <form @submit.prevent="saveConfig" class="p-6 space-y-6">
        <!-- Authentication Section -->
        <div class="space-y-4">
          <div class="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            <KeyIcon class="w-4 h-4 text-purple-500" />
            <span>认证配置</span>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 pl-6">
            <div class="lg:col-span-2">
              <label class="form-label">Cookie</label>
              <textarea
                v-model="config.cookie"
                rows="2"
                class="form-input font-mono text-xs"
                placeholder="从浏览器复制U2的Cookie..."
              ></textarea>
            </div>
            <div>
              <label class="form-label">API Token</label>
              <input v-model="config.api_token" type="password" class="form-input" placeholder="可选，用于API方式获取" />
            </div>
            <div>
              <label class="form-label">用户UID</label>
              <input v-model.number="config.uid" type="number" min="0" class="form-input" placeholder="U2用户ID" />
            </div>
          </div>
        </div>

        <!-- Directory Section -->
        <div class="space-y-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          <div class="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            <FolderIcon class="w-4 h-4 text-blue-500" />
            <span>目录配置</span>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 pl-6">
            <div>
              <label class="form-label">种子备份目录</label>
              <input v-model="config.backup_dir" type="text" class="form-input" placeholder="/path/to/backup" />
            </div>
            <div>
              <label class="form-label">监控目录</label>
              <input v-model="config.watch_dir" type="text" class="form-input" placeholder="/path/to/watch" />
            </div>
            <div>
              <label class="form-label">下载器</label>
              <select v-model="config.downloader_id" class="form-select">
                <option :value="null">使用监控目录</option>
                <option v-for="dl in downloaders" :key="dl.id" :value="dl.id">{{ dl.name }}</option>
              </select>
            </div>
            <div>
              <label class="form-label">检测间隔 (秒)</label>
              <input v-model.number="config.fetch_interval" type="number" min="30" class="form-input" />
            </div>
          </div>
        </div>

        <!-- Filter Section -->
        <div class="space-y-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          <div class="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            <FunnelIcon class="w-4 h-4 text-amber-500" />
            <span>过滤条件</span>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 pl-6">
            <div>
              <label class="form-label">最大做种人数</label>
              <input v-model.number="config.max_seeders" type="number" min="0" class="form-input" />
              <p class="text-xs text-gray-500 mt-1">0 = 不限制</p>
            </div>
            <div>
              <label class="form-label">最小体积 (GB)</label>
              <input v-model.number="config.min_size" type="number" step="0.1" min="0" class="form-input" />
            </div>
            <div>
              <label class="form-label">最大体积 (GB)</label>
              <input v-model.number="config.max_size" type="number" step="0.1" min="0" class="form-input" />
              <p class="text-xs text-gray-500 mt-1">0 = 不限制</p>
            </div>
            <div>
              <label class="form-label">新旧种判断天数</label>
              <input v-model.number="config.min_day" type="number" min="1" class="form-input" />
              <p class="text-xs text-gray-500 mt-1">发布超过此天数为旧种</p>
            </div>
            <div>
              <label class="form-label">魔法生效延迟 (秒)</label>
              <input v-model.number="config.effective_delay" type="number" min="0" class="form-input" />
            </div>
            <div>
              <label class="form-label">重复添加间隔 (秒)</label>
              <input v-model.number="config.min_add_interval" type="number" min="0" class="form-input" />
              <p class="text-xs text-gray-500 mt-1">0 = 不重复添加</p>
            </div>
            <div class="lg:col-span-2">
              <label class="form-label">分类过滤</label>
              <input v-model="config.categories" type="text" class="form-input" placeholder="逗号分隔，如: Movie,TV" />
            </div>
            <div>
              <label class="form-label">名称过滤关键词</label>
              <input v-model="config.name_filter" type="text" class="form-input" placeholder="逗号分隔" />
            </div>
          </div>
        </div>

        <!-- Options Section -->
        <div class="space-y-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          <div class="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
            <Cog6ToothIcon class="w-4 h-4 text-gray-500" />
            <span>高级选项</span>
          </div>
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 pl-6">
            <label class="flex items-center space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <input v-model="config.download_new" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
              <div>
                <span class="text-sm font-medium text-gray-900 dark:text-white">下载新种</span>
                <p class="text-xs text-gray-500">新发布的种子</p>
              </div>
            </label>
            <label class="flex items-center space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <input v-model="config.download_old" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
              <div>
                <span class="text-sm font-medium text-gray-900 dark:text-white">下载旧种</span>
                <p class="text-xs text-gray-500">老种子有魔法</p>
              </div>
            </label>
            <label class="flex items-center space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <input v-model="config.download_non_free" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
              <div>
                <span class="text-sm font-medium text-gray-900 dark:text-white">下载非Free</span>
                <p class="text-xs text-gray-500">2x/2xfree等</p>
              </div>
            </label>
            <label class="flex items-center space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <input v-model="config.magic_self" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
              <div>
                <span class="text-sm font-medium text-gray-900 dark:text-white">自己的魔法</span>
                <p class="text-xs text-gray-500">下载给自己的</p>
              </div>
            </label>
            <label class="flex items-center space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <input v-model="config.download_dead" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
              <div>
                <span class="text-sm font-medium text-gray-900 dark:text-white">无人做种</span>
                <p class="text-xs text-gray-500">旧种无做种者</p>
              </div>
            </label>
            <label class="flex items-center space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              <input v-model="config.da_qiao" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
              <div>
                <span class="text-sm font-medium text-gray-900 dark:text-white">搭桥模式</span>
                <p class="text-xs text-gray-500">帮助下载传输</p>
              </div>
            </label>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end space-x-3 pt-4 border-t border-gray-100 dark:border-gray-700">
          <Button variant="secondary" type="button" @click="fetchMagic" :loading="fetching">
            <MagnifyingGlassIcon class="w-4 h-4 mr-2" />
            立即检测
          </Button>
          <Button variant="primary" type="submit" :loading="saving">
            <CheckIcon class="w-4 h-4 mr-2" />
            保存配置
          </Button>
        </div>
      </form>
    </div>

    <!-- Records Card -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center space-x-3">
          <div class="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
            <ClockIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900 dark:text-white">魔法记录</h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">显示最近 {{ records.length }} 条记录</p>
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <select v-model="filter.downloaded" class="form-select text-sm py-1.5">
            <option :value="null">全部状态</option>
            <option :value="true">已下载</option>
            <option :value="false">已跳过</option>
          </select>
          <Button variant="ghost" size="sm" @click="loadRecords">
            <ArrowPathIcon class="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div v-if="loading" class="flex items-center justify-center py-16">
        <div class="w-10 h-10 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
      </div>

      <div v-else-if="records.length === 0" class="text-center py-16">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
          <SparklesIcon class="w-8 h-8 text-purple-500" />
        </div>
        <p class="text-gray-500 dark:text-gray-400 font-medium">暂无魔法记录</p>
        <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">启用追魔后将自动记录</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>种子名称</th>
              <th class="w-32">魔法类型</th>
              <th class="w-24">体积</th>
              <th class="w-20">做种</th>
              <th class="w-28">状态</th>
              <th class="w-32">时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in records" :key="record.id" class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
              <td>
                <div class="max-w-xs">
                  <p class="truncate font-medium text-gray-900 dark:text-white" :title="record.torrent_name">
                    {{ record.torrent_name }}
                  </p>
                  <p v-if="record.torrent_id" class="text-xs text-gray-400 mt-0.5">ID: {{ record.torrent_id }}</p>
                </div>
              </td>
              <td>
                <span :class="getMagicTypeClass(record.magic_type)">
                  {{ record.magic_type }}
                </span>
                <span v-if="record.magic_duration" class="text-xs text-gray-500 ml-1.5">
                  {{ record.magic_duration }}h
                </span>
              </td>
              <td class="text-gray-600 dark:text-gray-400">{{ formatSize(record.size) }}</td>
              <td>
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                  <UsersIcon class="w-3 h-3 mr-1" />
                  {{ record.seeders }}
                </span>
              </td>
              <td>
                <span v-if="record.downloaded" class="badge badge-success">
                  <CheckCircleIcon class="w-3.5 h-3.5 mr-1" />
                  已下载
                </span>
                <span v-else class="badge badge-gray" :title="record.skip_reason">
                  <XCircleIcon class="w-3.5 h-3.5 mr-1" />
                  {{ record.skip_reason ? record.skip_reason.slice(0, 8) : '跳过' }}
                </span>
              </td>
              <td class="text-xs text-gray-500 dark:text-gray-400">
                <div class="flex items-center">
                  <ClockIcon class="w-3.5 h-3.5 mr-1" />
                  {{ formatTime(record.created_at) }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, inject } from 'vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { u2MagicApi, downloadersApi } from '@/api'
import Button from '@/components/common/Button.vue'
import {
  ArrowPathIcon,
  SparklesIcon,
  ArrowDownTrayIcon,
  ForwardIcon,
  CircleStackIcon,
  KeyIcon,
  FolderIcon,
  FunnelIcon,
  Cog6ToothIcon,
  MagnifyingGlassIcon,
  CheckIcon,
  ClockIcon,
  UsersIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/vue/24/outline'

const $t = inject('t')

dayjs.locale('zh-cn')

const loading = ref(false)
const config = reactive({
  enabled: false,
  cookie: '',
  api_token: '',
  uid: 0,
  backup_dir: '',
  watch_dir: '',
  fetch_interval: 60,
  max_seeders: 20,
  download_new: true,
  download_old: true,
  download_non_free: false,
  magic_self: false,
  download_dead: false,
  da_qiao: true,
  min_size: 0,
  max_size: 0,
  min_day: 7,
  effective_delay: 60,
  min_add_interval: 0,
  categories: '',
  name_filter: '',
  downloader_id: null,
})

const records = ref([])
const downloaders = ref([])

const saving = ref(false)
const fetching = ref(false)

const filter = reactive({
  downloaded: null,
})

const stats = computed(() => {
  const total = records.value.length
  const downloaded = records.value.filter(r => r.downloaded).length
  const skipped = total - downloaded
  const totalSize = records.value
    .filter(r => r.downloaded)
    .reduce((sum, r) => sum + (r.size || 0), 0)

  return { total, downloaded, skipped, totalSize }
})

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatTime(timestamp) {
  return dayjs(timestamp).format('MM-DD HH:mm')
}

function getMagicTypeClass(type) {
  const typeMap = {
    'free': 'px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    '2xfree': 'px-2 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    '2x': 'px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    '50%': 'px-2 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  }
  const lowerType = (type || '').toLowerCase()
  for (const [key, value] of Object.entries(typeMap)) {
    if (lowerType.includes(key)) return value
  }
  return 'px-2 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

async function loadConfig() {
  try {
    const response = await u2MagicApi.getConfig()
    Object.assign(config, response.data)
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

async function saveConfig() {
  saving.value = true
  try {
    await u2MagicApi.updateConfig(config)
    alert('配置保存成功')
  } catch (error) {
    console.error('Failed to save config:', error)
    alert(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleEnabled() {
  config.enabled = !config.enabled
  await saveConfig()
}

async function fetchMagic() {
  fetching.value = true
  try {
    const response = await u2MagicApi.fetch()
    alert(`检测完成：发现 ${response.data.total} 个魔法，下载 ${response.data.downloaded} 个`)
    await loadRecords()
  } catch (error) {
    console.error('Failed to fetch magic:', error)
    alert('检测失败：' + (error.response?.data?.detail || error.message))
  } finally {
    fetching.value = false
  }
}

async function loadRecords() {
  loading.value = true
  try {
    const params = {
      limit: 100,
      ...(filter.downloaded !== null && { downloaded: filter.downloaded }),
    }
    const response = await u2MagicApi.getRecords(params)
    records.value = response.data
  } catch (error) {
    console.error('Failed to load records:', error)
  } finally {
    loading.value = false
  }
}

async function loadDownloaders() {
  try {
    const response = await downloadersApi.getAll()
    downloaders.value = response.data
  } catch (error) {
    console.error('Failed to load downloaders:', error)
  }
}

watch(filter, () => {
  loadRecords()
})

onMounted(() => {
  loadConfig()
  loadRecords()
  loadDownloaders()
})
</script>
