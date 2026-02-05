<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg shadow-amber-500/30">
          <BoltIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">动态限速</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">智能控制上传速度，优化做种效率</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <span class="text-sm font-medium" :class="config.enabled ? 'text-green-600 dark:text-green-400' : 'text-surface-500 dark:text-surface-400'">
          {{ config.enabled ? '已启用' : '已禁用' }}
        </span>
        <button
          @click="toggleEnabled"
          :class="[
            'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
            config.enabled ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
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

    <!-- 状态卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 上传速度卡片 -->
      <Card :padding="false">
        <div class="p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <ArrowUpIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <span class="text-xs text-blue-600 dark:text-blue-400 font-medium">目标</span>
          </div>
          <p class="text-2xl font-bold text-surface-900 dark:text-white">{{ formatSpeed(config.target_upload_speed) }}</p>
          <div class="mt-2">
            <div class="flex justify-between text-xs text-surface-500 dark:text-surface-400 mb-1">
              <span>当前总速度</span>
              <span>{{ formatSpeed(currentUploadSpeed) }}</span>
            </div>
            <div class="w-full h-1.5 bg-surface-100 dark:bg-surface-700 rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-500 transition-all duration-300 rounded-full"
                :style="{ width: `${Math.min(100, (currentUploadSpeed / (config.target_upload_speed || 1)) * 100)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </Card>

      <!-- 下载速度卡片 -->
      <Card :padding="false">
        <div class="p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
              <ArrowDownIcon class="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <span class="text-xs text-green-600 dark:text-green-400 font-medium">目标</span>
          </div>
          <p class="text-2xl font-bold text-surface-900 dark:text-white">{{ formatSpeed(config.target_download_speed) }}</p>
          <div class="mt-2">
            <div class="flex justify-between text-xs text-surface-500 dark:text-surface-400 mb-1">
              <span>当前</span>
              <span>{{ formatSpeed(currentDownloadSpeed) }}</span>
            </div>
            <div class="w-full h-1.5 bg-surface-100 dark:bg-surface-700 rounded-full overflow-hidden">
              <div
                class="h-full bg-green-500 transition-all duration-300 rounded-full"
                :style="{ width: `${Math.min(100, (currentDownloadSpeed / (config.target_download_speed || 1)) * 100)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </Card>

      <!-- 活跃会话卡片 -->
      <Card :padding="false">
        <div class="p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <BoltIcon class="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <span class="text-xs text-amber-600 dark:text-amber-400 font-medium">活跃</span>
          </div>
          <p class="text-2xl font-bold text-surface-900 dark:text-white">{{ Object.keys(status).length }}</p>
          <p class="text-xs text-surface-500 dark:text-surface-400 mt-1">个限速会话</p>
        </div>
      </Card>

      <!-- 操作卡片 -->
      <Card :padding="false">
        <div class="p-4 flex flex-col justify-center h-full">
          <div class="flex space-x-2">
            <Button variant="secondary" size="sm" @click="clearLimits" :loading="clearing" class="flex-1">
              <XCircleIcon class="w-4 h-4" />
              <span class="hidden sm:inline ml-1">清除</span>
            </Button>
            <Button variant="primary" size="sm" @click="applyLimits" :loading="applying" class="flex-1">
              <PlayIcon class="w-4 h-4" />
              <span class="hidden sm:inline ml-1">应用</span>
            </Button>
          </div>
          <Button variant="secondary" size="sm" @click="loadStatus" class="mt-2 w-full">
            <ArrowPathIcon class="w-4 h-4 mr-1" />
            刷新状态
          </Button>
        </div>
      </Card>
    </div>

    <!-- 活跃会话 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <BoltIcon class="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">当前会话</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">活跃的限速会话 · 实时推送更新</p>
            </div>
          </div>
          <div class="text-xs text-surface-400">
            {{ lastRefresh }}
          </div>
        </div>
      </template>

      <div v-if="Object.keys(status).length === 0" class="py-12 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-100 dark:bg-surface-700 mb-4">
          <CloudIcon class="w-8 h-8 text-surface-400" />
        </div>
        <p class="text-surface-600 dark:text-surface-400 font-medium">暂无活跃会话</p>
        <p class="text-sm text-surface-500 dark:text-surface-500 mt-1">当前没有正在进行限速的种子</p>
      </div>

      <div v-else class="p-4 space-y-4">
        <!-- 移动端优化的会话卡片 -->
        <div
          v-for="(data, hash) in status"
          :key="hash"
          class="p-4 bg-surface-50 dark:bg-surface-700/30 rounded-xl border border-surface-200 dark:border-surface-700"
        >
          <!-- 头部：名称和状态 -->
          <div class="flex items-start justify-between gap-3 mb-4">
            <div class="min-w-0 flex-1">
              <div class="font-medium text-surface-900 dark:text-white truncate text-sm sm:text-base">
                {{ data.name || hash.substring(0, 8) }}
              </div>
              <div class="text-xs text-surface-500 dark:text-surface-400 truncate mt-0.5">
                {{ data.tracker || '' }}
              </div>
            </div>
            <span :class="getPhaseClass(data.phase)" class="text-xs px-2 py-1 rounded-full flex-shrink-0 font-medium">
              {{ getPhaseLabel(data.phase) }}
            </span>
          </div>

          <!-- 下次汇报倒计时 - 突出显示 -->
          <div class="mb-4 p-3 rounded-lg bg-gradient-to-r from-indigo-500/10 to-purple-500/10 dark:from-indigo-500/20 dark:to-purple-500/20 border border-indigo-200 dark:border-indigo-800">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div class="flex items-center space-x-2">
                <ClockIcon class="w-4 h-4 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
                <span class="text-xs text-indigo-700 dark:text-indigo-300 font-medium">下次汇报</span>
                <!-- 数据来源指示器 -->
                <span
                  v-if="data.time_left_source"
                  class="px-1.5 py-0.5 text-[10px] rounded-full whitespace-nowrap"
                  :class="{
                    'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400': data.time_left_source === 'properties',
                    'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400': data.time_left_source === 'peerlist_elapsed' || data.time_left_source === 'peerlist_remaining',
                    'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-400': data.time_left_source === 'trackers',
                    'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/50 dark:text-yellow-400': data.time_left_source === 'saved_state' || data.time_left_source === 'state_calc',
                    'bg-surface-100 text-surface-600 dark:bg-surface-700 dark:text-surface-400': data.time_left_source === 'estimated' || data.time_left_source === 'properties_zero'
                  }"
                  :title="getSourceDescription(data.time_left_source)"
                >
                  {{ getSourceLabel(data.time_left_source) }}
                </span>
              </div>
              <div class="flex items-center justify-end flex-wrap gap-1">
                <span class="text-lg font-bold text-indigo-600 dark:text-indigo-400">
                  {{ formatCountdown(data.time_left) }}
                </span>
                <span v-if="data.cycle_interval" class="text-xs text-surface-500 dark:text-surface-400">
                  / {{ formatDuration(data.cycle_interval) }}
                </span>
                <!-- 间隔来源指示器 -->
                <span
                  v-if="data.interval_source"
                  class="px-1.5 py-0.5 text-[10px] rounded-full whitespace-nowrap"
                  :class="{
                    'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-400': data.interval_source === 'tracker',
                    'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-400': data.interval_source === 'synced' || data.interval_source === 'client',
                    'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-400': data.interval_source === 'custom',
                    'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400': data.interval_source?.startsWith('estimated')
                  }"
                  :title="getIntervalSourceDescription(data.interval_source)"
                >
                  {{ getIntervalSourceLabel(data.interval_source) }}
                </span>
              </div>
            </div>
            <!-- 汇报周期进度条 -->
            <div class="mt-2 h-1.5 bg-indigo-100 dark:bg-indigo-900/50 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000"
                :style="{ width: `${getTimeProgress(data)}%` }"
              ></div>
            </div>
          </div>

          <!-- 周期进度 -->
          <div class="mb-3">
            <div class="flex justify-between text-xs mb-1.5">
              <span class="text-surface-500 dark:text-surface-400">周期进度</span>
              <span :class="getCycleProgressClass(data.cycle_progress)" class="font-medium">
                {{ formatPercent(data.cycle_progress) }}
              </span>
            </div>
            <div class="w-full h-2 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
              <div
                class="h-full transition-all duration-300 rounded-full"
                :class="getCycleProgressBarClass(data.cycle_progress)"
                :style="{ width: `${Math.min(100, (data.cycle_progress || 0) * 100)}%` }"
              ></div>
            </div>
            <div class="flex justify-between text-[10px] text-surface-400 dark:text-surface-500 mt-1">
              <span>{{ formatSize(data.cycle_current_upload || 0) }}</span>
              <span>{{ formatSize(data.cycle_target_upload || 0) }}</span>
            </div>
          </div>

          <!-- 阶段进度 -->
          <div class="mb-4">
            <div class="flex justify-between text-xs mb-1.5">
              <span class="text-surface-500 dark:text-surface-400">阶段</span>
              <span class="text-surface-500 dark:text-surface-400">
                {{ getPhaseLabel(data.phase) }}
              </span>
            </div>
            <div class="flex space-x-1">
              <div
                v-for="phase in ['warmup', 'catch', 'steady', 'finish']"
                :key="phase"
                :class="[
                  'flex-1 h-1.5 rounded-full transition-colors',
                  getPhaseIndex(data.phase) >= getPhaseIndex(phase)
                    ? getPhaseBarColor(phase)
                    : 'bg-surface-200 dark:bg-surface-700'
                ]"
              ></div>
            </div>
            <div class="flex justify-between text-[10px] text-surface-400 mt-1">
              <span>预热</span>
              <span>追赶</span>
              <span>稳定</span>
              <span>完成</span>
            </div>
          </div>

          <!-- 速度信息网格 - 响应式布局 -->
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div class="p-2 rounded-lg bg-surface-100 dark:bg-surface-600/30">
              <span class="text-xs text-surface-500 dark:text-surface-400 block">当前速度</span>
              <span class="font-semibold text-blue-600 dark:text-blue-400">{{ formatSpeed(data.filtered_speed || 0) }}</span>
            </div>
            <div class="p-2 rounded-lg bg-surface-100 dark:bg-surface-600/30">
              <span class="text-xs text-surface-500 dark:text-surface-400 block">周期均速</span>
              <span class="font-semibold text-teal-600 dark:text-teal-400">{{ formatSpeed(data.cycle_avg_speed || 0) }}</span>
            </div>
            <div class="p-2 rounded-lg bg-surface-100 dark:bg-surface-600/30">
              <span class="text-xs text-surface-500 dark:text-surface-400 block">限速值</span>
              <span class="font-semibold" :class="data.last_limit > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-surface-400'">
                {{ data.last_limit > 0 ? formatSpeed(data.last_limit) : '无限制' }}
              </span>
            </div>
            <div class="p-2 rounded-lg bg-surface-100 dark:bg-surface-600/30">
              <span class="text-xs text-surface-500 dark:text-surface-400 block">预估完成</span>
              <span :class="getEstimatedCompletionClass(data.estimated_completion)" class="font-semibold">
                {{ formatPercent(data.estimated_completion) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <!-- 实时速度图表 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
              <ChartBarIcon class="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">速度历史</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">实时速度监控图表</p>
            </div>
          </div>
          <Button variant="secondary" size="sm" @click="loadRecords">
            <ArrowPathIcon class="w-4 h-4" />
          </Button>
        </div>
      </template>
      <div class="p-4">
        <div class="h-48 sm:h-64">
          <v-chart :option="chartOption" autoresize />
        </div>
      </div>
    </Card>

    <!-- 配置 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center space-x-3">
          <div class="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
            <Cog6ToothIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h3 class="font-semibold text-surface-900 dark:text-white">限速配置</h3>
            <p class="text-xs text-surface-500 dark:text-surface-400">设置目标速度和控制参数</p>
          </div>
        </div>
      </template>

      <div class="p-4">
        <form @submit.prevent="saveConfig" class="space-y-6">
          <!-- 速度设置 -->
          <div>
            <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
              <BoltIcon class="w-4 h-4 mr-2 text-surface-400" />
              速度设置
            </h4>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div class="form-group">
                <label class="form-label">目标上传速度 (KB/s)</label>
                <input v-model.number="displayTargetUploadSpeed" type="number" min="0" step="0.1" class="form-input" />
                <p class="text-xs text-surface-500 mt-1">{{ formatSpeed(config.target_upload_speed) }}</p>
              </div>
              <div class="form-group">
                <label class="form-label">目标下载速度 (KB/s)</label>
                <input v-model.number="displayTargetDownloadSpeed" type="number" min="0" step="0.1" class="form-input" />
                <p class="text-xs text-surface-500 mt-1">{{ formatSpeed(config.target_download_speed) }}</p>
              </div>
              <div class="form-group">
                <label class="form-label">安全余量 (%)</label>
                <input v-model.number="displaySafetyMargin" type="number" step="1" min="0" max="50" class="form-input" />
                <p class="text-xs text-surface-500 mt-1">
                  实际目标: {{ formatSpeed(config.target_upload_speed * (1 - config.safety_margin)) }}
                </p>
              </div>
            </div>
          </div>

          <!-- 汇报周期自动检测提示 -->
          <div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
            <div class="flex items-start space-x-3">
              <div class="p-1.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex-shrink-0">
                <ClockIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h4 class="font-medium text-blue-900 dark:text-blue-300">汇报周期自动检测</h4>
                <p class="text-sm text-blue-700 dark:text-blue-400 mt-1">
                  系统会通过监测上传量变化自动检测Tracker的汇报周期，无需手动设置。
                </p>
              </div>
            </div>
          </div>

          <!-- PID 参数 -->
          <div>
            <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
              <AdjustmentsHorizontalIcon class="w-4 h-4 mr-2 text-surface-400" />
              PID 控制参数
            </h4>
            <div class="grid grid-cols-3 gap-4">
              <div class="form-group">
                <label class="form-label">Kp</label>
                <input v-model.number="config.kp" type="number" step="0.01" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">Ki</label>
                <input v-model.number="config.ki" type="number" step="0.01" class="form-input" />
              </div>
              <div class="form-group">
                <label class="form-label">Kd</label>
                <input v-model.number="config.kd" type="number" step="0.01" class="form-input" />
              </div>
            </div>
          </div>

          <div class="flex justify-end">
            <Button variant="primary" type="submit" :loading="savingConfig">
              <CheckIcon class="w-4 h-4" />
              保存配置
            </Button>
          </div>
        </form>
      </div>
    </Card>

    <!-- 站点规则 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-teal-100 dark:bg-teal-900/30">
              <GlobeAltIcon class="w-5 h-5 text-teal-600 dark:text-teal-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">站点规则</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">针对不同站点的限速配置</p>
            </div>
          </div>
          <Button variant="primary" size="sm" @click="openSiteModal()">
            <PlusIcon class="w-4 h-4" />
            <span class="hidden sm:inline ml-1">添加</span>
          </Button>
        </div>
      </template>

      <div v-if="sites.length === 0" class="py-12 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-100 dark:bg-surface-700 mb-4">
          <GlobeAltIcon class="w-8 h-8 text-surface-400" />
        </div>
        <p class="text-surface-600 dark:text-surface-400 font-medium">暂无站点规则</p>
        <p class="text-sm text-surface-500 mt-1">添加站点规则进行针对性限速配置</p>
        <Button variant="primary" class="mt-4" @click="openSiteModal()">
          <PlusIcon class="w-4 h-4 mr-1" />
          添加站点
        </Button>
      </div>

      <div v-else class="divide-y divide-surface-100 dark:divide-surface-700">
        <div
          v-for="site in sites"
          :key="site.id"
          class="flex items-center justify-between p-4 gap-3"
        >
          <div class="flex items-center space-x-3 min-w-0 flex-1">
            <div class="flex items-center justify-center w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-900/30 flex-shrink-0">
              <GlobeAltIcon class="w-5 h-5 text-teal-600 dark:text-teal-400" />
            </div>
            <div class="min-w-0">
              <div class="font-medium text-surface-900 dark:text-white truncate">{{ site.tracker_domain }}</div>
              <div class="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-surface-500 dark:text-surface-400 mt-0.5">
                <span>↑ {{ formatSpeed(site.target_upload_speed) }}</span>
                <span>↓ {{ formatSpeed(site.target_download_speed) }}</span>
                <span v-if="site.limit_download_speed" class="text-amber-600 dark:text-amber-400">限下载</span>
                <span v-if="site.optimize_announce" class="text-indigo-600 dark:text-indigo-400">优化汇报</span>
                <span v-if="site.peerlist_enabled" class="text-emerald-600 dark:text-emerald-400">精准汇报</span>
              </div>
            </div>
          </div>
          <div class="flex items-center space-x-2 flex-shrink-0">
            <button
              @click="toggleSite(site)"
              :class="[
                'relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                site.enabled ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  site.enabled ? 'translate-x-4' : 'translate-x-0'
                ]"
              ></span>
            </button>
            <Button variant="ghost" size="sm" @click="openSiteModal(site)" class="!p-1.5">
              <PencilIcon class="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" @click="deleteSite(site)" class="!p-1.5">
              <TrashIcon class="w-4 h-4 text-red-500" />
            </Button>
          </div>
        </div>
      </div>
    </Card>

    <!-- 站点弹窗 -->
    <Modal v-model="siteModalOpen" :title="editingSite ? '编辑站点规则' : '添加站点规则'">
      <form @submit.prevent="saveSite" class="space-y-4">
        <div class="form-group">
          <label class="form-label">Tracker 域名</label>
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
          <div class="form-group">
            <label class="form-label">目标上传 (KB/s)</label>
            <input v-model.number="displaySiteUploadSpeed" type="number" min="0" step="0.1" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">目标下载 (KB/s)</label>
            <input v-model.number="displaySiteDownloadSpeed" type="number" min="0" step="0.1" class="form-input" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">安全边际</label>
          <input v-model.number="siteForm.safety_margin" type="number" step="0.01" min="0" max="0.5" class="form-input" />
        </div>

        <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
          <input v-model="siteForm.enabled" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
          <span class="text-sm text-surface-700 dark:text-surface-300">启用此规则</span>
        </label>

        <!-- 高级功能 -->
        <div class="mt-4 pt-4 border-t border-surface-200 dark:border-surface-600">
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
            <BoltIcon class="w-4 h-4 mr-2 text-surface-400" />
            高级功能
          </h4>

          <div class="space-y-3">
            <label class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
              <div class="flex items-center space-x-3">
                <div class="p-1.5 rounded-lg bg-amber-100 dark:bg-amber-900/30">
                  <ArrowDownIcon class="w-4 h-4 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <span class="text-sm font-medium text-surface-700 dark:text-surface-300">下载限速</span>
                  <p class="text-xs text-surface-500 dark:text-surface-400">防止汇报时平均上传速度超过50M/s</p>
                </div>
              </div>
              <button
                type="button"
                @click="siteForm.limit_download_speed = !siteForm.limit_download_speed"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                  siteForm.limit_download_speed ? 'bg-amber-500' : 'bg-surface-200 dark:bg-surface-600'
                ]"
              >
                <span
                  :class="[
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    siteForm.limit_download_speed ? 'translate-x-5' : 'translate-x-0'
                  ]"
                ></span>
              </button>
            </label>

            <label class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
              <div class="flex items-center space-x-3">
                <div class="p-1.5 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
                  <ClockIcon class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div>
                  <span class="text-sm font-medium text-surface-700 dark:text-surface-300">汇报优化</span>
                  <p class="text-xs text-surface-500 dark:text-surface-400">智能调整汇报时间以最大化上传量</p>
                </div>
              </div>
              <button
                type="button"
                @click="siteForm.optimize_announce = !siteForm.optimize_announce"
                :class="[
                  'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                  siteForm.optimize_announce ? 'bg-indigo-500' : 'bg-surface-200 dark:bg-surface-600'
                ]"
              >
                <span
                  :class="[
                    'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                    siteForm.optimize_announce ? 'translate-x-5' : 'translate-x-0'
                  ]"
                ></span>
              </button>
            </label>
          </div>
        </div>

        <!-- 精准汇报时间 -->
        <div class="mt-4 pt-4 border-t border-surface-200 dark:border-surface-600">
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
            <ClockIcon class="w-4 h-4 mr-2 text-surface-400" />
            精准汇报时间
          </h4>
          <label class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
            <div class="flex items-center space-x-3">
              <div class="p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                <ClockIcon class="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <span class="text-sm font-medium text-surface-700 dark:text-surface-300">使用 peer list 精准计算</span>
                <p class="text-xs text-surface-500 dark:text-surface-400">需要配置站点 Cookie 与 peer list URL 模板</p>
              </div>
            </div>
            <button
              type="button"
              @click="siteForm.peerlist_enabled = !siteForm.peerlist_enabled"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                siteForm.peerlist_enabled ? 'bg-emerald-500' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  siteForm.peerlist_enabled ? 'translate-x-5' : 'translate-x-0'
                ]"
              ></span>
            </button>
          </label>

          <div v-if="siteForm.peerlist_enabled" class="mt-3 space-y-3">
            <div class="form-group">
              <label class="form-label">站点 URL</label>
              <input v-model="siteForm.peerlist_url_template" type="text" class="form-input" placeholder="https://u2.dmhy.org" />
              <p class="text-xs text-surface-500 mt-1">站点地址，系统会自动通过hash搜索获取种子ID</p>
            </div>
            <div class="form-group">
              <label class="form-label">站点 Cookie</label>
              <textarea v-model="siteForm.peerlist_cookie" rows="3" class="form-input" placeholder="nexusphp_u2=...; c_secure_xxx=..."></textarea>
              <p class="text-xs text-surface-500 mt-1">从浏览器开发者工具复制Cookie</p>
            </div>
          </div>
        </div>
      </form>

      <template #footer>
        <Button variant="secondary" @click="siteModalOpen = false">取消</Button>
        <Button variant="primary" :loading="savingSite" @click="saveSite">
          <CheckIcon class="w-4 h-4" />
          保存
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { getToast } from '@/composables/useToast'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { speedLimitApi } from '@/api'
import { useSettingsStore } from '@/stores/settings'
import { formatSpeed, formatSize, formatDuration } from '@/utils/format'
import { useRealtime } from '@/services/realtime'
import Card from '@/components/common/Card.vue'
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
  ClockIcon,
  CheckIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/vue/24/outline'

