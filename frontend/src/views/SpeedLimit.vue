<template>
  <div class="space-y-6 ">
    <!-- Status Overview Cards -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Upload Speed Card -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ $t('speedLimit.targetUploadSpeed') }}</span>
          <ArrowUpIcon class="w-5 h-5 text-blue-500" />
        </div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ formatSpeed(config.target_upload_speed) }}
        </div>
        <div class="mt-3">
          <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
            <span>{{ $t('speedLimit.current') }}</span>
            <span>{{ formatSpeed(currentUploadSpeed) }}</span>
          </div>
          <div class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-blue-500 transition-all duration-300"
              :style="{ width: `${Math.min(100, (currentUploadSpeed / (config.target_upload_speed || 1)) * 100)}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Download Speed Card -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ $t('speedLimit.targetDownloadSpeed') }}</span>
          <ArrowDownIcon class="w-5 h-5 text-green-500" />
        </div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ formatSpeed(config.target_download_speed) }}
        </div>
        <div class="mt-3">
          <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
            <span>{{ $t('speedLimit.current') }}</span>
            <span>{{ formatSpeed(currentDownloadSpeed) }}</span>
          </div>
          <div class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-green-500 transition-all duration-300"
              :style="{ width: `${Math.min(100, (currentDownloadSpeed / (config.target_download_speed || 1)) * 100)}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Limiting Status Card -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ $t('common.status') }}</span>
          <div class="flex items-center space-x-2">
            <span :class="config.enabled ? 'text-green-500' : 'text-gray-400'" class="text-sm">
              {{ config.enabled ? $t('common.enabled') : $t('common.disabled') }}
            </span>
            <button
              @click="toggleEnabled"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                config.enabled ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  config.enabled ? 'translate-x-5' : 'translate-x-0'
                ]"
              ></span>
            </button>
          </div>
        </div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ Object.keys(status).length }} {{ $t('speedLimit.activeSessions') || '个活跃会话' }}
        </div>
        <div class="mt-3 flex space-x-2">
          <Button variant="secondary" size="sm" @click="clearLimits" :loading="clearing" class="flex-1">
            <XCircleIcon class="w-4 h-4 mr-1" />
            {{ $t('speedLimit.clearLimits') }}
          </Button>
          <Button variant="primary" size="sm" @click="applyLimits" :loading="applying" class="flex-1">
            <PlayIcon class="w-4 h-4 mr-1" />
            {{ $t('speedLimit.applyNow') }}
          </Button>
        </div>
      </div>
    </div>

    <!-- Real-time Speed Chart -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <div class="flex items-center space-x-3">
          <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
            <ChartBarIcon class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h3 class="font-medium text-gray-900 dark:text-white">{{ $t('speedLimit.speedHistory') }}</h3>
        </div>
        <Button variant="ghost" size="sm" @click="loadRecords">
          <ArrowPathIcon class="w-4 h-4" />
        </Button>
      </div>
      <div class="p-4">
        <div class="h-72">
          <v-chart :option="chartOption" autoresize />
        </div>
      </div>
    </div>

    <!-- Active Sessions -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <div class="flex items-center space-x-3">
          <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/30">
            <BoltIcon class="w-4 h-4 text-amber-600 dark:text-amber-400" />
          </div>
          <h3 class="font-medium text-gray-900 dark:text-white">{{ $t('speedLimit.currentStatus') }}</h3>
        </div>
        <Button variant="ghost" size="sm" @click="loadStatus">
          <ArrowPathIcon class="w-4 h-4" />
        </Button>
      </div>
      <div class="p-4">
        <div v-if="Object.keys(status).length === 0" class="text-center py-8">
          <CloudIcon class="w-12 h-12 mx-auto text-gray-400" />
          <p class="mt-4 text-gray-500 dark:text-gray-400">{{ $t('speedLimit.noActiveSessions') }}</p>
        </div>
        <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="(data, tracker) in status"
            :key="tracker"
            class="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
          >
            <div class="flex items-center justify-between gap-2 mb-3 min-w-0">
              <span class="font-medium text-gray-900 dark:text-white truncate min-w-0">{{ tracker }}</span>
              <span :class="getPhaseClass(data.phase)" class="text-xs px-2 py-1 rounded-full">
                {{ getPhaseLabel(data.phase) }}
              </span>
            </div>
            <!-- Phase Progress -->
            <div class="mb-3">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-gray-500 dark:text-gray-400">{{ $t('speedLimit.phase') }}</span>
              </div>
              <div class="flex space-x-1">
                <div
                  v-for="phase in ['warmup', 'catch', 'steady', 'finish']"
                  :key="phase"
                  :class="[
                    'flex-1 h-2 rounded-full transition-colors',
                    getPhaseIndex(data.phase) >= getPhaseIndex(phase)
                      ? getPhaseBarColor(phase)
                      : 'bg-gray-200 dark:bg-gray-700'
                  ]"
                ></div>
              </div>
            </div>
            <!-- Speed Info -->
            <div class="space-y-2">
              <div class="flex flex-col gap-1 text-sm sm:flex-row sm:items-center sm:justify-between">
                <span class="text-gray-500 dark:text-gray-400">{{ $t('speedLimit.currentSpeed') }}</span>
                <span class="font-medium text-blue-600 dark:text-blue-400">{{ formatSpeed(data.filtered_speed || 0) }}</span>
              </div>
              <div class="flex flex-col gap-1 text-sm sm:flex-row sm:items-center sm:justify-between">
                <span class="text-gray-500 dark:text-gray-400">{{ $t('speedLimit.limit') }}</span>
                <span class="font-medium text-amber-600 dark:text-amber-400">{{ formatSpeed(data.last_limit || 0) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Configuration -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <div class="flex items-center space-x-3">
          <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-100 dark:bg-purple-900/30">
            <Cog6ToothIcon class="w-4 h-4 text-purple-600 dark:text-purple-400" />
          </div>
          <h3 class="font-medium text-gray-900 dark:text-white">{{ $t('speedLimit.config') }}</h3>
        </div>
      </div>
      <div class="p-4">
        <form @submit.prevent="saveConfig" class="space-y-6">
          <!-- Speed Settings -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div>
              <label class="form-label">目标上传速度 (KB/s)</label>
              <input v-model.number="displayTargetUploadSpeed" type="number" min="0" step="0.1" class="form-input" />
              <p class="text-xs text-gray-500 mt-1">{{ formatSpeed(config.target_upload_speed) }}</p>
            </div>
            <div>
              <label class="form-label">目标下载速度 (KB/s)</label>
              <input v-model.number="displayTargetDownloadSpeed" type="number" min="0" step="0.1" class="form-input" />
              <p class="text-xs text-gray-500 mt-1">{{ formatSpeed(config.target_download_speed) }}</p>
            </div>
            <div>
              <label class="form-label">安全边际</label>
              <input v-model.number="config.safety_margin" type="number" step="0.01" min="0" max="0.5" class="form-input" />
              <p class="text-xs text-gray-500 mt-1">预留的安全空间比例 (0-0.5)</p>
            </div>
          </div>

          <!-- Auto Report Cycle Info -->
          <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <div class="flex items-start space-x-3">
              <div class="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                <ClockIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h4 class="font-medium text-blue-900 dark:text-blue-300">汇报周期自动检测</h4>
                <p class="text-sm text-blue-700 dark:text-blue-400 mt-1">
                  系统会通过监测上传量变化自动检测Tracker的汇报周期，无需手动设置。
                  检测到的周期会显示在活跃会话中。
                </p>
              </div>
            </div>
          </div>

          <!-- PID Parameters -->
          <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">{{ $t('speedLimit.pidParams') }}</h4>
            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="form-label">Kp</label>
                <input v-model.number="config.kp" type="number" step="0.01" class="form-input" />
              </div>
              <div>
                <label class="form-label">Ki</label>
                <input v-model.number="config.ki" type="number" step="0.01" class="form-input" />
              </div>
              <div>
                <label class="form-label">Kd</label>
                <input v-model.number="config.kd" type="number" step="0.01" class="form-input" />
              </div>
            </div>
          </div>

          <div class="flex justify-end">
            <Button variant="primary" type="submit" :loading="savingConfig">
              {{ $t('common.save') }}
            </Button>
          </div>
        </form>
      </div>
    </div>

    <!-- Site-specific Rules -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
        <div class="flex items-center space-x-3">
          <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-teal-100 dark:bg-teal-900/30">
            <GlobeAltIcon class="w-4 h-4 text-teal-600 dark:text-teal-400" />
          </div>
          <h3 class="font-medium text-gray-900 dark:text-white">{{ $t('speedLimit.siteRules') }}</h3>
        </div>
        <Button variant="primary" size="sm" @click="openSiteModal()">
          <PlusIcon class="w-4 h-4 mr-1" />
          {{ $t('speedLimit.addSite') }}
        </Button>
      </div>
      <div class="p-4">
        <div v-if="sites.length === 0" class="text-center py-8">
          <GlobeAltIcon class="w-12 h-12 mx-auto text-gray-400" />
          <p class="mt-4 text-gray-500 dark:text-gray-400">{{ $t('speedLimit.noSiteRules') }}</p>
          <Button variant="primary" class="mt-4" @click="openSiteModal()">
            {{ $t('speedLimit.addSite') }}
          </Button>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="site in sites"
            :key="site.id"
            class="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center space-x-3">
                <div class="flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700">
                  <GlobeAltIcon class="w-4 h-4 text-gray-500" />
                </div>
                <div>
                  <div class="font-medium text-gray-900 dark:text-white">{{ site.tracker_domain }}</div>
                  <div class="flex space-x-4 text-xs text-gray-500 dark:text-gray-400 mt-1">
                    <span>↑ {{ formatSpeed(site.target_upload_speed) }}</span>
                    <span>↓ {{ formatSpeed(site.target_download_speed) }}</span>
                    <span>{{ $t('speedLimit.safetyMargin') }}: {{ site.safety_margin }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-3">
              <button
                @click="toggleSite(site)"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                  site.enabled ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'
                ]"
              >
                <span
                  :class="[
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    site.enabled ? 'translate-x-5' : 'translate-x-0'
                  ]"
                ></span>
              </button>
              <Button variant="ghost" size="sm" @click="openSiteModal(site)">
                <PencilIcon class="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm" @click="deleteSite(site)">
                <TrashIcon class="w-4 h-4 text-red-500" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Site Modal -->
    <Modal v-model="siteModalOpen" :title="editingSite ? $t('speedLimit.editSite') : $t('speedLimit.addSite')">
      <form @submit.prevent="saveSite" class="space-y-4">
        <div>
          <label class="form-label">{{ $t('speedLimit.trackerDomain') }}</label>
          <input
            v-model="siteForm.tracker_domain"
            type="text"
            required
            :disabled="!!editingSite"
            class="form-input"
            placeholder="tracker.example.com"
          />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="form-label">{{ $t('speedLimit.targetUploadSpeed') }} (KB/s)</label>
            <input v-model.number="displaySiteUploadSpeed" type="number" min="0" step="0.1" class="form-input" />
            <p class="text-xs text-gray-500 mt-1">{{ formatSpeed(siteForm.target_upload_speed) }}</p>
          </div>
          <div>
            <label class="form-label">{{ $t('speedLimit.targetDownloadSpeed') }} (KB/s)</label>
            <input v-model.number="displaySiteDownloadSpeed" type="number" min="0" step="0.1" class="form-input" />
            <p class="text-xs text-gray-500 mt-1">{{ formatSpeed(siteForm.target_download_speed) }}</p>
          </div>
        </div>

        <div>
          <label class="form-label">{{ $t('speedLimit.safetyMargin') }}</label>
          <input v-model.number="siteForm.safety_margin" type="number" step="0.01" min="0" max="0.5" class="form-input" />
        </div>

        <label class="flex items-center space-x-2">
          <input v-model="siteForm.enabled" type="checkbox" class="rounded" />
          <span class="text-sm">{{ $t('common.enable') }}</span>
        </label>
      </form>

      <template #footer>
        <Button variant="secondary" @click="siteModalOpen = false">{{ $t('common.cancel') }}</Button>
        <Button variant="primary" :loading="savingSite" @click="saveSite">{{ $t('common.save') }}</Button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, inject } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { speedLimitApi } from '@/api'
