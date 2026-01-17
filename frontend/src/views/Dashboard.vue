<template>
  <div class="space-y-6 ">
    <!-- Stats Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatsCard
        :title="$t('dashboard.uploadSpeed')"
        :value="formatSpeed(stats.total_upload_speed)"
        icon="ArrowUpIcon"
        color="blue"
      />
      <StatsCard
        :title="$t('dashboard.downloadSpeed')"
        :value="formatSpeed(stats.total_download_speed)"
        icon="ArrowDownIcon"
        color="green"
      />
      <StatsCard
        :title="$t('dashboard.activeTorrents')"
        :value="stats.active_torrents.toString()"
        icon="BoltIcon"
        color="yellow"
      />
      <StatsCard
        :title="$t('dashboard.freeSpace')"
        :value="formatSize(stats.free_space)"
        icon="CircleStackIcon"
        color="purple"
      />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Speed Chart -->
      <Card :title="$t('dashboard.speedHistory')">
        <template #action>
          <select v-model="speedChartPeriod" class="form-select text-xs py-1">
            <option value="1h">{{ $t('dashboard.last1Hour') }}</option>
            <option value="6h">{{ $t('dashboard.last6Hours') }}</option>
            <option value="24h">{{ $t('dashboard.last24Hours') }}</option>
          </select>
        </template>
        <div class="h-64">
          <v-chart :option="speedChartOption" autoresize />
        </div>
      </Card>

      <!-- Downloaders Status -->
      <Card :title="$t('dashboard.downloaders')">
        <div v-if="downloadersStatus.length === 0" class="text-center text-gray-500 dark:text-gray-400 py-8">
          {{ $t('dashboard.noDownloaders') }}
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="dl in downloadersStatus"
            :key="dl.id"
            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <div
                class="w-2 h-2 rounded-full"
                :class="dl.online ? 'bg-green-500' : 'bg-red-500'"
              ></div>
              <div>
                <div class="text-sm font-medium text-gray-900 dark:text-white">{{ dl.name }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">{{ dl.type }}</div>
              </div>
            </div>
            <div v-if="dl.online" class="text-right">
              <div class="text-xs text-blue-500">↑ {{ formatSpeed(dl.upload_speed) }}</div>
              <div class="text-xs text-green-500">↓ {{ formatSpeed(dl.download_speed) }}</div>
            </div>
            <span v-else class="badge-danger">{{ $t('common.offline') }}</span>
          </div>
        </div>
      </Card>
    </div>

    <!-- Second Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Services Status -->
      <Card :title="$t('dashboard.servicesStatus')">
        <div class="space-y-3">
          <ServiceStatus
            :name="$t('nav.speedLimit')"
            :enabled="servicesStatus.speed_limit?.enabled"
            :detail="servicesStatus.speed_limit?.target_speed ? formatSpeed(servicesStatus.speed_limit.target_speed) : ''"
          />
          <ServiceStatus
            :name="$t('nav.u2Magic')"
            :enabled="servicesStatus.u2_magic?.enabled"
          />
          <ServiceStatus
            :name="$t('nav.rss')"
            :enabled="servicesStatus.rss?.enabled_feeds > 0"
            :detail="`${servicesStatus.rss?.enabled_feeds || 0} ${$t('common.active')}`"
          />
          <ServiceStatus
            :name="$t('nav.deleteRules')"
            :enabled="servicesStatus.delete?.enabled_rules > 0"
            :detail="`${servicesStatus.delete?.enabled_rules || 0} ${$t('common.active')}`"
          />
        </div>
      </Card>

      <!-- Recent Activity -->
      <Card :title="$t('dashboard.recentActivity')" class="lg:col-span-2">
        <div class="grid grid-cols-3 gap-4">
          <div class="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {{ recentActivity.rss_downloads || 0 }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ $t('dashboard.rssDownloads') }}</div>
          </div>
          <div class="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <div class="text-2xl font-bold text-red-600 dark:text-red-400">
              {{ recentActivity.deleted_torrents || 0 }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ $t('dashboard.deleted') }}</div>
          </div>
          <div class="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {{ recentActivity.magic_downloads || 0 }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ $t('dashboard.magicCaught') }}</div>
          </div>
        </div>
      </Card>
    </div>

    <!-- Activity Timeline -->
    <Card :title="$t('dashboard.activityTimeline')">
      <template #action>
        <Button variant="ghost" size="sm" @click="dashboardStore.fetchTimeline()">
          {{ $t('common.refresh') }}
        </Button>
      </template>
      <div v-if="timeline.length === 0" class="text-center text-gray-500 dark:text-gray-400 py-8">
        {{ $t('dashboard.noActivity') }}
      </div>
      <div v-else class="space-y-4">
        <div
          v-for="item in timeline.slice(0, 10)"
          :key="`${item.type}-${item.id}`"
          class="flex items-start space-x-3"
        >
          <div
            class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
            :class="getTimelineIconClass(item.type)"
          >
            <component :is="getTimelineIcon(item.type)" class="w-4 h-4" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm text-gray-900 dark:text-white truncate">{{ item.title }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ item.description }}</p>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ formatTime(item.timestamp) }}</p>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

