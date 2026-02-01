<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl bg-gradient-to-br from-pink-500 to-purple-600 shadow-lg shadow-pink-500/30">
          <SparklesIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">U2 追魔</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">自动追踪并下载 U2 魔法种子</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <span class="text-sm font-medium" :class="config.enabled ? 'text-green-600 dark:text-green-400' : 'text-surface-500 dark:text-surface-400'">
          {{ config.enabled ? '运行中' : '已停止' }}
        </span>
        <button
          @click="toggleEnabled"
          :class="[
            'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
            config.enabled ? 'bg-gradient-to-r from-pink-500 to-purple-600' : 'bg-surface-200 dark:bg-surface-600'
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

    <!-- 统计卡片 - 渐变玻璃风格 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-500/20 dark:to-pink-500/20 border border-purple-200/50 dark:border-purple-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-purple-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-purple-500/10 dark:bg-purple-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-purple-600/70 dark:text-purple-400/70 uppercase tracking-wide">发现魔法</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ stats.total }}</p>
          </div>
          <div class="p-3 rounded-xl bg-purple-500/20 dark:bg-purple-500/30">
            <SparklesIcon class="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
      </div>

      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 dark:from-emerald-500/20 dark:to-teal-500/20 border border-emerald-200/50 dark:border-emerald-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-emerald-600/70 dark:text-emerald-400/70 uppercase tracking-wide">已下载</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ stats.downloaded }}</p>
          </div>
          <div class="p-3 rounded-xl bg-emerald-500/20 dark:bg-emerald-500/30">
            <ArrowDownTrayIcon class="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
          </div>
        </div>
      </div>

      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-amber-500/10 to-orange-500/10 dark:from-amber-500/20 dark:to-orange-500/20 border border-amber-200/50 dark:border-amber-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-amber-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-amber-500/10 dark:bg-amber-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-amber-600/70 dark:text-amber-400/70 uppercase tracking-wide">已跳过</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ stats.skipped }}</p>
          </div>
          <div class="p-3 rounded-xl bg-amber-500/20 dark:bg-amber-500/30">
            <ForwardIcon class="w-6 h-6 text-amber-600 dark:text-amber-400" />
          </div>
        </div>
      </div>

      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 dark:from-blue-500/20 dark:to-indigo-500/20 border border-blue-200/50 dark:border-blue-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-blue-500/10 dark:bg-blue-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-blue-600/70 dark:text-blue-400/70 uppercase tracking-wide">下载体积</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ formatSize(stats.totalSize) }}</p>
          </div>
          <div class="p-3 rounded-xl bg-blue-500/20 dark:bg-blue-500/30">
            <CircleStackIcon class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </div>
    </div>

    <!-- 配置卡片 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center space-x-3">
          <div class="p-2 rounded-lg bg-gradient-to-br from-pink-100 to-purple-100 dark:from-pink-900/30 dark:to-purple-900/30">
            <Cog6ToothIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h3 class="font-semibold text-surface-900 dark:text-white">追魔配置</h3>
            <p class="text-xs text-surface-500 dark:text-surface-400">设置 U2 追魔的认证和过滤条件</p>
          </div>
        </div>
      </template>

      <div class="p-6">
        <form @submit.prevent="saveConfig" class="space-y-6">
          <!-- 认证配置 -->
          <div>
            <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
              <KeyIcon class="w-4 h-4 mr-2 text-purple-500" />
              认证配置
            </h4>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div class="lg:col-span-2 form-group">
                <label class="form-label">Cookie</label>
                <textarea
                  v-model="config.cookie"
                  rows="2"
                  class="form-input font-mono text-xs"
                  placeholder="从浏览器复制U2的Cookie..."
                ></textarea>
              </div>
              <div class="form-group">
                <label class="form-label">API Token</label>
                <input v-model="config.api_token" type="password" class="form-input" placeholder="可选，用于API方式获取" />
              </div>
              <div class="form-group">
                <label class="form-label">用户 UID</label>
                <input v-model.number="config.uid" type="number" min="0" class="form-input" placeholder="U2用户ID" />
              </div>
            </div>
          </div>

          <!-- 目录配置 -->
          <div>
            <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
              <FolderIcon class="w-4 h-4 mr-2 text-blue-500" />
              目录配置
            </h4>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div class="form-group">
                <label class="form-label">种子备份目录</label>
                <input v-model="config.backup_dir" type="text" class="form-input" placeholder="/path/to/backup" />
              </div>
              <div class="form-group">
                <label class="form-label">监控目录</label>
                <input v-model="config.watch_dir" type="text" class="form-input" placeholder="/path/to/watch" />
              </div>
              <div class="lg:col-span-2 form-group">
                <label class="form-label">下载器（多选，按空间智能分配）</label>
                <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  <label
                    v-for="dl in downloaders"
                    :key="dl.id"
                    class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer border transition-all"
                    :class="selectedDownloaderIds.includes(dl.id)
                      ? 'bg-purple-50 dark:bg-purple-900/30 border-purple-400 dark:border-purple-500'
                      : 'bg-surface-50 dark:bg-surface-700 border-surface-200 dark:border-surface-600 hover:border-purple-300'"
                  >
                    <input
                      type="checkbox"
                      :value="dl.id"
                      v-model="selectedDownloaderIds"
                      class="rounded text-purple-600 focus:ring-purple-500"
                    />
                    <span class="text-sm truncate" :class="selectedDownloaderIds.includes(dl.id) ? 'text-purple-700 dark:text-purple-300 font-medium' : 'text-surface-700 dark:text-surface-300'">{{ dl.name }}</span>
                  </label>
                </div>
                <p v-if="downloaders.length === 0" class="text-sm text-surface-400 mt-2">暂无下载器，请先添加</p>
                <p class="text-xs text-surface-500 mt-1">点击选择，自动根据种子大小和可用空间智能分配</p>
              </div>
              <div class="form-group">
                <label class="form-label">检测间隔 (秒)</label>
                <input v-model.number="config.fetch_interval" type="number" min="30" class="form-input" />
              </div>
            </div>
          </div>

          <!-- 过滤条件 -->
          <div>
            <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
              <FunnelIcon class="w-4 h-4 mr-2 text-amber-500" />
              过滤条件
            </h4>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div class="form-group">
                <label class="form-label">最大做种人数</label>
                <input v-model.number="config.max_seeders" type="number" min="0" class="form-input" />
                <p class="text-xs text-surface-500 mt-1">0 = 不限制</p>
              </div>
              <div class="form-group">
                <label class="form-label">最小体积 (GB)</label>
                <input v-model.number="config.min_size" type="number" step="0.1" min="0" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">最大体积 (GB)</label>
                <input v-model.number="config.max_size" type="number" step="0.1" min="0" class="form-input" />
                <p class="text-xs text-surface-500 mt-1">0 = 不限制</p>
              </div>
              <div class="form-group">
                <label class="form-label">新旧种判断天数</label>
                <input v-model.number="config.min_day" type="number" min="1" class="form-input" />
                <p class="text-xs text-surface-500 mt-1">发布超过此天数为旧种</p>
              </div>
              <div class="form-group">
                <label class="form-label">魔法生效延迟 (秒)</label>
                <input v-model.number="config.effective_delay" type="number" min="0" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">重复添加间隔 (秒)</label>
                <input v-model.number="config.min_add_interval" type="number" min="0" class="form-input" />
                <p class="text-xs text-surface-500 mt-1">0 = 不重复添加</p>
              </div>
              <div class="lg:col-span-2 form-group">
                <label class="form-label">分类过滤</label>
                <input v-model="config.categories" type="text" class="form-input" placeholder="逗号分隔，如: Movie,TV" />
              </div>
              <div class="form-group">
                <label class="form-label">名称过滤关键词</label>
                <input v-model="config.name_filter" type="text" class="form-input" placeholder="逗号分隔" />
              </div>
            </div>
          </div>

          <!-- 高级选项 -->
          <div>
            <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
              <AdjustmentsHorizontalIcon class="w-4 h-4 mr-2 text-surface-500" />
              高级选项
            </h4>
            <div class="grid grid-cols-2 lg:grid-cols-3 gap-4">
              <label class="flex items-center space-x-3 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
                <input v-model="config.download_new" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
                <div>
                  <span class="text-sm font-medium text-surface-900 dark:text-white">下载新种</span>
                  <p class="text-xs text-surface-500">新发布的种子</p>
                </div>
              </label>
              <label class="flex items-center space-x-3 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
                <input v-model="config.download_old" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
                <div>
                  <span class="text-sm font-medium text-surface-900 dark:text-white">下载旧种</span>
                  <p class="text-xs text-surface-500">老种子有魔法</p>
                </div>
              </label>
              <label class="flex items-center space-x-3 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
                <input v-model="config.download_non_free" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
                <div>
                  <span class="text-sm font-medium text-surface-900 dark:text-white">下载非Free</span>
                  <p class="text-xs text-surface-500">2x/2xfree等</p>
                </div>
              </label>
              <label class="flex items-center space-x-3 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
                <input v-model="config.magic_self" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
                <div>
                  <span class="text-sm font-medium text-surface-900 dark:text-white">自己的魔法</span>
                  <p class="text-xs text-surface-500">下载给自己的</p>
                </div>
              </label>
              <label class="flex items-center space-x-3 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
                <input v-model="config.download_dead" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
                <div>
                  <span class="text-sm font-medium text-surface-900 dark:text-white">无人做种</span>
                  <p class="text-xs text-surface-500">旧种无做种者</p>
                </div>
              </label>
              <label class="flex items-center space-x-3 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
                <input v-model="config.da_qiao" type="checkbox" class="rounded text-purple-600 focus:ring-purple-500" />
                <div>
                  <span class="text-sm font-medium text-surface-900 dark:text-white">搭桥模式</span>
                  <p class="text-xs text-surface-500">帮助下载传输</p>
                </div>
              </label>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex justify-end space-x-3 pt-4 border-t border-surface-200 dark:border-surface-700">
            <Button variant="secondary" type="button" @click="fetchMagic" :loading="fetching">
              <MagnifyingGlassIcon class="w-4 h-4" />
              立即检测
            </Button>
            <Button variant="primary" type="submit" :loading="saving">
              <CheckIcon class="w-4 h-4" />
              保存配置
            </Button>
          </div>
        </form>
      </div>
    </Card>

    <!-- 魔法记录 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
              <ClockIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">魔法记录</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">共 {{ pagination.total }} 条记录，第 {{ pagination.page }}/{{ pagination.pages }} 页</p>
            </div>
          </div>
          <div class="flex items-center space-x-3">
            <select v-model="filter.downloaded" class="form-select text-sm py-1.5">
              <option :value="null">全部状态</option>
              <option :value="true">已下载</option>
              <option :value="false">已跳过</option>
            </select>
            <Button variant="secondary" size="sm" @click="loadRecords">
              <ArrowPathIcon class="w-4 h-4" />
            </Button>
          </div>
        </div>
      </template>

      <div v-if="loading" class="flex flex-col items-center justify-center py-16">
        <div class="w-12 h-12 rounded-full border-4 border-purple-200 border-t-purple-600 animate-spin"></div>
        <p class="mt-4 text-surface-500 dark:text-surface-400">加载魔法记录...</p>
      </div>

      <div v-else-if="records.length === 0" class="empty-state py-12">
        <div class="empty-state-icon">
          <SparklesIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title">暂无魔法记录</p>
        <p class="empty-state-description">启用追魔后将自动记录发现的魔法</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>种子名称</th>
              <th class="w-32">魔法类型</th>
              <th class="w-24">体积</th>
              <th class="w-20">做种</th>
              <th class="w-28">状态</th>
              <th class="w-32">时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in records" :key="record.id" class="hover:bg-surface-50 dark:hover:bg-surface-800/50">
              <td>
                <div class="max-w-xs">
                  <p class="truncate font-medium text-surface-900 dark:text-white" :title="record.torrent_name">
                    {{ record.torrent_name }}
                  </p>
                  <p v-if="record.torrent_id" class="text-xs text-surface-400 mt-0.5">ID: {{ record.torrent_id }}</p>
                </div>
              </td>
              <td>
                <span :class="getMagicTypeClass(record.magic_type)">
                  {{ record.magic_type }}
                </span>
                <span v-if="record.magic_duration" class="text-xs text-surface-500 ml-1.5">
                  {{ record.magic_duration }}h
                </span>
              </td>
              <td class="text-surface-600 dark:text-surface-400">{{ formatSize(record.size) }}</td>
              <td>
                <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-surface-100 dark:bg-surface-700 text-surface-700 dark:text-surface-300">
                  <UsersIcon class="w-3 h-3 mr-1" />
                  {{ record.seeders }}
                </span>
              </td>
              <td>
                <span
                  v-if="record.downloaded"
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
                >
                  <CheckCircleIcon class="w-3.5 h-3.5 mr-1" />
                  已下载
                </span>
                <span
                  v-else
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-400"
                  :title="record.skip_reason"
                >
                  <XCircleIcon class="w-3.5 h-3.5 mr-1" />
                  {{ record.skip_reason ? record.skip_reason.slice(0, 8) : '跳过' }}
                </span>
              </td>
              <td class="text-xs text-surface-500 dark:text-surface-400">
                <div class="flex items-center">
                  <ClockIcon class="w-3.5 h-3.5 mr-1" />
                  {{ formatTime(record.created_at) }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 分页控件 -->
        <div v-if="pagination.pages > 1" class="flex items-center justify-between px-4 py-3 border-t border-surface-200 dark:border-surface-700">
          <div class="text-sm text-surface-500 dark:text-surface-400">
            显示 {{ (pagination.page - 1) * pagination.pageSize + 1 }} - {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} 条，共 {{ pagination.total }} 条
          </div>
          <div class="flex items-center space-x-2">
            <button
              @click="changePage(1)"
              :disabled="pagination.page === 1"
              class="px-3 py-1.5 text-sm rounded-lg border border-surface-200 dark:border-surface-700 hover:bg-surface-100 dark:hover:bg-surface-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              首页
            </button>
            <button
              @click="changePage(pagination.page - 1)"
              :disabled="pagination.page === 1"
              class="px-3 py-1.5 text-sm rounded-lg border border-surface-200 dark:border-surface-700 hover:bg-surface-100 dark:hover:bg-surface-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span class="px-3 py-1.5 text-sm text-surface-700 dark:text-surface-300">
              {{ pagination.page }} / {{ pagination.pages }}
            </span>
            <button
              @click="changePage(pagination.page + 1)"
              :disabled="pagination.page === pagination.pages"
              class="px-3 py-1.5 text-sm rounded-lg border border-surface-200 dark:border-surface-700 hover:bg-surface-100 dark:hover:bg-surface-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
            <button
              @click="changePage(pagination.pages)"
              :disabled="pagination.page === pagination.pages"
              class="px-3 py-1.5 text-sm rounded-lg border border-surface-200 dark:border-surface-700 hover:bg-surface-100 dark:hover:bg-surface-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              末页
            </button>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { u2MagicApi, downloadersApi } from '@/api'
import { formatSize, formatTime } from '@/utils/format'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import {
  ArrowPathIcon,
  SparklesIcon,
  ArrowDownTrayIcon,
  ForwardIcon,
  CircleStackIcon,
  KeyIcon,
  FolderIcon,
  FunnelIcon,
  Cog6ToothIcon,
  MagnifyingGlassIcon,
  CheckIcon,
  ClockIcon,
  UsersIcon,
  CheckCircleIcon,
  XCircleIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/vue/24/outline'

dayjs.locale('zh-cn')

const loading = ref(false)
const config = reactive({
  enabled: false,
  cookie: '',
  api_token: '',
  uid: 0,
  backup_dir: '',
  watch_dir: '',
  fetch_interval: 60,
  max_seeders: 20,
  download_new: true,
  download_old: true,
  download_non_free: false,
  magic_self: false,
  download_dead: false,
  da_qiao: true,
  min_size: 0,
  max_size: 0,
  min_day: 7,
  effective_delay: 60,
  min_add_interval: 0,
  categories: '',
  name_filter: '',
  downloader_id: null,
  downloader_ids: '',  // JSON数组格式
})

const records = ref([])
const downloaders = ref([])
const selectedDownloaderIds = ref([])  // 多选下载器ID列表

const saving = ref(false)
const fetching = ref(false)

// 分页状态
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
  pages: 1
})

