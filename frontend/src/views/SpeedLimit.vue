<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg shadow-amber-500/30">
          <BoltIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">动态限速</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">单种子独立周期控制 · 标签/分类命中后自动接管</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-sm font-medium" :class="config.enabled ? 'text-green-600 dark:text-green-400' : 'text-surface-500 dark:text-surface-400'">
          {{ config.enabled ? '已启用' : '已禁用' }}
        </span>
        <button
          @click="toggleEnabled"
          :class="[
            'relative inline-flex h-6 w-11 flex-shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out',
            config.enabled ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
          ]"
        >
          <span
            :class="[
              'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
              config.enabled ? 'translate-x-5' : 'translate-x-0'
            ]"
          />
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card :padding="false">
        <div class="p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <ShieldCheckIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <span class="text-xs text-blue-600 dark:text-blue-400 font-medium">单种安全上传</span>
          </div>
          <p class="text-2xl font-bold text-surface-900 dark:text-white">{{ formatBytes(config.safe_total_upload_per_torrent || 0) }}</p>
          <p class="text-xs text-surface-500 dark:text-surface-400 mt-2">基础安全均速 × 周期秒数</p>
        </div>
      </Card>

      <Card :padding="false">
        <div class="p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
              <HandRaisedIcon class="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <span class="text-xs text-red-600 dark:text-red-400 font-medium">绝对刹车阈值</span>
          </div>
          <p class="text-2xl font-bold text-surface-900 dark:text-white">{{ formatBytes(config.brake_threshold_per_torrent || 0) }}</p>
          <p class="text-xs text-surface-500 dark:text-surface-400 mt-2">到线立刻硬刹车</p>
        </div>
      </Card>

      <Card :padding="false">
        <div class="p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <BoltIcon class="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <span class="text-xs text-amber-600 dark:text-amber-400 font-medium">当前管理对象</span>
          </div>
          <p class="text-2xl font-bold text-surface-900 dark:text-white">{{ Object.keys(status).length }}</p>
          <p class="text-xs text-surface-500 dark:text-surface-400 mt-2">命中标签或分类的种子</p>
        </div>
      </Card>

      <Card :padding="false">
        <div class="p-4 flex flex-col justify-between h-full">
          <div>
            <div class="flex items-center justify-between mb-2">
              <div class="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                <ClockIcon class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <span class="text-xs text-emerald-600 dark:text-emerald-400 font-medium">最后刷新</span>
            </div>
            <p class="text-2xl font-bold text-surface-900 dark:text-white">{{ lastRefresh || '--:--:--' }}</p>
          </div>
          <div class="mt-3 flex gap-2">
            <Button variant="secondary" size="sm" @click="clearLimits" :loading="clearing" class="flex-1">
              清除
            </Button>
            <Button variant="primary" size="sm" @click="applyLimits" :loading="applying" class="flex-1">
              应用
            </Button>
          </div>
        </div>
      </Card>
    </div>

    <Card :padding="false">
      <template #header>
        <div class="flex items-center space-x-3">
          <div class="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
            <SparklesIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h3 class="font-semibold text-surface-900 dark:text-white">策略说明</h3>
            <p class="text-xs text-surface-500 dark:text-surface-400">严格按你给的脚本逻辑实现</p>
          </div>
        </div>
      </template>
      <div class="p-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3 text-sm">
        <div class="p-4 rounded-xl bg-surface-50 dark:bg-surface-800/50 border border-surface-200 dark:border-surface-700">
          <div class="font-medium text-surface-900 dark:text-white">对象过滤</div>
          <div class="text-surface-500 dark:text-surface-400 mt-1">命中标签 OR 分类即纳入管理</div>
        </div>
        <div class="p-4 rounded-xl bg-surface-50 dark:bg-surface-800/50 border border-surface-200 dark:border-surface-700">
          <div class="font-medium text-surface-900 dark:text-white">全局监控</div>
          <div class="text-surface-500 dark:text-surface-400 mt-1">本周期上传到阈值立刻硬刹车</div>
        </div>
        <div class="p-4 rounded-xl bg-surface-50 dark:bg-surface-800/50 border border-surface-200 dark:border-surface-700">
          <div class="font-medium text-surface-900 dark:text-white">延迟恢复</div>
          <div class="text-surface-500 dark:text-surface-400 mt-1">周期结束后再延迟恢复进入下一周期</div>
        </div>
        <div class="p-4 rounded-xl bg-surface-50 dark:bg-surface-800/50 border border-surface-200 dark:border-surface-700">
          <div class="font-medium text-surface-900 dark:text-white">上传压制</div>
          <div class="text-surface-500 dark:text-surface-400 mt-1">进度 ≥ 80% 且周期均速超标时压制上传</div>
        </div>
        <div class="p-4 rounded-xl bg-surface-50 dark:bg-surface-800/50 border border-surface-200 dark:border-surface-700">
          <div class="font-medium text-surface-900 dark:text-white">下载刹车</div>
          <div class="text-surface-500 dark:text-surface-400 mt-1">进度 ≥ 97% 且均速仍超标时锁定下载刹车</div>
        </div>
      </div>
    </Card>

    <Card :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
              <Cog6ToothIcon class="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">参数配置</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">全部都可直接可视化输入</p>
            </div>
          </div>
          <Button variant="secondary" size="sm" @click="loadStatus">刷新状态</Button>
        </div>
      </template>
      <div class="p-4">
        <form class="space-y-6" @submit.prevent="saveConfig">
          <div>
            <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3">匹配范围</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-group">
                <label class="form-label">目标标签（逗号分隔）</label>
                <input v-model="config.target_tags" class="form-input" placeholder="u2, vip" />
              </div>
              <div class="form-group">
                <label class="form-label">目标分类（逗号分隔）</label>
                <input v-model="config.target_categories" class="form-input" placeholder="u2, movies" />
              </div>
            </div>
          </div>

          <div>
            <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3">周期与安全线</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
              <div class="form-group">
                <label class="form-label">周期秒数</label>
                <input v-model.number="config.report_period_seconds" type="number" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">恢复延迟秒数</label>
                <input v-model.number="config.recovery_delay_seconds" type="number" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">基础安全均速 (B/s)</label>
                <input v-model.number="config.upload_limit_bps" type="number" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">周期均速阈值 (B/s)</label>
                <input v-model.number="config.avg_speed_threshold_bps" type="number" class="form-input" />
              </div>
            </div>
          </div>

          <div>
            <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3">刹车与压制</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <div class="form-group">
                <label class="form-label">刹车缓冲 (Bytes)</label>
                <input v-model.number="config.brake_buffer_bytes" type="number" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">上传刹车速度 (B/s)</label>
                <input v-model.number="config.brake_speed_bps" type="number" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">上传压制进度阈值</label>
                <input v-model.number="config.progress_threshold" type="number" step="0.01" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">上传压制速度 (B/s)</label>
                <input v-model.number="config.late_stage_limit_bps" type="number" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">下载刹车进度阈值</label>
                <input v-model.number="config.download_brake_progress_threshold" type="number" step="0.01" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">下载刹车速度 (B/s)</label>
                <input v-model.number="config.download_brake_speed_bps" type="number" class="form-input" />
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-2">
            <Button variant="secondary" type="button" @click="applyLimits" :loading="applying">立即应用</Button>
            <Button variant="primary" type="submit" :loading="saving">保存配置</Button>
          </div>
        </form>
      </div>
    </Card>

    <Card :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <ChartBarIcon class="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">当前管理对象</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">状态、阈值、限制值全部可视化</p>
            </div>
          </div>
          <div class="text-xs text-surface-400">{{ lastRefresh || '--:--:--' }}</div>
        </div>
      </template>

      <div v-if="Object.keys(status).length === 0" class="py-12 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-100 dark:bg-surface-700 mb-4">
          <CloudIcon class="w-8 h-8 text-surface-400" />
        </div>
        <p class="text-surface-600 dark:text-surface-400 font-medium">暂无管理中的种子</p>
        <p class="text-sm text-surface-500 mt-1">当前没有命中标签或分类的对象</p>
      </div>

      <div v-else class="p-4 space-y-4">
        <div
          v-for="(item, hash) in status"
          :key="hash"
          class="p-4 bg-surface-50 dark:bg-surface-700/30 rounded-xl border border-surface-200 dark:border-surface-700"
        >
          <div class="flex items-start justify-between gap-3 mb-4">
            <div class="min-w-0 flex-1">
              <div class="font-medium text-surface-900 dark:text-white truncate text-sm sm:text-base">{{ item.name }}</div>
              <div class="text-xs text-surface-500 dark:text-surface-400 truncate mt-0.5">{{ hash }}</div>
            </div>
            <span :class="statusClass(item.status)" class="text-xs px-2 py-1 rounded-full flex-shrink-0 font-medium">
              {{ statusLabel(item.status) }}
            </span>
          </div>

          <div class="mb-4 p-3 rounded-lg bg-gradient-to-r from-indigo-500/10 to-purple-500/10 dark:from-indigo-500/20 dark:to-purple-500/20 border border-indigo-200 dark:border-indigo-800">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div class="flex items-center space-x-2">
                <ClockIcon class="w-4 h-4 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
                <span class="text-xs text-indigo-700 dark:text-indigo-300 font-medium">本周期剩余</span>
              </div>
              <div class="flex items-center justify-end flex-wrap gap-2">
                <span class="text-lg font-bold text-indigo-600 dark:text-indigo-400">{{ formatSeconds(item.period_remaining) }}</span>
                <span v-if="item.recovery_remaining > 0" class="text-xs text-amber-600 dark:text-amber-400">恢复延迟 {{ formatSeconds(item.recovery_remaining) }}</span>
              </div>
            </div>
            <div class="mt-2 h-1.5 bg-indigo-100 dark:bg-indigo-900/50 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                :style="{ width: `${timeProgress(item)}%` }"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-2 text-sm">
            <InfoCell label="进度" :value="`${Math.round((item.progress || 0) * 100)}%`" />
            <InfoCell label="当前上传" :value="formatSpeed(item.upload_speed)" />
            <InfoCell label="当前下载" :value="formatSpeed(item.download_speed)" />
            <InfoCell label="周期上传" :value="formatBytes(item.period_uploaded)" />
            <InfoCell label="周期均速" :value="formatSpeed(item.period_avg_speed)" />
            <InfoCell label="周期编号" :value="`#${item.period_index}`" />
            <InfoCell label="上传限制" :value="item.upload_limit > 0 ? formatSpeed(item.upload_limit) : '不限'" />
            <InfoCell label="下载限制" :value="item.download_limit > 0 ? formatSpeed(item.download_limit) : '不限'" />
            <InfoCell label="标签命中" :value="item.matched_by_tag ? '是' : '否'" />
            <InfoCell label="分类命中" :value="item.matched_by_category ? '是' : '否'" />
            <InfoCell label="标签" :value="(item.tags || []).join(', ') || '无'" />
            <InfoCell label="分类" :value="item.category || '无'" />
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { defineComponent, h, onMounted, reactive, ref } from 'vue'
import dayjs from 'dayjs'
import { speedLimitApi } from '@/api'
import { getToast } from '@/composables/useToast'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import {
  BoltIcon,
  ChartBarIcon,
  ClockIcon,
  CloudIcon,
  Cog6ToothIcon,
  HandRaisedIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from '@heroicons/vue/24/outline'

const InfoCell = defineComponent({
  name: 'InfoCell',
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
  },
  setup(props) {
    return () => h('div', { class: 'p-2 rounded-lg bg-surface-100 dark:bg-surface-600/30' }, [
      h('span', { class: 'text-xs text-surface-500 dark:text-surface-400 block' }, props.label),
      h('span', { class: 'font-semibold text-surface-900 dark:text-white break-all' }, props.value),
    ])
  },
})

