<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl shadow-lg shadow-emerald-500/30"
             style="background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%)">
          <ServerStackIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">下载器管理</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">配置和管理 BitTorrent 下载客户端</p>
        </div>
      </div>
      <Button variant="primary" @click="openModal()">
        <PlusIcon class="w-4 h-4" />
        添加下载器
      </Button>
    </div>

    <!-- 空状态 -->
    <Card v-if="downloaders.length === 0">
      <div class="empty-state py-12">
        <div class="empty-state-icon">
          <ServerStackIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title">暂无下载器</p>
        <p class="empty-state-description">添加你的第一个下载器开始使用</p>
        <Button variant="primary" class="mt-4" @click="openModal()">
          <PlusIcon class="w-4 h-4" />
          添加下载器
        </Button>
      </div>
    </Card>

    <!-- 下载器列表 -->
    <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <Card
        v-for="dl in downloaders"
        :key="dl.id"
        :padding="false"
        class="overflow-hidden cursor-pointer transition-all duration-200 hover:shadow-lg"
        :class="{ 'ring-2 ring-primary-500': selectedDownloader?.id === dl.id }"
        @click="selectDownloader(dl)"
      >
        <!-- 头部 -->
        <div class="p-4 border-b border-surface-100 dark:border-surface-700">
          <div class="flex items-start justify-between">
            <div class="flex items-center space-x-3">
              <div
                class="w-12 h-12 rounded-xl flex items-center justify-center"
                :class="dl.enabled && getStatus(dl.id)?.online
                  ? 'shadow-lg shadow-emerald-500/30'
                  : 'bg-surface-100 dark:bg-surface-700'"
                :style="dl.enabled && getStatus(dl.id)?.online ? { background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)' } : {}"
              >
                <ServerIcon
                  class="w-6 h-6"
                  :class="dl.enabled && getStatus(dl.id)?.online ? 'text-white' : 'text-surface-400'"
                />
              </div>
              <div>
                <h3 class="font-semibold text-surface-900 dark:text-white">{{ dl.name }}</h3>
                <p class="text-xs text-surface-500 dark:text-surface-400 flex items-center space-x-2">
                  <span class="px-1.5 py-0.5 rounded bg-surface-100 dark:bg-surface-700">{{ dl.type }}</span>
                  <span>{{ dl.host }}:{{ dl.port }}</span>
                </p>
              </div>
            </div>
            <span
              class="badge"
              :class="[
                loadingStatuses && !getStatus(dl.id) ? 'badge-gray' :
                getStatus(dl.id)?.online ? 'badge-success badge-dot' : 'badge-danger'
              ]"
            >
              <template v-if="loadingStatuses && !getStatus(dl.id)">
                <span class="inline-block w-3 h-3 border-2 border-surface-300 border-t-surface-500 rounded-full animate-spin mr-1"></span>
                检测中
              </template>
              <template v-else>
                {{ getStatus(dl.id)?.online ? '在线' : '离线' }}
              </template>
            </span>
          </div>
        </div>

        <!-- 状态信息 -->
        <div class="p-4 bg-surface-50/50 dark:bg-surface-800/50">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400 mb-1">上传速度</p>
              <p class="font-semibold text-blue-600 dark:text-blue-400 flex items-center">
                <ArrowUpIcon class="w-3.5 h-3.5 mr-1" />
                {{ formatSpeed(getStatus(dl.id)?.upload_speed || 0) }}
              </p>
            </div>
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400 mb-1">下载速度</p>
              <p class="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center">
                <ArrowDownIcon class="w-3.5 h-3.5 mr-1" />
                {{ formatSpeed(getStatus(dl.id)?.download_speed || 0) }}
              </p>
            </div>
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400 mb-1">活动种子</p>
              <p class="font-semibold text-surface-900 dark:text-white">
                {{ getStatus(dl.id)?.active_torrents || 0 }} / {{ getStatus(dl.id)?.total_torrents || 0 }}
              </p>
            </div>
            <div>
              <p class="text-xs text-surface-500 dark:text-surface-400 mb-1">剩余空间</p>
              <p class="font-semibold text-surface-900 dark:text-white">
                {{ formatSize(getStatus(dl.id)?.free_space || 0) }}
              </p>
            </div>
          </div>
          <div class="mt-3 pt-3 border-t border-surface-200 dark:border-surface-700 text-xs text-surface-500 dark:text-surface-400">
            做种: {{ getStatus(dl.id)?.seeding_torrents || 0 }} · 下载中: {{ getStatus(dl.id)?.downloading_torrents || 0 }}
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="p-3 flex justify-end space-x-2 border-t border-surface-100 dark:border-surface-700">
          <Button variant="ghost" size="sm" @click.stop="testConnection(dl)" :loading="testingDownloader === dl.id">
            <SignalIcon class="w-4 h-4" />
            测试
          </Button>
          <Button variant="ghost" size="sm" @click.stop="openModal(dl)">
            <PencilIcon class="w-4 h-4" />
            编辑
          </Button>
          <Button variant="ghost" size="sm" @click.stop="deleteDownloader(dl)" :loading="deletingDownloader === dl.id">
            <TrashIcon class="w-4 h-4 text-red-500" />
          </Button>
        </div>
      </Card>
    </div>

    <!-- 种子列表 -->
    <Card v-if="selectedDownloader" :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
              <QueueListIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">种子列表</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">{{ selectedDownloader.name }} - {{ torrents.length }} 个种子</p>
            </div>
          </div>
          <Button variant="secondary" size="sm" @click="loadTorrents" :loading="loadingTorrents">
            <ArrowPathIcon class="w-4 h-4" />
            刷新
          </Button>
        </div>
      </template>

      <div v-if="loadingTorrents" class="flex flex-col items-center justify-center py-16">
        <div class="w-12 h-12 rounded-full border-4 border-primary-200 border-t-primary-600 animate-spin"></div>
        <p class="mt-4 text-surface-500 dark:text-surface-400">加载种子列表...</p>
      </div>

      <div v-else-if="torrents.length === 0" class="empty-state py-12">
        <div class="empty-state-icon !w-12 !h-12">
          <QueueListIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title text-base">暂无种子</p>
        <p class="empty-state-description">该下载器中没有种子任务</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>名称</th>
              <th class="w-24">大小</th>
              <th class="w-36">进度</th>
              <th class="w-32">速度</th>
              <th class="w-20">分享率</th>
              <th class="w-24">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="torrent in torrents" :key="torrent.hash" class="hover:bg-surface-50 dark:hover:bg-surface-800/50">
              <td class="max-w-xs">
                <p class="truncate font-medium text-surface-900 dark:text-white" :title="torrent.name">
                  {{ torrent.name }}
                </p>
              </td>
              <td class="text-surface-500 dark:text-surface-400">{{ formatSize(torrent.size) }}</td>
              <td>
                <div class="flex items-center space-x-2">
                  <div class="flex-1 bg-surface-200 dark:bg-surface-700 rounded-full h-2 overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all duration-300"
                      :class="torrent.progress >= 1 ? 'bg-green-500' : 'bg-primary-500'"
                      :style="{ width: `${torrent.progress * 100}%` }"
                    ></div>
                  </div>
                  <span class="text-xs font-medium text-surface-600 dark:text-surface-400 w-12 text-right">
                    {{ (torrent.progress * 100).toFixed(1) }}%
                  </span>
                </div>
              </td>
              <td>
                <div class="space-y-0.5">
                  <div class="text-xs text-blue-600 dark:text-blue-400 flex items-center">
                    <ArrowUpIcon class="w-3 h-3 mr-1" />
                    {{ formatSpeed(torrent.upload_speed) }}
                  </div>
                  <div class="text-xs text-green-600 dark:text-green-400 flex items-center">
                    <ArrowDownIcon class="w-3 h-3 mr-1" />
                    {{ formatSpeed(torrent.download_speed) }}
                  </div>
                </div>
              </td>
              <td>
                <span
                  class="font-medium"
                  :class="torrent.ratio >= 1 ? 'text-green-600 dark:text-green-400' : 'text-surface-600 dark:text-surface-400'"
                >
                  {{ torrent.ratio.toFixed(2) }}
                </span>
              </td>
              <td>
                <div class="flex items-center space-x-1">
                  <button
                    v-if="torrent.status === 'paused'"
                    @click.stop="resumeTorrent(torrent)"
                    :disabled="actioningTorrent === torrent.hash"
                    class="p-1.5 hover:bg-green-100 dark:hover:bg-green-900/30 rounded-lg transition-colors disabled:opacity-50"
                    title="恢复"
                  >
                    <svg v-if="actioningTorrent === torrent.hash" class="animate-spin w-4 h-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <PlayIcon v-else class="w-4 h-4 text-green-600 dark:text-green-400" />
                  </button>
                  <button
                    v-else
                    @click.stop="pauseTorrent(torrent)"
                    :disabled="actioningTorrent === torrent.hash"
                    class="p-1.5 hover:bg-yellow-100 dark:hover:bg-yellow-900/30 rounded-lg transition-colors disabled:opacity-50"
                    title="暂停"
                  >
                    <svg v-if="actioningTorrent === torrent.hash" class="animate-spin w-4 h-4 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <PauseIcon v-else class="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                  </button>
                  <button
                    @click.stop="deleteTorrent(torrent)"
                    :disabled="actioningTorrent === torrent.hash"
                    class="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors disabled:opacity-50"
                    title="删除"
                  >
                    <svg v-if="actioningTorrent === torrent.hash" class="animate-spin w-4 h-4 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <TrashIcon v-else class="w-4 h-4 text-red-600 dark:text-red-400" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- 添加/编辑弹窗 -->
    <Modal v-model="modalOpen" :title="editingDownloader ? '编辑下载器' : '添加下载器'" size="lg">
      <form @submit.prevent="saveDownloader" class="space-y-6">
        <!-- 基本信息 -->
        <div>
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
            <InformationCircleIcon class="w-4 h-4 mr-2 text-surface-400" />
            基本信息
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2 form-group">
              <label class="form-label">名称</label>
              <input v-model="form.name" type="text" required class="form-input" placeholder="我的下载器" />
            </div>
            <div class="form-group">
              <label class="form-label">类型</label>
              <select v-model="form.type" class="form-select">
                <option value="qbittorrent">qBittorrent</option>
                <option value="transmission">Transmission</option>
                <option value="deluge">Deluge</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">下载目录</label>
              <input v-model="form.download_dir" type="text" class="form-input" placeholder="/downloads" />
            </div>
          </div>
        </div>

        <!-- 连接设置 -->
        <div>
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
            <GlobeAltIcon class="w-4 h-4 mr-2 text-surface-400" />
            连接设置
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-group">
              <label class="form-label">主机地址</label>
              <input v-model="form.host" type="text" required class="form-input" placeholder="localhost" />
            </div>
            <div class="form-group">
              <label class="form-label">端口</label>
              <input v-model.number="form.port" type="number" required class="form-input" placeholder="8080" />
            </div>
            <div class="form-group">
              <label class="form-label">用户名</label>
              <input v-model="form.username" type="text" class="form-input" placeholder="可选" />
            </div>
            <div class="form-group">
              <label class="form-label">密码</label>
              <input v-model="form.password" type="password" class="form-input" placeholder="可选" />
            </div>
          </div>
        </div>

        <!-- 选项 -->
        <div>
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
            <Cog6ToothIcon class="w-4 h-4 mr-2 text-surface-400" />
            选项
          </h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
              <input v-model="form.enabled" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
              <span class="text-sm text-surface-700 dark:text-surface-300">启用</span>
            </label>
            <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
              <input v-model="form.use_ssl" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
              <span class="text-sm text-surface-700 dark:text-surface-300">使用 SSL</span>
            </label>
            <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
              <input v-model="form.auto_report" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
              <span class="text-sm text-surface-700 dark:text-surface-300">自动汇报</span>
            </label>
            <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
              <input v-model="form.auto_delete" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
              <span class="text-sm text-surface-700 dark:text-surface-300">自动删种</span>
            </label>
          </div>
        </div>
      </form>

      <template #footer>
        <Button variant="secondary" @click="modalOpen = false">取消</Button>
        <Button variant="primary" :loading="saving" @click="saveDownloader">
          <CheckIcon class="w-4 h-4" />
          保存
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { getToast } from '@/composables/useToast'
import { downloadersApi } from '@/api'
import { formatSpeed, formatSize } from '@/utils/format'
import { useRealtime } from '@/services/realtime'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'

