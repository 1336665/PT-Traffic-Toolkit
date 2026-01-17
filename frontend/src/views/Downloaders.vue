<template>
  <div class="space-y-6 ">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-medium text-gray-900 dark:text-white">{{ $t('downloaders.title') }}</h2>
      <Button variant="primary" @click="openModal()">
        <PlusIcon class="w-4 h-4 mr-2" />
        {{ $t('downloaders.addDownloader') }}
      </Button>
    </div>

    <!-- Downloaders List -->
    <div v-if="downloaders.length === 0" class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <ServerIcon class="w-12 h-12 mx-auto text-gray-400" />
      <p class="mt-2 text-gray-500 dark:text-gray-400">{{ $t('downloaders.noDownloadersConfigured') }}</p>
      <Button variant="primary" class="mt-4" @click="openModal()">
        {{ $t('downloaders.addFirstDownloader') }}
      </Button>
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="dl in downloaders"
        :key="dl.id"
        :class="['card-hover cursor-pointer', { 'ring-2 ring-primary-500': selectedDownloader?.id === dl.id }]"
        @click="selectDownloader(dl)"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center space-x-3">
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center"
              :class="dl.enabled ? 'bg-primary-100 dark:bg-primary-900/30' : 'bg-gray-100 dark:bg-gray-700'"
            >
              <ServerIcon class="w-5 h-5" :class="dl.enabled ? 'text-primary-600' : 'text-gray-400'" />
            </div>
            <div>
              <h3 class="font-medium text-gray-900 dark:text-white">{{ dl.name }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ dl.type }} - {{ dl.host }}:{{ dl.port }}
              </p>
            </div>
          </div>
          <div
            class="w-2 h-2 rounded-full"
            :class="getStatusColor(dl.id)"
          ></div>
        </div>

        <div class="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-500 dark:text-gray-400">{{ $t('common.upload') }}</span>
              <p class="font-medium text-blue-600 dark:text-blue-400">
                {{ formatSpeed(getStatus(dl.id)?.upload_speed || 0) }}
              </p>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">{{ $t('common.download') }}</span>
              <p class="font-medium text-green-600 dark:text-green-400">
                {{ formatSpeed(getStatus(dl.id)?.download_speed || 0) }}
              </p>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">{{ $t('downloaders.activeTorrents') }}</span>
              <p class="font-medium text-gray-900 dark:text-gray-100">
                {{ getStatus(dl.id)?.active_torrents || 0 }} / {{ getStatus(dl.id)?.total_torrents || 0 }}
              </p>
            </div>
            <div>
              <span class="text-gray-500 dark:text-gray-400">{{ $t('dashboard.freeSpace') }}</span>
              <p class="font-medium text-gray-900 dark:text-gray-100">
                {{ formatSize(getStatus(dl.id)?.free_space || 0) }}
              </p>
            </div>
          </div>
          <div class="mt-3 text-xs text-gray-500 dark:text-gray-400">
            {{ $t('downloaders.seedingCount') }}: {{ getStatus(dl.id)?.seeding_torrents || 0 }}
            · {{ $t('downloaders.downloadingCount') }}: {{ getStatus(dl.id)?.downloading_torrents || 0 }}
          </div>
        </div>

        <div class="mt-4 flex justify-end space-x-2">
          <Button variant="ghost" size="sm" @click.stop="testConnection(dl)">
            {{ $t('common.test') }}
          </Button>
          <Button variant="ghost" size="sm" @click.stop="openModal(dl)">
            {{ $t('common.edit') }}
          </Button>
          <Button variant="ghost" size="sm" @click.stop="deleteDownloader(dl)">
            <TrashIcon class="w-4 h-4 text-red-500" />
          </Button>
        </div>
      </Card>
    </div>

    <!-- Torrents Table -->
    <Card v-if="selectedDownloader" :title="`${$t('downloaders.torrents')} - ${selectedDownloader.name}`">
      <template #action>
        <Button variant="ghost" size="sm" @click="loadTorrents">
          <ArrowPathIcon class="w-4 h-4" />
        </Button>
      </template>

      <div v-if="loadingTorrents" class="text-center py-8">
        <ArrowPathIcon class="w-6 h-6 animate-spin mx-auto text-gray-400" />
      </div>

      <div v-else-if="torrents.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
        {{ $t('downloaders.noTorrents') }}
      </div>

      <div v-else class="table-container">
        <table class="data-table">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th>{{ $t('common.name') }}</th>
              <th>{{ $t('common.size') }}</th>
              <th>{{ $t('downloaders.progress') }}</th>
              <th>{{ $t('common.speed') }}</th>
              <th>{{ $t('downloaders.ratio') }}</th>
              <th>{{ $t('common.actions') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="torrent in torrents" :key="torrent.hash">
              <td class="max-w-xs truncate" :title="torrent.name">{{ torrent.name }}</td>
              <td>{{ formatSize(torrent.size) }}</td>
              <td>
                <div class="flex items-center space-x-2">
                  <div class="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div
                      class="h-2 rounded-full"
                      :class="torrent.progress >= 1 ? 'bg-green-500' : 'bg-blue-500'"
                      :style="{ width: `${torrent.progress * 100}%` }"
                    ></div>
                  </div>
                  <span class="text-xs">{{ (torrent.progress * 100).toFixed(1) }}%</span>
                </div>
              </td>
              <td>
                <div class="text-xs">
                  <span class="text-blue-500">{{ formatSpeed(torrent.upload_speed) }}</span>
                  <span class="text-gray-400 mx-1">/</span>
                  <span class="text-green-500">{{ formatSpeed(torrent.download_speed) }}</span>
                </div>
              </td>
              <td>{{ torrent.ratio.toFixed(2) }}</td>
              <td>
                <div class="flex space-x-1">
                  <button
                    v-if="torrent.status === 'paused'"
                    @click="resumeTorrent(torrent)"
                    class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    :title="$t('downloaders.resume')"
                  >
                    <PlayIcon class="w-4 h-4 text-green-500" />
                  </button>
                  <button
                    v-else
                    @click="pauseTorrent(torrent)"
                    class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    :title="$t('downloaders.pause')"
                  >
                    <PauseIcon class="w-4 h-4 text-yellow-500" />
                  </button>
                  <button
                    @click="deleteTorrent(torrent)"
                    class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    :title="$t('common.delete')"
                  >
                    <TrashIcon class="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Add/Edit Modal -->
    <Modal v-model="modalOpen" :title="editingDownloader ? $t('downloaders.editDownloader') : $t('downloaders.addDownloader')" size="lg">
      <form @submit.prevent="saveDownloader" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="form-label">{{ $t('common.name') }}</label>
            <input v-model="form.name" type="text" required class="form-input" />
          </div>

          <div>
            <label class="form-label">{{ $t('common.type') }}</label>
            <select v-model="form.type" class="form-select">
              <option value="qbittorrent">qBittorrent</option>
              <option value="transmission">Transmission</option>
              <option value="deluge">Deluge</option>
            </select>
          </div>

          <div>
            <label class="form-label">{{ $t('downloaders.host') }}</label>
            <input v-model="form.host" type="text" required class="form-input" placeholder="localhost" />
          </div>

          <div>
            <label class="form-label">{{ $t('downloaders.port') }}</label>
            <input v-model.number="form.port" type="number" required class="form-input" />
          </div>

          <div>
            <label class="form-label">{{ $t('downloaders.username') }}</label>
            <input v-model="form.username" type="text" class="form-input" />
          </div>

          <div>
            <label class="form-label">{{ $t('downloaders.password') }}</label>
            <input v-model="form.password" type="password" class="form-input" />
          </div>

          <div class="col-span-2">
            <label class="form-label">{{ $t('downloaders.downloadDir') }}</label>
            <input v-model="form.download_dir" type="text" class="form-input" />
          </div>

          <div class="col-span-2 grid grid-cols-2 gap-4">
            <label class="flex items-center space-x-2">
              <input v-model="form.enabled" type="checkbox" class="rounded" />
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ $t('common.enabled') }}</span>
            </label>
            <label class="flex items-center space-x-2">
              <input v-model="form.use_ssl" type="checkbox" class="rounded" />
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ $t('downloaders.useSSL') }}</span>
            </label>
            <label class="flex items-center space-x-2">
              <input v-model="form.auto_report" type="checkbox" class="rounded" />
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ $t('downloaders.autoReport') }}</span>
            </label>
            <label class="flex items-center space-x-2">
              <input v-model="form.auto_delete" type="checkbox" class="rounded" />
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ $t('downloaders.autoDelete') }}</span>
            </label>
          </div>
        </div>
      </form>

      <template #footer>
        <Button variant="secondary" @click="modalOpen = false">{{ $t('common.cancel') }}</Button>
        <Button variant="primary" :loading="saving" @click="saveDownloader">{{ $t('common.save') }}</Button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, inject } from 'vue'
