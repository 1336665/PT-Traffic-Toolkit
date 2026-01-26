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

    <!-- 统计卡片 - 4个今日上传/下载数据 -->
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
              <p class="text-xl font-bold text-slate-800">{{ formatSize(recentActivity.uploaded_24h || 0) }}</p>
            </div>
          </div>
          <div class="flex items-center text-emerald-500 text-sm font-medium">
            <ArrowTrendingUpIcon class="w-4 h-4 mr-1" />
            {{ uploadChangePercent }}%
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
              <p class="text-xl font-bold text-slate-800">{{ formatSize(recentActivity.downloaded_24h || 0) }}</p>
            </div>
          </div>
          <div class="flex items-center text-red-500 text-sm font-medium">
            <ArrowTrendingDownIcon class="w-4 h-4 mr-1" />
            {{ downloadChangePercent }}%
          </div>
        </div>
      </div>

      <!-- 总上传量 -->
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center space-x-3">
          <div class="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center">
            <CloudArrowUpIcon class="w-6 h-6 text-emerald-500" />
          </div>
          <div>
            <p class="text-sm text-slate-400">总上传量</p>
            <p class="text-xl font-bold text-slate-800">{{ formatSize(stats.total_uploaded || 0) }}</p>
          </div>
        </div>
      </div>

      <!-- 总下载量 -->
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-slate-100 hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center space-x-3">
          <div class="w-12 h-12 rounded-xl bg-orange-50 flex items-center justify-center">
            <CloudArrowDownIcon class="w-6 h-6 text-orange-500" />
          </div>
          <div>
            <p class="text-sm text-slate-400">总下载量</p>
            <p class="text-xl font-bold text-slate-800">{{ formatSize(stats.total_downloaded || 0) }}</p>
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

      <!-- 各站点今日上传 - 基于下载器数据 -->
      <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <h3 class="text-lg font-semibold text-slate-800 mb-6">各站点今日上传</h3>
        <div class="flex flex-col items-center">
          <div class="relative w-48 h-48">
            <v-chart v-if="downloaderUploadData.length > 0" :option="siteUploadChartOption" autoresize />
            <div v-else class="w-full h-full flex items-center justify-center text-slate-400 text-sm">
              暂无数据
            </div>
            <div v-if="downloaderUploadData.length > 0" class="absolute inset-0 flex flex-col items-center justify-center">
              <p class="text-3xl font-bold text-slate-800">{{ formatSizeShort(totalDownloaderUpload) }}</p>
              <p class="text-sm text-slate-400">今日总上传</p>
            </div>
          </div>
          <div class="mt-6 space-y-2 w-full">
            <div v-for="item in downloaderUploadData" :key="item.name" class="flex items-center justify-between text-sm">
              <div class="flex items-center">
                <span class="w-2 h-2 rounded-full mr-2" :style="{ backgroundColor: item.color }"></span>
                <span class="text-slate-600">{{ item.name }}: {{ formatSizeShort(item.value) }}</span>
              </div>
              <span class="text-slate-400">({{ item.percent }}%)</span>
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
      <!-- 活跃种子列表 - 真实数据 -->
      <div class="col-span-1 bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-800">活跃种子列表</h3>
          <button @click="refreshTorrents" class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer">
            <ArrowPathIcon class="w-5 h-5" :class="{ 'animate-spin': isRefreshingTorrents }" />
          </button>
        </div>
        <div class="overflow-x-auto max-h-64">
          <table v-if="activeTorrents.length > 0" class="w-full text-sm">
            <thead>
              <tr class="text-slate-400 text-left border-b border-slate-100">
                <th class="pb-3 font-medium">名称</th>
                <th class="pb-3 font-medium">上传</th>
                <th class="pb-3 font-medium">下载</th>
                <th class="pb-3 font-medium">进度</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="torrent in activeTorrents" :key="torrent.hash" class="border-b border-slate-50 hover:bg-slate-50">
                <td class="py-3 text-slate-700 truncate max-w-[100px]" :title="torrent.name">{{ torrent.name }}</td>
                <td class="py-3 text-blue-600 text-xs">{{ formatSpeed(torrent.upload_speed) }}</td>
                <td class="py-3 text-emerald-600 text-xs">{{ formatSpeed(torrent.download_speed) }}</td>
                <td class="py-3">
                  <div class="w-12 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full"
                      :style="{ width: (torrent.progress * 100) + '%' }"
                    ></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="flex flex-col items-center justify-center py-8 text-slate-400">
            <CircleStackIcon class="w-12 h-12 mb-2" />
            <p class="text-sm">暂无活跃种子</p>
          </div>
        </div>
      </div>

      <!-- 服务运行状态 - 参考原来的实现 -->
      <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-800">服务运行状态</h3>
          <button @click="refreshServices" class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer">
            <ArrowPathIcon class="w-5 h-5" :class="{ 'animate-spin': isRefreshing }" />
          </button>
        </div>
        <div class="space-y-3">
          <!-- 动态限速 -->
          <div class="flex items-center justify-between p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer" @click="$router.push('/speed-limit')">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                <BoltIcon class="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p class="text-sm font-medium text-slate-700">动态限速</p>
                <p v-if="servicesStatus.speed_limit?.target_speed" class="text-xs text-slate-400">
                  {{ formatSpeed(servicesStatus.speed_limit.target_speed) }}
                </p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span
                class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="servicesStatus.speed_limit?.enabled
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-slate-200 text-slate-600'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="servicesStatus.speed_limit?.enabled ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'"></span>
                <span>{{ servicesStatus.speed_limit?.enabled ? '运行中' : '已停止' }}</span>
              </span>
              <ChevronRightIcon class="w-4 h-4 text-slate-300" />
            </div>
          </div>

          <!-- U2追魔 -->
          <div class="flex items-center justify-between p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer" @click="$router.push('/u2-magic')">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-xl bg-pink-100 flex items-center justify-center">
                <SparklesIcon class="w-5 h-5 text-pink-600" />
              </div>
              <p class="text-sm font-medium text-slate-700">U2 追魔</p>
            </div>
            <div class="flex items-center space-x-2">
              <span
                class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="servicesStatus.u2_magic?.enabled
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-slate-200 text-slate-600'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="servicesStatus.u2_magic?.enabled ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'"></span>
                <span>{{ servicesStatus.u2_magic?.enabled ? '运行中' : '已停止' }}</span>
              </span>
              <ChevronRightIcon class="w-4 h-4 text-slate-300" />
            </div>
          </div>

          <!-- RSS订阅 -->
          <div class="flex items-center justify-between p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer" @click="$router.push('/rss')">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
                <RssIcon class="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <p class="text-sm font-medium text-slate-700">RSS 订阅</p>
                <p class="text-xs text-slate-400">{{ servicesStatus.rss?.enabled_feeds || 0 }} 个活跃</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span
                class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="servicesStatus.rss?.enabled_feeds > 0
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-slate-200 text-slate-600'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="servicesStatus.rss?.enabled_feeds > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'"></span>
                <span>{{ servicesStatus.rss?.enabled_feeds > 0 ? '运行中' : '已停止' }}</span>
              </span>
              <ChevronRightIcon class="w-4 h-4 text-slate-300" />
            </div>
          </div>

          <!-- 删种规则 -->
          <div class="flex items-center justify-between p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer" @click="$router.push('/delete-rules')">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center">
                <TrashIcon class="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p class="text-sm font-medium text-slate-700">删种规则</p>
                <p class="text-xs text-slate-400">{{ servicesStatus.delete?.enabled_rules || 0 }} 条规则</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <span
                class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="servicesStatus.delete?.enabled_rules > 0
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-slate-200 text-slate-600'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="servicesStatus.delete?.enabled_rules > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'"></span>
                <span>{{ servicesStatus.delete?.enabled_rules > 0 ? '运行中' : '已停止' }}</span>
              </span>
              <ChevronRightIcon class="w-4 h-4 text-slate-300" />
            </div>
          </div>
        </div>
      </div>

      <!-- 日志更新 -->
      <div class="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-800">日志更新</h3>
          <button @click="$router.push('/logs')" class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer">
            <AdjustmentsHorizontalIcon class="w-5 h-5" />
          </button>
        </div>
        <div class="space-y-4 max-h-64 overflow-y-auto">
          <div v-for="log in recentLogs" :key="log.id" class="border-l-2 pl-4 transition-colors"
               :class="getLogBorderClass(log.level)">
            <p class="text-sm font-medium text-slate-700">{{ formatLogTime(log.timestamp) }}</p>
            <p class="text-xs text-slate-400 mt-1 line-clamp-2">{{ log.message }}</p>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
  CloudArrowUpIcon,
  CloudArrowDownIcon,
  ArrowPathIcon,
  ChevronRightIcon,
  AdjustmentsHorizontalIcon,
  BoltIcon,
  SparklesIcon,
  RssIcon,
  TrashIcon,
  CircleStackIcon,
} from '@heroicons/vue/24/outline'