const toast = getToast()
import {
  PlusIcon,
  ServerStackIcon,
  ServerIcon,
  TrashIcon,
  ArrowPathIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  PlayIcon,
  PauseIcon,
  PencilIcon,
  SignalIcon,
  QueueListIcon,
  InformationCircleIcon,
  GlobeAltIcon,
  Cog6ToothIcon,
  CheckIcon,
} from '@heroicons/vue/24/outline'

const downloaders = ref([])
const statuses = ref({})
const selectedDownloader = ref(null)
const torrents = ref([])
const loadingTorrents = ref(false)
const loadingStatuses = ref(true)
const realtime = useRealtime()
const unsubscribeHandlers = []

const modalOpen = ref(false)
const editingDownloader = ref(null)
const saving = ref(false)
const testingDownloader = ref(null)
const deletingDownloader = ref(null)
const actioningTorrent = ref(null)

const defaultForm = {
  name: '',
  type: 'qbittorrent',
  host: 'localhost',
  port: 8080,
  username: '',
  password: '',
  use_ssl: false,
  download_dir: '',
  enabled: true,
  auto_report: true,
  auto_delete: true,
  auto_speed_limit: false,
}

const form = reactive({ ...defaultForm })

function getStatus(id) {
  return statuses.value[id]
}

async function loadDownloaders() {
  try {
    const response = await downloadersApi.getAll()
    downloaders.value = response.data
    // Load statuses in parallel after getting downloaders
    await loadStatuses()
  } catch (error) {
    console.error('Failed to load downloaders:', error)
  }
}