import { useSettingsStore } from '@/stores/settings'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import {
  PlusIcon,
  TrashIcon,
  ArrowPathIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ChartBarIcon,
  BoltIcon,
  Cog6ToothIcon,
  GlobeAltIcon,
  CloudIcon,
  PencilIcon,
  PlayIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/vue/24/outline'

const $t = inject('t')

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

dayjs.locale('zh-cn')

const settingsStore = useSettingsStore()

const config = reactive({
  enabled: false,
  target_upload_speed: 0,
  target_download_speed: 0,
  safety_margin: 0.1,
  kp: 0.6,
  ki: 0.1,
  kd: 0.05,
  telegram_enabled: false,
})

const sites = ref([])
const status = ref({})
const records = ref([])

const savingConfig = ref(false)
const applying = ref(false)
const clearing = ref(false)

const siteModalOpen = ref(false)
const editingSite = ref(null)
const savingSite = ref(false)

const defaultSiteForm = {
  tracker_domain: '',
  enabled: true,
  target_upload_speed: 0,
  target_download_speed: 0,
  safety_margin: 0.1,
}

const siteForm = reactive({ ...defaultSiteForm })
const KB = 1024

const displayTargetUploadSpeed = computed({
  get: () => (config.target_upload_speed || 0) / KB,
  set: (value) => {
    config.target_upload_speed = Math.max(0, Math.round((Number(value) || 0) * KB))
  },
})

const displayTargetDownloadSpeed = computed({
  get: () => (config.target_download_speed || 0) / KB,
  set: (value) => {
    config.target_download_speed = Math.max(0, Math.round((Number(value) || 0) * KB))
  },
})

const displaySiteUploadSpeed = computed({
  get: () => (siteForm.target_upload_speed || 0) / KB,
  set: (value) => {
    siteForm.target_upload_speed = Math.max(0, Math.round((Number(value) || 0) * KB))
  },
})

const displaySiteDownloadSpeed = computed({
  get: () => (siteForm.target_download_speed || 0) / KB,
  set: (value) => {
    siteForm.target_download_speed = Math.max(0, Math.round((Number(value) || 0) * KB))
  },
})

// Computed current speeds from status
const currentUploadSpeed = computed(() => {
  let total = 0
  Object.values(status.value).forEach(s => {
    total += s.filtered_speed || 0
  })
  return total
})

const currentDownloadSpeed = computed(() => {
  // For now, use a placeholder - in real implementation this would come from the API
  return 0
})

const chartOption = computed(() => ({
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
    data: [$t('speedLimit.current'), $t('speedLimit.target'), $t('speedLimit.applied')],
    textStyle: { color: settingsStore.darkMode ? '#9ca3af' : '#6b7280' }
  },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: records.value.map(r => dayjs(r.created_at).format('HH:mm')),
    axisLine: { lineStyle: { color: settingsStore.darkMode ? '#4b5563' : '#e5e7eb' } },
    axisLabel: { color: settingsStore.darkMode ? '#9ca3af' : '#6b7280' }
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: (v) => formatSpeed(v),
      color: settingsStore.darkMode ? '#9ca3af' : '#6b7280'
    },
    splitLine: { lineStyle: { color: settingsStore.darkMode ? '#374151' : '#f3f4f6' } }
  },
  series: [
    {
      name: $t('speedLimit.current'),
      type: 'line',
      smooth: true,
      data: records.value.map(r => r.current_speed),
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
      name: $t('speedLimit.target'),
      type: 'line',
      smooth: true,
      data: records.value.map(r => r.target_speed),
      itemStyle: { color: '#10b981' },
      lineStyle: { type: 'dashed' }
    },
    {
      name: $t('speedLimit.applied'),
      type: 'line',
      smooth: true,
      data: records.value.map(r => r.limit_applied),
      itemStyle: { color: '#f59e0b' },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(245, 158, 11, 0.2)' },
            { offset: 1, color: 'rgba(245, 158, 11, 0)' }
          ]
        }
      }
    }
  ]
}))