// ECharts setup
use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()
const dashboardStore = useDashboardStore()

const currentVersion = '2.2n'
const selectedPeriod = ref('day')
const isRefreshing = ref(false)
const isRefreshingTorrents = ref(false)

// 活跃种子数据
const activeTorrents = ref([])
// 下载器上传数据（用于环形图）
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

// 计算上传变化百分比
const uploadChangePercent = computed(() => {
  const current = recentActivity.value?.uploaded_24h || 0
  const previous = recentActivity.value?.uploaded_previous_24h || current
  if (previous === 0) return current > 0 ? 100 : 0
  return Math.round(((current - previous) / previous) * 100)
})

// 计算下载变化百分比
const downloadChangePercent = computed(() => {
  const current = recentActivity.value?.downloaded_24h || 0
  const previous = recentActivity.value?.downloaded_previous_24h || current
  if (previous === 0) return current > 0 ? 100 : 0
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
    backgroundColor: '#fff',
    borderColor: '#e2e8f0',
    textStyle: { color: '#334155' },
    formatter: (params) => {
      let result = `<div class="font-medium text-slate-800">${params[0].axisValue}</div>`
      params.forEach(param => {
        result += `<div class="flex items-center justify-between gap-4 mt-1">
          <span>${param.marker} ${param.seriesName}</span>
          <span class="font-medium">${formatSpeed(param.value)}</span>
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
    data: speedHistory.value.map(h => h.time),
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisLabel: { color: '#94a3b8', fontSize: 12 },
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    axisLabel: {
      color: '#94a3b8',
      fontSize: 12,
      formatter: (value) => formatSpeed(value)
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
      data: speedHistory.value.map(h => h.download),
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

function formatLogTime(timestamp) {
  if (!timestamp) return ''
  return dayjs(timestamp).format('M月D日 HH:mm')
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

    // 从所有下载器获取种子
    for (const downloader of downloadersStatus.value) {
      if (downloader.online) {
        try {
          const response = await downloadersApi.getTorrents(downloader.id)
          if (response.data) {
            // 只获取活跃的种子（有上传或下载速度的）
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

    // 按上传速度排序，取前10个
    activeTorrents.value = allTorrents
      .sort((a, b) => b.upload_speed - a.upload_speed)
      .slice(0, 10)
  } catch (error) {
    console.error('Failed to fetch active torrents:', error)
  }
}

// 获取下载器上传数据（用于环形图）
function updateDownloaderUploadData() {
  const data = downloadersStatus.value
    .filter(d => d.online)
    .map((d, index) => ({
      name: d.name,
      value: d.upload_speed || 0,
      color: chartColors[index % chartColors.length],
      percent: 0
    }))

  // 计算百分比
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

  // 只保留最近20个数据点
  if (speedHistory.value.length > 20) {
    speedHistory.value.shift()
  }
}

// Lifecycle
let refreshInterval

onMounted(async () => {
  // 初始化速度历史
  const now = dayjs()
  for (let i = 19; i >= 0; i--) {
    speedHistory.value.push({
      time: now.subtract(i * 3, 'second').format('HH:mm'),
      upload: 0,
      download: 0
    })
  }

  await dashboardStore.fetchAll()
  await fetchRecentLogs()

  // 等待下载器状态加载完成后获取种子
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
    updateSpeedHistory()
    updateDownloaderUploadData()
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>