async function loadStatuses() {
  if (downloaders.value.length === 0) {
    loadingStatuses.value = false
    return
  }

  try {
    const response = await downloadersApi.getAllStatus()
    const statusList = response.data
    // Convert array to object indexed by id
    const newStatuses = {}
    for (const status of statusList) {
      newStatuses[status.id] = status
    }
    statuses.value = newStatuses
  } catch (error) {
    console.error('Failed to load statuses:', error)
    // Fallback: mark all as offline
    for (const dl of downloaders.value) {
      if (!statuses.value[dl.id]) {
        statuses.value[dl.id] = { online: false }
      }
    }
  } finally {
    loadingStatuses.value = false
  }
}

function selectDownloader(dl) {
  selectedDownloader.value = dl
  loadTorrents()
}

async function loadTorrents(silent = false) {
  if (!selectedDownloader.value) return

  if (!silent) {
    loadingTorrents.value = true
  }
  try {
    const response = await downloadersApi.getTorrents(selectedDownloader.value.id)
    torrents.value = response.data
  } catch (error) {
    console.error('Failed to load torrents:', error)
    if (!silent) {
      torrents.value = []
    }
  } finally {
    if (!silent) {
      loadingTorrents.value = false
    }
  }
}

function applyRealtimeStatuses(statusList) {
  const newStatuses = {}
  for (const status of statusList) {
    newStatuses[status.id] = status
  }
  statuses.value = newStatuses
  loadingStatuses.value = false
}