const filter = reactive({
  downloaded: null,
})

// 统计数据单独从API获取
const stats = ref({
  total: 0,
  downloaded: 0,
  skipped: 0,
  totalSize: 0
})

function getMagicTypeClass(type) {
  const typeMap = {
    'free': 'px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    '2xfree': 'px-2 py-1 rounded-full text-xs font-semibold bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    '2x': 'px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    '50%': 'px-2 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  }
  const lowerType = (type || '').toLowerCase()
  for (const [key, value] of Object.entries(typeMap)) {
    if (lowerType.includes(key)) return value
  }
  return 'px-2 py-1 rounded-full text-xs font-semibold bg-surface-100 text-surface-700 dark:bg-surface-700 dark:text-surface-300'
}

async function loadConfig() {
  try {
    const response = await u2MagicApi.getConfig()
    Object.assign(config, response.data)
    // 解析多选下载器ID
    if (response.data.downloader_ids) {
      try {
        const ids = JSON.parse(response.data.downloader_ids)
        if (Array.isArray(ids)) {
          selectedDownloaderIds.value = ids
        }
      } catch {
        // 尝试按逗号分隔解析
        selectedDownloaderIds.value = response.data.downloader_ids
          .split(',')
          .map(s => parseInt(s.trim()))
          .filter(n => !isNaN(n))
      }
    } else if (response.data.downloader_id) {
      // 兼容旧的单选
      selectedDownloaderIds.value = [response.data.downloader_id]
    }
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

async function saveConfig() {
  saving.value = true
  try {
    // 将多选下载器ID转为JSON字符串
    const configToSave = {
      ...config,
      downloader_ids: JSON.stringify(selectedDownloaderIds.value),
      // 保持 downloader_id 为第一个选中的（向后兼容）
      downloader_id: selectedDownloaderIds.value.length > 0 ? selectedDownloaderIds.value[0] : null
    }
    await u2MagicApi.updateConfig(configToSave)
    alert('配置保存成功')
  } catch (error) {
    console.error('Failed to save config:', error)
    alert(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggleEnabled() {
  config.enabled = !config.enabled
  await saveConfig()
}

async function fetchMagic() {
  fetching.value = true
  try {
    const response = await u2MagicApi.fetch()
    alert(`检测完成：发现 ${response.data.total} 个魔法，下载 ${response.data.downloaded} 个`)
    await loadRecords()
  } catch (error) {
    console.error('Failed to fetch magic:', error)
    alert('检测失败：' + (error.response?.data?.detail || error.message))
  } finally {
    fetching.value = false
  }
}

async function loadRecords() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...(filter.downloaded !== null && { downloaded: filter.downloaded }),
    }
    const response = await u2MagicApi.getRecords(params)
    records.value = response.data.items
    pagination.total = response.data.total
    pagination.pages = response.data.pages
  } catch (error) {
    console.error('Failed to load records:', error)
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    // 获取全部记录的统计（不带过滤）
    const allResponse = await u2MagicApi.getRecords({ page: 1, page_size: 1 })
    const downloadedResponse = await u2MagicApi.getRecords({ page: 1, page_size: 1, downloaded: true })
    stats.value.total = allResponse.data.total
    stats.value.downloaded = downloadedResponse.data.total
    stats.value.skipped = stats.value.total - stats.value.downloaded
    // totalSize 需要单独计算，暂时保持为0或从后端获取
  } catch (error) {
    console.error('Failed to load stats:', error)
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

function changePage(newPage) {
  if (newPage >= 1 && newPage <= pagination.pages) {
    pagination.page = newPage
    loadRecords()
  }
}

watch(filter, () => {
  pagination.page = 1  // 重置到第一页
  loadRecords()
})

onMounted(() => {
  loadConfig()
  loadRecords()
  loadStats()
  loadDownloaders()
})
</script>
