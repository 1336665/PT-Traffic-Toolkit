<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl shadow-lg shadow-primary-500/30"
             style="background: var(--gradient-primary)">
          <HomeIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">仪表盘</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">系统运行状态概览</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <div v-if="lastUpdate" class="hidden sm:flex items-center text-xs text-surface-400">
          <ClockIcon class="w-3.5 h-3.5 mr-1" />
          {{ lastUpdate }}
        </div>
        <span class="flex items-center text-sm text-surface-500 dark:text-surface-400 bg-surface-100 dark:bg-surface-800 px-3 py-1.5 rounded-lg">
          <span class="relative flex h-2 w-2 mr-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          实时更新中
        </span>
      </div>
    </div>

    <!-- 统计卡片 - 渐变玻璃风格 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 dark:from-blue-500/20 dark:to-indigo-500/20 border border-blue-200/50 dark:border-blue-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-blue-500/10 dark:bg-blue-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-blue-600/70 dark:text-blue-400/70 uppercase tracking-wide">上传速度</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">
              {{ formatSpeed(stats.total_upload_speed) }}
            </p>
          </div>
          <div class="p-3 rounded-xl bg-blue-500/20 dark:bg-blue-500/30">
            <ArrowUpIcon class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
      </div>

      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 dark:from-emerald-500/20 dark:to-teal-500/20 border border-emerald-200/50 dark:border-emerald-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-emerald-600/70 dark:text-emerald-400/70 uppercase tracking-wide">下载速度</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">
              {{ formatSpeed(stats.total_download_speed) }}
            </p>
          </div>
          <div class="p-3 rounded-xl bg-emerald-500/20 dark:bg-emerald-500/30">
            <ArrowDownIcon class="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
          </div>
        </div>
      </div>

      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-amber-500/10 to-orange-500/10 dark:from-amber-500/20 dark:to-orange-500/20 border border-amber-200/50 dark:border-amber-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-amber-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-amber-500/10 dark:bg-amber-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-amber-600/70 dark:text-amber-400/70 uppercase tracking-wide">今日上传</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">
              {{ formatSize(recentActivity.today_uploaded || 0) }}
            </p>
          </div>
          <div class="p-3 rounded-xl bg-amber-500/20 dark:bg-amber-500/30">
            <ArrowUpIcon class="w-6 h-6 text-amber-600 dark:text-amber-400" />
          </div>
        </div>
      </div>

      <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-500/20 dark:to-pink-500/20 border border-purple-200/50 dark:border-purple-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-purple-500/10 transition-all duration-300">
        <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-purple-500/10 dark:bg-purple-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
        <div class="relative flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-purple-600/70 dark:text-purple-400/70 uppercase tracking-wide">今日下载</p>
            <p class="text-2xl lg:text-3xl font-bold text-surface-900 dark:text-white mt-1 tabular-nums">
              {{ formatSize(recentActivity.today_downloaded || 0) }}
            </p>
          </div>
          <div class="p-3 rounded-xl bg-purple-500/20 dark:bg-purple-500/30">
            <ArrowDownIcon class="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <router-link
        to="/rss"
        class="flex items-center space-x-3 p-3 rounded-xl bg-white/50 dark:bg-surface-800/50 border border-surface-200/50 dark:border-surface-700/50 hover:border-orange-300 dark:hover:border-orange-500/50 hover:bg-orange-50/50 dark:hover:bg-orange-900/10 transition-all duration-200 group cursor-pointer"
      >
        <div class="p-2 rounded-lg bg-orange-100 dark:bg-orange-900/30 group-hover:bg-orange-200 dark:group-hover:bg-orange-900/50 transition-colors">
          <RssIcon class="w-5 h-5 text-orange-600 dark:text-orange-400" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-surface-900 dark:text-white truncate">RSS 订阅</p>
          <p class="text-xs text-surface-500 dark:text-surface-400">{{ servicesStatus.rss?.enabled_feeds || 0 }} 个活跃</p>
        </div>
      </router-link>

      <router-link
        to="/delete-rules"
        class="flex items-center space-x-3 p-3 rounded-xl bg-white/50 dark:bg-surface-800/50 border border-surface-200/50 dark:border-surface-700/50 hover:border-red-300 dark:hover:border-red-500/50 hover:bg-red-50/50 dark:hover:bg-red-900/10 transition-all duration-200 group cursor-pointer"
      >
        <div class="p-2 rounded-lg bg-red-100 dark:bg-red-900/30 group-hover:bg-red-200 dark:group-hover:bg-red-900/50 transition-colors">
          <TrashIcon class="w-5 h-5 text-red-600 dark:text-red-400" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-surface-900 dark:text-white truncate">删种规则</p>
          <p class="text-xs text-surface-500 dark:text-surface-400">{{ servicesStatus.delete?.enabled_rules || 0 }} 条规则</p>
        </div>
      </router-link>

      <router-link
        to="/speed-limit"
        class="flex items-center space-x-3 p-3 rounded-xl bg-white/50 dark:bg-surface-800/50 border border-surface-200/50 dark:border-surface-700/50 hover:border-amber-300 dark:hover:border-amber-500/50 hover:bg-amber-50/50 dark:hover:bg-amber-900/10 transition-all duration-200 group cursor-pointer"
      >
        <div class="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30 group-hover:bg-amber-200 dark:group-hover:bg-amber-900/50 transition-colors">
          <BoltIcon class="w-5 h-5 text-amber-600 dark:text-amber-400" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-surface-900 dark:text-white truncate">动态限速</p>
          <p class="text-xs text-surface-500 dark:text-surface-400">{{ servicesStatus.speed_limit?.enabled ? '运行中' : '已停止' }}</p>
        </div>
      </router-link>

      <router-link
        to="/statistics"
        class="flex items-center space-x-3 p-3 rounded-xl bg-white/50 dark:bg-surface-800/50 border border-surface-200/50 dark:border-surface-700/50 hover:border-indigo-300 dark:hover:border-indigo-500/50 hover:bg-indigo-50/50 dark:hover:bg-indigo-900/10 transition-all duration-200 group cursor-pointer"
      >
        <div class="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 group-hover:bg-indigo-200 dark:group-hover:bg-indigo-900/50 transition-colors">
          <ChartBarIcon class="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-surface-900 dark:text-white truncate">数据统计</p>
          <p class="text-xs text-surface-500 dark:text-surface-400">查看详情</p>
        </div>
      </router-link>
    </div>

    <!-- 图表和下载器状态 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
      <!-- 速度图表 -->
      <Card>
        <template #header>
          <div class="flex items-center justify-between w-full">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                <ChartAreaIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 class="font-semibold text-surface-900 dark:text-white">速度历史</h3>
                <p class="text-xs text-surface-500 dark:text-surface-400">实时速度曲线图</p>
              </div>
            </div>
            <div class="flex rounded-lg bg-surface-100 dark:bg-surface-700 p-0.5">
              <button
                v-for="p in ['1h', '6h', '24h']"
                :key="p"
                @click="speedChartPeriod = p"
                class="px-2.5 py-1 text-xs font-medium rounded-md transition-all duration-200"
                :class="speedChartPeriod === p
                  ? 'bg-white dark:bg-surface-600 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-300'"
              >
                {{ p }}
              </button>
            </div>
          </div>
        </template>
        <div class="h-64">
          <v-chart :option="speedChartOption" autoresize />
        </div>
      </Card>

      <!-- 下载器状态 -->
      <Card>
        <template #header>
          <div class="flex items-center justify-between w-full">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-900/30">
                <ServerStackIcon class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <h3 class="font-semibold text-surface-900 dark:text-white">下载器状态</h3>
                <p class="text-xs text-surface-500 dark:text-surface-400">已配置 {{ downloadersStatus.length }} 个下载器</p>
              </div>
            </div>
            <router-link to="/downloaders" class="text-xs text-primary-600 dark:text-primary-400 hover:underline">
              管理
            </router-link>
          </div>
        </template>
        <div v-if="downloadersStatus.length === 0" class="empty-state py-8">
          <div class="empty-state-icon !w-12 !h-12">
            <ServerStackIcon class="w-full h-full" />
          </div>
          <p class="empty-state-title text-base">暂无下载器</p>
          <p class="empty-state-description">请先添加下载器配置</p>
          <router-link to="/downloaders" class="mt-3 inline-flex items-center text-sm text-primary-600 dark:text-primary-400 hover:underline">
            <PlusIcon class="w-4 h-4 mr-1" />
            添加下载器
          </router-link>
        </div>
        <div v-else class="space-y-2 h-64 overflow-y-auto pr-1">
          <div
            v-for="dl in downloadersStatus"
            :key="dl.id"
            class="relative overflow-hidden p-3 rounded-xl border transition-all duration-200 hover:shadow-md group"
            :class="dl.online
              ? 'bg-gradient-to-r from-emerald-50/50 to-teal-50/30 dark:from-emerald-900/20 dark:to-teal-900/10 border-emerald-200/50 dark:border-emerald-500/20'
              : 'bg-gradient-to-r from-red-50/50 to-rose-50/30 dark:from-red-900/20 dark:to-rose-900/10 border-red-200/50 dark:border-red-500/20'"
          >
            <div class="flex items-center gap-3">
              <!-- 图标 -->
              <div
                class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm"
                :class="dl.online
                  ? 'bg-gradient-to-br from-emerald-500 to-teal-500 shadow-emerald-500/20'
                  : 'bg-gradient-to-br from-red-500 to-rose-500 shadow-red-500/20'"
              >
                <ServerIcon class="w-4 h-4 text-white" />
              </div>

              <!-- 名称和状态 -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-sm text-surface-900 dark:text-white truncate">{{ dl.name }}</span>
                  <span class="text-[10px] text-surface-500 dark:text-surface-400 bg-surface-100 dark:bg-surface-800 px-1.5 py-0.5 rounded flex-shrink-0">{{ dl.type }}</span>
                  <span
                    class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium flex-shrink-0"
                    :class="dl.online
                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/50 dark:text-red-400'"
                  >
                    <span class="w-1.5 h-1.5 rounded-full" :class="dl.online ? 'bg-emerald-500' : 'bg-red-500'"></span>
                    {{ dl.online ? '在线' : '离线' }}
                  </span>
                </div>
                <!-- 在线状态：显示速度和磁盘 -->
                <div v-if="dl.online" class="flex items-center gap-3 mt-1 text-xs">
                  <span class="inline-flex items-center gap-1 text-blue-600 dark:text-blue-400">
                    <ArrowUpIcon class="w-3 h-3" />
                    <span class="font-mono tabular-nums">{{ formatSpeed(dl.upload_speed) }}</span>
                  </span>
                  <span class="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                    <ArrowDownIcon class="w-3 h-3" />
                    <span class="font-mono tabular-nums">{{ formatSpeed(dl.download_speed) }}</span>
                  </span>
                  <span class="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
                    <BoltIcon class="w-3 h-3" />
                    <span class="tabular-nums">{{ dl.total_torrents || 0 }}</span>
                  </span>
                </div>
                <!-- 离线状态 -->
                <div v-else class="text-xs text-red-500 dark:text-red-400 mt-1">
                  无法连接
                </div>
              </div>

              <!-- 磁盘剩余空间指示器 -->
              <div v-if="dl.online" class="flex-shrink-0 flex flex-col items-center gap-0.5">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                     :class="getFreeSpaceBgClass(dl.free_space)">
                  <CircleStackIcon class="w-4 h-4" :class="getFreeSpaceTextClass(dl.free_space)" />
                </div>
                <span class="text-[9px] font-medium tabular-nums" :class="getFreeSpaceTextClass(dl.free_space)">
                  {{ formatCompactSize(dl.free_space || 0) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- 服务状态和活动统计 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 服务状态 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-xl bg-purple-100 dark:bg-purple-900/30">
              <CpuChipIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">服务状态</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">自动化服务运行情况</p>
            </div>
          </div>
        </template>
        <div class="space-y-3">
          <div class="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-800/30 rounded-xl hover:bg-surface-100 dark:hover:bg-surface-700/30 transition-colors">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-xl bg-amber-100 dark:bg-amber-900/30">
                <BoltIcon class="w-4 h-4 text-amber-600 dark:text-amber-400" />
              </div>
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">动态限速</span>
            </div>
            <div class="flex items-center space-x-2">
              <span v-if="servicesStatus.speed_limit?.target_speed" class="text-xs text-surface-500 font-mono">
                {{ formatSpeed(servicesStatus.speed_limit.target_speed) }}
              </span>
              <span
                class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="servicesStatus.speed_limit?.enabled
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  : 'bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-400'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="servicesStatus.speed_limit?.enabled ? 'bg-emerald-500 animate-pulse' : 'bg-surface-400'"></span>
                <span>{{ servicesStatus.speed_limit?.enabled ? '运行中' : '已停止' }}</span>
              </span>
            </div>
          </div>
          <div class="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-800/30 rounded-xl hover:bg-surface-100 dark:hover:bg-surface-700/30 transition-colors">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-xl bg-pink-100 dark:bg-pink-900/30">
                <SparklesIcon class="w-4 h-4 text-pink-600 dark:text-pink-400" />
              </div>
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">U2 追魔</span>
            </div>
            <span
              class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium"
              :class="servicesStatus.u2_magic?.enabled
                ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                : 'bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-400'"
            >
              <span class="w-1.5 h-1.5 rounded-full" :class="servicesStatus.u2_magic?.enabled ? 'bg-emerald-500 animate-pulse' : 'bg-surface-400'"></span>
              <span>{{ servicesStatus.u2_magic?.enabled ? '运行中' : '已停止' }}</span>
            </span>
          </div>
          <div class="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-800/30 rounded-xl hover:bg-surface-100 dark:hover:bg-surface-700/30 transition-colors">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-xl bg-orange-100 dark:bg-orange-900/30">
                <RssIcon class="w-4 h-4 text-orange-600 dark:text-orange-400" />
              </div>
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">RSS 订阅</span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-xs text-surface-500">{{ servicesStatus.rss?.enabled_feeds || 0 }} 个活跃</span>
              <span
                class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="servicesStatus.rss?.enabled_feeds > 0
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  : 'bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-400'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="servicesStatus.rss?.enabled_feeds > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-surface-400'"></span>
                <span>{{ servicesStatus.rss?.enabled_feeds > 0 ? '运行中' : '已停止' }}</span>
              </span>
            </div>
          </div>
          <div class="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-800/30 rounded-xl hover:bg-surface-100 dark:hover:bg-surface-700/30 transition-colors">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-xl bg-red-100 dark:bg-red-900/30">
                <TrashIcon class="w-4 h-4 text-red-600 dark:text-red-400" />
              </div>
              <span class="text-sm font-medium text-surface-700 dark:text-surface-300">删种规则</span>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-xs text-surface-500">{{ servicesStatus.delete?.enabled_rules || 0 }} 条规则</span>
              <span
                class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium"
                :class="servicesStatus.delete?.enabled_rules > 0
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  : 'bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-400'"
              >
                <span class="w-1.5 h-1.5 rounded-full" :class="servicesStatus.delete?.enabled_rules > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-surface-400'"></span>
                <span>{{ servicesStatus.delete?.enabled_rules > 0 ? '运行中' : '已停止' }}</span>
              </span>
            </div>
          </div>
        </div>
      </Card>

      <!-- 近期活动统计 -->
      <Card class="lg:col-span-2">
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-xl bg-cyan-100 dark:bg-cyan-900/30">
              <ChartPieIcon class="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">流量统计</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">实时数据与24小时活动</p>
            </div>
          </div>
        </template>
        <div class="space-y-4">
          <!-- 第一排：总上传、总下载、分享率 -->
          <div class="grid grid-cols-3 gap-4">
            <!-- 总上传 -->
            <div class="relative overflow-hidden p-5 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-blue-500/10 dark:from-cyan-500/20 dark:to-blue-500/20 border border-cyan-200/50 dark:border-cyan-500/20 group hover:shadow-lg hover:shadow-cyan-500/10 transition-all duration-300">
              <div class="absolute -right-4 -top-4 w-16 h-16 rounded-full bg-cyan-500/10 dark:bg-cyan-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
              <div class="relative z-10">
                <div class="text-2xl font-bold text-cyan-600 dark:text-cyan-400 tabular-nums">
                  {{ formatSize(stats.total_uploaded || 0) }}
                </div>
                <div class="text-xs text-cyan-500/80 dark:text-cyan-400/60 mt-0.5">
                  <span class="inline-flex items-center">
                    <ArrowUpIcon class="w-3 h-3 mr-0.5" />
                    {{ formatSpeed(stats.total_upload_speed || 0) }}
                  </span>
                </div>
                <div class="text-sm text-cyan-600/70 dark:text-cyan-400/70 mt-1 font-medium">总上传</div>
              </div>
              <ArrowUpIcon class="absolute -right-2 -bottom-2 w-16 h-16 text-cyan-200/50 dark:text-cyan-800/30" />
            </div>
            <!-- 总下载 -->
            <div class="relative overflow-hidden p-5 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-teal-500/10 dark:from-emerald-500/20 dark:to-teal-500/20 border border-emerald-200/50 dark:border-emerald-500/20 group hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-300">
              <div class="absolute -right-4 -top-4 w-16 h-16 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
              <div class="relative z-10">
                <div class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 tabular-nums">
                  {{ formatSize(stats.total_downloaded || 0) }}
                </div>
                <div class="text-xs text-emerald-500/80 dark:text-emerald-400/60 mt-0.5">
                  <span class="inline-flex items-center">
                    <ArrowDownIcon class="w-3 h-3 mr-0.5" />
                    {{ formatSpeed(stats.total_download_speed || 0) }}
                  </span>
                </div>
                <div class="text-sm text-emerald-600/70 dark:text-emerald-400/70 mt-1 font-medium">总下载</div>
              </div>
              <ArrowDownIcon class="absolute -right-2 -bottom-2 w-16 h-16 text-emerald-200/50 dark:text-emerald-800/30" />
            </div>
            <!-- 分享率 -->
            <div class="relative overflow-hidden p-5 rounded-2xl bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 dark:from-violet-500/20 dark:to-fuchsia-500/20 border border-violet-200/50 dark:border-violet-500/20 group hover:shadow-lg hover:shadow-violet-500/10 transition-all duration-300">
              <div class="absolute -right-4 -top-4 w-16 h-16 rounded-full bg-violet-500/10 dark:bg-violet-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
              <div class="relative z-10">
                <div class="text-2xl font-bold text-violet-600 dark:text-violet-400 tabular-nums">
                  {{ totalShareRatio }}
                </div>
                <div class="text-xs text-violet-500/80 dark:text-violet-400/60 mt-0.5">
                  {{ stats.total_torrents || 0 }} 种子
                </div>
                <div class="text-sm text-violet-600/70 dark:text-violet-400/70 mt-1 font-medium">分享率</div>
              </div>
              <ChartBarIcon class="absolute -right-2 -bottom-2 w-16 h-16 text-violet-200/50 dark:text-violet-800/30" />
            </div>
          </div>
          <!-- 第二排：原有的24小时统计 -->
          <div class="grid grid-cols-3 gap-4">
            <div class="relative overflow-hidden p-5 rounded-2xl bg-gradient-to-br from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20 border border-blue-200/50 dark:border-blue-500/20 group hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300">
              <div class="absolute -right-4 -top-4 w-16 h-16 rounded-full bg-blue-500/10 dark:bg-blue-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
              <div class="relative z-10">
                <div class="text-3xl font-bold text-blue-600 dark:text-blue-400 tabular-nums">
                  <AnimatedNumber :value="recentActivity.rss_downloads || 0" />
                </div>
                <div class="text-sm text-blue-600/70 dark:text-blue-400/70 mt-1 font-medium">RSS 下载</div>
              </div>
              <RssIcon class="absolute -right-2 -bottom-2 w-16 h-16 text-blue-200/50 dark:text-blue-800/30" />
            </div>
            <div class="relative overflow-hidden p-5 rounded-2xl bg-gradient-to-br from-red-500/10 to-rose-500/10 dark:from-red-500/20 dark:to-rose-500/20 border border-red-200/50 dark:border-red-500/20 group hover:shadow-lg hover:shadow-red-500/10 transition-all duration-300">
              <div class="absolute -right-4 -top-4 w-16 h-16 rounded-full bg-red-500/10 dark:bg-red-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
              <div class="relative z-10">
                <div class="text-3xl font-bold text-red-600 dark:text-red-400 tabular-nums">
                  <AnimatedNumber :value="recentActivity.deleted_torrents || 0" />
                </div>
                <div class="text-sm text-red-600/70 dark:text-red-400/70 mt-1 font-medium">已删除</div>
              </div>
              <TrashIcon class="absolute -right-2 -bottom-2 w-16 h-16 text-red-200/50 dark:text-red-800/30" />
            </div>
            <div class="relative overflow-hidden p-5 rounded-2xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-500/20 dark:to-pink-500/20 border border-purple-200/50 dark:border-purple-500/20 group hover:shadow-lg hover:shadow-purple-500/10 transition-all duration-300">
              <div class="absolute -right-4 -top-4 w-16 h-16 rounded-full bg-purple-500/10 dark:bg-purple-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
              <div class="relative z-10">
                <div class="text-3xl font-bold text-purple-600 dark:text-purple-400 tabular-nums">
                  <AnimatedNumber :value="recentActivity.magic_downloads || 0" />
                </div>
                <div class="text-sm text-purple-600/70 dark:text-purple-400/70 mt-1 font-medium">追魔抓取</div>
              </div>
              <SparklesIcon class="absolute -right-2 -bottom-2 w-16 h-16 text-purple-200/50 dark:text-purple-800/30" />
            </div>
          </div>
        </div>
      </Card>
    </div>

    <!-- 活动时间线 -->
    <Card>
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-xl bg-primary-100 dark:bg-primary-900/30">
              <ClockIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">活动时间线</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">最近系统活动记录</p>
            </div>
          </div>
          <Button variant="secondary" size="sm" @click="dashboardStore.fetchTimeline()">
            <ArrowPathIcon class="w-4 h-4" />
            刷新
          </Button>
        </div>
      </template>
      <div v-if="timeline.length === 0" class="empty-state py-8">
        <div class="empty-state-icon !w-12 !h-12">
          <ClockIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title text-base">暂无活动记录</p>
        <p class="empty-state-description">系统活动将会显示在这里</p>
      </div>
      <div v-else class="space-y-1">
        <div
          v-for="(item, index) in timeline.slice(0, 10)"
          :key="`${item.type}-${item.id}`"
          class="flex items-start space-x-4 p-3 rounded-xl hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors"
        >
          <div class="relative">
            <div
              class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              :class="getTimelineIconClass(item.type)"
            >
              <component :is="getTimelineIcon(item.type)" class="w-5 h-5" />
            </div>
            <div
              v-if="index < timeline.slice(0, 10).length - 1"
              class="absolute top-12 left-1/2 -translate-x-1/2 w-0.5 h-6 bg-surface-200 dark:bg-surface-700"
            ></div>
          </div>
          <div class="flex-1 min-w-0 pt-1">
            <p class="text-sm font-medium text-surface-900 dark:text-white">{{ item.title }}</p>
            <p class="text-xs text-surface-500 dark:text-surface-400 mt-0.5 line-clamp-1">{{ item.description }}</p>
            <p class="text-xs text-surface-400 dark:text-surface-500 mt-1 flex items-center">
              <ClockIcon class="w-3 h-3 mr-1" />
              {{ formatTime(item.timestamp) }}
            </p>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, h } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

import { useDashboardStore } from '@/stores/dashboard'
import { useSettingsStore } from '@/stores/settings'
import { formatSpeed, formatSize, formatRelativeTime } from '@/utils/format'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import {
  HomeIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  BoltIcon,
  CircleStackIcon,
  ChartBarIcon,
  ServerStackIcon,
  ServerIcon,
  CpuChipIcon,
  ChartPieIcon,
  ClockIcon,
  ArrowPathIcon,
  RssIcon,
  TrashIcon,
  SparklesIcon,
  PlusIcon,
  HeartIcon,
} from '@heroicons/vue/24/outline'

// Custom chart icon
const ChartAreaIcon = {
  render() {
    return h('svg', {
      xmlns: 'http://www.w3.org/2000/svg',
      fill: 'none',
      viewBox: '0 0 24 24',
      'stroke-width': '1.5',
      stroke: 'currentColor',
      class: 'w-5 h-5'
    }, [
      h('path', {
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
        d: 'M3 13.5l6-6 4 4 8-8M3 13.5V21h18V7.5'
      })
    ])
  }
}

// Animated number component
const AnimatedNumber = {
  props: {
    value: { type: Number, default: 0 },
    duration: { type: Number, default: 800 }
  },
  setup(props) {
    const displayValue = ref(0)
    let animation = null

    const animate = (target) => {
      if (animation) cancelAnimationFrame(animation)
      const start = displayValue.value
      const startTime = performance.now()

      const step = (currentTime) => {
        const elapsed = currentTime - startTime
        const progress = Math.min(elapsed / props.duration, 1)
        const easeProgress = 1 - Math.pow(1 - progress, 3)
        displayValue.value = Math.round(start + (target - start) * easeProgress)

        if (progress < 1) {
          animation = requestAnimationFrame(step)
        }
      }
      animation = requestAnimationFrame(step)
    }

    watch(() => props.value, (newVal) => animate(newVal), { immediate: true })
    onUnmounted(() => animation && cancelAnimationFrame(animation))

    return () => h('span', {}, displayValue.value.toLocaleString())
  }
}

// ECharts setup
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const dashboardStore = useDashboardStore()
const settingsStore = useSettingsStore()

const speedChartPeriod = ref('1h')
const speedHistory = ref([])
const lastUpdate = ref('')

// 速度历史最大存储点数 (每5秒一个点，24小时 = 17280个点，但我们限制为2000个)
const MAX_SPEED_HISTORY_POINTS = 2000

// 根据时间段计算显示的数据点数量
const speedChartDataPoints = computed(() => {
  // 每5秒记录一个点
  const pointsPerPeriod = {
    '1h': 720,   // 1小时 = 720个点 (每5秒)
    '6h': 720,   // 6小时取样720个点
    '24h': 720,  // 24小时取样720个点
  }
  return pointsPerPeriod[speedChartPeriod.value] || 720
})

// 根据时间段过滤和取样显示的历史数据
const filteredSpeedHistory = computed(() => {
  const history = speedHistory.value
  if (history.length === 0) return []

  // 根据时间段决定取多少秒的数据
  const secondsPerPeriod = {
    '1h': 3600,
    '6h': 21600,
    '24h': 86400,
  }
  const targetSeconds = secondsPerPeriod[speedChartPeriod.value] || 3600
  const targetPoints = Math.min(targetSeconds / 5, history.length) // 每5秒一个点

  if (history.length <= targetPoints) {
    return history
  }

  // 取样：从历史数据中均匀取点
  const step = Math.ceil(history.length / targetPoints)
  const sampled = []
  for (let i = history.length - 1; i >= 0 && sampled.length < targetPoints; i -= step) {
    sampled.unshift(history[i])
  }
  return sampled
})

// Computed
const stats = computed(() => dashboardStore.stats)
const timeline = computed(() => dashboardStore.timeline)
const downloadersStatus = computed(() => dashboardStore.downloadersStatus)
const servicesStatus = computed(() => dashboardStore.servicesStatus)
const recentActivity = computed(() => dashboardStore.recentActivity)

// 实时分享率计算（使用总上传/下载量）
const totalShareRatio = computed(() => {
  const uploaded = stats.value?.total_uploaded || 0
  const downloaded = stats.value?.total_downloaded || 1
  if (downloaded === 0) return uploaded > 0 ? '∞' : '0.00'
  return (uploaded / downloaded).toFixed(2)
})

const speedChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: settingsStore.darkMode ? '#1e293b' : '#ffffff',
    borderColor: settingsStore.darkMode ? '#334155' : '#e2e8f0',
    textStyle: {
      color: settingsStore.darkMode ? '#f1f5f9' : '#0f172a'
    },
    formatter: (params) => {
      let result = `<div class="font-medium">${params[0].axisValue}</div>`
      params.forEach(param => {
        result += `<div class="flex items-center justify-between gap-4 mt-1">
          <span>${param.marker} ${param.seriesName}</span>
          <span class="font-medium">${formatSpeed(param.value)}</span>
        </div>`
      })
      return result
    }
  },
  legend: {
    data: ['上传', '下载'],
    textStyle: {
      color: settingsStore.darkMode ? '#94a3b8' : '#64748b'
    },
    icon: 'roundRect',
    itemWidth: 12,
    itemHeight: 12,
    itemGap: 20
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '15%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: filteredSpeedHistory.value.map(h => h.time),
    axisLine: {
      lineStyle: {
        color: settingsStore.darkMode ? '#475569' : '#e2e8f0'
      }
    },
    axisLabel: {
      color: settingsStore.darkMode ? '#94a3b8' : '#64748b',
      fontSize: 11,
      // 根据数据点数量动态调整显示间隔
      interval: Math.max(0, Math.floor(filteredSpeedHistory.value.length / 8) - 1)
    }
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: (value) => formatSpeed(value),
      color: settingsStore.darkMode ? '#94a3b8' : '#64748b',
      fontSize: 11
    },
    splitLine: {
      lineStyle: {
        color: settingsStore.darkMode ? '#334155' : '#f1f5f9',
        type: 'dashed'
      }
    }
  },
  series: [
    {
      name: '上传',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: filteredSpeedHistory.value.map(h => h.upload),
      itemStyle: { color: '#6366f1' },
      lineStyle: { width: 2.5 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0)' }
          ]
        }
      }
    },
    {
      name: '下载',
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: filteredSpeedHistory.value.map(h => h.download),
      itemStyle: { color: '#10b981' },
      lineStyle: { width: 2.5 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0)' }
          ]
        }
      }
    }
  ]
}))

