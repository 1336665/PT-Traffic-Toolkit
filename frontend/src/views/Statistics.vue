<template>
  <div class="space-y-6">
    <!-- 页头 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl shadow-lg shadow-indigo-500/30"
             style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)">
          <ChartBarIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">数据统计</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">查看详细的上传下载和刷流统计数据</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <div v-if="lastRefresh" class="text-xs text-surface-400 hidden sm:block">
          <ClockIcon class="w-3.5 h-3.5 inline mr-1" />
          {{ lastRefresh }}
        </div>
        <Button variant="secondary" size="sm" @click="refreshData" :loading="loading">
          <ArrowPathIcon class="w-4 h-4" :class="{ 'animate-spin': loading }" />
          刷新
        </Button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && !overview" class="flex flex-col items-center justify-center py-20">
      <div class="relative">
        <div class="w-16 h-16 rounded-full border-4 border-primary-200 dark:border-primary-800"></div>
        <div class="absolute top-0 left-0 w-16 h-16 rounded-full border-4 border-transparent border-t-primary-600 animate-spin"></div>
      </div>
      <p class="mt-4 text-surface-500 dark:text-surface-400">加载统计数据...</p>
    </div>

    <template v-else>
      <!-- 核心指标卡片 - 渐变玻璃风格 -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- 种子数 -->
        <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20 border border-blue-200/50 dark:border-blue-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300">
          <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-blue-500/10 dark:bg-blue-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative">
            <div class="flex items-center justify-between">
              <div class="p-2 rounded-xl bg-blue-500/20 dark:bg-blue-500/30">
                <ServerStackIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div class="flex items-center space-x-1">
                <span class="w-2 h-2 rounded-full animate-pulse" :class="overview?.online_downloaders > 0 ? 'bg-green-500' : 'bg-red-500'"></span>
                <span class="text-xs font-medium text-surface-500 dark:text-surface-400">
                  {{ overview?.online_downloaders || 0 }}/{{ overview?.total_downloaders || 0 }}
                </span>
              </div>
            </div>
            <div class="mt-3">
              <p class="text-3xl font-bold text-surface-900 dark:text-white tabular-nums">
                <AnimatedNumber :value="overview?.total_torrents || 0" />
              </p>
              <p class="text-sm text-surface-500 dark:text-surface-400 mt-0.5">总种子数</p>
            </div>
          </div>
        </div>

        <!-- 数据总量 -->
        <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 dark:from-emerald-500/20 dark:to-teal-500/20 border border-emerald-200/50 dark:border-emerald-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-300">
          <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative">
            <div class="flex items-center justify-between">
              <div class="p-2 rounded-xl bg-emerald-500/20 dark:bg-emerald-500/30">
                <CircleStackIcon class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <span class="text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                剩余 {{ formatSize(overview?.total_free_space || 0) }}
              </span>
            </div>
            <div class="mt-3">
              <p class="text-3xl font-bold text-surface-900 dark:text-white tabular-nums">
                {{ formatSize(overview?.total_size || 0) }}
              </p>
              <p class="text-sm text-surface-500 dark:text-surface-400 mt-0.5">数据总量</p>
            </div>
          </div>
        </div>

        <!-- 总上传 -->
        <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 dark:from-cyan-500/20 dark:to-blue-500/20 border border-cyan-200/50 dark:border-cyan-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-cyan-500/10 transition-all duration-300">
          <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-cyan-500/10 dark:bg-cyan-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative">
            <div class="flex items-center justify-between">
              <div class="p-2 rounded-xl bg-cyan-500/20 dark:bg-cyan-500/30">
                <ArrowUpTrayIcon class="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
              </div>
              <div class="flex items-center space-x-1 text-cyan-600 dark:text-cyan-400">
                <ArrowTrendingUpIcon class="w-3.5 h-3.5" />
                <span class="text-xs font-medium">{{ formatSpeed(overview?.current_upload_speed || 0) }}</span>
              </div>
            </div>
            <div class="mt-3">
              <p class="text-3xl font-bold text-surface-900 dark:text-white tabular-nums">
                {{ formatSize(overview?.total_uploaded || 0) }}
              </p>
              <p class="text-sm text-surface-500 dark:text-surface-400 mt-0.5">总上传量</p>
            </div>
          </div>
        </div>

        <!-- 总下载 -->
        <div class="relative overflow-hidden rounded-2xl p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 dark:from-purple-500/20 dark:to-pink-500/20 border border-purple-200/50 dark:border-purple-500/20 backdrop-blur-sm group hover:shadow-lg hover:shadow-purple-500/10 transition-all duration-300">
          <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-purple-500/10 dark:bg-purple-500/20 blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative">
            <div class="flex items-center justify-between">
              <div class="p-2 rounded-xl bg-purple-500/20 dark:bg-purple-500/30">
                <ArrowDownTrayIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div class="flex items-center space-x-1 text-purple-600 dark:text-purple-400">
                <ArrowTrendingDownIcon class="w-3.5 h-3.5" />
                <span class="text-xs font-medium">{{ formatSpeed(overview?.current_download_speed || 0) }}</span>
              </div>
            </div>
            <div class="mt-3">
              <p class="text-3xl font-bold text-surface-900 dark:text-white tabular-nums">
                {{ formatSize(overview?.total_downloaded || 0) }}
              </p>
              <p class="text-sm text-surface-500 dark:text-surface-400 mt-0.5">总下载量</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 分享率和效率统计 - 带圆环 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <!-- 分享率圆环 -->
        <div class="relative overflow-hidden rounded-2xl p-4 bg-white/50 dark:bg-surface-800/50 border border-surface-200/50 dark:border-surface-700/50 backdrop-blur-sm">
          <div class="flex flex-col items-center">
            <div class="relative w-20 h-20">
              <svg class="w-full h-full -rotate-90">
                <circle
                  cx="40" cy="40" r="35"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="6"
                  class="text-surface-200 dark:text-surface-700"
                />
                <circle
                  cx="40" cy="40" r="35"
                  fill="none"
                  stroke="url(#ratioGradient)"
                  stroke-width="6"
                  stroke-linecap="round"
                  :stroke-dasharray="`${ratioProgress * 2.2} 220`"
                  class="transition-all duration-1000 ease-out"
                />
                <defs>
                  <linearGradient id="ratioGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#10b981" />
                    <stop offset="100%" stop-color="#34d399" />
                  </linearGradient>
                </defs>
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <span class="text-lg font-bold text-surface-900 dark:text-white">{{ overallRatio }}</span>
              </div>
            </div>
            <p class="text-sm text-surface-500 dark:text-surface-400 mt-2">总分享率</p>
          </div>
        </div>

        <!-- 日均上传 -->
        <div class="relative overflow-hidden rounded-2xl p-4 bg-white/50 dark:bg-surface-800/50 border border-surface-200/50 dark:border-surface-700/50 backdrop-blur-sm">
          <div class="flex flex-col items-center justify-center h-full">
            <div class="p-2.5 rounded-xl bg-amber-500/10 dark:bg-amber-500/20 mb-2">
              <FireIcon class="w-6 h-6 text-amber-500" />
            </div>
            <p class="text-xl font-bold text-amber-600 dark:text-amber-400">
              {{ formatSize(avgDailyUpload) }}
            </p>
            <p class="text-sm text-surface-500 dark:text-surface-400 mt-1">日均上传</p>
          </div>
        </div>

        <!-- 今日RSS -->
        <div class="relative overflow-hidden rounded-2xl p-4 bg-white/50 dark:bg-surface-800/50 border border-surface-200/50 dark:border-surface-700/50 backdrop-blur-sm">
          <div class="flex flex-col items-center justify-center h-full">
            <div class="p-2.5 rounded-xl bg-orange-500/10 dark:bg-orange-500/20 mb-2">
              <RssIcon class="w-6 h-6 text-orange-500" />
            </div>
            <p class="text-xl font-bold text-orange-600 dark:text-orange-400">
              <AnimatedNumber :value="overview?.today_rss_downloads || 0" />
            </p>
            <p class="text-sm text-surface-500 dark:text-surface-400 mt-1">今日RSS</p>
          </div>
        </div>

        <!-- 今日删种 -->
        <div class="relative overflow-hidden rounded-2xl p-4 bg-white/50 dark:bg-surface-800/50 border border-surface-200/50 dark:border-surface-700/50 backdrop-blur-sm">
          <div class="flex flex-col items-center justify-center h-full">
            <div class="p-2.5 rounded-xl bg-rose-500/10 dark:bg-rose-500/20 mb-2">
              <TrashIcon class="w-6 h-6 text-rose-500" />
            </div>
            <p class="text-xl font-bold text-rose-600 dark:text-rose-400">
              <AnimatedNumber :value="overview?.today_deleted_count || 0" />
            </p>
            <p class="text-sm text-surface-500 dark:text-surface-400 mt-1">今日删种</p>
          </div>
        </div>
      </div>

      <!-- 时间段统计 - 改进的卡片设计 -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- 今日 -->
        <div class="rounded-2xl overflow-hidden bg-gradient-to-br from-amber-500 to-orange-500 p-[1px]">
          <div class="h-full rounded-2xl bg-white dark:bg-surface-800 p-4">
            <div class="flex items-center space-x-2 mb-4">
              <div class="p-1.5 rounded-lg bg-amber-500/10">
                <CalendarIcon class="w-5 h-5 text-amber-500" />
              </div>
              <span class="font-semibold text-surface-900 dark:text-white">今日统计</span>
            </div>
            <div class="space-y-3">
              <StatRow label="删除种子" :value="`${overview?.today_deleted_count || 0} 个`" color="text-surface-900 dark:text-white" />
              <StatRow label="释放空间" :value="formatSize(overview?.today_deleted_size || 0)" color="text-red-500" />
              <StatRow label="RSS下载" :value="`${overview?.today_rss_downloads || 0} 个`" color="text-orange-500" />
              <StatRow label="追魔下载" :value="`${overview?.today_magic_downloads || 0} 个`" color="text-pink-500" />
            </div>
          </div>
        </div>

        <!-- 本周 -->
        <div class="rounded-2xl overflow-hidden bg-gradient-to-br from-blue-500 to-cyan-500 p-[1px]">
          <div class="h-full rounded-2xl bg-white dark:bg-surface-800 p-4">
            <div class="flex items-center space-x-2 mb-4">
              <div class="p-1.5 rounded-lg bg-blue-500/10">
                <CalendarDaysIcon class="w-5 h-5 text-blue-500" />
              </div>
              <span class="font-semibold text-surface-900 dark:text-white">本周统计</span>
            </div>
            <div class="space-y-3">
              <StatRow label="删除种子" :value="`${overview?.week_deleted_count || 0} 个`" color="text-surface-900 dark:text-white" />
              <StatRow label="释放空间" :value="formatSize(overview?.week_deleted_size || 0)" color="text-red-500" />
              <StatRow label="RSS下载" :value="`${overview?.week_rss_downloads || 0} 个`" color="text-orange-500" />
              <StatRow label="追魔下载" :value="`${overview?.week_magic_downloads || 0} 个`" color="text-pink-500" />
            </div>
          </div>
        </div>

        <!-- 本月 -->
        <div class="rounded-2xl overflow-hidden bg-gradient-to-br from-purple-500 to-pink-500 p-[1px]">
          <div class="h-full rounded-2xl bg-white dark:bg-surface-800 p-4">
            <div class="flex items-center space-x-2 mb-4">
              <div class="p-1.5 rounded-lg bg-purple-500/10">
                <ArchiveBoxIcon class="w-5 h-5 text-purple-500" />
              </div>
              <span class="font-semibold text-surface-900 dark:text-white">本月统计</span>
            </div>
            <div class="space-y-3">
              <StatRow label="删除种子" :value="`${overview?.month_deleted_count || 0} 个`" color="text-surface-900 dark:text-white" />
              <StatRow label="释放空间" :value="formatSize(overview?.month_deleted_size || 0)" color="text-red-500" />
              <StatRow label="RSS下载" :value="`${overview?.month_rss_downloads || 0} 个`" color="text-orange-500" />
              <StatRow label="追魔下载" :value="`${overview?.month_magic_downloads || 0} 个`" color="text-pink-500" />
            </div>
          </div>
        </div>
      </div>

      <!-- 趋势图表 - 使用 ECharts -->
      <Card>
        <template #header>
          <div class="flex items-center justify-between w-full">
            <div class="flex items-center space-x-2">
              <div class="p-1.5 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
                <ChartBarIcon class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              </div>
              <span class="font-medium text-surface-900 dark:text-white">趋势统计</span>
            </div>
            <div class="flex items-center space-x-2">
              <div class="flex rounded-lg bg-surface-100 dark:bg-surface-700 p-0.5">
                <button
                  v-for="d in [7, 14, 30]"
                  :key="d"
                  @click="trendDays = d; loadTrendData()"
                  class="px-3 py-1 text-xs font-medium rounded-md transition-all duration-200"
                  :class="trendDays === d
                    ? 'bg-white dark:bg-surface-600 text-indigo-600 dark:text-indigo-400 shadow-sm'
                    : 'text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-300'"
                >
                  {{ d }}天
                </button>
              </div>
            </div>
          </div>
        </template>

        <div v-if="trendData.length > 0" class="space-y-6">
          <!-- 删除趋势图表 -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 rounded-full bg-gradient-to-r from-red-500 to-rose-400"></div>
                <p class="text-sm font-medium text-surface-700 dark:text-surface-300">删除种子趋势</p>
              </div>
              <p class="text-xs text-surface-500 dark:text-surface-400 bg-surface-100 dark:bg-surface-700 px-2 py-1 rounded-full">
                总计: {{ trendData.reduce((s, d) => s + d.deleted_count, 0) }} 个 / {{ formatSize(trendData.reduce((s, d) => s + d.deleted_size, 0)) }}
              </p>
            </div>
            <div ref="deleteChartRef" class="h-48"></div>
          </div>

          <!-- RSS趋势图表 -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-2">
                <div class="w-3 h-3 rounded-full bg-gradient-to-r from-orange-500 to-amber-400"></div>
                <p class="text-sm font-medium text-surface-700 dark:text-surface-300">RSS 下载趋势</p>
              </div>
              <p class="text-xs text-surface-500 dark:text-surface-400 bg-surface-100 dark:bg-surface-700 px-2 py-1 rounded-full">
                总计: {{ trendData.reduce((s, d) => s + d.rss_downloads, 0) }} 个
              </p>
            </div>
            <div ref="rssChartRef" class="h-48"></div>
          </div>
        </div>
        <div v-else class="py-12 text-center">
          <ChartBarIcon class="w-12 h-12 mx-auto text-surface-300 dark:text-surface-600 mb-3" />
          <p class="text-surface-500 dark:text-surface-400">暂无趋势数据</p>
        </div>
      </Card>

      <!-- 下载器详细统计 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-2">
            <div class="p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
              <ServerStackIcon class="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <span class="font-medium text-surface-900 dark:text-white">下载器统计</span>
            <span class="text-xs text-surface-400 bg-surface-100 dark:bg-surface-700 px-2 py-0.5 rounded-full">
              {{ downloaderStats.length }} 个
            </span>
          </div>
        </template>

        <div v-if="downloaderStats.length > 0">
          <!-- 桌面端表格 -->
          <div class="hidden md:block overflow-x-auto">
            <table class="data-table">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>状态</th>
                  <th>种子数</th>
                  <th>数据量</th>
                  <th>总上传</th>
                  <th>总下载</th>
                  <th>当前速度</th>
                  <th>剩余空间</th>
                  <th>已删除</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="dl in downloaderStats" :key="dl.id" class="group">
                  <td>
                    <div class="flex items-center space-x-2">
                      <span class="font-medium text-surface-900 dark:text-white">{{ dl.name }}</span>
                      <span class="badge badge-info text-xs">{{ dl.type }}</span>
                    </div>
                  </td>
                  <td>
                    <span
                      class="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                      :class="dl.online
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'"
                    >
                      <span class="w-1.5 h-1.5 rounded-full" :class="dl.online ? 'bg-green-500 animate-pulse' : 'bg-red-500'"></span>
                      <span>{{ dl.online ? '在线' : '离线' }}</span>
                    </span>
                  </td>
                  <td class="text-surface-600 dark:text-surface-400">
                    {{ dl.total_torrents?.toLocaleString() || 0 }}
                    <span class="text-xs text-emerald-500 ml-1">({{ dl.seeding_torrents }} 做种)</span>
                  </td>
                  <td class="text-surface-600 dark:text-surface-400 font-medium">{{ formatSize(dl.total_size) }}</td>
                  <td class="text-cyan-600 dark:text-cyan-400 font-medium">{{ formatSize(dl.total_uploaded) }}</td>
                  <td class="text-purple-600 dark:text-purple-400 font-medium">{{ formatSize(dl.total_downloaded) }}</td>
                  <td>
                    <div class="flex flex-col space-y-0.5">
                      <span class="text-xs text-cyan-600 dark:text-cyan-400 flex items-center">
                        <ArrowUpIcon class="w-3 h-3 mr-0.5" />{{ formatSpeed(dl.upload_speed) }}
                      </span>
                      <span class="text-xs text-purple-600 dark:text-purple-400 flex items-center">
                        <ArrowDownIcon class="w-3 h-3 mr-0.5" />{{ formatSpeed(dl.download_speed) }}
                      </span>
                    </div>
                  </td>
                  <td>
                    <span
                      class="font-medium"
                      :class="dl.free_space < 100 * 1024 * 1024 * 1024 ? 'text-red-500' : 'text-emerald-500'"
                    >
                      {{ formatSize(dl.free_space) }}
                    </span>
                  </td>
                  <td>
                    <div class="text-xs">
                      <span class="text-surface-600 dark:text-surface-400">{{ dl.deleted_count }} 个</span>
                      <span class="text-red-500 ml-1">({{ formatSize(dl.deleted_size) }})</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 移动端卡片 -->
          <div class="md:hidden space-y-3">
            <div
              v-for="dl in downloaderStats"
              :key="dl.id"
              class="p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30 border border-surface-200/50 dark:border-surface-600/30"
            >
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center space-x-2">
                  <span class="font-semibold text-surface-900 dark:text-white">{{ dl.name }}</span>
                  <span class="badge badge-info text-xs">{{ dl.type }}</span>
                </div>
                <span
                  class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs"
                  :class="dl.online
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                    : 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :class="dl.online ? 'bg-green-500' : 'bg-red-500'"></span>
                  <span>{{ dl.online ? '在线' : '离线' }}</span>
                </span>
              </div>
              <div class="grid grid-cols-2 gap-3 text-sm">
                <div class="flex justify-between">
                  <span class="text-surface-500 dark:text-surface-400">种子</span>
                  <span class="font-medium text-surface-900 dark:text-white">{{ dl.total_torrents }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-surface-500 dark:text-surface-400">容量</span>
                  <span class="font-medium text-surface-900 dark:text-white">{{ formatSize(dl.total_size) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-surface-500 dark:text-surface-400">上传</span>
                  <span class="font-medium text-cyan-600 dark:text-cyan-400">{{ formatSize(dl.total_uploaded) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-surface-500 dark:text-surface-400">下载</span>
                  <span class="font-medium text-purple-600 dark:text-purple-400">{{ formatSize(dl.total_downloaded) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-surface-500 dark:text-surface-400">速度</span>
                  <span class="text-cyan-500">↑{{ formatSpeed(dl.upload_speed) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-surface-500 dark:text-surface-400">空间</span>
                  <span :class="dl.free_space < 100 * 1024 * 1024 * 1024 ? 'text-red-500' : 'text-emerald-500'">
                    {{ formatSize(dl.free_space) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="py-12 text-center">
          <ServerStackIcon class="w-12 h-12 mx-auto text-surface-300 dark:text-surface-600 mb-3" />
          <p class="text-surface-500 dark:text-surface-400">暂无下载器数据</p>
        </div>
      </Card>

      <!-- 删除汇总 & RSS汇总 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- 删除汇总 -->
        <Card>
          <template #header>
            <div class="flex items-center justify-between w-full">
              <div class="flex items-center space-x-2">
                <div class="p-1.5 rounded-lg bg-red-100 dark:bg-red-900/30">
                  <TrashIcon class="w-4 h-4 text-red-600 dark:text-red-400" />
                </div>
                <span class="font-medium text-surface-900 dark:text-white">删除汇总</span>
              </div>
              <span class="text-xs text-surface-500 dark:text-surface-400 bg-surface-100 dark:bg-surface-700 px-2 py-0.5 rounded-full">近30天</span>
            </div>
          </template>

          <div v-if="deleteSummary" class="space-y-4">
            <div class="grid grid-cols-2 gap-3">
              <div class="p-3 rounded-xl bg-gradient-to-br from-surface-50 to-surface-100 dark:from-surface-700/50 dark:to-surface-700/30 border border-surface-200/50 dark:border-surface-600/30">
                <p class="text-xs text-surface-500 dark:text-surface-400">总删除数</p>
                <p class="text-2xl font-bold text-surface-900 dark:text-white mt-1">
                  <AnimatedNumber :value="deleteSummary.total_count || 0" />
                </p>
              </div>
              <div class="p-3 rounded-xl bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20 border border-red-200/50 dark:border-red-500/20">
                <p class="text-xs text-surface-500 dark:text-surface-400">释放空间</p>
                <p class="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
                  {{ formatSize(deleteSummary.total_size || 0) }}
                </p>
              </div>
              <div class="p-3 rounded-xl bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20 border border-emerald-200/50 dark:border-emerald-500/20">
                <p class="text-xs text-surface-500 dark:text-surface-400">平均分享率</p>
                <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                  {{ deleteSummary.avg_ratio || 0 }}
                </p>
              </div>
              <div class="p-3 rounded-xl bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border border-blue-200/50 dark:border-blue-500/20">
                <p class="text-xs text-surface-500 dark:text-surface-400">平均做种时长</p>
                <p class="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                  {{ deleteSummary.avg_seeding_time_hours || 0 }}h
                </p>
              </div>
            </div>

            <!-- 按规则统计 -->
            <div v-if="deleteSummary.by_rule?.length > 0">
              <p class="text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 flex items-center">
                <span class="w-1 h-4 rounded-full bg-indigo-500 mr-2"></span>
                按规则统计
              </p>
              <div class="space-y-2">
                <div
                  v-for="(rule, idx) in deleteSummary.by_rule.slice(0, 5)"
                  :key="rule.rule_name"
                  class="flex items-center justify-between p-2.5 rounded-lg bg-surface-50 dark:bg-surface-700/30 hover:bg-surface-100 dark:hover:bg-surface-700/50 transition-colors"
                >
                  <div class="flex items-center space-x-2 min-w-0">
                    <span class="w-5 h-5 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 text-xs flex items-center justify-center font-medium flex-shrink-0">
                      {{ idx + 1 }}
                    </span>
                    <span class="text-sm text-surface-600 dark:text-surface-400 truncate">{{ rule.rule_name }}</span>
                  </div>
                  <div class="text-sm flex items-center space-x-2 flex-shrink-0 ml-2">
                    <span class="font-medium text-surface-900 dark:text-white">{{ rule.count }}</span>
                    <span class="text-red-500 text-xs">{{ formatSize(rule.size) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 按下载器统计 -->
            <div v-if="deleteSummary.by_downloader?.length > 0">
              <p class="text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 flex items-center">
                <span class="w-1 h-4 rounded-full bg-emerald-500 mr-2"></span>
                按下载器统计
              </p>
              <div class="space-y-2">
                <div
                  v-for="(dl, idx) in deleteSummary.by_downloader.slice(0, 5)"
                  :key="dl.downloader_name"
                  class="flex items-center justify-between p-2.5 rounded-lg bg-surface-50 dark:bg-surface-700/30 hover:bg-surface-100 dark:hover:bg-surface-700/50 transition-colors"
                >
                  <div class="flex items-center space-x-2">
                    <span class="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 text-xs flex items-center justify-center font-medium flex-shrink-0">
                      {{ idx + 1 }}
                    </span>
                    <span class="text-sm text-surface-600 dark:text-surface-400">{{ dl.downloader_name }}</span>
                  </div>
                  <div class="text-sm flex items-center space-x-2 flex-shrink-0">
                    <span class="font-medium text-surface-900 dark:text-white">{{ dl.count }}</span>
                    <span class="text-red-500 text-xs">{{ formatSize(dl.size) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="py-12 text-center">
            <TrashIcon class="w-12 h-12 mx-auto text-surface-300 dark:text-surface-600 mb-3" />
            <p class="text-surface-500 dark:text-surface-400">暂无删除数据</p>
          </div>
        </Card>

        <!-- RSS汇总 -->
        <Card>
          <template #header>
            <div class="flex items-center justify-between w-full">
              <div class="flex items-center space-x-2">
                <div class="p-1.5 rounded-lg bg-orange-100 dark:bg-orange-900/30">
                  <RssIcon class="w-4 h-4 text-orange-600 dark:text-orange-400" />
                </div>
                <span class="font-medium text-surface-900 dark:text-white">RSS 汇总</span>
              </div>
              <span class="text-xs text-surface-500 dark:text-surface-400 bg-surface-100 dark:bg-surface-700 px-2 py-0.5 rounded-full">近30天</span>
            </div>
          </template>

          <div v-if="rssSummary" class="space-y-4">
            <div class="p-4 rounded-xl bg-gradient-to-br from-orange-500/10 to-amber-500/10 dark:from-orange-500/20 dark:to-amber-500/20 border border-orange-200/50 dark:border-orange-500/20">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm text-surface-500 dark:text-surface-400">总下载数</p>
                  <p class="text-3xl font-bold text-orange-600 dark:text-orange-400 mt-1">
                    <AnimatedNumber :value="rssSummary.total_downloads || 0" />
                  </p>
                </div>
                <div class="p-3 rounded-xl bg-orange-500/20">
                  <RssIcon class="w-8 h-8 text-orange-500" />
                </div>
              </div>
            </div>

            <!-- 按订阅统计 -->
            <div v-if="rssSummary.by_feed?.length > 0">
              <p class="text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 flex items-center">
                <span class="w-1 h-4 rounded-full bg-orange-500 mr-2"></span>
                按订阅统计
              </p>
              <div class="space-y-2">
                <div
                  v-for="(feed, idx) in rssSummary.by_feed.slice(0, 5)"
                  :key="feed.feed_name"
                  class="flex items-center justify-between p-2.5 rounded-lg bg-surface-50 dark:bg-surface-700/30 hover:bg-surface-100 dark:hover:bg-surface-700/50 transition-colors"
                >
                  <div class="flex items-center space-x-2 min-w-0 flex-1">
                    <span class="w-5 h-5 rounded-full bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 text-xs flex items-center justify-center font-medium flex-shrink-0">
                      {{ idx + 1 }}
                    </span>
                    <span class="text-sm text-surface-600 dark:text-surface-400 truncate">
                      {{ feed.feed_name }}
                    </span>
                  </div>
                  <span class="font-medium text-orange-600 dark:text-orange-400 ml-2 flex-shrink-0">{{ feed.count }}</span>
                </div>
              </div>
            </div>

            <!-- 每日趋势 - 使用 ECharts -->
            <div v-if="rssSummary.daily_trend?.length > 0">
              <p class="text-sm font-medium text-surface-700 dark:text-surface-300 mb-2 flex items-center">
                <span class="w-1 h-4 rounded-full bg-amber-500 mr-2"></span>
                每日下载
              </p>
              <div ref="rssDailyChartRef" class="h-32"></div>
            </div>
          </div>
          <div v-else class="py-12 text-center">
            <RssIcon class="w-12 h-12 mx-auto text-surface-300 dark:text-surface-600 mb-3" />
            <p class="text-surface-500 dark:text-surface-400">暂无 RSS 数据</p>
          </div>
        </Card>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick, h } from 'vue'
import { statisticsApi } from '@/api'
import { formatSize, formatSpeed } from '@/utils/format'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import * as echarts from 'echarts'
import {
  ChartBarIcon,
  ArrowPathIcon,
  ServerStackIcon,
  CircleStackIcon,
  ArrowUpTrayIcon,
  ArrowDownTrayIcon,
  CalendarIcon,
  CalendarDaysIcon,
  ArchiveBoxIcon,
  TrashIcon,
  RssIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  FireIcon,
  ClockIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from '@heroicons/vue/24/outline'

// 动画数字组件
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

// 统计行组件
const StatRow = {
  props: {
    label: String,
    value: String,
    color: { type: String, default: 'text-surface-900 dark:text-white' }
  },
  setup(props) {
    return () => h('div', { class: 'flex justify-between items-center' }, [
      h('span', { class: 'text-surface-500 dark:text-surface-400 text-sm' }, props.label),
      h('span', { class: `font-semibold ${props.color}` }, props.value)
    ])
  }
}

const loading = ref(false)
const overview = ref(null)
const downloaderStats = ref([])
const trendData = ref([])
const trendDays = ref(7)
const deleteSummary = ref(null)
const rssSummary = ref(null)
const lastRefresh = ref('')

// Chart refs
const deleteChartRef = ref(null)
const rssChartRef = ref(null)
const rssDailyChartRef = ref(null)
let deleteChart = null
let rssChart = null
let rssDailyChart = null

// 计算总分享率
const overallRatio = computed(() => {
  if (!overview.value) return '0.00'
  const uploaded = overview.value.total_uploaded || 0
  const downloaded = overview.value.total_downloaded || 1
  return (uploaded / downloaded).toFixed(2)
})

// 分享率圆环进度
const ratioProgress = computed(() => {
  const ratio = parseFloat(overallRatio.value)
  return Math.min(ratio * 25, 100) // 4.0 ratio = 100%
})

// 计算日均上传量
const avgDailyUpload = computed(() => {
  if (!trendData.value || trendData.value.length === 0) return 0
  const totalUploaded = trendData.value.reduce((sum, d) => sum + (d.uploaded || 0), 0)
  return Math.round(totalUploaded / trendData.value.length)
})

// 初始化趋势图表
function initDeleteChart() {
  if (!deleteChartRef.value || trendData.value.length === 0) return

  if (deleteChart) deleteChart.dispose()
  deleteChart = echarts.init(deleteChartRef.value)

  const isDark = document.documentElement.classList.contains('dark')

  deleteChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? '#1f2937' : '#fff',
      borderColor: isDark ? '#374151' : '#e5e7eb',
      textStyle: { color: isDark ? '#f3f4f6' : '#1f2937' },
      formatter: (params) => {
        const data = params[0]
        const item = trendData.value[data.dataIndex]
        return `<div class="text-sm">
          <div class="font-medium">${data.name}</div>
          <div>删除: ${item.deleted_count} 个</div>
          <div>释放: ${formatSize(item.deleted_size)}</div>
        </div>`
      }
    },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: trendData.value.map(d => formatTrendDate(d.date)),
      axisLine: { lineStyle: { color: isDark ? '#374151' : '#e5e7eb' } },
      axisLabel: { color: isDark ? '#9ca3af' : '#6b7280', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: isDark ? '#374151' : '#f3f4f6' } },
      axisLabel: { color: isDark ? '#9ca3af' : '#6b7280', fontSize: 11 }
    },
    series: [{
      type: 'bar',
      data: trendData.value.map(d => d.deleted_count),
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#ef4444' },
          { offset: 1, color: '#f87171' }
        ])
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#dc2626' },
            { offset: 1, color: '#ef4444' }
          ])
        }
      }
    }]
  })
}

function initRssChart() {
  if (!rssChartRef.value || trendData.value.length === 0) return

  if (rssChart) rssChart.dispose()
  rssChart = echarts.init(rssChartRef.value)

  const isDark = document.documentElement.classList.contains('dark')

  rssChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? '#1f2937' : '#fff',
      borderColor: isDark ? '#374151' : '#e5e7eb',
      textStyle: { color: isDark ? '#f3f4f6' : '#1f2937' }
    },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: trendData.value.map(d => formatTrendDate(d.date)),
      axisLine: { lineStyle: { color: isDark ? '#374151' : '#e5e7eb' } },
      axisLabel: { color: isDark ? '#9ca3af' : '#6b7280', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: isDark ? '#374151' : '#f3f4f6' } },
      axisLabel: { color: isDark ? '#9ca3af' : '#6b7280', fontSize: 11 }
    },
    series: [{
      type: 'line',
      data: trendData.value.map(d => d.rss_downloads),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 3, color: '#f97316' },
      itemStyle: { color: '#f97316' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(249, 115, 22, 0.3)' },
          { offset: 1, color: 'rgba(249, 115, 22, 0.05)' }
        ])
      }
    }]
  })
}

