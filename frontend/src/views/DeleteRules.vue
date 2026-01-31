<template>
  <div class="space-y-6 ">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl bg-gradient-to-br from-red-500 to-red-600 shadow-lg shadow-red-500/30">
          <TrashIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">删种规则</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">智能管理种子，自动清理释放空间</p>
        </div>
      </div>
      <Button variant="primary" @click="openRuleModal()">
        <PlusIcon class="w-4 h-4" />
        <span class="hidden sm:inline ml-1">添加规则</span>
      </Button>
    </div>

    <!-- Stats Row -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 规则总数 -->
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20 border border-blue-200/50 dark:border-blue-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-blue-500/10 dark:bg-blue-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-blue-600/70 dark:text-blue-400/70 uppercase tracking-wide">规则总数</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ rules.length }}</p>
          </div>
          <div class="p-3 rounded-xl bg-blue-500/20 dark:bg-blue-500/30">
            <AdjustmentsHorizontalIcon class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </div>

      <!-- 已启用 -->
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-green-500/10 to-emerald-500/10 dark:from-green-500/20 dark:to-emerald-500/20 border border-green-200/50 dark:border-green-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-green-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-green-500/10 dark:bg-green-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-green-600/70 dark:text-green-400/70 uppercase tracking-wide">已启用</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ rules.filter(r => r.enabled).length }}</p>
          </div>
          <div class="p-3 rounded-xl bg-green-500/20 dark:bg-green-500/30">
            <CheckCircleIcon class="w-6 h-6 text-green-600 dark:text-green-400" />
          </div>
        </div>
      </div>

      <!-- 今日删除 -->
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-red-500/10 to-rose-500/10 dark:from-red-500/20 dark:to-rose-500/20 border border-red-200/50 dark:border-red-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-red-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-red-500/10 dark:bg-red-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-red-600/70 dark:text-red-400/70 uppercase tracking-wide">今日删除</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ todayDeleteCount }}</p>
          </div>
          <div class="p-3 rounded-xl bg-red-500/20 dark:bg-red-500/30">
            <TrashIcon class="w-6 h-6 text-red-600 dark:text-red-400" />
          </div>
        </div>
      </div>

      <!-- 释放空间 -->
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-500/20 dark:to-pink-500/20 border border-purple-200/50 dark:border-purple-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-purple-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-purple-500/10 dark:bg-purple-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-purple-600/70 dark:text-purple-400/70 uppercase tracking-wide">释放空间</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">{{ formatSize(totalFreedSpace) }}</p>
          </div>
          <div class="p-3 rounded-xl bg-purple-500/20 dark:bg-purple-500/30">
            <CircleStackIcon class="w-6 h-6 text-purple-600 dark:text-purple-400" />
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
        <div class="px-5 py-4 border-b border-surface-100 dark:border-surface-700/50 flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <div
              class="w-12 h-12 rounded-xl flex items-center justify-center transition-colors"
              :class="rule.enabled
                ? 'bg-gradient-to-br from-red-500 to-red-600 text-white shadow-lg shadow-red-500/30'
                : 'bg-surface-100 dark:bg-surface-700 text-surface-400'"
            >
              <TrashIcon class="w-6 h-6" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">{{ rule.name }}</h3>
              <div class="flex items-center space-x-2 mt-1">
                <span class="text-xs text-surface-500 dark:text-surface-400">
                  优先级: {{ rule.priority }}
                </span>
                <span class="text-surface-300 dark:text-surface-600">|</span>
                <span :class="rule.enabled ? 'text-green-500' : 'text-surface-400'" class="text-xs flex items-center">
                  <span class="w-1.5 h-1.5 rounded-full mr-1" :class="rule.enabled ? 'bg-green-500' : 'bg-surface-400'"></span>
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
        <div class="px-5 py-4 bg-surface-50/50 dark:bg-surface-800/30">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs font-semibold text-surface-500 dark:text-surface-400 uppercase tracking-wider">触发条件</span>
            <span class="px-2 py-0.5 text-xs font-bold rounded-full" :class="rule.condition_logic === 'AND' ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' : 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'">
              {{ rule.condition_logic }}
            </span>
          </div>
          <div class="space-y-2">
            <div
              v-if="rule.rule_type === 'javascript'"
              class="p-4 bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 shadow-sm text-sm text-surface-600 dark:text-surface-300"
            >
              JavaScript 规则
              <pre class="mt-2 text-xs text-surface-500 dark:text-surface-400 whitespace-pre-wrap">{{ rule.code || '未填写代码' }}</pre>
            </div>
            <template v-else>
              <div
                v-for="(cond, idx) in rule.conditions"
                :key="idx"
                class="flex items-center p-3 bg-white dark:bg-surface-800 rounded-xl border border-surface-200 dark:border-surface-700 shadow-sm"
              >
                <span class="flex items-center justify-center w-7 h-7 rounded-lg bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 text-xs font-bold mr-3">
                  {{ idx + 1 }}
                </span>
                <div class="flex-1 flex items-center flex-wrap gap-2">
                  <span class="badge badge-info">{{ getFieldLabel(cond.field) }}</span>
                  <span class="text-lg font-bold text-surface-400">{{ getOperatorSymbol(cond.operator) }}</span>
                  <span class="badge bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
                    {{ cond.value }}{{ getFieldUnit(cond.field) ? ' ' + getFieldUnit(cond.field) : '' }}
                  </span>
                  <span v-if="cond.duration && cond.duration > 0" class="badge badge-warning">
                    <ClockIcon class="w-3 h-3 mr-1" />
                    {{ formatConditionDuration(cond.duration, cond.duration_unit) }}
                  </span>
                </div>
              </div>
              <div v-if="rule.conditions.length === 0" class="text-center py-4 text-surface-400 text-sm">
                暂无条件
              </div>
            </template>
          </div>
        </div>

        <!-- Options Row -->
        <div class="px-5 py-3 border-t border-surface-100 dark:border-surface-700/50">
          <div class="flex flex-wrap gap-2">
            <span class="badge badge-gray">
              {{ rule.rule_type === 'javascript' ? 'JavaScript' : '普通' }}
            </span>
            <span v-if="rule.duration_seconds" class="badge badge-info">
              <ClockIcon class="w-3 h-3 mr-1" />
              持续 {{ formatDuration(rule.duration_seconds) }}
            </span>
            <span :class="rule.delete_files ? 'badge badge-danger' : 'badge badge-success'">
              {{ rule.delete_files ? '删除文件' : '仅移除' }}
            </span>
            <span v-if="rule.only_delete_torrent" class="badge badge-gray">
              仅删除种子
            </span>
            <span v-if="rule.pause" class="badge badge-warning">
              暂停种子
            </span>
            <span v-if="rule.limit_speed" class="badge badge-purple">
              限速 {{ formatSpeed(rule.limit_speed) }}
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
            <span v-if="rule.downloader_ids && rule.downloader_ids.length > 0" class="badge badge-info">
              <ServerStackIcon class="w-3 h-3 mr-1" />
              {{ rule.downloader_ids.length }} 个下载器
            </span>
            <span v-else class="badge badge-gray">
              全部下载器
            </span>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="px-5 py-4 border-t border-surface-100 dark:border-surface-700/50 flex justify-between">
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
            <button @click="duplicateRule(rule)" class="btn-icon text-surface-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20" title="复制规则">
              <DocumentDuplicateIcon class="w-5 h-5" />
            </button>
            <button @click="openRuleModal(rule)" class="btn-icon text-surface-400 hover:text-surface-600 hover:bg-surface-100 dark:hover:bg-surface-700" title="编辑">
              <PencilIcon class="w-5 h-5" />
            </button>
            <button @click="deleteRule(rule)" class="btn-icon text-surface-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20" title="删除">
              <TrashIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <Card v-else>
      <div class="empty-state py-12">
        <div class="empty-state-icon">
          <TrashIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title">暂无删种规则</p>
        <p class="empty-state-description">创建规则自动清理不需要的种子，释放磁盘空间</p>
        <Button variant="primary" class="mt-4" @click="openRuleModal()">
          <PlusIcon class="w-4 h-4" />
          添加第一条规则
        </Button>
      </div>
    </Card>

    <!-- Delete Records -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
              <ClockIcon class="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">删除历史</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">最近的种子删除记录</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" @click="loadRecords">
            <ArrowPathIcon class="w-4 h-4" />
          </Button>
        </div>
      </template>

      <div v-if="records.length === 0" class="empty-state py-8">
        <div class="empty-state-icon !w-12 !h-12">
          <ClockIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title text-base">暂无删除记录</p>
        <p class="empty-state-description">种子删除记录将显示在这里</p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>种子名称</th>
              <th>下载器</th>
              <th>规则</th>
              <th>大小</th>
              <th>分享率</th>
              <th>删除时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in records" :key="record.id" class="hover:bg-surface-50 dark:hover:bg-surface-800/50">
              <td>
                <div class="max-w-xs truncate font-medium" :title="record.torrent_name">{{ record.torrent_name }}</div>
              </td>
              <td>
                <span class="badge badge-info">{{ record.downloader_name || '未知' }}</span>
              </td>
              <td>
                <span class="badge badge-gray">{{ record.rule_name }}</span>
              </td>
              <td class="speed-display">{{ formatSize(record.size) }}</td>
              <td class="speed-display">{{ record.ratio.toFixed(2) }}</td>
              <td class="text-surface-400 text-xs">{{ formatTime(record.deleted_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Rule Modal - Enhanced Vertex Style -->
    <Modal v-model="ruleModalOpen" :title="editingRule ? '编辑规则' : '添加规则'" size="2xl">
      <form @submit.prevent="saveRule" class="space-y-6">
        <!-- Basic Info -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="md:col-span-2 form-group">
            <label class="form-label">规则名称</label>
            <input v-model="ruleForm.name" type="text" required class="form-input" placeholder="例如：低分享率自动清理" />
          </div>
          <div class="form-group">
            <label class="form-label">优先级</label>
            <input v-model.number="ruleForm.priority" type="number" class="form-input" placeholder="数字越大优先级越高" />
          </div>
          <div class="form-group">
            <label class="form-label">类型</label>
            <select v-model="ruleForm.rule_type" class="form-select">
              <option value="normal">普通</option>
              <option value="javascript">JavaScript</option>
            </select>
          </div>
        </div>

        <!-- Conditions Builder - Enhanced Vertex Style -->
        <div v-if="ruleForm.rule_type === 'normal'" class="card overflow-hidden">
          <div class="px-5 py-4 bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-b border-surface-200 dark:border-surface-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <div class="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
                  <FunnelIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <h4 class="font-semibold text-surface-900 dark:text-white">触发条件</h4>
                  <p class="text-xs text-surface-500 dark:text-surface-400">设置删种的触发条件</p>
                </div>
              </div>
              <div class="flex items-center space-x-3">
                <span class="text-sm text-surface-600 dark:text-surface-400">条件关系:</span>
                <div class="flex rounded-lg overflow-hidden border border-surface-300 dark:border-surface-600">
                  <button
                    type="button"
                    @click="ruleForm.condition_logic = 'AND'"
                    :class="[
                      'px-4 py-1.5 text-sm font-medium transition-colors',
                      ruleForm.condition_logic === 'AND'
                        ? 'bg-blue-500 text-white'
                        : 'bg-white dark:bg-surface-800 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-700'
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
                        : 'bg-white dark:bg-surface-800 text-surface-600 dark:text-surface-400 hover:bg-surface-50 dark:hover:bg-surface-700'
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
                class="p-4 bg-surface-50 dark:bg-surface-700/30 rounded-xl border border-surface-200 dark:border-surface-700 hover:border-primary-300 dark:hover:border-primary-700 transition-colors"
              >
                <!-- Condition Header -->
                <div class="flex items-center justify-between mb-4">
                  <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500 text-white text-sm font-bold shadow">
                    {{ idx + 1 }}
                  </span>
                  <button
                    type="button"
                    @click="removeCondition(idx)"
                    class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  >
                    <XMarkIcon class="w-5 h-5" />
                  </button>
                </div>

                <!-- Condition Fields - 主要条件行 -->
                <div class="grid grid-cols-12 gap-3 mb-4">
                  <!-- Field Select -->
                  <div class="col-span-12 sm:col-span-4">
                    <label class="condition-label">
                      <span class="flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-primary-500"></span>
                        字段
                      </span>
                    </label>
                    <select v-model="cond.field" class="form-select text-sm">
                      <optgroup label="基础信息">
                        <option value="name">种子名称</option>
                        <option value="progress">种子进度 (%)</option>
                        <option value="state">种子状态</option>
                        <option value="category">种子分类</option>
                        <option value="tags">种子标签</option>
                        <option value="tracker">站点域名</option>
                        <option value="trackerStatus">返回信息</option>
                        <option value="savePath">保存路径</option>
                      </optgroup>
                      <optgroup label="数据量 (GB)">
                        <option value="size">选择大小</option>
                        <option value="totalSize">种子大小</option>
                        <option value="completed">已完成量</option>
                        <option value="downloaded">已下载量</option>
                        <option value="uploaded">已上传量</option>
                        <option value="freeSpace">剩余空间</option>
                      </optgroup>
                      <optgroup label="分享率">
                        <option value="ratio">分享率一</option>
                        <option value="trueRatio">分享率二</option>
                        <option value="ratio3">分享率三</option>
                      </optgroup>
                      <optgroup label="时间 (秒)">
                        <option value="addedTime">添加时间</option>
                        <option value="completedTime">完成时间</option>
                        <option value="seeding_time">做种时间</option>
                        <option value="secondFromZero">当前时间</option>
                      </optgroup>
                      <optgroup label="速度 (KB/s)">
                        <option value="uploadSpeed">上传速度</option>
                        <option value="downloadSpeed">下载速度</option>
                        <option value="globalUploadSpeed">全局上传</option>
                        <option value="globalDownloadSpeed">全局下载</option>
                      </optgroup>
                      <optgroup label="连接/任务">
                        <option value="seeder">做种连接</option>
                        <option value="leecher">下载连接</option>
                        <option value="leechingCount">下载任务</option>
                        <option value="seedingCount">做种任务</option>
                      </optgroup>
                    </select>
                  </div>

                  <!-- Operator Select -->
                  <div class="col-span-6 sm:col-span-3">
                    <label class="condition-label">
                      <span class="flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                        运算符
                      </span>
                    </label>
                    <select v-model="cond.operator" class="form-select text-sm">
                      <option value="equals">等于 (=)</option>
                      <option value="bigger">大于 (>)</option>
                      <option value="smaller">小于 (<)</option>
                      <option value="contain">包含</option>
                      <option value="includeIn">包含于</option>
                      <option value="notContain">不包含</option>
                      <option value="notIncludeIn">不包含于</option>
                      <option value="regExp">正则匹配</option>
                      <option value="notRegExp">正则不匹配</option>
                    </select>
                  </div>

                  <!-- Value Input with Unit -->
                  <div class="col-span-6 sm:col-span-5">
                    <label class="condition-label">
                      <span class="flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                        值
                        <span class="text-[10px] px-1.5 py-0.5 rounded bg-surface-200 dark:bg-surface-600 text-surface-600 dark:text-surface-300 font-normal">
                          {{ getFieldUnit(cond.field) }}
                        </span>
                      </span>
                    </label>
                    <div class="relative">
                      <input
                        v-model="cond.value"
                        type="text"
                        class="form-input text-sm"
                        :class="{ 'pr-14': getFieldUnit(cond.field) }"
                        :placeholder="getFieldPlaceholder(cond.field)"
                      />
                      <span v-if="getFieldUnit(cond.field)" class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-surface-400 dark:text-surface-500 font-medium pointer-events-none">
                        {{ getFieldUnit(cond.field) }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Duration - 独立行显示 -->
                <div class="pt-3 border-t border-surface-200 dark:border-surface-600">
                  <div class="flex flex-wrap items-center gap-3">
                    <label class="condition-label !mb-0 flex items-center gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                      持续时间
                      <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 font-normal">
                        可选
                      </span>
                    </label>
                    <div class="flex items-center gap-2">
                      <input
                        v-model.number="cond.duration"
                        type="number"
                        min="0"
                        class="form-input text-sm w-20 text-center"
                        placeholder="0"
                      />
                      <select v-model="cond.duration_unit" class="form-select text-sm w-24">
                        <option value="seconds">秒</option>
                        <option value="minutes">分钟</option>
                        <option value="hours">小时</option>
                        <option value="days">天</option>
                      </select>
                    </div>
                    <p v-if="cond.duration > 0" class="text-xs text-amber-600 dark:text-amber-400">
                      条件需持续满足 {{ formatConditionDuration(cond.duration, cond.duration_unit) }} 后才触发
                    </p>
                  </div>
                </div>
              </div>
            </TransitionGroup>

            <button
              type="button"
              @click="addCondition"
              class="w-full p-4 border-2 border-dashed border-surface-300 dark:border-surface-600 rounded-xl text-surface-500 dark:text-surface-400 hover:border-primary-400 hover:text-primary-600 dark:hover:border-primary-500 dark:hover:text-primary-400 transition-colors flex items-center justify-center space-x-2"
            >
              <PlusCircleIcon class="w-5 h-5" />
              <span>添加条件</span>
            </button>
          </div>
        </div>

        <div v-else class="card overflow-hidden">
          <div class="px-5 py-4 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 border-b border-surface-200 dark:border-surface-700">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
                <DocumentDuplicateIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h4 class="font-semibold text-surface-900 dark:text-white">JavaScript 规则</h4>
                <p class="text-xs text-surface-500 dark:text-surface-400">返回 true 触发动作</p>
              </div>
            </div>
          </div>
          <div class="p-5">
            <textarea
              v-model="ruleForm.code"
              rows="8"
              class="form-input font-mono text-sm"
              placeholder="(maindata, torrent) => { return false; }"
            ></textarea>
          </div>
        </div>

        <!-- Advanced Options - Enhanced Style -->
        <div class="card overflow-hidden">
          <div class="px-5 py-4 bg-gradient-to-r from-surface-50 to-slate-50 dark:from-surface-800/50 dark:to-slate-800/50 border-b border-surface-200 dark:border-surface-700">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-lg bg-surface-100 dark:bg-surface-700">
                <AdjustmentsHorizontalIcon class="w-5 h-5 text-surface-600 dark:text-surface-400" />
              </div>
              <div>
                <h4 class="font-semibold text-surface-900 dark:text-white">高级设置</h4>
                <p class="text-xs text-surface-500 dark:text-surface-400">配置规则的执行参数</p>
              </div>
            </div>
          </div>
          <div class="p-5 space-y-5">
            <!-- 数值设置区 -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div class="form-group">
                <label class="form-label flex items-center gap-2">
                  <ClockIcon class="w-4 h-4 text-blue-500" />
                  检测间隔
                </label>
                <div class="relative">
                  <input v-model.number="deleteIntervalSeconds" type="number" min="5" class="form-input pr-10" />
                  <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-surface-400 font-medium">秒</span>
                </div>
                <p class="form-hint">规则检测的运行间隔时间</p>
              </div>

              <div class="form-group">
                <label class="form-label flex items-center gap-2">
                  <TrashIcon class="w-4 h-4 text-red-500" />
                  单次最大删除数
                </label>
                <div class="relative">
                  <input v-model.number="ruleForm.max_delete_count" type="number" min="0" class="form-input pr-10" />
                  <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-surface-400 font-medium">个</span>
                </div>
                <p class="form-hint">0 表示不限制</p>
              </div>

              <div class="form-group">
                <label class="form-label flex items-center gap-2">
                  <ArrowPathIcon class="w-4 h-4 text-amber-500" />
                  限速
                </label>
                <div class="relative">
                  <input v-model.number="ruleForm.limit_speed" type="number" min="0" class="form-input pr-14" />
                  <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-surface-400 font-medium">Byte/s</span>
                </div>
                <p class="form-hint">填写后将改为限制下载速度</p>
              </div>
            </div>

            <!-- 下载器选择区域 -->
            <div class="form-group">
              <label class="form-label flex items-center gap-2">
                <ServerStackIcon class="w-4 h-4 text-cyan-500" />
                应用到下载器
              </label>
              <div class="space-y-3">
                <!-- 全选按钮 -->
                <label
                  class="flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors"
                  :class="ruleForm.downloader_ids.length === 0
                    ? 'bg-cyan-50 dark:bg-cyan-900/20 border-2 border-cyan-500'
                    : 'bg-surface-50 dark:bg-surface-700/30 border border-surface-200 dark:border-surface-700 hover:bg-surface-100 dark:hover:bg-surface-700/50'"
                  @click="selectAllDownloaders"
                >
                  <div class="flex items-center space-x-3">
                    <div class="p-1.5 rounded-lg" :class="ruleForm.downloader_ids.length === 0 ? 'bg-cyan-100 dark:bg-cyan-900/30' : 'bg-surface-100 dark:bg-surface-600'">
                      <ServerStackIcon class="w-4 h-4" :class="ruleForm.downloader_ids.length === 0 ? 'text-cyan-600 dark:text-cyan-400' : 'text-surface-600 dark:text-surface-400'" />
                    </div>
                    <span class="text-sm font-medium" :class="ruleForm.downloader_ids.length === 0 ? 'text-cyan-700 dark:text-cyan-300' : 'text-surface-700 dark:text-surface-300'">
                      全部下载器
                    </span>
                  </div>
                  <span v-if="ruleForm.downloader_ids.length === 0" class="text-xs text-cyan-600 dark:text-cyan-400 font-medium">
                    已选择
                  </span>
                </label>
                <!-- 下载器列表 -->
                <div v-if="downloaders.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  <label
                    v-for="dl in downloaders"
                    :key="dl.id"
                    class="flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors"
                    :class="isDownloaderSelected(dl.id)
                      ? 'bg-primary-50 dark:bg-primary-900/20 border-2 border-primary-500'
                      : 'bg-surface-50 dark:bg-surface-700/30 border border-surface-200 dark:border-surface-700 hover:bg-surface-100 dark:hover:bg-surface-700/50'"
                    @click.prevent="toggleDownloaderSelection(dl.id)"
                  >
                    <div class="flex items-center space-x-3">
                      <div class="p-1.5 rounded-lg" :class="isDownloaderSelected(dl.id) ? 'bg-primary-100 dark:bg-primary-900/30' : 'bg-surface-100 dark:bg-surface-600'">
                        <ServerIcon class="w-4 h-4" :class="isDownloaderSelected(dl.id) ? 'text-primary-600 dark:text-primary-400' : 'text-surface-600 dark:text-surface-400'" />
                      </div>
                      <div>
                        <span class="text-sm font-medium" :class="isDownloaderSelected(dl.id) ? 'text-primary-700 dark:text-primary-300' : 'text-surface-700 dark:text-surface-300'">
                          {{ dl.name }}
                        </span>
                        <p class="text-xs text-surface-500 dark:text-surface-400">
                          {{ dl.type }} · {{ dl.host }}
                        </p>
                      </div>
                    </div>
                    <div class="flex items-center">
                      <span v-if="!dl.auto_delete" class="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 mr-2">
                        自动删种关闭
                      </span>
                      <div class="w-5 h-5 rounded border-2 flex items-center justify-center transition-colors"
                           :class="isDownloaderSelected(dl.id) ? 'bg-primary-500 border-primary-500' : 'border-surface-300 dark:border-surface-600'">
                        <CheckIcon v-if="isDownloaderSelected(dl.id)" class="w-3 h-3 text-white" />
                      </div>
                    </div>
                  </label>
                </div>
                <p v-else class="text-sm text-surface-500 dark:text-surface-400 text-center py-4">
                  暂无下载器，请先添加下载器
                </p>
              </div>
              <p class="form-hint mt-2">
                选择要应用此规则的下载器，留空则应用到所有下载器
              </p>
            </div>

            <!-- 过滤器区域 -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-group">
                <label class="form-label flex items-center gap-2">
                  <FunnelIcon class="w-4 h-4 text-purple-500" />
                  Tracker 过滤
                </label>
                <input v-model="ruleForm.tracker_filter" type="text" class="form-input" placeholder="例如: hdsky.me" />
                <p class="form-hint">只对包含此关键词的 Tracker 生效</p>
              </div>

              <div class="form-group">
                <label class="form-label flex items-center gap-2">
                  <FunnelIcon class="w-4 h-4 text-indigo-500" />
                  标签过滤
                </label>
                <input v-model="ruleForm.tag_filter" type="text" class="form-input" placeholder="例如: free" />
                <p class="form-hint">只对包含此标签的种子生效</p>
              </div>
            </div>

            <!-- 开关选项区域 -->
            <div class="pt-4 border-t border-surface-200 dark:border-surface-700">
              <p class="text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wider mb-4">执行选项</p>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <!-- 启用规则 -->
                <label class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-700/30 border border-surface-200 dark:border-surface-700 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700/50 transition-colors group">
                  <div class="flex items-center space-x-3">
                    <div class="p-1.5 rounded-lg bg-green-100 dark:bg-green-900/30">
                      <CheckCircleIcon class="w-4 h-4 text-green-600 dark:text-green-400" />
                    </div>
                    <span class="text-sm font-medium text-surface-700 dark:text-surface-300">启用规则</span>
                  </div>
                  <div class="relative">
                    <input v-model="ruleForm.enabled" type="checkbox" class="sr-only peer" />
                    <div class="w-10 h-5 bg-surface-200 rounded-full peer dark:bg-surface-600 peer-checked:bg-green-500 transition-colors"></div>
                    <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5"></div>
                  </div>
                </label>

                <!-- 删除本地文件 -->
                <label class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-700/30 border border-surface-200 dark:border-surface-700 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700/50 transition-colors group">
                  <div class="flex items-center space-x-3">
                    <div class="p-1.5 rounded-lg bg-red-100 dark:bg-red-900/30">
                      <TrashIcon class="w-4 h-4 text-red-600 dark:text-red-400" />
                    </div>
                    <span class="text-sm font-medium text-surface-700 dark:text-surface-300">删除本地文件</span>
                  </div>
                  <div class="relative">
                    <input v-model="ruleForm.delete_files" type="checkbox" class="sr-only peer" />
                    <div class="w-10 h-5 bg-surface-200 rounded-full peer dark:bg-surface-600 peer-checked:bg-red-500 transition-colors"></div>
                    <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5"></div>
                  </div>
                </label>

                <!-- 仅删除种子 -->
                <label class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-700/30 border border-surface-200 dark:border-surface-700 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700/50 transition-colors group">
                  <div class="flex items-center space-x-3">
                    <div class="p-1.5 rounded-lg bg-surface-100 dark:bg-surface-600">
                      <DocumentDuplicateIcon class="w-4 h-4 text-surface-600 dark:text-surface-400" />
                    </div>
                    <span class="text-sm font-medium text-surface-700 dark:text-surface-300">仅删除种子</span>
                  </div>
                  <div class="relative">
                    <input v-model="ruleForm.only_delete_torrent" type="checkbox" class="sr-only peer" />
                    <div class="w-10 h-5 bg-surface-200 rounded-full peer dark:bg-surface-600 peer-checked:bg-surface-500 transition-colors"></div>
                    <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5"></div>
                  </div>
                </label>

                <!-- 暂停种子 -->
                <label class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-700/30 border border-surface-200 dark:border-surface-700 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700/50 transition-colors group">
                  <div class="flex items-center space-x-3">
                    <div class="p-1.5 rounded-lg bg-yellow-100 dark:bg-yellow-900/30">
                      <ClockIcon class="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
                    </div>
                    <span class="text-sm font-medium text-surface-700 dark:text-surface-300">暂停种子</span>
                  </div>
                  <div class="relative">
                    <input v-model="ruleForm.pause" type="checkbox" class="sr-only peer" />
                    <div class="w-10 h-5 bg-surface-200 rounded-full peer dark:bg-surface-600 peer-checked:bg-yellow-500 transition-colors"></div>
                    <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5"></div>
                  </div>
                </label>

                <!-- 删除前强制汇报 -->
                <label class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-700/30 border border-surface-200 dark:border-surface-700 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700/50 transition-colors group">
                  <div class="flex items-center space-x-3">
                    <div class="p-1.5 rounded-lg bg-purple-100 dark:bg-purple-900/30">
                      <ArrowPathIcon class="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    </div>
                    <span class="text-sm font-medium text-surface-700 dark:text-surface-300">删除前强制汇报</span>
                  </div>
                  <div class="relative">
                    <input v-model="ruleForm.force_report" type="checkbox" class="sr-only peer" />
                    <div class="w-10 h-5 bg-surface-200 rounded-full peer dark:bg-surface-600 peer-checked:bg-purple-500 transition-colors"></div>
                    <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5"></div>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </div>
      </form>

      <template #footer>
        <Button variant="secondary" @click="ruleModalOpen = false">取消</Button>
        <Button variant="primary" :loading="savingRule" @click="saveRule">
          <CheckCircleIcon class="w-4 h-4" />
          保存规则
        </Button>
      </template>
    </Modal>

    <!-- Preview Modal -->
    <Modal v-model="previewModalOpen" title="预览匹配结果" size="xl">
      <!-- Warnings -->
      <div v-if="previewWarnings.length > 0" class="mb-4 space-y-2">
        <div v-for="(warning, idx) in previewWarnings" :key="idx"
             class="flex items-start gap-2 px-4 py-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg text-amber-700 dark:text-amber-400 text-sm">
          <ExclamationTriangleIcon class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{{ warning }}</span>
        </div>
      </div>

      <div v-if="previewResults.length === 0" class="empty-state py-8">
        <CheckCircleIcon class="w-16 h-16 text-green-400 mx-auto mb-4" />
        <p class="empty-state-title">没有匹配的种子</p>
        <p class="empty-state-description">当前条件下没有种子会被删除</p>
      </div>
      <div v-else class="space-y-3">
        <div class="flex items-center justify-between px-4 py-2 bg-surface-50 dark:bg-surface-700/30 rounded-lg">
          <span class="text-surface-700 dark:text-surface-300 text-sm">
            共 {{ previewResults.length }} 个种子符合条件
          </span>
          <span v-if="previewWillDeleteCount > 0" class="text-red-600 dark:text-red-400 text-sm font-medium">
            {{ previewWillDeleteCount }} 个将被删除
          </span>
        </div>
        <div
          v-for="item in previewResults"
          :key="item.hash"
          class="flex items-center justify-between p-4 rounded-xl border"
          :class="item.will_delete
            ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
            : 'bg-surface-50 dark:bg-surface-700/30 border-surface-200 dark:border-surface-700'"
        >
          <div class="flex-1 min-w-0 mr-4">
            <div class="truncate font-medium text-surface-900 dark:text-white">{{ item.name }}</div>
            <div class="text-xs text-surface-500 dark:text-surface-400 mt-1 flex items-center flex-wrap gap-2">
              <span class="flex items-center">
                <span class="w-1.5 h-1.5 rounded-full mr-1"
                      :class="item.auto_delete_enabled ? 'bg-green-500' : 'bg-surface-400'"></span>
                {{ item.downloader }}
              </span>
              <span>{{ formatSize(item.size) }}</span>
              <span>分享率: {{ item.ratio.toFixed(2) }}</span>
            </div>
          </div>
          <div class="flex flex-col items-end gap-1">
            <span v-if="!item.auto_delete_enabled" class="badge badge-gray text-xs">
              自动删种未启用
            </span>
            <span v-else-if="!item.duration_met" class="badge badge-warning">
              等待持续时间
            </span>
            <span v-else class="badge badge-danger">
              即将删除
            </span>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { deleteRulesApi, downloadersApi } from '@/api'
import { formatSize, formatTime, formatSpeed, formatDuration } from '@/utils/format'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import {
  PlusIcon, TrashIcon, ArrowPathIcon, XMarkIcon,
  ClockIcon, EyeIcon, PlayIcon, PencilIcon,
  FunnelIcon, PlusCircleIcon, DocumentDuplicateIcon,
  AdjustmentsHorizontalIcon, CheckCircleIcon, CircleStackIcon,
  ExclamationTriangleIcon, ServerStackIcon, ServerIcon, CheckIcon
} from '@heroicons/vue/24/outline'

dayjs.locale('zh-cn')

const rules = ref([])
const records = ref([])
const downloaders = ref([])

const ruleModalOpen = ref(false)
const editingRule = ref(null)
const savingRule = ref(false)
const runningRule = ref(null)
const previewingRule = ref(null)
const deleteIntervalSeconds = ref(60)
const savingInterval = ref(false)

const previewModalOpen = ref(false)
const previewResults = ref([])
const previewWarnings = ref([])
const previewWillDeleteCount = ref(0)

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
  pause: false,
  only_delete_torrent: false,
  limit_speed: 0,
  rule_type: 'normal',
  code: '(maindata, torrent) => {\n  return false;\n}',
  downloader_ids: [],
  tracker_filter: '',
  tag_filter: '',
}

const ruleForm = reactive({ ...defaultRuleForm })

// Helper functions
function getFieldLabel(field) {
  const labels = {
    name: '种子名称',
    progress: '种子进度',
    uploadSpeed: '上传速度',
    downloadSpeed: '下载速度',
    category: '种子分类',
    tags: '种子标签',
    size: '选择大小',
    totalSize: '种子大小',
    state: '种子状态',
    tracker: '站点域名',
    trackerStatus: '返回信息',
    completed: '已完成量',
    downloaded: '已下载量',
    uploaded: '已上传量',
    ratio: '分享率一',
    trueRatio: '分享率二',
    ratio3: '分享率三',
    addedTime: '添加时间',
    completedTime: '完成时间',
    savePath: '保存路径',
    seeder: '做种连接',
    leecher: '下载连接',
    freeSpace: '剩余空间',
    leechingCount: '下载任务',
    seedingCount: '做种任务',
    globalUploadSpeed: '全局上传',
    globalDownloadSpeed: '全局下载',
    secondFromZero: '当前时间',
    seeding_time: '做种时间',
  }
  return labels[field] || field
}

function getOperatorSymbol(op) {
  const symbols = {
    gt: '>',
    gte: '≥',
    lt: '<',
    lte: '≤',
    eq: '=',
    contains: '含',
    not_contains: '非',
    equals: '=',
    bigger: '>',
    smaller: '<',
    contain: '含',
    includeIn: '∈',
    notContain: '非',
    notIncludeIn: '∉',
    regExp: '正则',
    notRegExp: '非正则',
  }
  return symbols[op] || op
}

// 获取字段单位
function getFieldUnit(field) {
  const units = {
    // 数据量
    size: 'GB',
    totalSize: 'GB',
    completed: 'GB',
    downloaded: 'GB',
    uploaded: 'GB',
    freeSpace: 'GB',
    // 速度
    uploadSpeed: 'KB/s',
    downloadSpeed: 'KB/s',
    globalUploadSpeed: 'KB/s',
    globalDownloadSpeed: 'KB/s',
    // 时间
    addedTime: '秒',
    completedTime: '秒',
    seeding_time: '秒',
    secondFromZero: '秒',
    // 进度
    progress: '%',
    // 分享率无单位
    // 连接数无单位
  }
  return units[field] || ''
}

// 获取字段输入占位符
function getFieldPlaceholder(field) {
  const placeholders = {
    name: '输入种子名称关键词',
    progress: '例如: 100',
    state: '例如: downloading',
    category: '输入分类名称',
    tags: '输入标签名称',
    tracker: '例如: hdsky.me',
    trackerStatus: '输入状态关键词',
    savePath: '输入保存路径',
    size: '例如: 10',
    totalSize: '例如: 50',
    completed: '例如: 5',
    downloaded: '例如: 10',
    uploaded: '例如: 20',
    ratio: '例如: 1.0',
    trueRatio: '例如: 1.5',
    ratio3: '例如: 2.0',
    addedTime: '例如: 86400',
    completedTime: '例如: 3600',
    seeding_time: '例如: 604800',
    uploadSpeed: '例如: 1024',
    downloadSpeed: '例如: 2048',
    globalUploadSpeed: '例如: 5120',
    globalDownloadSpeed: '例如: 10240',
    seeder: '例如: 5',
    leecher: '例如: 10',
    leechingCount: '例如: 3',
    seedingCount: '例如: 20',
    freeSpace: '例如: 100',
    secondFromZero: '例如: 3600',
  }
  return placeholders[field] || '输入值'
}

// 获取持续时间单位短标签
function getDurationUnitLabel(unit) {
  const labels = {
    seconds: '秒',
    minutes: '分',
    hours: '时',
    days: '天',
  }
  return labels[unit] || ''
}

// 格式化条件持续时间显示
function formatConditionDuration(duration, unit) {
  if (!duration) return ''
  const unitNames = {
    seconds: '秒',
    minutes: '分钟',
    hours: '小时',
    days: '天',
  }
  return `${duration} ${unitNames[unit] || ''}`
}

async function loadRules() {
  try {
    const response = await deleteRulesApi.getAll()
    rules.value = response.data
  } catch (error) {
    console.error('Failed to load rules:', error)
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

function getDownloaderName(id) {
  const dl = downloaders.value.find(d => d.id === id)
  return dl ? dl.name : `下载器 #${id}`
}

function getSelectedDownloaderNames(ids) {
  if (!ids || ids.length === 0) return '全部下载器'
  return ids.map(id => getDownloaderName(id)).join(', ')
}

function toggleDownloaderSelection(downloaderId) {
  const index = ruleForm.downloader_ids.indexOf(downloaderId)
  if (index === -1) {
    ruleForm.downloader_ids.push(downloaderId)
  } else {
    ruleForm.downloader_ids.splice(index, 1)
  }
}

function selectAllDownloaders() {
  ruleForm.downloader_ids = []
}

function isDownloaderSelected(downloaderId) {
  return ruleForm.downloader_ids.includes(downloaderId)
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
    Object.assign(ruleForm, {
      ...defaultRuleForm,
      ...rule,
      rule_type: rule.rule_type || 'normal',
      // 确保每个条件都有完整的默认值
      conditions: rule.conditions.map(c => ({
        field: c.field || 'ratio',
        operator: c.operator || 'bigger',
        value: c.value || '',
        duration: c.duration || 0,
        duration_unit: c.duration_unit || 'seconds',
      })),
    })
  } else {
    Object.assign(ruleForm, { ...defaultRuleForm, conditions: [] })
  }
  ruleModalOpen.value = true
}

function addCondition() {
  ruleForm.conditions.push({ field: 'ratio', operator: 'bigger', value: '', duration: 0, duration_unit: 'seconds' })
}

function removeCondition(idx) {
  ruleForm.conditions.splice(idx, 1)
}

async function saveRule() {
  if (ruleForm.rule_type === 'normal' && ruleForm.conditions.length === 0) {
    alert('请至少添加一个条件')
    return
  }

  if (ruleForm.rule_type === 'javascript' && !ruleForm.code.trim()) {
    alert('请填写 JavaScript 规则')
    return
  }

  if (!ruleForm.name.trim()) {
    alert('请输入规则名称')
    return
  }

  savingRule.value = true
  try {
    // Save interval first
    await saveDeleteInterval()

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
  const newRule = {
    ...defaultRuleForm,
    ...rule,
    name: rule.name + ' (副本)',
    conditions: rule.conditions.map(c => ({
      field: c.field || 'ratio',
      operator: c.operator || 'bigger',
      value: c.value || '',
      duration: c.duration || 0,
      duration_unit: c.duration_unit || 'seconds',
    }))
  }
  delete newRule.id
  editingRule.value = null
  Object.assign(ruleForm, newRule)
  ruleModalOpen.value = true
}

async function previewRule(rule) {
  previewingRule.value = rule.id
  try {
    const response = await deleteRulesApi.preview(rule.id)
    previewResults.value = response.data.matches || []
    previewWarnings.value = response.data.warnings || []
    previewWillDeleteCount.value = response.data.will_delete_count || 0
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

async function loadDeleteInterval() {
  try {
    const response = await deleteRulesApi.getInterval()
    deleteIntervalSeconds.value = response.data.seconds
  } catch (error) {
    console.error('Failed to load delete interval:', error)
  }
}

async function saveDeleteInterval() {
  savingInterval.value = true
  try {
    const response = await deleteRulesApi.updateInterval(deleteIntervalSeconds.value)
    deleteIntervalSeconds.value = response.data.seconds
  } catch (error) {
    console.error('Failed to save delete interval:', error)
  } finally {
    savingInterval.value = false
  }
}

onMounted(() => {
  loadRules()
  loadRecords()
  loadDeleteInterval()
  loadDownloaders()
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

/* 条件标签样式 */
.condition-label {
  @apply text-xs font-medium text-surface-600 dark:text-surface-400 mb-1 block;
}

/* 条件卡片悬停效果 */
.condition-card {
  @apply p-4 bg-surface-50 dark:bg-surface-700/30 rounded-xl;
  @apply border border-surface-200 dark:border-surface-700;
  @apply hover:border-primary-300 dark:hover:border-primary-700;
  @apply hover:shadow-md hover:shadow-primary-500/5;
  @apply transition-all duration-200;
}
</style>