// Methods
function formatTime(timestamp) {
  return formatRelativeTime(timestamp)
}

function getTimelineIcon(type) {
  const icons = {
    rss: RssIcon,
    delete: TrashIcon,
    magic: SparklesIcon,
  }
  return icons[type] || RssIcon
}

function getTimelineIconClass(type) {
  const classes = {
    rss: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    delete: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    magic: 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
  }
  return classes[type] || classes.rss
}

// 基于剩余空间的颜色类
function getFreeSpaceBgClass(freeSpace) {
  const gb = (freeSpace || 0) / (1024 * 1024 * 1024)
  if (gb < 50) return 'bg-red-100 dark:bg-red-900/40'
  if (gb < 100) return 'bg-amber-100 dark:bg-amber-900/40'
  return 'bg-emerald-100 dark:bg-emerald-900/40'
}

function getFreeSpaceTextClass(freeSpace) {
  const gb = (freeSpace || 0) / (1024 * 1024 * 1024)
  if (gb < 50) return 'text-red-600 dark:text-red-400'
  if (gb < 100) return 'text-amber-600 dark:text-amber-400'
  return 'text-emerald-600 dark:text-emerald-400'
}

// 紧凑格式化大小
function formatCompactSize(bytes) {
  if (!bytes || bytes === 0) return '0'
  const units = ['B', 'K', 'M', 'G', 'T']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const value = bytes / Math.pow(k, i)
  return value >= 100 ? Math.round(value) + units[i] : value.toFixed(1).replace(/\.0$/, '') + units[i]
}

