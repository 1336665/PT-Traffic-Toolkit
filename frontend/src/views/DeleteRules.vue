<template>
  <div class="space-y-6 ">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl bg-gradient-to-br from-red-500 to-red-600 shadow-lg shadow-red-500/30">
          <TrashIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">删种规则</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">智能管理种子，自动清理释放空间</p>
        </div>
      </div>
      <Button variant="primary" @click="openRuleModal()">
        <PlusIcon class="w-4 h-4" />
        添加规则
      </Button>
    </div>

    <!-- Stats Row -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="stats-card stats-card-blue">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">规则总数</p>
            <p class="stats-value">{{ rules.length }}</p>
          </div>
          <div class="stats-icon">
            <AdjustmentsHorizontalIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-green">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">已启用</p>
            <p class="stats-value">{{ rules.filter(r => r.enabled).length }}</p>
          </div>
          <div class="stats-icon">
            <CheckCircleIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-red">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">今日删除</p>
            <p class="stats-value">{{ todayDeleteCount }}</p>
          </div>
          <div class="stats-icon">
            <TrashIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
      <div class="stats-card stats-card-purple">
        <div class="flex items-center justify-between">
          <div>
            <p class="stats-label">释放空间</p>
            <p class="stats-value">{{ formatSize(totalFreedSpace) }}</p>
          </div>
          <div class="stats-icon">
            <CircleStackIcon class="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>

    <!-- Rules List - Modern Vertex Style Cards -->
    <div v-if="rules.length > 0" class="grid gap-4 lg:grid-cols-2">
      <div
        v-for="rule in rules"
        :key="rule.id"
        class="card card-hover overflow-hidden"
      >
        <!-- Card Header -->
        <div class="px-5 py-4 border-b border-gray-100 dark:border-gray-700/50 flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <div
              class="w-12 h-12 rounded-xl flex items-center justify-center transition-colors"
              :class="rule.enabled
                ? 'bg-gradient-to-br from-red-500 to-red-600 text-white shadow-lg shadow-red-500/30'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-400'"
            >
              <TrashIcon class="w-6 h-6" />
            </div>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">{{ rule.name }}</h3>
              <div class="flex items-center space-x-2 mt-1">
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  优先级: {{ rule.priority }}
                </span>
                <span class="text-gray-300 dark:text-gray-600">|</span>
                <span :class="rule.enabled ? 'text-green-500' : 'text-gray-400'" class="text-xs flex items-center">
                  <span class="w-1.5 h-1.5 rounded-full mr-1" :class="rule.enabled ? 'bg-green-500' : 'bg-gray-400'"></span>
                  {{ rule.enabled ? '已启用' : '已禁用' }}
                </span>
              </div>
            </div>
          </div>
          <!-- Toggle Switch -->
          <button
            @click="toggleRuleEnabled(rule)"
            :class="[
              'switch',
              rule.enabled ? 'switch-on' : 'switch-off'
            ]"
          >
            <span :class="['switch-dot', rule.enabled ? 'switch-dot-on' : 'switch-dot-off']" />
          </button>
        </div>

        <!-- Conditions Display - Vertex Style -->
        <div class="px-5 py-4 bg-gray-50/50 dark:bg-gray-800/30">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">触发条件</span>
            <span class="px-2 py-0.5 text-xs font-bold rounded-full" :class="rule.condition_logic === 'AND' ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'">
              {{ rule.condition_logic }}
            </span>
          </div>
          <div class="space-y-2">
            <div
              v-for="(cond, idx) in rule.conditions"
              :key="idx"
              class="flex items-center p-3 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm"
            >
              <span class="flex items-center justify-center w-7 h-7 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 text-xs font-bold mr-3">
                {{ idx + 1 }}
              </span>
              <div class="flex-1 flex items-center flex-wrap gap-2">
                <span class="badge badge-info">{{ getFieldLabel(cond.field) }}</span>
                <span class="text-lg font-bold text-gray-400">{{ getOperatorSymbol(cond.operator) }}</span>
                <span class="badge bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
                  {{ cond.value }}{{ cond.unit ? ' ' + cond.unit : '' }}
                </span>
              </div>
            </div>
            <div v-if="rule.conditions.length === 0" class="text-center py-4 text-gray-400 text-sm">
              暂无条件
            </div>
          </div>
        </div>

        <!-- Options Row -->
        <div class="px-5 py-3 border-t border-gray-100 dark:border-gray-700/50">
          <div class="flex flex-wrap gap-2">
            <span v-if="rule.duration_seconds" class="badge badge-info">
              <ClockIcon class="w-3 h-3 mr-1" />
              持续 {{ formatDuration(rule.duration_seconds) }}
            </span>
            <span :class="rule.delete_files ? 'badge badge-danger' : 'badge badge-success'">
              {{ rule.delete_files ? '删除文件' : '仅移除' }}
            </span>
            <span v-if="rule.force_report" class="badge badge-purple">
              删前汇报
            </span>
            <span v-if="rule.max_delete_count" class="badge badge-warning">
              最多 {{ rule.max_delete_count }} 个
            </span>
            <span v-if="rule.tracker_filter" class="badge badge-gray">
              Tracker: {{ rule.tracker_filter }}
            </span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="px-5 py-4 border-t border-gray-100 dark:border-gray-700/50 flex justify-between">
          <div class="flex space-x-2">
            <Button variant="secondary" size="sm" @click="previewRule(rule)" :loading="previewingRule === rule.id">
              <EyeIcon class="w-4 h-4" />
              预览
            </Button>
            <Button variant="danger" size="sm" @click="runRule(rule)" :loading="runningRule === rule.id">
              <PlayIcon class="w-4 h-4" />
              执行
            </Button>
          </div>
          <div class="flex space-x-1">
            <button @click="duplicateRule(rule)" class="btn-icon text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20" title="复制规则">
              <DocumentDuplicateIcon class="w-5 h-5" />
            </button>
            <button @click="openRuleModal(rule)" class="btn-icon text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700" title="编辑">
              <PencilIcon class="w-5 h-5" />
            </button>
            <button @click="deleteRule(rule)" class="btn-icon text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20" title="删除">
              <TrashIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <div class="w-20 h-20 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
        <TrashIcon class="w-10 h-10 text-gray-300 dark:text-gray-600" />
      </div>
      <h3 class="empty-state-title">暂无删种规则</h3>
      <p class="empty-state-description">创建规则自动清理不需要的种子，释放磁盘空间</p>
      <Button variant="primary" class="mt-4" @click="openRuleModal()">
        <PlusIcon class="w-4 h-4" />
        添加第一条规则
      </Button>
    </div>

    <!-- Delete Records -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
              <ClockIcon class="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">删除历史</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">最近的种子删除记录</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" @click="loadRecords">
            <ArrowPathIcon class="w-4 h-4" />
          </Button>
        </div>
      </template>

      <div v-if="records.length === 0" class="text-center py-8 text-gray-500">
        暂无删除记录
      </div>
      <div v-else class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>种子名称</th>
              <th>规则</th>
              <th>大小</th>
              <th>分享率</th>
              <th>删除时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in records" :key="record.id">
              <td>
                <div class="max-w-xs truncate font-medium" :title="record.torrent_name">{{ record.torrent_name }}</div>
              </td>
              <td>
                <span class="badge badge-gray">{{ record.rule_name }}</span>
              </td>
              <td class="speed-display">{{ formatSize(record.size) }}</td>
              <td class="speed-display">{{ record.ratio.toFixed(2) }}</td>
              <td class="text-gray-400 text-xs">{{ formatTime(record.deleted_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Rule Modal - Enhanced Vertex Style -->
    <Modal v-model="ruleModalOpen" :title="editingRule ? '编辑规则' : '添加规则'" size="2xl">
      <form @submit.prevent="saveRule" class="space-y-6">
        <!-- Basic Info -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="md:col-span-2 form-group">
            <label class="form-label">规则名称</label>
            <input v-model="ruleForm.name" type="text" required class="form-input" placeholder="例如：低分享率自动清理" />
          </div>
          <div class="form-group">
            <label class="form-label">优先级</label>
            <input v-model.number="ruleForm.priority" type="number" class="form-input" placeholder="数字越大优先级越高" />
          </div>
        </div>

        <!-- Conditions Builder - Enhanced Vertex Style -->
        <div class="card overflow-hidden">
          <div class="px-5 py-4 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
                  <FunnelIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <h4 class="font-semibold text-gray-900 dark:text-white">触发条件</h4>
                  <p class="text-xs text-gray-500 dark:text-gray-400">设置删种的触发条件</p>
                </div>
              </div>
              <div class="flex items-center space-x-3">
                <span class="text-sm text-gray-600 dark:text-gray-400">条件关系:</span>
                <div class="flex rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600">
                  <button
                    type="button"
                    @click="ruleForm.condition_logic = 'AND'"
                    :class="[
                      'px-4 py-1.5 text-sm font-medium transition-colors',
                      ruleForm.condition_logic === 'AND'
                        ? 'bg-blue-500 text-white'
                        : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                    ]"
                  >
                    AND
                  </button>
                  <button
                    type="button"
                    @click="ruleForm.condition_logic = 'OR'"
                    :class="[
                      'px-4 py-1.5 text-sm font-medium transition-colors',
                      ruleForm.condition_logic === 'OR'
                        ? 'bg-purple-500 text-white'
                        : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                    ]"
                  >
                    OR
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="p-5 space-y-3">
            <TransitionGroup name="list" tag="div" class="space-y-3">
              <div
                v-for="(cond, idx) in ruleForm.conditions"
                :key="idx"
                class="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700/30 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors"
              >
                <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500 text-white text-sm font-bold shadow">
                  {{ idx + 1 }}
                </span>

                <div class="flex-1 grid grid-cols-4 gap-3">
                  <!-- Field Select -->
                  <div>
                    <select v-model="cond.field" class="form-select text-sm">
                      <optgroup label="进度相关">
                        <option value="progress">种子进度</option>
                        <option value="ratio">分享率</option>
                      </optgroup>
                      <optgroup label="时间相关">
                        <option value="seeding_time">做种时间</option>
                        <option value="added_time">添加时间</option>
                      </optgroup>
                      <optgroup label="数据量">
                        <option value="uploaded">上传量</option>
                        <option value="downloaded">下载量</option>
                        <option value="size">种子大小</option>
                      </optgroup>
                      <optgroup label="速度">
                        <option value="upload_speed">上传速度</option>
                        <option value="download_speed">下载速度</option>
                      </optgroup>
                      <optgroup label="连接">
                        <option value="seeders">做种人数</option>
                        <option value="leechers">下载人数</option>
                      </optgroup>
                      <optgroup label="其他">
                        <option value="tracker">Tracker</option>
                        <option value="tags">标签</option>
                        <option value="status">状态</option>
                      </optgroup>
                    </select>
                  </div>

                  <!-- Operator Select -->
                  <div>
                    <select v-model="cond.operator" class="form-select text-sm">
                      <option value="gt">大于 (&gt;)</option>
                      <option value="gte">大于等于 (&ge;)</option>
                      <option value="lt">小于 (&lt;)</option>
                      <option value="lte">小于等于 (&le;)</option>
                      <option value="eq">等于 (=)</option>
                      <option value="contains">包含</option>
                      <option value="not_contains">不包含</option>
                    </select>
                  </div>

                  <!-- Value Input -->
                  <div>
                    <input
                      v-model="cond.value"
                      type="text"
                      class="form-input text-sm"
                      placeholder="输入值"
                    />
                  </div>

                  <!-- Unit Select -->
                  <div>
                    <select v-model="cond.unit" class="form-select text-sm">
                      <option value="">无单位</option>
                      <template v-if="isTimeField(cond.field)">
                        <option value="seconds">秒</option>
                        <option value="minutes">分钟</option>
                        <option value="hours">小时</option>
                        <option value="days">天</option>
                      </template>
                      <template v-else-if="isSizeField(cond.field)">
                        <option value="KB">KB</option>
                        <option value="MB">MB</option>
                        <option value="GB">GB</option>
                        <option value="TB">TB</option>
                      </template>
                      <template v-else-if="isSpeedField(cond.field)">
                        <option value="KB/s">KB/s</option>
                        <option value="MB/s">MB/s</option>
                      </template>
                      <template v-else-if="cond.field === 'progress'">
                        <option value="%">%</option>
                      </template>
                    </select>
                  </div>
                </div>

                <button
                  type="button"
                  @click="removeCondition(idx)"
                  class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  <XMarkIcon class="w-5 h-5" />
                </button>
              </div>
            </TransitionGroup>

            <button
              type="button"
              @click="addCondition"
              class="w-full p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl text-gray-500 dark:text-gray-400 hover:border-primary-400 hover:text-primary-600 dark:hover:border-primary-500 dark:hover:text-primary-400 transition-colors flex items-center justify-center space-x-2"
            >
              <PlusCircleIcon class="w-5 h-5" />
              <span>添加条件</span>
            </button>
          </div>
        </div>

        <!-- Advanced Options -->
        <div class="card">
          <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
            <h4 class="font-semibold text-gray-900 dark:text-white">高级设置</h4>
          </div>
          <div class="p-5 space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-group">
                <label class="form-label">持续时间（秒）</label>
                <input v-model.number="ruleForm.duration_seconds" type="number" min="0" class="form-input" />
                <p class="form-hint">条件必须持续满足指定秒数才执行删除</p>
              </div>

              <div class="form-group">
                <label class="form-label">单次最大删除数</label>
                <input v-model.number="ruleForm.max_delete_count" type="number" min="0" class="form-input" />
                <p class="form-hint">0 表示不限制</p>
              </div>

              <div class="form-group">
                <label class="form-label">Tracker过滤</label>
                <input v-model="ruleForm.tracker_filter" type="text" class="form-input" placeholder="例如: hdsky.me" />
                <p class="form-hint">只对包含此关键词的Tracker生效</p>
              </div>

              <div class="form-group">
                <label class="form-label">标签过滤</label>
                <input v-model="ruleForm.tag_filter" type="text" class="form-input" placeholder="例如: free" />
                <p class="form-hint">只对包含此标签的种子生效</p>
              </div>
            </div>

            <div class="flex flex-wrap gap-x-8 gap-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <label class="flex items-center space-x-3 cursor-pointer group">
                <div class="relative">
                  <input v-model="ruleForm.enabled" type="checkbox" class="sr-only peer" />
                  <div class="w-10 h-5 bg-gray-200 rounded-full peer dark:bg-gray-700 peer-checked:bg-green-500 peer-focus:ring-2 peer-focus:ring-green-300 transition-colors"></div>
                  <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                </div>
                <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">启用规则</span>
              </label>

              <label class="flex items-center space-x-3 cursor-pointer group">
                <div class="relative">
                  <input v-model="ruleForm.delete_files" type="checkbox" class="sr-only peer" />
                  <div class="w-10 h-5 bg-gray-200 rounded-full peer dark:bg-gray-700 peer-checked:bg-red-500 peer-focus:ring-2 peer-focus:ring-red-300 transition-colors"></div>
                  <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                </div>
                <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">删除本地文件</span>
              </label>

              <label class="flex items-center space-x-3 cursor-pointer group">
                <div class="relative">
                  <input v-model="ruleForm.force_report" type="checkbox" class="sr-only peer" />
                  <div class="w-10 h-5 bg-gray-200 rounded-full peer dark:bg-gray-700 peer-checked:bg-purple-500 peer-focus:ring-2 peer-focus:ring-purple-300 transition-colors"></div>
                  <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                </div>
                <span class="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">删除前强制汇报</span>
              </label>
            </div>
          </div>
        </div>
      </form>

      <template #footer>
        <Button variant="secondary" @click="ruleModalOpen = false">取消</Button>
        <Button variant="primary" :loading="savingRule" @click="saveRule">保存规则</Button>
      </template>
    </Modal>

    <!-- Preview Modal -->
    <Modal v-model="previewModalOpen" title="预览匹配结果" size="xl">
      <div v-if="previewResults.length === 0" class="empty-state py-8">
        <CheckCircleIcon class="w-16 h-16 text-green-400 mx-auto mb-4" />
        <p class="empty-state-title">没有匹配的种子</p>
        <p class="empty-state-description">当前条件下没有种子会被删除</p>
      </div>
      <div v-else class="space-y-3">
        <div class="flex items-center justify-between px-4 py-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
          <span class="text-yellow-700 dark:text-yellow-400 text-sm">
            <ExclamationTriangleIcon class="w-4 h-4 inline mr-1" />
            共 {{ previewResults.length }} 个种子符合删除条件
          </span>
        </div>
        <div
          v-for="item in previewResults"
          :key="item.hash"
          class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/30 rounded-xl"
        >
          <div class="flex-1 min-w-0 mr-4">
            <div class="truncate font-medium text-gray-900 dark:text-white">{{ item.name }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center space-x-3">
              <span>{{ item.downloader }}</span>
              <span>{{ formatSize(item.size) }}</span>
              <span>分享率: {{ item.ratio.toFixed(2) }}</span>
            </div>
          </div>
          <span :class="item.duration_met ? 'badge badge-danger' : 'badge badge-warning'">
            {{ item.duration_met ? '即将删除' : '等待中' }}
          </span>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { deleteRulesApi } from '@/api'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import {
  PlusIcon, TrashIcon, ArrowPathIcon, XMarkIcon,
  ClockIcon, EyeIcon, PlayIcon, PencilIcon,
  FunnelIcon, PlusCircleIcon, DocumentDuplicateIcon,
  AdjustmentsHorizontalIcon, CheckCircleIcon, CircleStackIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'

dayjs.locale('zh-cn')

const rules = ref([])
const records = ref([])

const ruleModalOpen = ref(false)
const editingRule = ref(null)
const savingRule = ref(false)
const runningRule = ref(null)
const previewingRule = ref(null)

const previewModalOpen = ref(false)
const previewResults = ref([])

// Computed stats
const todayDeleteCount = computed(() => {
  const today = dayjs().startOf('day')
  return records.value.filter(r => dayjs(r.deleted_at).isAfter(today)).length
})

const totalFreedSpace = computed(() => {
  return records.value.reduce((sum, r) => sum + (r.size || 0), 0)
})

const defaultRuleForm = {
  name: '',
  enabled: true,
  priority: 0,
  conditions: [],
  condition_logic: 'AND',
  duration_seconds: 0,
  delete_files: true,
  force_report: true,
  max_delete_count: 0,
  downloader_ids: [],
  tracker_filter: '',
  tag_filter: '',
}

const ruleForm = reactive({ ...defaultRuleForm })

// Helper functions
function isTimeField(field) {
  return ['seeding_time', 'added_time'].includes(field)
}

function isSizeField(field) {
  return ['uploaded', 'downloaded', 'size'].includes(field)
}

function isSpeedField(field) {
  return ['upload_speed', 'download_speed'].includes(field)
}

function getFieldLabel(field) {
  const labels = {
    progress: '进度',
    seeding_time: '做种时间',
    uploaded: '上传量',
    downloaded: '下载量',
    ratio: '分享率',
    upload_speed: '上传速度',
    download_speed: '下载速度',
    size: '大小',
    seeders: '做种数',
    leechers: '下载数',
    added_time: '添加时间',
    tracker: 'Tracker',
    tags: '标签',
    status: '状态',
  }
  return labels[field] || field
}

function getOperatorSymbol(op) {
  const symbols = { gt: '>', gte: '≥', lt: '<', lte: '≤', eq: '=', contains: '含', not_contains: '非' }
  return symbols[op] || op
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

function formatDuration(seconds) {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时`
  return `${Math.floor(seconds / 86400)}天`
}

async function loadRules() {
  try {
    const response = await deleteRulesApi.getAll()
    rules.value = response.data
  } catch (error) {
    console.error('Failed to load rules:', error)
  }
}

async function loadRecords() {
  try {
    const response = await deleteRulesApi.getRecords({ limit: 50 })
    records.value = response.data
  } catch (error) {
    console.error('Failed to load records:', error)
  }
}

function openRuleModal(rule = null) {
  editingRule.value = rule
  if (rule) {
    Object.assign(ruleForm, { ...rule, conditions: rule.conditions.map(c => ({ ...c })) })
  } else {
    Object.assign(ruleForm, { ...defaultRuleForm, conditions: [] })
  }
  ruleModalOpen.value = true
}

function addCondition() {
  ruleForm.conditions.push({ field: 'ratio', operator: 'gt', value: '', unit: '' })
}

function removeCondition(idx) {
  ruleForm.conditions.splice(idx, 1)
}

async function saveRule() {
  if (ruleForm.conditions.length === 0) {
    alert('请至少添加一个条件')
    return
  }

  if (!ruleForm.name.trim()) {
    alert('请输入规则名称')
    return
  }

  savingRule.value = true
  try {
    if (editingRule.value) {
      await deleteRulesApi.update(editingRule.value.id, ruleForm)
    } else {
      await deleteRulesApi.create(ruleForm)
    }
    ruleModalOpen.value = false
    await loadRules()
  } catch (error) {
    console.error('Failed to save rule:', error)
    alert(error.response?.data?.detail || '保存失败')
  } finally {
    savingRule.value = false
  }
}

async function toggleRuleEnabled(rule) {
  try {
    await deleteRulesApi.update(rule.id, { ...rule, enabled: !rule.enabled })
    await loadRules()
  } catch (error) {
    console.error('Failed to toggle rule:', error)
  }
}

async function deleteRule(rule) {
  if (!confirm(`确定要删除规则"${rule.name}"吗？`)) return

  try {
    await deleteRulesApi.delete(rule.id)
    await loadRules()
  } catch (error) {
    console.error('Failed to delete rule:', error)
  }
}

function duplicateRule(rule) {
  const newRule = { ...rule, name: rule.name + ' (副本)', conditions: rule.conditions.map(c => ({ ...c })) }
  delete newRule.id
  editingRule.value = null
  Object.assign(ruleForm, newRule)
  ruleModalOpen.value = true
}

async function previewRule(rule) {
  previewingRule.value = rule.id
  try {
    const response = await deleteRulesApi.preview(rule.id)
    previewResults.value = response.data.matches
    previewModalOpen.value = true
  } catch (error) {
    console.error('Failed to preview rule:', error)
  } finally {
    previewingRule.value = null
  }
}

async function runRule(rule) {
  if (!confirm(`确定要立即执行规则"${rule.name}"吗？符合条件的种子将被删除。`)) return

  runningRule.value = rule.id
  try {
    const response = await deleteRulesApi.run(rule.id)
    alert(`已删除 ${response.data.deleted_count} 个种子`)
    await loadRecords()
  } catch (error) {
    console.error('Failed to run rule:', error)
    alert('执行失败')
  } finally {
    runningRule.value = null
  }
}

onMounted(() => {
  loadRules()
  loadRecords()
})
</script>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.btn-icon {
  @apply p-2 rounded-lg transition-colors;
}
</style>