import { downloadersApi } from '@/api'
import { useDashboardStore } from '@/stores/dashboard'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import {
  PlusIcon,
  ServerIcon,
  TrashIcon,
  ArrowPathIcon,
  PlayIcon,
  PauseIcon,
} from '@heroicons/vue/24/outline'

const $t = inject('t')
const dashboardStore = useDashboardStore()

const downloaders = ref([])
const statuses = ref({})
const selectedDownloader = ref(null)
const torrents = ref([])
const loadingTorrents = ref(false)

const modalOpen = ref(false)
const editingDownloader = ref(null)
const saving = ref(false)

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

function getStatus(id) {
  return statuses.value[id]
}

function getStatusColor(id) {
  const status = statuses.value[id]
  if (!status) return 'bg-gray-400'
  return status.online ? 'bg-green-500' : 'bg-red-500'
}

async function loadDownloaders() {
  try {
    const response = await downloadersApi.getAll()
    downloaders.value = response.data

    // Load status for each downloader
    for (const dl of downloaders.value) {
      try {
        const statusRes = await downloadersApi.getStatus(dl.id)
        statuses.value[dl.id] = statusRes.data
      } catch (e) {
        statuses.value[dl.id] = { online: false }
      }
    }
  } catch (error) {
    console.error('Failed to load downloaders:', error)
  }
}