import { useDashboardStore } from '@/stores/dashboard'
import { useSettingsStore } from '@/stores/settings'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import StatsCard from '@/components/dashboard/StatsCard.vue'
import ServiceStatus from '@/components/dashboard/ServiceStatus.vue'
import { RssIcon, TrashIcon, SparklesIcon } from '@heroicons/vue/24/outline'

const $t = inject('t')

// ECharts setup
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const dashboardStore = useDashboardStore()
const settingsStore = useSettingsStore()

const speedChartPeriod = ref('1h')
const speedHistory = ref([])

// Computed
const stats = computed(() => dashboardStore.stats)
const timeline = computed(() => dashboardStore.timeline)
const downloadersStatus = computed(() => dashboardStore.downloadersStatus)
const servicesStatus = computed(() => dashboardStore.servicesStatus)
const recentActivity = computed(() => dashboardStore.recentActivity)

const speedChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      let result = params[0].axisValue + '<br/>'
      params.forEach(param => {
        result += `${param.marker} ${param.seriesName}: ${formatSpeed(param.value)}<br/>`
      })
      return result
    }
  },
  legend: {
    data: [$t('dashboard.upload'), $t('dashboard.download')],
    textStyle: {
      color: settingsStore.darkMode ? '#9ca3af' : '#6b7280'
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: speedHistory.value.map(h => h.time),
    axisLine: {
      lineStyle: {
        color: settingsStore.darkMode ? '#4b5563' : '#e5e7eb'
      }
    },
    axisLabel: {
      color: settingsStore.darkMode ? '#9ca3af' : '#6b7280'
    }
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: (value) => formatSpeed(value),
      color: settingsStore.darkMode ? '#9ca3af' : '#6b7280'
    },
    splitLine: {
      lineStyle: {
        color: settingsStore.darkMode ? '#374151' : '#f3f4f6'
      }
    }
  },
  series: [
    {
      name: $t('dashboard.upload'),
      type: 'line',
      smooth: true,
      data: speedHistory.value.map(h => h.upload),
      itemStyle: { color: '#3b82f6' },
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
      name: $t('dashboard.download'),
      type: 'line',
      smooth: true,
      data: speedHistory.value.map(h => h.download),
      itemStyle: { color: '#10b981' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0)' }
          ]
        }
      }
    }
  ]
}))

// Methods
function formatSpeed(bytes) {
  if (bytes === 0) return '0 B/s'
  const k = 1024
  const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatTime(timestamp) {
  return dayjs(timestamp).fromNow()
}

function getTimelineIcon(type) {
  const icons = {
    rss: RssIcon,
    delete: TrashIcon,
    magic: SparklesIcon,
  }
  return icons[type] || RssIcon
}

function getTimelineIconClass(type) {
  const classes = {
    rss: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    delete: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    magic: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
  }
  return classes[type] || classes.rss
}

function updateSpeedHistory() {
  const now = dayjs().format('HH:mm:ss')
  speedHistory.value.push({
    time: now,
    upload: stats.value.total_upload_speed,
    download: stats.value.total_download_speed,
  })
  // Keep only last 60 points
  if (speedHistory.value.length > 60) {
    speedHistory.value.shift()
  }
}

// Lifecycle
let refreshInterval

onMounted(async () => {
  await dashboardStore.fetchAll()
  updateSpeedHistory()

  // Refresh every 5 seconds
  refreshInterval = setInterval(async () => {
    await dashboardStore.fetchStats()
    updateSpeedHistory()
  }, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>