const toast = getToast()
const realtime = useRealtime()
const unsubscribeHandlers = []

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
const lastRefresh = ref('')

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
  limit_download_speed: false,
  optimize_announce: false,
  peerlist_enabled: false,
  peerlist_url_template: '',  // 站点URL，如 https://u2.dmhy.org
  peerlist_cookie: '',
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

const displaySafetyMargin = computed({
  get: () => Math.round((config.safety_margin || 0) * 100),
  set: (value) => {
    config.safety_margin = Math.max(0, Math.min(0.5, (Number(value) || 0) / 100))
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
    data: ['当前速度', '目标速度', '应用限速'],
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
      name: '当前速度',
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
      name: '目标速度',
      type: 'line',
      smooth: true,
      data: records.value.map(r => r.target_speed),
      itemStyle: { color: '#10b981' },
      lineStyle: { type: 'dashed' }
    },
    {
      name: '应用限速',
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

function getPhaseIndex(phase) {
  const phases = ['warmup', 'catch', 'steady', 'finish', 'idle']
  return phases.indexOf(phase)
}

function getPhaseClass(phase) {
  const classes = {
    warmup: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    catch: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    steady: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    finish: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
    idle: 'bg-surface-100 text-surface-600 dark:bg-surface-700 dark:text-surface-400',
  }
  return classes[phase] || 'bg-surface-100 text-surface-700 dark:bg-surface-700 dark:text-surface-300'
}

function getPhaseBarColor(phase) {
  const colors = {
    warmup: 'bg-blue-500',
    catch: 'bg-amber-500',
    steady: 'bg-green-500',
    finish: 'bg-purple-500',
    idle: 'bg-surface-400',
  }
  return colors[phase] || 'bg-surface-500'
}

function getPhaseLabel(phase) {
  const labels = {
    warmup: '预热',
    catch: '追赶',
    steady: '稳定',
    finish: '完成',
    idle: '空闲',
  }
  return labels[phase] || phase
}

// 格式化百分比
function formatPercent(value) {
  if (value === null || value === undefined) return '-'
  return `${Math.round((value || 0) * 100)}%`
}

// 格式化倒计时
function formatCountdown(seconds) {
  if (!seconds || seconds <= 0) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 计算时间进度百分比
function getTimeProgress(data) {
  if (!data.cycle_interval || data.cycle_interval <= 0) return 0
  const elapsed = data.cycle_interval - (data.time_left || 0)
  return Math.min(100, Math.max(0, (elapsed / data.cycle_interval) * 100))
}

// 数据来源标签
function getSourceLabel(source) {
  const labels = {
    'properties': '实时',
    'trackers': 'Tracker',
    'torrent_info': '客户端',
    'peerlist': 'PeerList',
    'peerlist_elapsed': '精准',
    'peerlist_remaining': '精准',
    'saved_state': '缓存',
    'state_calc': '计算',
    'estimated': '估算',
    'properties_zero': '刚汇报'
  }
  return labels[source] || source || ''
}

// 数据来源描述
function getSourceDescription(source) {
  const descriptions = {
    'properties': '从 qBittorrent properties API 获取的实时数据',
    'trackers': '从 qBittorrent trackers API 获取',
    'torrent_info': '从客户端 torrents/info 获取',
    'peerlist': '从站点 peer list 解析空闲时间',
    'peerlist_elapsed': '从站点 peer list 解析空闲时间计算',
    'peerlist_remaining': '从站点 peer list 解析剩余时间',
    'saved_state': '使用已保存的状态数据',
    'state_calc': '基于已有状态计算得出',
    'estimated': '根据种子年龄估算',
    'properties_zero': '刚刚完成汇报，等待更新'
  }
  return descriptions[source] || '未知来源'
}

// 间隔来源标签
function getIntervalSourceLabel(source) {
  const labels = {
    'tracker': 'Tracker',
    'synced': '已同步',
    'client': '客户端',
    'custom': '自定义',
    'estimated': '估算',
    'estimated_publish': '发布时间',
    'estimated_seeding': '做种时间',
    'estimated_added': '添加时间'
  }
  return labels[source] || source || ''
}

// 间隔来源描述
function getIntervalSourceDescription(source) {
  const descriptions = {
    'tracker': '从 Tracker 的 min_announce 获取的实际间隔',
    'synced': '通过周期检测同步得到的间隔',
    'client': '从客户端数据获取的间隔',
    'custom': '站点规则中配置的自定义间隔',
    'estimated': '根据种子年龄估算（新种30分/中龄45分/老种60分）',
    'estimated_publish': '根据种子发布时间估算汇报间隔',
    'estimated_seeding': '根据做种时间估算汇报间隔',
    'estimated_added': '根据添加时间估算汇报间隔'
  }
  return descriptions[source] || '未知来源'
}

// 周期进度文字颜色
function getCycleProgressClass(progress) {
  if (!progress) return 'text-surface-500 dark:text-surface-400'
  if (progress >= 1) return 'text-green-600 dark:text-green-400'
  if (progress >= 0.8) return 'text-blue-600 dark:text-blue-400'
  if (progress >= 0.5) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-500 dark:text-red-400'
}

// 周期进度条颜色
function getCycleProgressBarClass(progress) {
  if (!progress) return 'bg-surface-400'
  if (progress >= 1) return 'bg-green-500'
  if (progress >= 0.8) return 'bg-blue-500'
  if (progress >= 0.5) return 'bg-amber-500'
  return 'bg-red-500'
}

// 预估完成率颜色
function getEstimatedCompletionClass(completion) {
  if (!completion) return 'text-surface-500 dark:text-surface-400'
  if (completion >= 0.95) return 'text-green-600 dark:text-green-400'
  if (completion >= 0.8) return 'text-blue-600 dark:text-blue-400'
  if (completion >= 0.6) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-500 dark:text-red-400'
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
    toast.success('配置保存成功')
  } catch (error) {
    console.error('Failed to save config:', error)
    toast.error('配置保存失败')
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
    toast.success('限速规则已应用')
  } catch (error) {
    console.error('Failed to apply limits:', error)
    toast.error('应用限速失败')
  } finally {
    applying.value = false
  }
}

async function clearLimits() {
  if (!confirm('确定要清除所有限速吗？')) return

  clearing.value = true
  try {
    await speedLimitApi.clear()
    await loadStatus()
    toast.success('限速已清除')
  } catch (error) {
    console.error('Failed to clear limits:', error)
    toast.error('清除限速失败')
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
    lastRefresh.value = dayjs().format('HH:mm:ss')
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
    toast.success('站点规则保存成功')
  } catch (error) {
    console.error('Failed to save site:', error)
    toast.error(error.response?.data?.detail || '保存失败')
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
  if (!confirm('确定要删除此站点规则吗？')) return

  try {
    await speedLimitApi.deleteSite(site.id)
    await loadSites()
    toast.success('站点规则已删除')
  } catch (error) {
    console.error('Failed to delete site:', error)
    toast.error('删除站点规则失败')
  }
}

onMounted(() => {
  loadConfig()
  loadSites()
  loadStatus()
  loadRecords()
  realtime.connect()
  unsubscribeHandlers.push(
    realtime.subscribe('speed_limit_status', (data) => {
      status.value = data
      lastRefresh.value = dayjs().format('HH:mm:ss')
    })
  )
})

onUnmounted(() => {
  unsubscribeHandlers.forEach((unsubscribe) => unsubscribe())
})
</script>
