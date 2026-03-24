<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-surface-900 dark:text-white">动态限速重构版</h2>
        <p class="text-sm text-surface-500 dark:text-surface-400">按周期、按标签/分类管理种子的上传与下载刹车</p>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm" :class="config.enabled ? 'text-green-600 dark:text-green-400' : 'text-surface-500 dark:text-surface-400'">
          {{ config.enabled ? '已启用' : '已禁用' }}
        </span>
        <button
          @click="toggleEnabled"
          :class="[
            'relative inline-flex h-6 w-11 rounded-full transition-colors',
            config.enabled ? 'bg-primary-600' : 'bg-surface-300 dark:bg-surface-600'
          ]"
        >
          <span :class="['inline-block h-5 w-5 rounded-full bg-white transition-transform mt-0.5', config.enabled ? 'translate-x-5' : 'translate-x-0.5']"></span>
        </button>
      </div>
    </div>

    <Card>
      <template #header>
        <div>
          <h3 class="font-semibold text-surface-900 dark:text-white">策略说明</h3>
          <p class="text-xs text-surface-500 dark:text-surface-400">这部分直接对应你给的脚本逻辑</p>
        </div>
      </template>
      <div class="space-y-2 text-sm text-surface-700 dark:text-surface-300">
        <div>1. 命中标签 <b>或</b> 分类的种子才纳入管理。</div>
        <div>2. 本周期上传量达到刹车阈值后，立刻上传硬刹车。</div>
        <div>3. 周期结束并经过恢复延迟后，自动解除所有限制进入下一周期。</div>
        <div>4. 进度达到上传阈值后，若周期均速超标则上传压制。</div>
        <div>5. 进度达到下载阈值后，若周期均速仍超标则下载刹车，并锁定到周期结束。</div>
      </div>
    </Card>

    <Card>
      <template #header>
        <div>
          <h3 class="font-semibold text-surface-900 dark:text-white">参数配置</h3>
          <p class="text-xs text-surface-500 dark:text-surface-400">全部参数都可视化输入</p>
        </div>
      </template>
      <form class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" @submit.prevent="saveConfig">
        <div>
          <label class="form-label">qB 地址</label>
          <input v-model="config.qb_url" class="form-input" />
        </div>
        <div>
          <label class="form-label">qB 用户名</label>
          <input v-model="config.qb_username" class="form-input" />
        </div>
        <div>
          <label class="form-label">qB 密码</label>
          <input v-model="config.qb_password" type="password" class="form-input" />
        </div>

        <div>
          <label class="form-label">目标标签（逗号分隔）</label>
          <input v-model="config.target_tags" class="form-input" />
        </div>
        <div>
          <label class="form-label">目标分类（逗号分隔）</label>
          <input v-model="config.target_categories" class="form-input" />
        </div>
        <div>
          <label class="form-label">周期秒数</label>
          <input v-model.number="config.report_period_seconds" type="number" class="form-input" />
        </div>

        <div>
          <label class="form-label">恢复延迟秒数</label>
          <input v-model.number="config.recovery_delay_seconds" type="number" class="form-input" />
        </div>
        <div>
          <label class="form-label">基础安全均速 (B/s)</label>
          <input v-model.number="config.upload_limit_bps" type="number" class="form-input" />
        </div>
        <div>
          <label class="form-label">周期均速阈值 (B/s)</label>
          <input v-model.number="config.avg_speed_threshold_bps" type="number" class="form-input" />
        </div>

        <div>
          <label class="form-label">刹车缓冲 (Bytes)</label>
          <input v-model.number="config.brake_buffer_bytes" type="number" class="form-input" />
        </div>
        <div>
          <label class="form-label">上传刹车速度 (B/s)</label>
          <input v-model.number="config.brake_speed_bps" type="number" class="form-input" />
        </div>
        <div>
          <label class="form-label">上传压制进度阈值 (0-1)</label>
          <input v-model.number="config.progress_threshold" type="number" step="0.01" class="form-input" />
        </div>

        <div>
          <label class="form-label">上传压制速度 (B/s)</label>
          <input v-model.number="config.late_stage_limit_bps" type="number" class="form-input" />
        </div>
        <div>
          <label class="form-label">下载刹车进度阈值 (0-1)</label>
          <input v-model.number="config.download_brake_progress_threshold" type="number" step="0.01" class="form-input" />
        </div>
        <div>
          <label class="form-label">下载刹车速度 (B/s)</label>
          <input v-model.number="config.download_brake_speed_bps" type="number" class="form-input" />
        </div>

        <div class="md:col-span-2 xl:col-span-3 flex justify-end gap-2">
          <Button variant="secondary" type="button" @click="loadStatus">刷新状态</Button>
          <Button variant="secondary" type="button" @click="clearLimits" :loading="clearing">清除限制</Button>
          <Button variant="secondary" type="button" @click="applyLimits" :loading="applying">立即应用</Button>
          <Button variant="primary" type="submit" :loading="saving">保存配置</Button>
        </div>
      </form>
    </Card>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <div class="text-sm text-surface-500 dark:text-surface-400">安全总流量/种</div>
        <div class="mt-2 text-lg font-semibold text-surface-900 dark:text-white">{{ formatBytes(config.safe_total_upload_per_torrent || 0) }}</div>
      </Card>
      <Card>
        <div class="text-sm text-surface-500 dark:text-surface-400">刹车阈值/种</div>
        <div class="mt-2 text-lg font-semibold text-surface-900 dark:text-white">{{ formatBytes(config.brake_threshold_per_torrent || 0) }}</div>
      </Card>
      <Card>
        <div class="text-sm text-surface-500 dark:text-surface-400">管理中的种子</div>
        <div class="mt-2 text-lg font-semibold text-surface-900 dark:text-white">{{ Object.keys(status).length }}</div>
      </Card>
      <Card>
        <div class="text-sm text-surface-500 dark:text-surface-400">最后刷新</div>
        <div class="mt-2 text-lg font-semibold text-surface-900 dark:text-white">{{ lastRefresh || '--' }}</div>
      </Card>
    </div>

    <Card>
      <template #header>
        <div>
          <h3 class="font-semibold text-surface-900 dark:text-white">当前管理对象</h3>
          <p class="text-xs text-surface-500 dark:text-surface-400">所有状态均可视化展示</p>
        </div>
      </template>
      <div v-if="Object.keys(status).length === 0" class="text-sm text-surface-500 dark:text-surface-400 py-6 text-center">
        当前没有命中标签/分类的种子
      </div>
      <div v-else class="space-y-4">
        <div v-for="(item, hash) in status" :key="hash" class="p-4 rounded-xl border border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800/40">
          <div class="flex flex-wrap items-start justify-between gap-3 mb-3">
            <div>
              <div class="font-semibold text-surface-900 dark:text-white">{{ item.name }}</div>
              <div class="text-xs text-surface-500 dark:text-surface-400">{{ hash }}</div>
            </div>
            <div class="text-xs px-2 py-1 rounded-full" :class="statusClass(item.status)">
              {{ statusLabel(item.status) }}
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-3 text-sm">
            <div><div class="text-surface-500 dark:text-surface-400">进度</div><div class="font-medium">{{ Math.round((item.progress || 0) * 100) }}%</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">当前上传</div><div class="font-medium">{{ formatSpeed(item.upload_speed) }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">当前下载</div><div class="font-medium">{{ formatSpeed(item.download_speed) }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">周期上传</div><div class="font-medium">{{ formatBytes(item.period_uploaded) }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">周期均速</div><div class="font-medium">{{ formatSpeed(item.period_avg_speed) }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">周期编号</div><div class="font-medium">#{{ item.period_index }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">上传限制</div><div class="font-medium">{{ item.upload_limit > 0 ? formatSpeed(item.upload_limit) : '不限' }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">下载限制</div><div class="font-medium">{{ item.download_limit > 0 ? formatSpeed(item.download_limit) : '不限' }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">周期剩余</div><div class="font-medium">{{ formatSeconds(item.period_remaining) }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">恢复剩余</div><div class="font-medium">{{ formatSeconds(item.recovery_remaining) }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">标签命中</div><div class="font-medium">{{ item.matched_by_tag ? '是' : '否' }}</div></div>
            <div><div class="text-surface-500 dark:text-surface-400">分类命中</div><div class="font-medium">{{ item.matched_by_category ? '是' : '否' }}</div></div>
          </div>

          <div class="mt-3 text-xs text-surface-500 dark:text-surface-400">
            标签：{{ (item.tags || []).join(', ') || '无' }} ｜ 分类：{{ item.category || '无' }} ｜ 下载器：{{ item.downloader_name || '-' }}
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import dayjs from 'dayjs'
import { speedLimitApi } from '@/api'
import { getToast } from '@/composables/useToast'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'

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