const toast = getToast()
const config = reactive({})
const status = ref({})
const lastRefresh = ref('')
const saving = ref(false)
const applying = ref(false)
const clearing = ref(false)

function formatBytes(v) {
  if (!v) return '0 B'
  const units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
  let value = Number(v)
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${value.toFixed(2)} ${units[index]}`
}

function formatSpeed(v) {
  return `${formatBytes(v)}/s`
}

function formatSeconds(v) {
  const value = Number(v || 0)
  const h = Math.floor(value / 3600)
  const m = Math.floor((value % 3600) / 60)
  const s = Math.floor(value % 60)
  if (h > 0) return `${h}h ${m}m ${s}s`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

function statusLabel(v) {
  const map = {
    normal: '前段放流',
    upload_limit: '上传压制',
    period_brake: '周期刹车',
    download_brake: '下载刹车',
    dual_limit: '上下双限',
  }
  return map[v] || v
}

function statusClass(v) {
  const map = {
    normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    upload_limit: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    period_brake: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    download_brake: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    dual_limit: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  }
  return map[v] || 'bg-surface-100 text-surface-700 dark:bg-surface-700 dark:text-surface-300'
}

function timeProgress(item) {
  const total = Number(config.report_period_seconds || 0)
  const remaining = Number(item.period_remaining || 0)
  if (!total) return 0
  return Math.min(100, Math.max(0, ((total - remaining) / total) * 100))
}

async function loadConfig() {
  const { data } = await speedLimitApi.getConfig()
  Object.assign(config, data)
}

async function saveConfig() {
  saving.value = true
  try {
    const { data } = await speedLimitApi.updateConfig(config)
    Object.assign(config, data)
    toast.success('动态限速配置已保存')
  } catch (error) {
    toast.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function loadStatus() {
  const { data } = await speedLimitApi.getStatus()
  status.value = data
  lastRefresh.value = dayjs().format('HH:mm:ss')
}

async function applyLimits() {
  applying.value = true
  try {
    await speedLimitApi.apply()
    await loadStatus()
    toast.success('已按新策略应用限速')
  } catch (error) {
    toast.error(error.response?.data?.detail || '应用失败')
  } finally {
    applying.value = false
  }
}

async function clearLimits() {
  clearing.value = true
  try {
    await speedLimitApi.clear()
    await loadStatus()
    toast.success('已清除所有限制')
  } catch (error) {
    toast.error(error.response?.data?.detail || '清除失败')
  } finally {
    clearing.value = false
  }
}

async function toggleEnabled() {
  config.enabled = !config.enabled
  await saveConfig()
}

onMounted(async () => {
  await loadConfig()
  await loadStatus()
})
</script>