function initRssDailyChart() {
  if (!rssDailyChartRef.value || !rssSummary.value?.daily_trend?.length) return

  if (rssDailyChart) rssDailyChart.dispose()
  rssDailyChart = echarts.init(rssDailyChartRef.value)

  const isDark = document.documentElement.classList.contains('dark')
  const data = rssSummary.value.daily_trend

  rssDailyChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? '#1f2937' : '#fff',
      borderColor: isDark ? '#374151' : '#e5e7eb',
      textStyle: { color: isDark ? '#f3f4f6' : '#1f2937' }
    },
    grid: { left: 30, right: 10, top: 10, bottom: 25 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: isDark ? '#374151' : '#e5e7eb' } },
      axisLabel: { color: isDark ? '#9ca3af' : '#6b7280', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: isDark ? '#374151' : '#f3f4f6' } },
      axisLabel: { color: isDark ? '#9ca3af' : '#6b7280', fontSize: 10 }
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.count),
      itemStyle: {
        borderRadius: [3, 3, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#f97316' },
          { offset: 1, color: '#fbbf24' }
        ])
      }
    }]
  })
}

function formatTrendDate(dateStr) {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// 处理窗口大小变化
function handleResize() {
  deleteChart?.resize()
  rssChart?.resize()
  rssDailyChart?.resize()
}

async function loadOverview() {
  try {
    const response = await statisticsApi.getOverview()
    overview.value = response.data
  } catch (error) {
    console.error('Failed to load overview:', error)
  }
}

async function loadDownloaderStats() {
  try {
    const response = await statisticsApi.getDownloaderStats()
    downloaderStats.value = response.data
  } catch (error) {
    console.error('Failed to load downloader stats:', error)
  }
}

async function loadTrendData() {
  try {
    const response = await statisticsApi.getTrend({ days: trendDays.value })
    trendData.value = response.data
    await nextTick()
    initDeleteChart()
    initRssChart()
  } catch (error) {
    console.error('Failed to load trend data:', error)
  }
}

async function loadDeleteSummary() {
  try {
    const response = await statisticsApi.getDeleteSummary(30)
    deleteSummary.value = response.data
  } catch (error) {
    console.error('Failed to load delete summary:', error)
  }
}

async function loadRssSummary() {
  try {
    const response = await statisticsApi.getRssSummary(30)
    rssSummary.value = response.data
    await nextTick()
    initRssDailyChart()
  } catch (error) {
    console.error('Failed to load RSS summary:', error)
  }
}

async function refreshData() {
  loading.value = true
  try {
    await Promise.all([
      loadOverview(),
      loadDownloaderStats(),
      loadTrendData(),
      loadDeleteSummary(),
      loadRssSummary(),
    ])
    lastRefresh.value = new Date().toLocaleTimeString()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  deleteChart?.dispose()
  rssChart?.dispose()
  rssDailyChart?.dispose()
})
</script>