function selectDownloader(dl) {
  selectedDownloader.value = dl
  loadTorrents()
}

async function loadTorrents() {
  if (!selectedDownloader.value) return

  loadingTorrents.value = true
  try {
    const response = await downloadersApi.getTorrents(selectedDownloader.value.id)
    torrents.value = response.data
  } catch (error) {
    console.error('Failed to load torrents:', error)
    torrents.value = []
  } finally {
    loadingTorrents.value = false
  }
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
  } catch (error) {
    console.error('Failed to save downloader:', error)
    alert(error.response?.data?.detail || $t('messages.saveFailed'))
  } finally {
    saving.value = false
  }
}

async function deleteDownloader(dl) {
  if (!confirm($t('messages.confirmDelete'))) return

  try {
    await downloadersApi.delete(dl.id)
    if (selectedDownloader.value?.id === dl.id) {
      selectedDownloader.value = null
      torrents.value = []
    }
    await loadDownloaders()
  } catch (error) {
    console.error('Failed to delete downloader:', error)
  }
}

async function testConnection(dl) {
  try {
    const response = await downloadersApi.test(dl.id)
    if (response.data.success) {
      alert($t('downloaders.testSuccess'))
    } else {
      alert(`${$t('downloaders.testFailed')}: ${response.data.message}`)
    }
  } catch (error) {
    alert($t('downloaders.testFailed'))
  }
}

async function pauseTorrent(torrent) {
  try {
    await downloadersApi.pauseTorrent(selectedDownloader.value.id, torrent.hash)
    await loadTorrents()
  } catch (error) {
    console.error('Failed to pause torrent:', error)
  }
}

async function resumeTorrent(torrent) {
  try {
    await downloadersApi.resumeTorrent(selectedDownloader.value.id, torrent.hash)
    await loadTorrents()
  } catch (error) {
    console.error('Failed to resume torrent:', error)
  }
}

async function deleteTorrent(torrent) {
  const deleteFiles = confirm($t('downloaders.deleteWithFiles'))
  try {
    await downloadersApi.deleteTorrent(selectedDownloader.value.id, torrent.hash, deleteFiles)
    await loadTorrents()
  } catch (error) {
    console.error('Failed to delete torrent:', error)
  }
}

onMounted(() => {
  loadDownloaders()
})
</script>