function updateSpeedHistory() {
  const now = dayjs().format('HH:mm:ss')
  speedHistory.value.push({
    time: now,
    upload: stats.value.total_upload_speed,
    download: stats.value.total_download_speed,
  })
  // 限制最大存储点数
  if (speedHistory.value.length > MAX_SPEED_HISTORY_POINTS) {
    speedHistory.value.shift()
  }
  lastUpdate.value = dayjs().format('HH:mm:ss')
}

// Lifecycle
let refreshInterval
let dashboardRefreshing = false

async function refreshDashboard() {
  if (document.hidden || dashboardRefreshing) return
  dashboardRefreshing = true
  try {
    await Promise.all([
      dashboardStore.fetchStats(),
      dashboardStore.fetchDownloadersStatus(),
      dashboardStore.fetchRecentActivity(),
    ])
    updateSpeedHistory()
  } finally {
    dashboardRefreshing = false
  }
}

function handleDashboardVisibilityChange() {
  if (!document.hidden) refreshDashboard()
}


onMounted(async () => {
  await dashboardStore.fetchAll()
  updateSpeedHistory()

  // Refresh stats, downloader status and recent activity every 5 seconds
  refreshInterval = setInterval(refreshDashboard, 5000)
  document.addEventListener('visibilitychange', handleDashboardVisibilityChange)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  document.removeEventListener('visibilitychange', handleDashboardVisibilityChange)
})
</script>

<style scoped>
/* Stagger animation for cards */
.grid > * {
  animation: fadeInUp 0.5s ease-out both;
}

.grid > *:nth-child(1) { animation-delay: 0ms; }
.grid > *:nth-child(2) { animation-delay: 50ms; }
.grid > *:nth-child(3) { animation-delay: 100ms; }
.grid > *:nth-child(4) { animation-delay: 150ms; }
.grid > *:nth-child(5) { animation-delay: 200ms; }
.grid > *:nth-child(6) { animation-delay: 250ms; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Pulse animation for live indicator */
@keyframes pulse-ring {
  0% {
    transform: scale(1);
    opacity: 0.75;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

/* Floating effect for icon hover */
.group:hover .p-3 {
  animation: float 1s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

/* Enhanced card hover glow */
.group:hover {
  transform: translateY(-2px);
}

/* Shimmer effect for loading states */
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* Number animation enhancement */
.tabular-nums {
  font-variant-numeric: tabular-nums;
  transition: color 0.3s ease;
}
</style>
