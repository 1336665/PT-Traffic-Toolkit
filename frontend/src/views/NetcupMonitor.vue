<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-600 shadow-lg shadow-teal-500/30">
          <SignalIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">Netcup 限速监控</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">通过 SCP API 监控服务器带宽限速状态</p>
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

    <!-- 状态概览 -->
    <div v-if="servers.length > 0" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 服务器总数 -->
      <div class="p-4 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-100 dark:border-blue-800/50">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wide">监控服务器</p>
            <p class="text-2xl font-bold text-blue-700 dark:text-blue-300 mt-1">{{ servers.length }}</p>
          </div>
          <div class="p-2.5 rounded-xl bg-blue-100 dark:bg-blue-800/50">
            <ServerStackIcon class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </div>

      <!-- 正常状态 -->
      <div class="p-4 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border border-emerald-100 dark:border-emerald-800/50">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">正常运行</p>
            <p class="text-2xl font-bold text-emerald-700 dark:text-emerald-300 mt-1">{{ normalServersCount }}</p>
          </div>
          <div class="p-2.5 rounded-xl bg-emerald-100 dark:bg-emerald-800/50">
            <CheckCircleIcon class="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
          </div>
        </div>
      </div>

      <!-- 限速中 -->
      <div class="p-4 rounded-2xl bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 border border-orange-100 dark:border-orange-800/50">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-orange-600 dark:text-orange-400 uppercase tracking-wide">限速中</p>
            <p class="text-2xl font-bold text-orange-700 dark:text-orange-300 mt-1">{{ throttledServersCount }}</p>
          </div>
          <div class="p-2.5 rounded-xl bg-orange-100 dark:bg-orange-800/50">
            <ExclamationTriangleIcon class="w-6 h-6 text-orange-600 dark:text-orange-400" />
          </div>
        </div>
      </div>

      <!-- 整体健康度 -->
      <div class="p-4 rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-100 dark:border-purple-800/50">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-purple-600 dark:text-purple-400 uppercase tracking-wide">健康度</p>
            <p class="text-2xl font-bold text-purple-700 dark:text-purple-300 mt-1">{{ overallHealthPercent }}%</p>
          </div>
          <div class="p-2.5 rounded-xl bg-purple-100 dark:bg-purple-800/50">
            <ChartBarIcon class="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
        <div class="mt-2 h-1.5 rounded-full bg-purple-200 dark:bg-purple-800 overflow-hidden">
          <div
            class="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
            :style="{ width: `${overallHealthPercent}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- SCP 账户管理 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <KeyIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">SCP 账户</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">绑定 Netcup SCP 控制面板账户</p>
            </div>
          </div>
          <Button variant="primary" size="sm" @click="openAccountModal()">
            <PlusIcon class="w-4 h-4" />
            <span class="hidden sm:inline ml-1">添加账户</span>
          </Button>
        </div>
      </template>

      <!-- 空状态 -->
      <div v-if="accounts.length === 0" class="py-12 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-100 dark:bg-surface-700 mb-4">
          <KeyIcon class="w-8 h-8 text-surface-400" />
        </div>
        <p class="text-surface-600 dark:text-surface-400 font-medium">暂无账户</p>
        <p class="text-sm text-surface-500 mt-1">添加 Netcup SCP 账户开始监控</p>
        <Button variant="primary" class="mt-4" @click="openAccountModal()">
          <PlusIcon class="w-4 h-4 mr-1" />
          添加账户
        </Button>
      </div>

      <!-- 账户列表 -->
      <div v-else class="divide-y divide-surface-100 dark:divide-surface-700">
        <div
          v-for="account in accounts"
          :key="account.id"
          class="px-6 py-4 flex items-center justify-between hover:bg-surface-50 dark:hover:bg-surface-800/30 transition-colors"
        >
          <div class="flex items-center space-x-4">
            <div class="p-2 rounded-lg" :class="account.enabled ? 'bg-green-100 dark:bg-green-900/30' : 'bg-surface-100 dark:bg-surface-700'">
              <UserCircleIcon class="w-5 h-5" :class="account.enabled ? 'text-green-600 dark:text-green-400' : 'text-surface-400'" />
            </div>
            <div>
              <div class="font-medium text-surface-900 dark:text-white">{{ account.name }}</div>
              <div class="text-sm text-surface-500 dark:text-surface-400">{{ account.loginname }}</div>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <Button variant="secondary" size="sm" @click="testAccount(account.id)" :loading="testingAccount === account.id">
              <SignalIcon class="w-4 h-4" />
              测试
            </Button>
            <Button variant="secondary" size="sm" @click="fetchAccountServers(account.id)" :loading="fetchingServers === account.id">
              <CloudArrowDownIcon class="w-4 h-4" />
              获取服务器
            </Button>
            <Button variant="secondary" size="sm" @click="openAccountModal(account)">
              <PencilIcon class="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" @click="deleteAccount(account.id)" :loading="deletingAccount === account.id" class="text-red-500 hover:text-red-600">
              <TrashIcon class="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </Card>

    <!-- 服务器状态表格 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-teal-100 dark:bg-teal-900/30">
              <ServerStackIcon class="w-5 h-5 text-teal-600 dark:text-teal-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">服务器状态</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">点击展开查看详情</p>
            </div>
          </div>
          <Button variant="primary" size="sm" @click="openServerModal()" :disabled="accounts.length === 0">
            <PlusIcon class="w-4 h-4" />
            <span class="hidden sm:inline ml-1">添加服务器</span>
          </Button>
        </div>
      </template>

      <!-- 表头 -->
      <div class="hidden lg:grid grid-cols-8 gap-4 px-6 py-3 bg-surface-50 dark:bg-surface-800/50 text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wide border-b border-surface-200 dark:border-surface-700">
        <div>服务器</div>
        <div>当前状态</div>
        <div>当前持续</div>
        <div>月流量</div>
        <div>今日正常</div>
        <div>今日限速</div>
        <div>限速占比</div>
        <div class="text-right">详情</div>
      </div>

      <!-- 空状态 -->
      <div v-if="servers.length === 0" class="py-12 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-surface-100 dark:bg-surface-700 mb-4">
          <ServerStackIcon class="w-8 h-8 text-surface-400" />
        </div>
        <p class="text-surface-600 dark:text-surface-400 font-medium">暂无服务器</p>
        <p class="text-sm text-surface-500 mt-1">{{ accounts.length === 0 ? '请先添加 SCP 账户' : '添加 Netcup 服务器开始监控' }}</p>
        <Button v-if="accounts.length > 0" variant="primary" class="mt-4" @click="openServerModal()">
          <PlusIcon class="w-4 h-4 mr-1" />
          添加服务器
        </Button>
      </div>

      <!-- 服务器列表 -->
      <div v-else class="divide-y divide-surface-100 dark:divide-surface-700">
        <div
          v-for="server in servers"
          :key="server.id"
          class="group"
        >
          <!-- 主行 -->
          <div class="grid grid-cols-2 lg:grid-cols-8 gap-4 px-6 py-4 items-center hover:bg-surface-50 dark:hover:bg-surface-800/30 transition-colors">
            <!-- 服务器名称 -->
            <div class="flex items-center space-x-2">
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">{{ server.name }}</span>
              <span v-if="server.whitelist" class="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">白名单</span>
            </div>

            <!-- 当前状态 -->
            <div class="flex items-center space-x-2">
              <span
                class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
                :class="getStatusClass(server.current_status)"
              >
                <span class="w-2 h-2 rounded-full mr-1.5" :class="getStatusDotClass(server.current_status)"></span>
                {{ getStatusLabel(server.current_status) }}
              </span>
            </div>

            <!-- 当前持续时间 -->
            <div class="text-sm text-surface-700 dark:text-surface-300 hidden lg:block">
              {{ formatDuration(getServerStatus(server.id)?.status_duration || 0) }}
            </div>

            <!-- 月流量 -->
            <div class="text-sm text-surface-700 dark:text-surface-300 hidden lg:block">
              <div>↑ {{ server.monthly_tx_gib?.toFixed(1) || 0 }} GiB</div>
              <div class="text-xs text-surface-500">↓ {{ server.monthly_rx_gib?.toFixed(1) || 0 }} GiB</div>
            </div>

            <!-- 今日正常时间 -->
            <div class="text-sm text-surface-700 dark:text-surface-300 hidden lg:block">
              {{ formatDuration(server.today_normal_seconds || 0) }}
            </div>

            <!-- 今日限速时间 -->
            <div class="text-sm text-surface-700 dark:text-surface-300 hidden lg:block">
              {{ formatDuration(server.today_throttled_seconds || 0) }}
            </div>

            <!-- 限速占比 -->
            <div class="hidden lg:block">
              <span
                class="text-sm font-medium"
                :class="getThrottleRatioClass(server)"
              >
                {{ formatPercent(getThrottleRatio(server)) }}
              </span>
            </div>

            <!-- 详情按钮 -->
            <div class="flex items-center justify-end space-x-2">
              <button
                @click="toggleExpand(server.id)"
                class="px-3 py-1.5 text-sm text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg transition-colors cursor-pointer"
              >
                {{ expandedServers.includes(server.id) ? '收起' : '展开' }}
              </button>
            </div>
          </div>

          <!-- 展开详情 -->
          <transition
            enter-active-class="transition-all duration-300 ease-out"
            enter-from-class="opacity-0 max-h-0"
            enter-to-class="opacity-100 max-h-96"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="opacity-100 max-h-96"
            leave-to-class="opacity-0 max-h-0"
          >
            <div v-if="expandedServers.includes(server.id)" class="overflow-hidden">
              <div class="px-6 py-4 bg-surface-50/50 dark:bg-surface-800/20 border-t border-surface-100 dark:border-surface-700">
                <!-- 统计卡片 -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                  <!-- 传输量 -->
                  <div class="p-4 rounded-xl bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
                    <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-2">传输量</h4>
                    <div class="space-y-1 text-sm text-surface-600 dark:text-surface-400">
                      <div>月上行 {{ server.monthly_tx_gib?.toFixed(2) || 0 }} GiB</div>
                      <div>月下行 {{ server.monthly_rx_gib?.toFixed(2) || 0 }} GiB</div>
                      <div>接口速度 {{ server.interface_speed_mbits || 0 }} Mbit/s</div>
                    </div>
                  </div>

                  <!-- 服务器信息 -->
                  <div class="p-4 rounded-xl bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
                    <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-2">服务器信息</h4>
                    <div class="space-y-1 text-sm text-surface-600 dark:text-surface-400">
                      <div>IP {{ server.ip_address }}</div>
                      <div>SCP ID {{ server.server_id_scp || '未知' }}</div>
                      <div>状态 {{ server.server_status || '未知' }}</div>
                    </div>
                  </div>

                  <!-- 控制方式 -->
                  <div class="p-4 rounded-xl bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
                    <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-2">控制方式</h4>
                    <div class="space-y-1 text-sm text-surface-600 dark:text-surface-400">
                      <template v-if="server.downloader_id">
                        <div class="flex items-center space-x-1.5">
                          <span class="inline-block w-2 h-2 rounded-full bg-teal-500"></span>
                          <span>下载器 API</span>
                        </div>
                        <div class="text-xs">{{ getDownloaderName(server.downloader_id) }}</div>
                        <div class="text-xs text-teal-600 dark:text-teal-400">暂停/恢复种子</div>
                      </template>
                      <template v-else>
                        <div class="flex items-center space-x-1.5">
                          <span class="inline-block w-2 h-2 rounded-full bg-amber-500"></span>
                          <span>SSH {{ server.qb_control_type === 'docker' ? 'Docker' : 'Systemd' }}</span>
                        </div>
                        <div class="text-xs">{{ server.ssh_username }}@{{ server.ip_address }}:{{ server.ssh_port }}</div>
                      </template>
                    </div>
                  </div>

                  <!-- 状态趋势 -->
                  <div class="p-4 rounded-xl bg-white dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
                    <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-2">状态趋势</h4>
                    <div class="mt-3">
                      <div class="h-2 rounded-full bg-surface-200 dark:bg-surface-700 overflow-hidden">
                        <div
                          class="h-full bg-gradient-to-r from-emerald-400 to-teal-500 rounded-full transition-all duration-500"
                          :style="{ width: `${100 - getThrottleRatio(server) * 100}%` }"
                        ></div>
                      </div>
                      <div class="flex justify-between text-xs text-surface-500 mt-1">
                        <span>正常 {{ formatPercent(1 - getThrottleRatio(server)) }}</span>
                        <span>限速 {{ formatPercent(getThrottleRatio(server)) }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 操作按钮 -->
                <div class="flex items-center justify-end space-x-2">
                  <Button variant="secondary" size="sm" @click="testServer(server.id)" :loading="testingServer === server.id">
                    <SignalIcon class="w-4 h-4" />
                    测试连接
                  </Button>
                  <Button variant="secondary" size="sm" @click="openServerModal(server)">
                    <PencilIcon class="w-4 h-4" />
                    编辑
                  </Button>
                  <Button variant="ghost" size="sm" @click="deleteServer(server.id)" :loading="deletingServer === server.id" class="text-red-500 hover:text-red-600">
                    <TrashIcon class="w-4 h-4" />
                    删除
                  </Button>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </Card>

    <!-- 全局配置 -->
    <Card :padding="false">
      <template #header>
        <div class="flex items-center space-x-3">
          <div class="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
            <Cog6ToothIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h3 class="font-semibold text-surface-900 dark:text-white">监控配置</h3>
            <p class="text-xs text-surface-500 dark:text-surface-400">设置检查间隔和自动控制</p>
          </div>
        </div>
      </template>

      <div class="p-6">
        <form @submit.prevent="saveConfig" class="space-y-6">
          <!-- 时间间隔设置 -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="form-group">
              <label class="form-label">检查间隔 (秒)</label>
              <input v-model.number="config.check_interval" type="number" min="10" max="300" class="form-input" />
              <p class="text-xs text-surface-500 mt-1">每隔多少秒检查一次服务器限速状态</p>
            </div>
            <div class="form-group">
              <label class="form-label">重试间隔 (秒)</label>
              <input v-model.number="config.retry_interval" type="number" min="5" max="120" class="form-input" />
              <p class="text-xs text-surface-500 mt-1">API 请求失败后的重试等待时间</p>
            </div>
          </div>

          <!-- 自动控制下载器 -->
          <div
            class="relative overflow-hidden rounded-2xl border transition-all duration-300 cursor-pointer"
            :class="config.auto_control_enabled
              ? 'border-teal-200 dark:border-teal-800 bg-gradient-to-br from-teal-50 to-cyan-50 dark:from-teal-900/20 dark:to-cyan-900/20'
              : 'border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800/50 hover:border-surface-300 dark:hover:border-surface-600'"
            @click="config.auto_control_enabled = !config.auto_control_enabled"
          >
            <div class="p-5">
              <div class="flex items-start justify-between">
                <div class="flex items-start space-x-4">
                  <div
                    class="p-3 rounded-xl transition-colors duration-300"
                    :class="config.auto_control_enabled
                      ? 'bg-gradient-to-br from-teal-500 to-cyan-600 shadow-lg shadow-teal-500/30'
                      : 'bg-surface-200 dark:bg-surface-700'"
                  >
                    <PauseCircleIcon
                      class="w-6 h-6 transition-colors duration-300"
                      :class="config.auto_control_enabled ? 'text-white' : 'text-surface-500'"
                    />
                  </div>
                  <div class="flex-1">
                    <h4 class="font-semibold text-surface-900 dark:text-white flex items-center space-x-2">
                      <span>自动控制下载器</span>
                      <span
                        v-if="config.auto_control_enabled"
                        class="text-xs px-2 py-0.5 rounded-full bg-teal-100 dark:bg-teal-900/50 text-teal-700 dark:text-teal-300"
                      >
                        已启用
                      </span>
                    </h4>
                    <p class="text-sm text-surface-600 dark:text-surface-400 mt-1">
                      当检测到服务器被限速时，自动暂停关联的下载器中所有种子
                    </p>
                    <div class="mt-3 space-y-2">
                      <div class="flex items-center space-x-2 text-xs text-surface-500 dark:text-surface-400">
                        <ArrowRightIcon class="w-3.5 h-3.5 text-orange-500" />
                        <span><strong class="text-orange-600 dark:text-orange-400">限速时</strong>：暂停所有种子，停止上传和下载流量</span>
                      </div>
                      <div class="flex items-center space-x-2 text-xs text-surface-500 dark:text-surface-400">
                        <ArrowRightIcon class="w-3.5 h-3.5 text-emerald-500" />
                        <span><strong class="text-emerald-600 dark:text-emerald-400">恢复时</strong>：恢复所有种子，继续正常传输</span>
                      </div>
                    </div>
                    <div class="mt-3 p-2.5 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800">
                      <p class="text-xs text-blue-700 dark:text-blue-300">
                        <InformationCircleIcon class="w-3.5 h-3.5 inline mr-1" />
                        使用暂停/恢复代替限速，避免与动态限速功能冲突
                      </p>
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  :class="[
                    'relative inline-flex h-7 w-12 flex-shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 dark:focus:ring-offset-surface-800',
                    config.auto_control_enabled ? 'bg-teal-500' : 'bg-surface-300 dark:bg-surface-600'
                  ]"
                  @click.stop="config.auto_control_enabled = !config.auto_control_enabled"
                >
                  <span
                    :class="[
                      'pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                      config.auto_control_enabled ? 'translate-x-5' : 'translate-x-0'
                    ]"
                  ></span>
                </button>
              </div>
            </div>
          </div>

          <!-- Telegram 通知 -->
          <div
            class="relative overflow-hidden rounded-2xl border transition-all duration-300 cursor-pointer"
            :class="config.telegram_enabled
              ? 'border-blue-200 dark:border-blue-800 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20'
              : 'border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800/50 hover:border-surface-300 dark:hover:border-surface-600'"
            @click="config.telegram_enabled = !config.telegram_enabled"
          >
            <div class="p-5">
              <div class="flex items-start justify-between">
                <div class="flex items-start space-x-4">
                  <div
                    class="p-3 rounded-xl transition-colors duration-300"
                    :class="config.telegram_enabled
                      ? 'bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/30'
                      : 'bg-surface-200 dark:bg-surface-700'"
                  >
                    <BellAlertIcon
                      class="w-6 h-6 transition-colors duration-300"
                      :class="config.telegram_enabled ? 'text-white' : 'text-surface-500'"
                    />
                  </div>
                  <div class="flex-1">
                    <h4 class="font-semibold text-surface-900 dark:text-white flex items-center space-x-2">
                      <span>Telegram 通知</span>
                      <span
                        v-if="config.telegram_enabled"
                        class="text-xs px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300"
                      >
                        已启用
                      </span>
                    </h4>
                    <p class="text-sm text-surface-600 dark:text-surface-400 mt-1">
                      当服务器限速状态发生变化时，发送 Telegram 消息通知
                    </p>
                    <div class="mt-3 space-y-2">
                      <div class="flex items-center space-x-2 text-xs text-surface-500 dark:text-surface-400">
                        <ExclamationTriangleIcon class="w-3.5 h-3.5 text-orange-500" />
                        <span>服务器<strong class="text-orange-600 dark:text-orange-400">开始限速</strong>时发送警告通知</span>
                      </div>
                      <div class="flex items-center space-x-2 text-xs text-surface-500 dark:text-surface-400">
                        <CheckCircleIcon class="w-3.5 h-3.5 text-emerald-500" />
                        <span>服务器<strong class="text-emerald-600 dark:text-emerald-400">恢复正常</strong>时发送恢复通知（含限速时长）</span>
                      </div>
                    </div>
                    <div class="mt-3 p-2.5 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800">
                      <p class="text-xs text-amber-700 dark:text-amber-300">
                        <InformationCircleIcon class="w-3.5 h-3.5 inline mr-1" />
                        需要先在「设置」页面配置 Telegram Bot Token 和 Chat ID
                      </p>
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  :class="[
                    'relative inline-flex h-7 w-12 flex-shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-surface-800',
                    config.telegram_enabled ? 'bg-blue-500' : 'bg-surface-300 dark:bg-surface-600'
                  ]"
                  @click.stop="config.telegram_enabled = !config.telegram_enabled"
                >
                  <span
                    :class="[
                      'pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                      config.telegram_enabled ? 'translate-x-5' : 'translate-x-0'
                    ]"
                  ></span>
                </button>
              </div>
            </div>
          </div>

          <div class="flex justify-end space-x-3 pt-2">
            <Button variant="secondary" type="button" @click="runManualCheck" :loading="checking">
              <ArrowPathIcon class="w-4 h-4" />
              立即检查
            </Button>
            <Button variant="primary" type="submit" :loading="savingConfig">
              <CheckIcon class="w-4 h-4" />
              保存配置
            </Button>
          </div>
        </form>
      </div>
    </Card>

    <!-- 账户编辑弹窗 -->
    <Modal v-model="accountModalOpen" :title="editingAccount ? '编辑账户' : '添加账户'">
      <form @submit.prevent="saveAccount" class="space-y-4">
        <div class="form-group">
          <label class="form-label">账户名称</label>
          <input v-model="accountForm.name" type="text" required class="form-input" placeholder="My Netcup Account" />
        </div>

        <div class="form-group">
          <label class="form-label">SCP 登录名</label>
          <input v-model="accountForm.loginname" type="text" required class="form-input" placeholder="您的 SCP 用户名" />
          <p class="text-xs text-surface-500 mt-1">在 servercontrolpanel.de 登录时使用的用户名</p>
        </div>

        <div class="form-group">
          <label class="form-label">SCP 密码</label>
          <input v-model="accountForm.password" type="password" required class="form-input" placeholder="您的 SCP 密码" />
          <p class="text-xs text-surface-500 mt-1">在 servercontrolpanel.de 登录时使用的密码</p>
        </div>

        <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
          <input v-model="accountForm.enabled" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
          <span class="text-sm text-surface-700 dark:text-surface-300">启用账户</span>
        </label>
      </form>

      <template #footer>
        <Button variant="secondary" @click="accountModalOpen = false">取消</Button>
        <Button variant="primary" :loading="savingAccount" @click="saveAccount">
          <CheckIcon class="w-4 h-4" />
          保存
        </Button>
      </template>
    </Modal>

    <!-- 服务器编辑弹窗 -->
    <Modal v-model="serverModalOpen" :title="editingServer ? '编辑服务器' : '添加服务器'">
      <form @submit.prevent="saveServer" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="form-group">
            <label class="form-label">所属账户</label>
            <select v-model="serverForm.account_id" required class="form-input">
              <option value="">选择账户</option>
              <option v-for="account in accounts" :key="account.id" :value="account.id">{{ account.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">关联下载器 <span v-if="downloaders.length > 0" class="text-xs text-surface-500">({{ downloaders.length }} 个可用)</span></label>
            <select v-model="serverForm.downloader_id" class="form-input">
              <option :value="null">不关联（手动配置SSH）</option>
              <option v-for="d in downloaders" :key="d.id" :value="d.id">{{ d.name }} ({{ d.host }}:{{ d.port }})</option>
            </select>
            <p v-if="downloaders.length === 0" class="text-xs text-amber-500 mt-1">未找到下载器，请先在"下载器"页面添加</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="form-group">
            <label class="form-label">服务器名称</label>
            <input v-model="serverForm.name" type="text" required class="form-input" placeholder="My Netcup Server" />
          </div>
          <div class="form-group">
            <label class="form-label">SCP 服务器 ID</label>
            <input v-model.number="serverForm.server_id_scp" type="number" class="form-input" placeholder="可选，留空自动匹配" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">IP 地址</label>
          <input v-model="serverForm.ip_address" type="text" required class="form-input" placeholder="192.168.1.1" />
          <p class="text-xs text-surface-500 mt-1">用于匹配 SCP 服务器（需与 SCP 中的 IP 一致）</p>
        </div>

        <!-- 仅在未关联下载器时显示 SSH 配置 -->
        <div v-if="!serverForm.downloader_id" class="border-t border-surface-200 dark:border-surface-700 pt-4 mt-4">
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3">SSH 配置（用于控制 qBittorrent）</h4>
          <div class="grid grid-cols-2 gap-4">
            <div class="form-group">
              <label class="form-label">SSH 端口</label>
              <input v-model.number="serverForm.ssh_port" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label class="form-label">SSH 用户名</label>
              <input v-model="serverForm.ssh_username" type="text" class="form-input" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="form-group">
              <label class="form-label">SSH 密码</label>
              <input v-model="serverForm.ssh_password" type="password" class="form-input" placeholder="留空使用密钥" />
            </div>
            <div class="form-group">
              <label class="form-label">SSH 密钥路径</label>
              <input v-model="serverForm.ssh_key_path" type="text" class="form-input" placeholder="/root/.ssh/id_rsa" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4 mt-3">
            <div class="form-group">
              <label class="form-label">控制类型</label>
              <select v-model="serverForm.qb_control_type" class="form-input">
                <option value="systemd">Systemd</option>
                <option value="docker">Docker</option>
              </select>
            </div>
            <div v-if="serverForm.qb_control_type === 'docker'" class="form-group">
              <label class="form-label">容器名称</label>
              <input v-model="serverForm.qb_docker_container" type="text" class="form-input" placeholder="qbittorrent" />
            </div>
            <div v-else class="form-group">
              <label class="form-label">服务名称</label>
              <input v-model="serverForm.qb_systemd_service" type="text" class="form-input" placeholder="qbittorrent-nox" />
            </div>
          </div>
        </div>

        <!-- 关联下载器时显示提示 -->
        <div v-else class="p-4 rounded-xl bg-gradient-to-r from-teal-50 to-cyan-50 dark:from-teal-900/20 dark:to-cyan-900/20 border border-teal-200 dark:border-teal-800">
          <div class="flex items-start space-x-3">
            <div class="p-1.5 rounded-lg bg-teal-100 dark:bg-teal-800/50">
              <PauseCircleIcon class="w-4 h-4 text-teal-600 dark:text-teal-400" />
            </div>
            <div>
              <p class="text-sm font-medium text-teal-800 dark:text-teal-200">已关联下载器控制</p>
              <p class="text-xs text-teal-600 dark:text-teal-400 mt-1">
                当检测到限速时，将通过下载器 API 暂停所有种子；恢复正常后自动恢复种子。
              </p>
            </div>
          </div>
        </div>

        <div class="space-y-3">
          <label class="flex items-center justify-between p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
            <div class="flex items-center space-x-3">
              <div class="p-1.5 rounded-lg bg-amber-100 dark:bg-amber-900/30">
                <ShieldExclamationIcon class="w-4 h-4 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <span class="text-sm font-medium text-surface-700 dark:text-surface-300">白名单模式</span>
                <p class="text-xs text-surface-500 dark:text-surface-400">只监控不自动控制</p>
              </div>
            </div>
            <button
              type="button"
              @click="serverForm.whitelist = !serverForm.whitelist"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                serverForm.whitelist ? 'bg-amber-500' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  serverForm.whitelist ? 'translate-x-5' : 'translate-x-0'
                ]"
              ></span>
            </button>
          </label>

          <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
            <input v-model="serverForm.enabled" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
            <span class="text-sm text-surface-700 dark:text-surface-300">启用监控</span>
          </label>
        </div>
      </form>

      <template #footer>
        <Button variant="secondary" @click="serverModalOpen = false">取消</Button>
        <Button variant="primary" :loading="savingServer" @click="saveServer">
          <CheckIcon class="w-4 h-4" />
          保存
        </Button>
      </template>
    </Modal>

    <!-- SCP 服务器列表弹窗 -->
    <Modal v-model="scpServersModalOpen" title="选择服务器" size="lg">
      <div v-if="scpServers.length === 0" class="py-8 text-center text-surface-500">
        暂无可用服务器
      </div>
      <div v-else class="divide-y divide-surface-100 dark:divide-surface-700">
        <div
          v-for="srv in scpServers"
          :key="srv.id"
          class="py-3 flex items-center justify-between hover:bg-surface-50 dark:hover:bg-surface-800/30 px-2 rounded-lg cursor-pointer"
          @click="selectScpServer(srv)"
        >
          <div>
            <div class="font-medium text-surface-900 dark:text-white">{{ srv.name }}</div>
            <div class="text-sm text-surface-500">{{ srv.ip_address }} | ID: {{ srv.id }}</div>
            <div class="text-xs text-surface-400">
              流量: ↑{{ srv.monthly_tx_gib?.toFixed(1) || 0 }} GiB ↓{{ srv.monthly_rx_gib?.toFixed(1) || 0 }} GiB
              <span v-if="srv.traffic_throttled" class="text-orange-500 ml-2">限速中</span>
            </div>
          </div>
          <div>
            <span
              class="px-2 py-1 rounded text-xs"
              :class="getScpStatusClass(srv.status)"
            >
              {{ srv.status || 'UNKNOWN' }}
            </span>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { getToast } from '@/composables/useToast'
import { netcupApi, downloadersApi } from '@/api'
import { formatSize, formatDuration } from '@/utils/format'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Modal from '@/components/common/Modal.vue'
import {
  SignalIcon,
  ServerStackIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
  CheckIcon,
  ShieldExclamationIcon,
  KeyIcon,
  UserCircleIcon,
  CloudArrowDownIcon,
  PauseCircleIcon,
  BellAlertIcon,
  ArrowRightIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ChartBarIcon,
} from '@heroicons/vue/24/outline'

const toast = getToast()

// State
const config = reactive({
  enabled: false,
  check_interval: 60,
  retry_interval: 30,
  auto_control_enabled: true,
  telegram_enabled: false
})

const accounts = ref([])
const servers = ref([])
const downloaders = ref([])
const serverStatus = ref({})
const serverStats = ref({})
const expandedServers = ref([])

const savingConfig = ref(false)
const checking = ref(false)
const testingServer = ref(null)
const testingAccount = ref(null)
const fetchingServers = ref(null)
const deletingServer = ref(null)
const deletingAccount = ref(null)

// Account modal
const accountModalOpen = ref(false)
const editingAccount = ref(null)
const savingAccount = ref(false)

const defaultAccountForm = {
  name: '',
  loginname: '',
  password: '',
  enabled: true
}

const accountForm = reactive({ ...defaultAccountForm })

// Server modal
const serverModalOpen = ref(false)
const editingServer = ref(null)
const savingServer = ref(false)

const defaultServerForm = {
  name: '',
  account_id: '',
  server_id_scp: null,
  ip_address: '',
  ssh_port: 22,
  ssh_username: 'root',
  ssh_password: '',
  ssh_key_path: '',
  qb_control_type: 'systemd',
  qb_docker_container: '',
  qb_systemd_service: 'qbittorrent-nox',
  downloader_id: null,
  whitelist: false,
  enabled: true
}

const serverForm = reactive({ ...defaultServerForm })

// SCP servers modal
const scpServersModalOpen = ref(false)
const scpServers = ref([])
const selectedAccountId = ref(null)

// Stats computed properties
const normalServersCount = computed(() => {
  return servers.value.filter(s => s.current_status === 'normal').length
})

const throttledServersCount = computed(() => {
  return servers.value.filter(s => s.current_status === 'throttled').length
})

const overallHealthPercent = computed(() => {
  if (servers.value.length === 0) return 100
  const totalNormal = servers.value.reduce((sum, s) => sum + (s.today_normal_seconds || 0), 0)
  const totalThrottled = servers.value.reduce((sum, s) => sum + (s.today_throttled_seconds || 0), 0)
  const total = totalNormal + totalThrottled
  if (total === 0) return 100
  return Math.round((totalNormal / total) * 100)
})

// Computed
function getServerStatus(serverId) {
  return serverStatus.value[serverId] || null
}

function getThrottleRatio(server) {
  const total = (server.today_normal_seconds || 0) + (server.today_throttled_seconds || 0)
  if (total === 0) return 0
  return (server.today_throttled_seconds || 0) / total
}

function getShareRatio(server) {
  if (!server.today_download || server.today_download === 0) {
    return server.today_upload > 0 ? '∞' : '-'
  }
  return (server.today_upload / server.today_download).toFixed(2)
}

function getMaxThrottleDuration(serverId) {
  return 0
}

function getMaxNormalDuration(serverId) {
  return 0
}

// Status helpers
function getStatusClass(status) {
  if (status === 'throttled') {
    return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
  } else if (status === 'normal') {
    return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
  }
  return 'bg-surface-100 text-surface-600 dark:bg-surface-700 dark:text-surface-400'
}

function getStatusDotClass(status) {
  if (status === 'throttled') {
    return 'bg-orange-500'
  } else if (status === 'normal') {
    return 'bg-emerald-500'
  }
  return 'bg-surface-400'
}

function getStatusLabel(status) {
  if (status === 'throttled') return '限速'
  if (status === 'normal') return '正常'
  return '未知'
}

function getScpStatusClass(status) {
  const s = (status || '').toUpperCase()
  if (s === 'RUNNING' || s === 'ONLINE' || s === 'ACTIVE') {
    return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
  } else if (s === 'STOPPED' || s === 'OFFLINE' || s === 'INACTIVE') {
    return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  }
  return 'bg-surface-100 text-surface-600 dark:bg-surface-700 dark:text-surface-400'
}

function getThrottleRatioClass(server) {
  const ratio = getThrottleRatio(server)
  if (ratio >= 0.5) return 'text-red-500 dark:text-red-400'
  if (ratio >= 0.2) return 'text-orange-500 dark:text-orange-400'
  return 'text-emerald-500 dark:text-emerald-400'
}

function getDownloaderName(downloaderId) {
  if (!downloaderId) return null
  const downloader = downloaders.value.find(d => d.id === downloaderId)
  return downloader ? downloader.name : `ID: ${downloaderId}`
}

// Format helpers
function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`
}

function formatPercentDiff(current, previous) {
  const diff = (current - previous) * 100
  if (diff > 0) return `+${diff.toFixed(1)}%`
  return `${diff.toFixed(1)}%`
}

// Actions
function toggleExpand(serverId) {
  const index = expandedServers.value.indexOf(serverId)
  if (index >= 0) {
    expandedServers.value.splice(index, 1)
  } else {
    expandedServers.value.push(serverId)
  }
}

async function loadConfig() {
  try {
    const response = await netcupApi.getConfig()
    Object.assign(config, response.data)
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

async function saveConfig() {
  savingConfig.value = true
  try {
    await netcupApi.updateConfig(config)
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

// Account management
async function loadAccounts() {
  try {
    const response = await netcupApi.getAccounts()
    accounts.value = response.data
  } catch (error) {
    console.error('Failed to load accounts:', error)
  }
}

function openAccountModal(account = null) {
  editingAccount.value = account
  if (account) {
    Object.assign(accountForm, account)
  } else {
    Object.assign(accountForm, defaultAccountForm)
  }
  accountModalOpen.value = true
}

async function saveAccount() {
  savingAccount.value = true
  try {
    if (editingAccount.value) {
      await netcupApi.updateAccount(editingAccount.value.id, accountForm)
    } else {
      await netcupApi.createAccount(accountForm)
    }
    accountModalOpen.value = false
    await loadAccounts()
    toast.success('账户保存成功')
  } catch (error) {
    console.error('Failed to save account:', error)
    toast.error(error.response?.data?.detail || '保存失败')
  } finally {
    savingAccount.value = false
  }
}

async function deleteAccount(accountId) {
  if (!confirm('确定要删除此账户及其所有服务器吗？')) return

  deletingAccount.value = accountId
  try {
    await netcupApi.deleteAccount(accountId)
    await loadAccounts()
    await loadServers()
    toast.success('账户已删除')
  } catch (error) {
    console.error('Failed to delete account:', error)
    toast.error('删除失败')
  } finally {
    deletingAccount.value = null
  }
}

async function testAccount(accountId) {
  testingAccount.value = accountId
  try {
    const response = await netcupApi.testAccount(accountId)
    toast.success(response.data.message || '连接成功')
  } catch (error) {
    toast.error(error.response?.data?.detail || '连接失败')
  } finally {
    testingAccount.value = null
  }
}

async function fetchAccountServers(accountId) {
  fetchingServers.value = accountId
  try {
    const response = await netcupApi.getAccountServers(accountId)
    scpServers.value = response.data
    selectedAccountId.value = accountId
    scpServersModalOpen.value = true
  } catch (error) {
    toast.error(error.response?.data?.detail || '获取服务器失败')
  } finally {
    fetchingServers.value = null
  }
}

async function selectScpServer(srv) {
  scpServersModalOpen.value = false

  // Ensure downloaders are loaded before opening modal
  if (downloaders.value.length === 0) {
    await loadDownloaders()
  }

  Object.assign(serverForm, {
    ...defaultServerForm,
    account_id: selectedAccountId.value,
    server_id_scp: srv.id,
    name: srv.name,
    ip_address: srv.ip_address
  })
  serverModalOpen.value = true
}

// Server management
async function loadServers() {
  try {
    const response = await netcupApi.getServers()
    servers.value = response.data
  } catch (error) {
    console.error('Failed to load servers:', error)
  }
}

async function loadDownloaders() {
  try {
    const response = await downloadersApi.getAll()
    downloaders.value = response.data || []
    console.log('Loaded downloaders:', downloaders.value)
  } catch (error) {
    console.error('Failed to load downloaders:', error)
    downloaders.value = []
  }
}

async function loadStatus() {
  try {
    const response = await netcupApi.getStatus()
    const statusMap = {}
    for (const s of response.data) {
      statusMap[s.id] = s
    }
    serverStatus.value = statusMap
  } catch (error) {
    console.error('Failed to load status:', error)
  }
}

async function loadStatistics() {
  try {
    const response = await netcupApi.getStatistics()
    serverStats.value = { global: response.data }
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

async function runManualCheck() {
  checking.value = true
  try {
    await netcupApi.check()
    await loadServers()
    await loadStatus()
    toast.success('检查完成')
  } catch (error) {
    console.error('Failed to run check:', error)
    toast.error('检查失败')
  } finally {
    checking.value = false
  }
}

async function testServer(serverId) {
  testingServer.value = serverId
  try {
    const response = await netcupApi.testServer(serverId)
    toast.success(response.data?.message || '连接成功')
  } catch (error) {
    toast.error(error.response?.data?.detail || '连接失败')
  } finally {
    testingServer.value = null
  }
}

async function openServerModal(server = null) {
  // Ensure downloaders are loaded before opening modal
  if (downloaders.value.length === 0) {
    await loadDownloaders()
  }

  editingServer.value = server
  if (server) {
    Object.assign(serverForm, server)
  } else {
    Object.assign(serverForm, defaultServerForm)
    // Default to first account if available
    if (accounts.value.length > 0) {
      serverForm.account_id = accounts.value[0].id
    }
  }
  serverModalOpen.value = true
}

async function saveServer() {
  savingServer.value = true
  try {
    const data = { ...serverForm }
    if (!data.server_id_scp) {
      delete data.server_id_scp
    }
    if (editingServer.value) {
      await netcupApi.updateServer(editingServer.value.id, data)
    } else {
      await netcupApi.createServer(data)
    }
    serverModalOpen.value = false
    await loadServers()
    toast.success('服务器保存成功')
  } catch (error) {
    console.error('Failed to save server:', error)
    toast.error(error.response?.data?.detail || '保存失败')
  } finally {
    savingServer.value = false
  }
}

async function deleteServer(serverId) {
  if (!confirm('确定要删除此服务器吗？')) return

  deletingServer.value = serverId
  try {
    await netcupApi.deleteServer(serverId)
    await loadServers()
    toast.success('服务器已删除')
  } catch (error) {
    console.error('Failed to delete server:', error)
    toast.error('删除失败')
  } finally {
    deletingServer.value = null
  }
}

// Lifecycle
let refreshTimer

onMounted(async () => {
  await Promise.all([
    loadConfig(),
    loadAccounts(),
    loadServers(),
    loadDownloaders(),
    loadStatus(),
    loadStatistics()
  ])

  refreshTimer = setInterval(async () => {
    await loadServers()
    await loadStatus()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>