function formatSpeed(bytes) {
  if (!bytes) return '0 KB/s'
  const k = 1024
  const sizes = ['KB/s', 'MB/s', 'GB/s', 'TB/s']
  let value = bytes / k
  let i = 0
  while (value >= k && i < sizes.length - 1) {
    value /= k
    i += 1
  }
  return parseFloat(value.toFixed(2)) + ' ' + sizes[i]
}

function getPhaseIndex(phase) {
  const phases = ['warmup', 'catch', 'steady', 'finish']
  return phases.indexOf(phase)
}

function getPhaseClass(phase) {
  const classes = {
    warmup: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    catch: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    steady: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    finish: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  }
  return classes[phase] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

function getPhaseBarColor(phase) {
  const colors = {
    warmup: 'bg-blue-500',
    catch: 'bg-amber-500',
    steady: 'bg-green-500',
    finish: 'bg-purple-500',
  }
  return colors[phase] || 'bg-gray-500'
}

function getPhaseLabel(phase) {
  return $t(`speedLimit.phases.${phase}`) || phase
}

async function loadConfig() {
  try {
    const response = await speedLimitApi.getConfig()
    Object.assign(config, response.data)
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

async function saveConfig() {
  savingConfig.value = true
  try {
    await speedLimitApi.updateConfig(config)
    alert($t('messages.saveSuccess'))
  } catch (error) {
    console.error('Failed to save config:', error)
    alert($t('messages.saveFailed'))
  } finally {
    savingConfig.value = false
  }
}

async function toggleEnabled() {
  config.enabled = !config.enabled
  await saveConfig()
}

async function applyLimits() {
  applying.value = true
  try {
    await speedLimitApi.apply()
    await loadStatus()
  } catch (error) {
    console.error('Failed to apply limits:', error)
    alert($t('messages.operationFailed'))
  } finally {
    applying.value = false
  }
}

async function clearLimits() {
  if (!confirm($t('messages.confirmDelete'))) return

  clearing.value = true
  try {
    await speedLimitApi.clear()
    await loadStatus()
  } catch (error) {
    console.error('Failed to clear limits:', error)
  } finally {
    clearing.value = false
  }
}

async function loadSites() {
  try {
    const response = await speedLimitApi.getSites()
    sites.value = response.data
  } catch (error) {
    console.error('Failed to load sites:', error)
  }
}

async function loadStatus() {
  try {
    const response = await speedLimitApi.getStatus()
    status.value = response.data
  } catch (error) {
    console.error('Failed to load status:', error)
  }
}

async function loadRecords() {
  try {
    const response = await speedLimitApi.getRecords({ limit: 60 })
    records.value = response.data.reverse()
  } catch (error) {
    console.error('Failed to load records:', error)
  }
}

function openSiteModal(site = null) {
  editingSite.value = site
  if (site) {
    Object.assign(siteForm, site)
  } else {
    Object.assign(siteForm, defaultSiteForm)
  }
  siteModalOpen.value = true
}

async function saveSite() {
  savingSite.value = true
  try {
    if (editingSite.value) {
      await speedLimitApi.updateSite(editingSite.value.id, siteForm)
    } else {
      await speedLimitApi.createSite(siteForm)
    }
    siteModalOpen.value = false
    await loadSites()
  } catch (error) {
    console.error('Failed to save site:', error)
    alert(error.response?.data?.detail || $t('messages.saveFailed'))
  } finally {
    savingSite.value = false
  }
}

async function toggleSite(site) {
  try {
    await speedLimitApi.updateSite(site.id, { ...site, enabled: !site.enabled })
    await loadSites()
  } catch (error) {
    console.error('Failed to toggle site:', error)
  }
}

async function deleteSite(site) {
  if (!confirm($t('messages.confirmDelete'))) return

  try {
    await speedLimitApi.deleteSite(site.id)
    await loadSites()
  } catch (error) {
    console.error('Failed to delete site:', error)
  }
}

let refreshInterval

onMounted(() => {
  loadConfig()
  loadSites()
  loadStatus()
  loadRecords()

  refreshInterval = setInterval(() => {
    loadStatus()
    loadRecords()
  }, 10000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>
