<template>
  <div class="space-y-6">
    <!-- 顶部标题栏 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">PT自动刷流概览</h1>
        <p class="text-sm text-slate-400 mt-1">选量最适度的件下单信息 时间随流{{ currentVersion }}</p>
      </div>

      <!-- 时间范围选择器 -->
      <div class="flex items-center bg-white rounded-full shadow-sm border border-slate-200 p-1">
        <button
          v-for="period in timePeriods"
          :key="period.value"
          @click="selectedPeriod = period.value"
          class="px-4 py-1.5 text-sm font-medium rounded-full transition-all duration-200 cursor-pointer"
          :class="[
            selectedPeriod === period.value
              ? 'bg-blue-500 text-white shadow-md'
              : 'text-slate-500 hover:text-slate-700'
          ]"
        >
          {{ period.label }}
        </button>
        <button class="p-2 text-slate-400 hover:text-slate-600 cursor-pointer">
          <CalendarIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-4 gap-4">
      <!-- 今日上传 -->
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
              <ArrowUpIcon class="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <p class="text-sm text-slate-400">今日上传</p>
              <p class="text-xl font-bold text-slate-800">{{ formatSize(todayStats.upload || 0) }}</p>
            </div>
          </div>
          <div class="flex items-center text-emerald-500 text-sm font-medium">
            <ArrowTrendingUpIcon class="w-4 h-4 mr-1" />
            {{ todayStats.uploadChange || 55 }}%
          </div>
        </div>
      </div>

      <!-- 今日下载 -->
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center">
              <ArrowDownIcon class="w-6 h-6 text-purple-500" />
            </div>
            <div>
              <p class="text-sm text-slate-400">今日下载</p>
              <p class="text-xl font-bold text-slate-800">{{ formatSize(todayStats.download || 0) }}</p>
            </div>
          </div>
          <div class="flex items-center text-red-500 text-sm font-medium">
            <ArrowTrendingDownIcon class="w-4 h-4 mr-1" />
            {{ todayStats.downloadChange || 10 }}%
          </div>
        </div>
      </div>

      <!-- 做种数 -->
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center space-x-3">
          <div class="w-12 h-12 rounded-xl bg-orange-50 flex items-center justify-center">
            <UserGroupIcon class="w-6 h-6 text-orange-500" />
          </div>
          <div>
            <p class="text-sm text-slate-400">做种数</p>
            <p class="text-xl font-bold text-slate-800">{{ stats.seeding_torrents || 35 }}</p>
          </div>
        </div>
      </div>

      <!-- 连接数 -->
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center space-x-3">
          <div class="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center">
            <ArrowsRightLeftIcon class="w-6 h-6 text-purple-500" />
          </div>
          <div>
            <p class="text-sm text-slate-400">连接数</p>
            <p class="text-xl font-bold text-slate-800">{{ connectionCount }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid grid-cols-3 gap-6">
      <!-- 流量趋势图 -->
      <div class="col-span-2 bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-slate-800">流量趋势图</h3>
          <div class="flex items-center space-x-4 text-sm">
            <div class="flex items-center">
              <span class="w-3 h-3 rounded-full bg-blue-500 mr-2"></span>
              <span class="text-slate-500">Upload Speed</span>
            </div>
            <div class="flex items-center">
              <span class="w-3 h-3 rounded-full bg-cyan-400 mr-2"></span>
              <span class="text-slate-500">Download Speed</span>
            </div>
          </div>
        </div>
        <div class="h-64">
          <v-chart :option="trafficChartOption" autoresize />
        </div>
      </div>

      <!-- 各站点今日上传 -->
      <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <h3 class="text-lg font-semibold text-slate-800 mb-6">各站点今日上传</h3>
        <div class="flex flex-col items-center">
          <div class="relative w-48 h-48">
            <v-chart :option="siteUploadChartOption" autoresize />
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <p class="text-3xl font-bold text-slate-800">{{ formatSizeShort(totalSiteUpload) }}</p>
              <p class="text-sm text-slate-400">今日总上传</p>
            </div>
          </div>
          <div class="mt-6 space-y-2 w-full">
            <div v-for="site in siteUploadData" :key="site.name" class="flex items-center justify-between text-sm">
              <div class="flex items-center">
                <span class="w-2 h-2 rounded-full mr-2" :style="{ backgroundColor: site.color }"></span>
                <span class="text-slate-600">{{ site.name }}: {{ formatSizeShort(site.value) }}</span>
              </div>
              <span class="text-slate-400">({{ site.percent }}%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部区域 -->
    <div class="grid grid-cols-3 gap-6">
      <!-- 活跃种子列表 -->
      <div class="col-span-1 bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <h3 class="text-lg font-semibold text-slate-800 mb-4">活跃种子列表</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-slate-400 text-left border-b border-slate-100">
                <th class="pb-3 font-medium">名称</th>
                <th class="pb-3 font-medium">上传位置</th>
                <th class="pb-3 font-medium">下载位置</th>
                <th class="pb-3 font-medium">进度</th>
                <th class="pb-3 font-medium">限时时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="torrent in activeTorrents" :key="torrent.id" class="border-b border-slate-50 hover:bg-slate-50">
                <td class="py-3 text-slate-700 truncate max-w-[120px]">{{ torrent.name }}</td>
                <td class="py-3 text-slate-600">{{ formatSpeed(torrent.upload_speed) }}</td>
                <td class="py-3 text-slate-600">{{ formatSpeed(torrent.download_speed) }}</td>
                <td class="py-3">
                  <div class="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full"
                      :style="{ width: torrent.progress + '%' }"
                    ></div>
                  </div>
                </td>
                <td class="py-3 text-slate-500 text-xs">{{ torrent.addedTime }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 任务队列 -->
      <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-800">任务队列</h3>
          <button @click="refreshTasks" class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer">
            <ArrowPathIcon class="w-5 h-5" :class="{ 'animate-spin': isRefreshing }" />
          </button>
        </div>
        <div class="space-y-3">
          <div
            v-for="task in taskQueue"
            :key="task.id"
            @click="navigateToTask(task)"
            class="flex items-center p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <div
              class="w-10 h-10 rounded-xl flex items-center justify-center mr-3"
              :class="task.iconBg"
            >
              <component :is="task.icon" class="w-5 h-5" :class="task.iconColor" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-slate-700">{{ task.title }}</p>
              <p class="text-xs text-slate-400">{{ task.subtitle }}</p>
            </div>
            <ChevronRightIcon class="w-5 h-5 text-slate-300" />
          </div>
        </div>
      </div>

      <!-- 日志更新 -->
      <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-800">日志更新</h3>
          <button @click="openLogFilter" class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer">
            <AdjustmentsHorizontalIcon class="w-5 h-5" />
          </button>
        </div>
        <div class="space-y-4">
          <div v-for="log in recentLogs" :key="log.id" class="border-l-2 border-slate-200 pl-4">
            <p class="text-sm font-medium text-slate-700">{{ log.date }}</p>
            <p class="text-xs text-slate-400 mt-1 line-clamp-2">{{ log.content }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'

import { useDashboardStore } from '@/stores/dashboard'
import { formatSpeed, formatSize } from '@/utils/format'
import {
  CalendarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  UserGroupIcon,
  ArrowsRightLeftIcon,
  ArrowPathIcon,
  ChevronRightIcon,
  AdjustmentsHorizontalIcon,
  CloudArrowUpIcon,
  CloudArrowDownIcon,
  ClockIcon,
} from '@heroicons/vue/24/outline'

// ECharts setup
use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()
const dashboardStore = useDashboardStore()

const currentVersion = '2.2n'
const selectedPeriod = ref('day')
const isRefreshing = ref(false)

const timePeriods = [
  { label: '前', value: 'prev' },
  { label: '月', value: 'month' },
  { label: '月', value: 'month2' },
  { label: '年', value: 'year' },
]

// Computed
const stats = computed(() => dashboardStore.stats)

const todayStats = computed(() => ({
  upload: stats.value.total_uploaded || 1.5 * 1024 * 1024 * 1024 * 1024,
  download: stats.value.total_downloaded || 4500,
  uploadChange: 55,
  downloadChange: 10,
}))

const connectionCount = computed(() => {
  // 模拟连接数
  return 120
})

const totalSiteUpload = computed(() => {
  return siteUploadData.value.reduce((sum, site) => sum + site.value, 0)
})

const siteUploadData = ref([
  { name: 'HDSky', value: 0.75 * 1024 * 1024 * 1024 * 1024, color: '#3B82F6', percent: 50 },
  { name: 'U2', value: 0.45 * 1024 * 1024 * 1024 * 1024, color: '#8B5CF6', percent: 30 },
  { name: 'M-Team', value: 0.30 * 1024 * 1024 * 1024 * 1024, color: '#EF4444', percent: 20 },
])

const activeTorrents = ref([
  { id: 1, name: '活跃种子', upload_speed: 4.7 * 1024 * 1024, download_speed: 10.9 * 1024 * 1024, progress: 60, addedTime: '2021-04-19:20' },
  { id: 2, name: '活跃种子', upload_speed: 12.2 * 1024 * 1024, download_speed: 42.2 * 1024 * 1024, progress: 85, addedTime: '2021-04-16:30' },
  { id: 3, name: '真文件描江...', upload_speed: 2.2 * 1024 * 1024, download_speed: 1.58, progress: 45, addedTime: '2021-04-16:30' },
])

const taskQueue = ref([
  {
    id: 1,
    title: '性体',
    subtitle: '在上比: 123.4TB',
    icon: CloudArrowUpIcon,
    iconBg: 'bg-blue-100',
    iconColor: 'text-blue-500',
    route: '/statistics',
  },
  {
    id: 2,
    title: '载种',
    subtitle: '径/E 46.2TB',
    icon: CloudArrowDownIcon,
    iconBg: 'bg-orange-100',
    iconColor: 'text-orange-500',
    route: '/rss',
  },
  {
    id: 3,
    title: '载种时间',
    subtitle: '工等惶: CA75',
    icon: ClockIcon,
    iconBg: 'bg-emerald-100',
    iconColor: 'text-emerald-500',
    route: '/delete-rules',
  },
])

const recentLogs = ref([
  {
    id: 1,
    date: '7月4日 21:10',
    content: '高达拓服器推送开在护,用户用户特指实转构,是什构。',
  },
  {
    id: 2,
    date: '6月51日 10:30',
    content: '站点/月期月万月月独治,请户周野代区大件特、立所体。',
  },
])

// 流量趋势图配置
const trafficChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#fff',
    borderColor: '#e2e8f0',
    textStyle: { color: '#334155' },
    formatter: (params) => {
      let result = `<div class="font-medium text-slate-800">${params[0].axisValue}</div>`
      params.forEach(param => {
        result += `<div class="flex items-center justify-between gap-4 mt-1">
          <span>${param.marker} ${param.seriesName}</span>
          <span class="font-medium">${param.value}</span>
        </div>`
      })
      return result
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['一月', '二月', '三月', '四月', '五月', '大月'],
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: { color: '#94a3b8', fontSize: 12 },
  },
  yAxis: {
    type: 'value',
    max: 160,
    axisLine: { show: false },
    splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    axisLabel: { color: '#94a3b8', fontSize: 12 },
  },
  series: [
    {
      name: 'Upload Speed',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: [40, 80, 60, 100, 80, 120],
      itemStyle: { color: '#3B82F6' },
      lineStyle: { width: 3 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0)' }
          ]
        }
      }
    },
    {
      name: 'Download Speed',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: [30, 60, 80, 70, 90, 100],
      itemStyle: { color: '#22D3EE' },
      lineStyle: { width: 3 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(34, 211, 238, 0.3)' },
            { offset: 1, color: 'rgba(34, 211, 238, 0)' }
          ]
        }
      }
    }
  ]
}))

// 各站点上传环形图配置
const siteUploadChartOption = computed(() => ({
  series: [
    {
      type: 'pie',
      radius: ['65%', '85%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { scale: false },
      data: siteUploadData.value.map(site => ({
        value: site.value,
        name: site.name,
        itemStyle: { color: site.color }
      }))
    }
  ]
}))

// Methods
function formatSizeShort(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const value = bytes / Math.pow(k, i)
  return value.toFixed(1) + ' ' + units[i]
}

async function refreshTasks() {
  isRefreshing.value = true
  await dashboardStore.fetchAll()
  setTimeout(() => {
    isRefreshing.value = false
  }, 1000)
}

function navigateToTask(task) {
  router.push(task.route)
}

function openLogFilter() {
  router.push('/logs')
}

// Lifecycle
let refreshInterval

onMounted(async () => {
  await dashboardStore.fetchAll()

  refreshInterval = setInterval(async () => {
    await Promise.all([
      dashboardStore.fetchStats(),
      dashboardStore.fetchDownloadersStatus(),
      dashboardStore.fetchRecentActivity(),
    ])
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>