function applyTorrentChanges(payload) {
  if (!selectedDownloader.value || payload.downloader_id !== selectedDownloader.value.id) return
  const updated = [...torrents.value]
  for (const change of payload.changes || []) {
    const index = updated.findIndex(t => t.hash === change.hash)
    if (index >= 0) {
      updated[index] = { ...updated[index], ...change }
    } else {
      updated.unshift(change)
    }
  }
  for (const removedHash of payload.removed || []) {
    const index = updated.findIndex(t => t.hash === removedHash)
    if (index >= 0) {
      updated.splice(index, 1)
    }
  }
  torrents.value = updated
}

function openModal(downloader = null) {
  editingDownloader.value = downloader
  if (downloader) {
    Object.assign(form, downloader)
  } else {
    Object.assign(form, defaultForm)
  }
  modalOpen.value = true
}

async function saveDownloader() {
  saving.value = true
  try {
    if (editingDownloader.value) {
      await downloadersApi.update(editingDownloader.value.id, form)
    } else {
      await downloadersApi.create(form)
    }
    modalOpen.value = false
    await loadDownloaders()
    toast.success('保存成功')
  } catch (error) {
    console.error('Failed to save downloader:', error)
    toast.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteDownloader(dl) {
  if (!confirm('确定要删除此下载器吗？')) return

  deletingDownloader.value = dl.id
  try {
    await downloadersApi.delete(dl.id)
    if (selectedDownloader.value?.id === dl.id) {
      selectedDownloader.value = null
      torrents.value = []
    }
    await loadDownloaders()
    toast.success('下载器已删除')
  } catch (error) {
    console.error('Failed to delete downloader:', error)
    toast.error('删除失败')
  } finally {
    deletingDownloader.value = null
  }
}

async function testConnection(dl) {
  testingDownloader.value = dl.id
  try {
    const response = await downloadersApi.test(dl.id)
    if (response.data.success) {
      toast.success('连接测试成功')
    } else {
      toast.error(`连接测试失败: ${response.data.message}`)
    }
  } catch (error) {
    toast.error('连接测试失败')
  } finally {
    testingDownloader.value = null
  }
}

async function pauseTorrent(torrent) {
  actioningTorrent.value = torrent.hash
  try {
    await downloadersApi.pauseTorrent(selectedDownloader.value.id, torrent.hash)
    await loadTorrents()
    toast.success('已暂停')
  } catch (error) {
    console.error('Failed to pause torrent:', error)
    toast.error('暂停失败')
  } finally {
    actioningTorrent.value = null
  }
}

async function resumeTorrent(torrent) {
  actioningTorrent.value = torrent.hash
  try {
    await downloadersApi.resumeTorrent(selectedDownloader.value.id, torrent.hash)
    await loadTorrents()
    toast.success('已恢复')
  } catch (error) {
    console.error('Failed to resume torrent:', error)
    toast.error('恢复失败')
  } finally {
    actioningTorrent.value = null
  }
}

async function deleteTorrent(torrent) {
  const deleteFiles = confirm('是否同时删除文件？')
  actioningTorrent.value = torrent.hash
  try {
    await downloadersApi.deleteTorrent(selectedDownloader.value.id, torrent.hash, deleteFiles)
    await loadTorrents()
    toast.success('种子已删除')
  } catch (error) {
    console.error('Failed to delete torrent:', error)
    toast.error('删除失败')
  } finally {
    actioningTorrent.value = null
  }
}

onMounted(() => {
  loadDownloaders()
  realtime.connect()
  unsubscribeHandlers.push(
    realtime.subscribe('downloaders_status', applyRealtimeStatuses),
    realtime.subscribe('torrent_changes', applyTorrentChanges)
  )
})

onUnmounted(() => {
  unsubscribeHandlers.forEach((unsubscribe) => unsubscribe())
})

// Watch for selectedDownloader changes to manage torrent refresh
watch(selectedDownloader, (newVal, oldVal) => {
  if (!newVal) {
    torrents.value = []
  }
})
</script>
