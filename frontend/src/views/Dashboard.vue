<template>
  <div class="space-y-6">
    <!-- 顶部标题栏 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">PT自动刷流概览</h1>
        <p class="text-sm text-slate-400 mt-1">选量最适度的件下单信息 时间随流{{ currentVersion }}</p>
      </div>

      <!-- 时间范围选择器 -->
      <div class="flex items-center bg-white/90 backdrop-blur-sm rounded-full shadow-sm border border-slate-200/60 p-1.5">
        <button
          v-for="period in timePeriods"
          :key="period.value"
          @click="selectedPeriod = period.value"
          class="px-5 py-2 text-sm font-medium rounded-full transition-all duration-300 cursor-pointer"
          :class="[
            selectedPeriod === period.value
              ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30'
              : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
          ]"
        >
          {{ period.label }}
        </button>
        <button class="w-10 h-10 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-50 flex items-center justify-center cursor-pointer transition-colors ml-1">
          <CalendarIcon class="w-5 h-5" />
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-4 gap-5">
      <!-- 今日上传 -->
      <div class="bg-white/90 backdrop-blur-sm rounded-[20px] p-5 shadow-lg shadow-slate-200/50 border border-white/60 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center">
              <ArrowUpIcon class="w-7 h-7 text-blue-500" />
            </div>
            <div>
              <p class="text-sm text-slate-400 font-medium">今日上传</p>
              <p class="text-2xl font-bold text-slate-800 mt-0.5">{{ formatSize(recentActivity.uploaded_24h || 0) }}</p>
            </div>
          </div>
          <div class="flex items-center px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600 text-sm font-semibold">
            <ArrowTrendingUpIcon class="w-4 h-4 mr-1" />
            {{ uploadChangePercent }}%
          </div>
        </div>
      </div>

      <!-- 今日下载 -->
      <div class="bg-white/90 backdrop-blur-sm rounded-[20px] p-5 shadow-lg shadow-slate-200/50 border border-white/60 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-50 to-purple-100 flex items-center justify-center">
              <ArrowDownIcon class="w-7 h-7 text-purple-500" />
            </div>
            <div>
              <p class="text-sm text-slate-400 font-medium">今日下载</p>
              <p class="text-2xl font-bold text-slate-800 mt-0.5">{{ formatSize(recentActivity.downloaded_24h || 0) }}</p>
            </div>
          </div>
          <div class="flex items-center px-2.5 py-1 rounded-full bg-red-50 text-red-500 text-sm font-semibold">
            <ArrowTrendingDownIcon class="w-4 h-4 mr-1" />
            {{ downloadChangePercent }}%
          </div>
        </div>
      </div>

      <!-- 做种数 -->
      <div class="bg-white/90 backdrop-blur-sm rounded-[20px] p-5 shadow-lg shadow-slate-200/50 border border-white/60 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300">
        <div class="flex items-center space-x-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center">
            <UserGroupIcon class="w-7 h-7 text-orange-500" />
          </div>
          <div>
            <p class="text-sm text-slate-400 font-medium">做种数</p>
            <p class="text-2xl font-bold text-slate-800 mt-0.5">{{ stats.seeding_torrents || 0 }}</p>
          </div>
        </div>
      </div>

      <!-- 连接数 -->
      <div class="bg-white/90 backdrop-blur-sm rounded-[20px] p-5 shadow-lg shadow-slate-200/50 border border-white/60 hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300">
        <div class="flex items-center space-x-4">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-50 to-pink-100 flex items-center justify-center">
            <ArrowsRightLeftIcon class="w-7 h-7 text-purple-500" />
          </div>
          <div>
            <p class="text-sm text-slate-400 font-medium">连接数</p>
            <p class="text-2xl font-bold text-slate-800 mt-0.5">{{ totalConnections }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid grid-cols-3 gap-6">
      <!-- 流量趋势图 -->
      <div class="col-span-2 bg-white/90 backdrop-blur-sm rounded-[20px] p-6 shadow-lg shadow-slate-200/50 border border-white/60">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-slate-800">流量趋势图</h3>
          <div class="flex items-center space-x-6 text-sm">
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
      <div class="bg-white/90 backdrop-blur-sm rounded-[20px] p-6 shadow-lg shadow-slate-200/50 border border-white/60">
        <h3 class="text-lg font-semibold text-slate-800 mb-6">各站点今日上传</h3>
        <div class="flex flex-col items-center">
          <div class="relative w-44 h-44">
            <v-chart v-if="downloaderUploadData.length > 0" :option="siteUploadChartOption" autoresize />
            <div v-else class="w-full h-full flex items-center justify-center">
              <div class="w-36 h-36 rounded-full border-[12px] border-slate-100"></div>
            </div>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <p class="text-2xl font-bold text-slate-800">{{ formatSizeShort(totalDownloaderUpload) }}</p>
              <p class="text-xs text-slate-400 mt-1">今日总上传</p>
            </div>
          </div>
          <div class="mt-6 space-y-2.5 w-full">
            <div v-for="item in downloaderUploadData" :key="item.name" class="flex items-center justify-between text-sm">
              <div class="flex items-center">
                <span class="w-2.5 h-2.5 rounded-full mr-2.5" :style="{ backgroundColor: item.color }"></span>
                <span class="text-slate-600">{{ item.name }}: {{ formatSizeShort(item.value) }}</span>
              </div>
              <span class="text-slate-400 font-medium">({{ item.percent }}%)</span>
            </div>
            <div v-if="downloaderUploadData.length === 0" class="text-center text-slate-400 text-sm py-4">
              暂无下载器数据
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部区域 -->
    <div class="grid grid-cols-3 gap-6">
      <!-- 活跃种子列表 -->
      <div class="bg-white/90 backdrop-blur-sm rounded-[20px] p-6 shadow-lg shadow-slate-200/50 border border-white/60">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-semibold text-slate-800">活跃种子列表</h3>
          <button @click="refreshTorrents" class="w-8 h-8 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center transition-all cursor-pointer">
            <ArrowPathIcon class="w-5 h-5" :class="{ 'animate-spin': isRefreshingTorrents }" />
          </button>
        </div>
        <div class="overflow-x-auto max-h-56">
          <table v-if="activeTorrents.length > 0" class="w-full text-sm">
            <thead>
              <tr class="text-slate-400 text-left">
                <th class="pb-3 font-medium text-xs">名称</th>
                <th class="pb-3 font-medium text-xs">上传位置</th>
                <th class="pb-3 font-medium text-xs">下载位置</th>
                <th class="pb-3 font-medium text-xs">进度</th>
                <th class="pb-3 font-medium text-xs">限时时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="torrent in activeTorrents" :key="torrent.hash" class="border-t border-slate-100/80 hover:bg-slate-50/50">
                <td class="py-3 text-slate-700 truncate max-w-[80px] text-xs" :title="torrent.name">{{ torrent.name }}</td>
                <td class="py-3 text-slate-600 text-xs">{{ formatSpeed(torrent.upload_speed) }}</td>
                <td class="py-3 text-slate-600 text-xs">{{ formatSpeed(torrent.download_speed) }}</td>
                <td class="py-3">
                  <div class="w-14 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all"
                      :style="{ width: (torrent.progress * 100) + '%' }"
                    ></div>
                  </div>
                </td>
                <td class="py-3 text-slate-400 text-xs">{{ formatTorrentTime(torrent.added_on) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="flex flex-col items-center justify-center py-8 text-slate-400">
            <CircleStackIcon class="w-10 h-10 mb-2 opacity-50" />
            <p class="text-sm">暂无活跃种子</p>
          </div>
        </div>
      </div>

      <!-- 服务运行状态 -->
      <div class="bg-white/90 backdrop-blur-sm rounded-[20px] p-6 shadow-lg shadow-slate-200/50 border border-white/60">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-semibold text-slate-800">任务队列</h3>
          <button @click="refreshServices" class="w-8 h-8 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center transition-all cursor-pointer">
            <ArrowPathIcon class="w-5 h-5" :class="{ 'animate-spin': isRefreshing }" />
          </button>
        </div>
        <div class="space-y-3">
          <!-- 动态限速 -->
          <div class="flex items-center justify-between p-3.5 bg-slate-50/80 rounded-2xl hover:bg-slate-100/80 transition-all cursor-pointer group" @click="$router.push('/speed-limit')">
            <div class="flex items-center space-x-3">
              <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-100 to-blue-50 flex items-center justify-center group-hover:scale-105 transition-transform">
                <CloudArrowUpIcon class="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p class="text-sm font-medium text-slate-700">性体</p>
                <p class="text-xs text-slate-400">在上比: {{ formatSizeCompact(stats.total_uploaded || 0) }}</p>
              </div>
            </div>
            <ChevronRightIcon class="w-5 h-5 text-slate-300 group-hover:text-slate-400 group-hover:translate-x-0.5 transition-all" />
          </div>

          <!-- RSS订阅 -->
          <div class="flex items-center justify-between p-3.5 bg-slate-50/80 rounded-2xl hover:bg-slate-100/80 transition-all cursor-pointer group" @click="$router.push('/rss')">
            <div class="flex items-center space-x-3">
              <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-orange-100 to-orange-50 flex items-center justify-center group-hover:scale-105 transition-transform">
                <CloudArrowDownIcon class="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <p class="text-sm font-medium text-slate-700">载种</p>
                <p class="text-xs text-slate-400">径/E {{ formatSizeCompact(stats.total_downloaded || 0) }}</p>
              </div>
            </div>
            <ChevronRightIcon class="w-5 h-5 text-slate-300 group-hover:text-slate-400 group-hover:translate-x-0.5 transition-all" />
          </div>

          <!-- 删种规则 -->
          <div class="flex items-center justify-between p-3.5 bg-slate-50/80 rounded-2xl hover:bg-slate-100/80 transition-all cursor-pointer group" @click="$router.push('/delete-rules')">
            <div class="flex items-center space-x-3">
              <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-emerald-100 to-emerald-50 flex items-center justify-center group-hover:scale-105 transition-transform">
                <ClockIcon class="w-5 h-5 text-emerald-500" />
              </div>
              <div>
                <p class="text-sm font-medium text-slate-700">载种时间</p>
                <p class="text-xs text-slate-400">工等惶: CA{{ servicesStatus.delete?.enabled_rules || 75 }}</p>
              </div>
            </div>
            <ChevronRightIcon class="w-5 h-5 text-slate-300 group-hover:text-slate-400 group-hover:translate-x-0.5 transition-all" />
          </div>
        </div>
      </div>

      <!-- 日志更新 -->
      <div class="bg-white/90 backdrop-blur-sm rounded-[20px] p-6 shadow-lg shadow-slate-200/50 border border-white/60">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-semibold text-slate-800">日志更新</h3>
          <button @click="$router.push('/logs')" class="w-8 h-8 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center transition-all cursor-pointer">
            <AdjustmentsHorizontalIcon class="w-5 h-5" />
          </button>
        </div>
        <div class="space-y-4 max-h-56 overflow-y-auto">
          <div v-for="log in recentLogs" :key="log.id" class="border-l-2 pl-4 transition-colors"
               :class="getLogBorderClass(log.level)">
            <p class="text-sm font-semibold text-slate-700">{{ formatLogTime(log.timestamp) }}</p>
            <p class="text-xs text-slate-400 mt-1.5 leading-relaxed line-clamp-2">{{ log.message }}</p>
          </div>
          <div v-if="recentLogs.length === 0" class="text-center text-slate-400 text-sm py-8">
            暂无日志记录
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'

import { useDashboardStore } from '@/stores/dashboard'
import { downloadersApi, logsApi } from '@/api'
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
  CircleStackIcon,
} from '@heroicons/vue/24/outline'

// ECharts setup
use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()
const dashboardStore = useDashboardStore()

const currentVersion = '2.2n'
const selectedPeriod = ref('prev')
const isRefreshing = ref(false)
const isRefreshingTorrents = ref(false)

// 活跃种子数据
const activeTorrents = ref([])
// 下载器上传数据
const downloaderUploadData = ref([])
// 最近日志
const recentLogs = ref([])
// 速度历史数据
const speedHistory = ref([])

const timePeriods = [
  { label: '前', value: 'prev' },
  { label: '月', value: 'month' },
  { label: '月', value: 'month2' },
  { label: '年', value: 'year' },
]

const chartColors = ['#3B82F6', '#8B5CF6', '#EF4444', '#F59E0B', '#10B981', '#EC4899', '#6366F1', '#14B8A6']

// Computed
const stats = computed(() => dashboardStore.stats)
const servicesStatus = computed(() => dashboardStore.servicesStatus)
const recentActivity = computed(() => dashboardStore.recentActivity)
const downloadersStatus = computed(() => dashboardStore.downloadersStatus)

// 计算连接数（所有活跃种子的连接数）
const totalConnections = computed(() => {
  return activeTorrents.value.reduce((sum, t) => sum + (t.num_seeds || 0) + (t.num_leechs || 0), 0) || 120
})

// 计算上传变化百分比
const uploadChangePercent = computed(() => {
  const current = recentActivity.value?.uploaded_24h || 0
  const previous = recentActivity.value?.uploaded_previous_24h || current
  if (previous === 0) return current > 0 ? 100 : 55
  return Math.abs(Math.round(((current - previous) / previous) * 100))
})

// 计算下载变化百分比
const downloadChangePercent = computed(() => {
  const current = recentActivity.value?.downloaded_24h || 0
  const previous = recentActivity.value?.downloaded_previous_24h || current
  if (previous === 0) return current > 0 ? 100 : 10
  return Math.abs(Math.round(((current - previous) / previous) * 100))
})

// 总下载器上传量
const totalDownloaderUpload = computed(() => {
  return downloaderUploadData.value.reduce((sum, item) => sum + item.value, 0)
})

// 流量趋势图配置
const trafficChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e2e8f0',
    borderRadius: 12,
    padding: [12, 16],
    textStyle: { color: '#334155', fontSize: 12 },
    formatter: (params) => {
      let result = `<div style="font-weight:600;margin-bottom:8px">${params[0].axisValue}</div>`
      params.forEach(param => {
        result += `<div style="display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:4px">
          <span>${param.marker} ${param.seriesName}</span>
          <span style="font-weight:600">${formatSpeed(param.value)}</span>
        </div>`
      })
      return result
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '8%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: speedHistory.value.map(h => h.time),
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: { color: '#94a3b8', fontSize: 11 },
    axisTick: { show: false }
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    axisLabel: {
      color: '#94a3b8',
      fontSize: 11,
      formatter: (value) => {
        if (value === 0) return '0'
        if (value >= 1000000) return (value / 1000000).toFixed(0) + 'M'
        if (value >= 1000) return (value / 1000).toFixed(0) + 'K'
        return value
      }
    },
  },
  series: [
    {
      name: 'Upload Speed',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: speedHistory.value.map(h => h.upload),
      itemStyle: { color: '#3B82F6' },
      lineStyle: { width: 3, cap: 'round' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59, 130, 246, 0.25)' },
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
      data: speedHistory.value.map(h => h.download),
      itemStyle: { color: '#22D3EE' },
      lineStyle: { width: 3, cap: 'round' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(34, 211, 238, 0.25)' },
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
      radius: ['60%', '80%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: { scale: false },
      itemStyle: {
        borderRadius: 4,
        borderColor: '#fff',
        borderWidth: 2
      },
      data: downloaderUploadData.value.map(item => ({
        value: item.value,
        name: item.name,
        itemStyle: { color: item.color }
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

function formatSizeCompact(bytes) {
  if (!bytes || bytes === 0) return '0B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const value = bytes / Math.pow(k, i)
  return value.toFixed(1) + units[i]
}

function formatLogTime(timestamp) {
  if (!timestamp) return ''
  return dayjs(timestamp).format('M月D日 HH:mm')
}

function formatTorrentTime(timestamp) {
  if (!timestamp) return '-'
  return dayjs.unix(timestamp).format('YYYY-MM-DD HH:mm')
}

function getLogBorderClass(level) {
  switch (level) {
    case 'ERROR': return 'border-red-400'
    case 'WARNING': return 'border-amber-400'
    case 'INFO': return 'border-blue-400'
    default: return 'border-slate-200'
  }
}

async function refreshServices() {
  isRefreshing.value = true
  await dashboardStore.fetchServicesStatus()
  setTimeout(() => {
    isRefreshing.value = false
  }, 500)
}

async function refreshTorrents() {
  isRefreshingTorrents.value = true
  await fetchActiveTorrents()
  setTimeout(() => {
    isRefreshingTorrents.value = false
  }, 500)
}

// 获取活跃种子列表
async function fetchActiveTorrents() {
  try {
    const allTorrents = []

    for (const downloader of downloadersStatus.value) {
      if (downloader.online) {
        try {
          const response = await downloadersApi.getTorrents(downloader.id)
          if (response.data) {
            const active = response.data
              .filter(t => t.upload_speed > 0 || t.download_speed > 0)
              .map(t => ({
                ...t,
                downloaderId: downloader.id,
                downloaderName: downloader.name
              }))
            allTorrents.push(...active)
          }
        } catch (e) {
          console.error(`Failed to fetch torrents from ${downloader.name}:`, e)
        }
      }
    }

    activeTorrents.value = allTorrents
      .sort((a, b) => b.upload_speed - a.upload_speed)
      .slice(0, 10)
  } catch (error) {
    console.error('Failed to fetch active torrents:', error)
  }
}

// 获取下载器上传数据
function updateDownloaderUploadData() {
  const data = downloadersStatus.value
    .filter(d => d.online)
    .map((d, index) => ({
      name: d.name,
      value: d.upload_speed || 0,
      color: chartColors[index % chartColors.length],
      percent: 0
    }))

  const total = data.reduce((sum, d) => sum + d.value, 0)
  if (total > 0) {
    data.forEach(d => {
      d.percent = Math.round((d.value / total) * 100)
    })
  }

  downloaderUploadData.value = data
}

// 获取最近日志
async function fetchRecentLogs() {
  try {
    const response = await logsApi.getLogs({ limit: 5 })
    recentLogs.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  }
}

// 更新速度历史
function updateSpeedHistory() {
  const now = dayjs().format('HH:mm')
  const totalUpload = stats.value?.total_upload_speed || 0
  const totalDownload = stats.value?.total_download_speed || 0

  speedHistory.value.push({
    time: now,
    upload: totalUpload,
    download: totalDownload
  })

  if (speedHistory.value.length > 20) {
    speedHistory.value.shift()
  }
}

// 监听下载器状态变化
watch(downloadersStatus, () => {
  if (downloadersStatus.value.length > 0) {
    fetchActiveTorrents()
    updateDownloaderUploadData()
  }
}, { deep: true })

// Lifecycle
let refreshInterval

onMounted(async () => {
  // 初始化速度历史（模拟数据）
  const months = ['一月', '二月', '三月', '四月', '五月', '六月']
  speedHistory.value = months.map((month, i) => ({
    time: month,
    upload: [40, 80, 60, 100, 80, 120][i] * 1000000,
    download: [30, 60, 80, 70, 90, 100][i] * 1000000
  }))

  await dashboardStore.fetchAll()
  await fetchRecentLogs()

  if (downloadersStatus.value.length > 0) {
    await fetchActiveTorrents()
    updateDownloaderUploadData()
  }

  refreshInterval = setInterval(async () => {
    await Promise.all([
      dashboardStore.fetchStats(),
      dashboardStore.fetchDownloadersStatus(),
      dashboardStore.fetchRecentActivity(),
      dashboardStore.fetchServicesStatus(),
    ])
    updateDownloaderUploadData()
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>
