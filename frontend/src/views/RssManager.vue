<template>
  <div class="space-y-6 ">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-medium text-gray-900 dark:text-white">{{ $t('rss.title') }}</h2>
      <Button variant="primary" @click="openFeedModal()">
        <PlusIcon class="w-4 h-4 mr-2" />
        {{ $t('rss.addFeed') }}
      </Button>
    </div>

    <!-- Feeds List - Vertex Style Cards -->
    <div v-if="feeds.length === 0" class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <RssIcon class="w-12 h-12 mx-auto text-gray-400" />
      <p class="mt-4 text-gray-500 dark:text-gray-400">{{ $t('messages.noData') }}</p>
      <Button variant="primary" class="mt-4" @click="openFeedModal()">
        {{ $t('rss.addFeed') }}
      </Button>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="feed in feeds"
        :key="feed.id"
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <!-- Card Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
          <div class="flex items-center space-x-3">
            <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <RssIcon class="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 class="font-medium text-gray-900 dark:text-white">{{ feed.name }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-md">{{ feed.url }}</p>
            </div>
          </div>
          <div class="flex items-center space-x-3">
            <!-- Toggle Switch -->
            <button
              @click="toggleFeed(feed)"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                feed.enabled ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  feed.enabled ? 'translate-x-5' : 'translate-x-0'
                ]"
              ></span>
            </button>
            <span :class="feed.enabled ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'" class="text-sm font-medium min-w-16">
              {{ feed.enabled ? $t('common.enabled') : $t('common.disabled') }}
            </span>
          </div>
        </div>

        <!-- Card Body -->
        <div class="p-4">
          <!-- Filter Conditions -->
          <div class="mb-4">
            <div class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              {{ $t('rss.filterConditions') || '过滤条件' }}
            </div>
            <div class="flex flex-wrap gap-2">
              <!-- Size Filter -->
              <span v-if="feed.min_size > 0 || feed.max_size > 0" class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
                <CubeIcon class="w-3.5 h-3.5 mr-1" />
                {{ feed.min_size || 0 }}GB - {{ feed.max_size > 0 ? feed.max_size + 'GB' : 'unlimited' }}
              </span>
              <!-- Seeders Filter -->
              <span v-if="feed.min_seeders > 0 || feed.max_seeders > 0" class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
                <UsersIcon class="w-3.5 h-3.5 mr-1" />
                {{ feed.min_seeders || 0 }} - {{ feed.max_seeders > 0 ? feed.max_seeders : 'unlimited' }} {{ $t('rss.seeders') }}
              </span>
              <!-- Free Only -->
              <span v-if="feed.only_free" class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300">
                <SparklesIcon class="w-3.5 h-3.5 mr-1" />
                {{ $t('rss.freeOnly') }}
              </span>
              <!-- Exclude HR -->
              <span v-if="feed.exclude_hr" class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">
                <NoSymbolIcon class="w-3.5 h-3.5 mr-1" />
                {{ $t('rss.excludeHR') }}
              </span>
              <!-- Include Keywords -->
              <span v-if="feed.include_keywords" class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                <MagnifyingGlassIcon class="w-3.5 h-3.5 mr-1" />
                {{ $t('rss.includeKeywords') }}: {{ feed.include_keywords }}
              </span>
              <!-- Exclude Keywords -->
              <span v-if="feed.exclude_keywords" class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300">
                <XMarkIcon class="w-3.5 h-3.5 mr-1" />
                {{ $t('rss.excludeKeywords') }}: {{ feed.exclude_keywords }}
              </span>
              <!-- No Conditions -->
              <span v-if="!feed.only_free && !feed.exclude_hr && !feed.min_size && !feed.max_size && !feed.min_seeders && !feed.max_seeders && !feed.include_keywords && !feed.exclude_keywords" class="text-xs text-gray-400 dark:text-gray-500">
                {{ $t('common.none') }}
              </span>
            </div>
          </div>

          <!-- Options Row -->
          <div class="flex flex-wrap gap-2 mb-4">
            <span class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
              <ClockIcon class="w-3.5 h-3.5 mr-1" />
              {{ $t('rss.fetchInterval') }}: {{ feed.fetch_interval }}s
            </span>
            <span class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
              <ServerIcon class="w-3.5 h-3.5 mr-1" />
              {{ getDownloaderName(feed.downloader_id) }}
            </span>
            <span :class="[
              'inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium',
              feed.first_run_done
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
            ]">
              <CheckCircleIcon v-if="feed.first_run_done" class="w-3.5 h-3.5 mr-1" />
              <ExclamationCircleIcon v-else class="w-3.5 h-3.5 mr-1" />
              {{ feed.first_run_done ? $t('rss.initialized') : $t('rss.firstRunPending') }}
            </span>
          </div>
        </div>

        <!-- Card Footer -->
        <div class="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
          <div class="flex space-x-2">
            <Button variant="ghost" size="sm" @click="fetchFeed(feed)" :loading="fetchingFeed === feed.id">
              <ArrowPathIcon class="w-4 h-4 mr-1" />
              {{ $t('rss.fetch') }}
            </Button>
            <Button variant="ghost" size="sm" @click="resetFeed(feed)">
              <ArrowUturnLeftIcon class="w-4 h-4 mr-1" />
              {{ $t('common.reset') }}
            </Button>
          </div>
          <div class="flex space-x-2">
            <Button variant="ghost" size="sm" @click="openFeedModal(feed)">
              <PencilIcon class="w-4 h-4 mr-1" />
              {{ $t('common.edit') }}
            </Button>
            <Button variant="ghost" size="sm" @click="deleteFeed(feed)">
              <TrashIcon class="w-4 h-4 text-red-500" />
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Records Table -->
    <Card :title="$t('rss.records')">
      <template #action>
        <div class="flex items-center space-x-2">
          <select v-model="recordFilter.feed_id" class="form-select text-xs py-1">
            <option :value="null">{{ $t('rss.allFeeds') }}</option>
            <option v-for="feed in feeds" :key="feed.id" :value="feed.id">{{ feed.name }}</option>
          </select>
          <select v-model="recordFilter.downloaded" class="form-select text-xs py-1">
            <option :value="null">{{ $t('common.all') }}</option>
            <option :value="true">{{ $t('rss.downloaded') }}</option>
            <option :value="false">{{ $t('rss.skipped') }}</option>
          </select>
          <Button variant="ghost" size="sm" @click="loadRecords">
            <ArrowPathIcon class="w-4 h-4" />
          </Button>
        </div>
      </template>

      <div v-if="records.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
        {{ $t('messages.noData') }}
      </div>
      <div v-else class="table-container">
        <table class="data-table">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th>{{ $t('rss.title_') }}</th>
              <th>{{ $t('common.size') }}</th>
              <th>{{ $t('rss.seeders') }}</th>
              <th>{{ $t('common.status') }}</th>
              <th>{{ $t('common.time') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="record in records" :key="record.id">
              <td class="max-w-xs">
                <div class="truncate" :title="record.title">{{ record.title }}</div>
                <div class="flex space-x-1 mt-1">
                  <span v-if="record.is_free" class="badge-success text-xs">{{ $t('rss.free') }}</span>
                  <span v-if="record.is_hr" class="badge-warning text-xs">{{ $t('rss.hr') }}</span>
                </div>
              </td>
              <td>{{ formatSize(record.size) }}</td>
              <td>{{ record.seeders }}</td>
              <td>
                <span v-if="record.downloaded" class="badge-success">{{ $t('rss.downloaded') }}</span>
                <span v-else class="badge-gray" :title="record.skip_reason">
                  {{ record.skip_reason || $t('rss.skipped') }}
                </span>
              </td>
              <td class="text-xs">{{ formatTime(record.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Feed Modal -->
    <Modal v-model="feedModalOpen" :title="editingFeed ? $t('rss.editFeed') : $t('rss.addFeed')" size="xl">
      <form @submit.prevent="saveFeed" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="form-label">{{ $t('rss.feedName') }}</label>
            <input v-model="feedForm.name" type="text" required class="form-input" />
          </div>

          <div class="col-span-2">
            <label class="form-label">{{ $t('rss.feedUrl') }}</label>
            <input v-model="feedForm.url" type="url" required class="form-input" />
          </div>

          <div>
            <label class="form-label">{{ $t('rss.downloader') }}</label>
            <select v-model="feedForm.downloader_id" class="form-select">
              <option :value="null">{{ $t('rss.autoAssign') }}</option>
              <option v-for="dl in downloaders" :key="dl.id" :value="dl.id">{{ dl.name }}</option>
            </select>
          </div>

          <div>
            <label class="form-label">{{ $t('rss.fetchInterval') }}</label>
            <input v-model.number="feedForm.fetch_interval" type="number" min="60" class="form-input" />
          </div>

          <div class="col-span-2">
            <label class="form-label">{{ $t('rss.siteCookie') }}</label>
            <textarea v-model="feedForm.site_cookie" rows="2" class="form-input"></textarea>
          </div>

          <div>
            <label class="form-label">{{ $t('rss.minSize') }}</label>
            <input v-model.number="feedForm.min_size" type="number" step="0.1" min="0" class="form-input" />
          </div>

          <div>
            <label class="form-label">{{ $t('rss.maxSize') }}</label>
            <input v-model.number="feedForm.max_size" type="number" step="0.1" min="0" class="form-input" />
          </div>

          <div>
            <label class="form-label">{{ $t('rss.minSeeders') }}</label>
            <input v-model.number="feedForm.min_seeders" type="number" min="0" class="form-input" />
          </div>

          <div>
            <label class="form-label">{{ $t('rss.maxSeeders') }}</label>
            <input v-model.number="feedForm.max_seeders" type="number" min="0" class="form-input" />
          </div>

          <div class="col-span-2">
            <label class="form-label">{{ $t('rss.includeKeywords') }}</label>
            <input v-model="feedForm.include_keywords" type="text" class="form-input" />
          </div>

          <div class="col-span-2">
            <label class="form-label">{{ $t('rss.excludeKeywords') }}</label>
            <input v-model="feedForm.exclude_keywords" type="text" class="form-input" />
          </div>

          <div class="col-span-2 grid grid-cols-3 gap-4">
            <label class="flex items-center space-x-2">
              <input v-model="feedForm.enabled" type="checkbox" class="rounded" />
              <span class="text-sm">{{ $t('common.enable') }}</span>
            </label>
            <label class="flex items-center space-x-2">
              <input v-model="feedForm.only_free" type="checkbox" class="rounded" />
              <span class="text-sm">{{ $t('rss.freeOnly') }}</span>
            </label>
            <label class="flex items-center space-x-2">
              <input v-model="feedForm.exclude_hr" type="checkbox" class="rounded" />
              <span class="text-sm">{{ $t('rss.excludeHR') }}</span>
            </label>
          </div>
        </div>
      </form>

      <template #footer>
        <Button variant="secondary" @click="feedModalOpen = false">{{ $t('common.cancel') }}</Button>
        <Button variant="primary" :loading="savingFeed" @click="saveFeed">{{ $t('common.save') }}</Button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, inject, computed } from 'vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { rssApi, downloadersApi } from '@/api'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import {
  PlusIcon,
  TrashIcon,
  ArrowPathIcon,
  RssIcon,
  PencilIcon,
  ClockIcon,
  ServerIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowUturnLeftIcon,
  CubeIcon,
  UsersIcon,
  SparklesIcon,
  NoSymbolIcon,
  MagnifyingGlassIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const $t = inject('t')

dayjs.locale('zh-cn')

const feeds = ref([])
const records = ref([])
const downloaders = ref([])

const feedModalOpen = ref(false)
const editingFeed = ref(null)
const savingFeed = ref(false)
const fetchingFeed = ref(null)

const recordFilter = reactive({
  feed_id: null,
  downloaded: null,
})

const defaultFeedForm = {
  name: '',
  url: '',
  enabled: true,
  downloader_id: null,
  auto_assign: true,
  site_cookie: '',
  fetch_interval: 300,
  only_free: false,
  exclude_hr: false,
  min_size: 0,
  max_size: 0,
  min_seeders: 0,
  max_seeders: 0,
  include_keywords: '',
  exclude_keywords: '',
}

const feedForm = reactive({ ...defaultFeedForm })

const downloaderMap = computed(() => {
  const map = {}
  downloaders.value.forEach(dl => {
    map[dl.id] = dl.name
  })
  return map
})

function getDownloaderName(id) {
  if (!id) return $t('rss.autoAssign')
  return downloaderMap.value[id] || $t('common.unknown')
}

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

async function loadFeeds() {
  try {
    const response = await rssApi.getFeeds()
    feeds.value = response.data
  } catch (error) {
    console.error('Failed to load feeds:', error)
  }
}

async function loadRecords() {
  try {
    const params = {
      limit: 100,
      ...(recordFilter.feed_id && { feed_id: recordFilter.feed_id }),
      ...(recordFilter.downloaded !== null && { downloaded: recordFilter.downloaded }),
    }
    const response = await rssApi.getRecords(params)
    records.value = response.data
  } catch (error) {
    console.error('Failed to load records:', error)
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

function openFeedModal(feed = null) {
  editingFeed.value = feed
  if (feed) {
    Object.assign(feedForm, feed)
  } else {
    Object.assign(feedForm, defaultFeedForm)
  }
  feedModalOpen.value = true
}

async function saveFeed() {
  savingFeed.value = true
  try {
    if (editingFeed.value) {
      await rssApi.updateFeed(editingFeed.value.id, feedForm)
    } else {
      await rssApi.createFeed(feedForm)
    }
    feedModalOpen.value = false
    await loadFeeds()
  } catch (error) {
    console.error('Failed to save feed:', error)
    alert(error.response?.data?.detail || $t('messages.saveFailed'))
  } finally {
    savingFeed.value = false
  }
}

async function toggleFeed(feed) {
  try {
    await rssApi.updateFeed(feed.id, { ...feed, enabled: !feed.enabled })
    await loadFeeds()
  } catch (error) {
    console.error('Failed to toggle feed:', error)
  }
}

async function deleteFeed(feed) {
  if (!confirm($t('messages.confirmDelete'))) return

  try {
    await rssApi.deleteFeed(feed.id)
    await loadFeeds()
  } catch (error) {
    console.error('Failed to delete feed:', error)
  }
}

async function fetchFeed(feed) {
  fetchingFeed.value = feed.id
  try {
    const response = await rssApi.fetchFeed(feed.id)
    alert($t('rss.fetchResult', { total: response.data.total, downloaded: response.data.downloaded }))
    await loadRecords()
  } catch (error) {
    console.error('Failed to fetch feed:', error)
    alert($t('messages.operationFailed'))
  } finally {
    fetchingFeed.value = null
  }
}

async function resetFeed(feed) {
  if (!confirm($t('rss.resetConfirm'))) return

  try {
    await rssApi.resetFeed(feed.id)
    await loadFeeds()
  } catch (error) {
    console.error('Failed to reset feed:', error)
  }
}

watch(recordFilter, () => {
  loadRecords()
})

onMounted(() => {
  loadFeeds()
  loadRecords()
  loadDownloaders()
})
</script>
