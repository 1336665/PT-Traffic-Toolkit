<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 shadow-lg shadow-orange-500/30">
          <RssIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">RSS 订阅</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">管理订阅源和自动下载规则</p>
        </div>
      </div>
      <Button variant="primary" @click="openFeedModal()">
        <PlusIcon class="w-4 h-4" />
        <span class="hidden sm:inline">添加订阅</span>
        <span class="sm:hidden">添加</span>
      </Button>
    </div>

    <!-- 空状态 -->
    <Card v-if="feeds.length === 0">
      <div class="empty-state py-12">
        <div class="empty-state-icon">
          <RssIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title">暂无订阅源</p>
        <p class="empty-state-description">添加 RSS 订阅源开始自动下载</p>
        <Button variant="primary" class="mt-4" @click="openFeedModal()">
          <PlusIcon class="w-4 h-4" />
          添加订阅
        </Button>
      </div>
    </Card>

    <!-- 订阅源列表 -->
    <div v-else class="space-y-4">
      <Card
        v-for="feed in feeds"
        :key="feed.id"
        :padding="false"
        class="overflow-hidden"
      >
        <!-- 卡片头部 -->
        <div class="flex items-start sm:items-center justify-between px-4 py-3 border-b border-surface-100 dark:border-surface-700 bg-surface-50/50 dark:bg-surface-800/50 gap-3">
          <div class="flex items-center space-x-3 min-w-0 flex-1">
            <!-- PT站点图标 -->
            <div
              class="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden"
              :class="feed.enabled
                ? 'shadow-lg'
                : 'bg-surface-100 dark:bg-surface-700'"
              :style="feed.enabled && getSiteInfo(feed.url).color ? { background: getSiteInfo(feed.url).color } : {}"
            >
              <img
                v-if="getSiteInfo(feed.url).icon"
                :src="getSiteInfo(feed.url).icon"
                :alt="getSiteInfo(feed.url).name"
                class="w-6 h-6 object-contain"
                @error="(e) => e.target.style.display = 'none'"
              />
              <RssIcon
                v-else
                class="w-5 h-5"
                :class="feed.enabled ? 'text-white' : 'text-surface-400'"
              />
            </div>
            <div class="min-w-0 flex-1">
              <h3 class="font-semibold text-surface-900 dark:text-white truncate">{{ feed.name }}</h3>
              <div class="flex items-center space-x-2 text-xs text-surface-500 dark:text-surface-400">
                <span class="inline-flex items-center px-1.5 py-0.5 rounded bg-surface-100 dark:bg-surface-700">
                  {{ getSiteInfo(feed.url).name }}
                </span>
                <span class="truncate hidden sm:inline">{{ getSiteDomain(feed.url) }}</span>
              </div>
            </div>
          </div>
          <div class="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
            <!-- 切换开关 -->
            <button
              @click="toggleFeed(feed)"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                feed.enabled ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  feed.enabled ? 'translate-x-5' : 'translate-x-0'
                ]"
              ></span>
            </button>
            <span
              class="text-sm font-medium hidden sm:inline min-w-12"
              :class="feed.enabled ? 'text-green-600 dark:text-green-400' : 'text-surface-500 dark:text-surface-400'"
            >
              {{ feed.enabled ? '启用' : '禁用' }}
            </span>
          </div>
        </div>

        <!-- 卡片内容 -->
        <div class="p-4">
          <!-- 过滤条件 -->
          <div class="mb-4">
            <div class="text-xs font-medium text-surface-500 dark:text-surface-400 uppercase tracking-wider mb-2">
              过滤条件
            </div>
            <div class="flex flex-wrap gap-1.5 sm:gap-2">
              <!-- 大小过滤 -->
              <span v-if="feed.min_size > 0 || feed.max_size > 0" class="inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
                <CubeIcon class="w-3.5 h-3.5 mr-1 hidden sm:inline" />
                {{ feed.min_size || 0 }}-{{ feed.max_size > 0 ? feed.max_size : '∞' }}GB
              </span>
              <!-- 做种人数过滤 -->
              <span v-if="feed.min_seeders > 0 || feed.max_seeders > 0" class="inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
                <UsersIcon class="w-3.5 h-3.5 mr-1 hidden sm:inline" />
                {{ feed.min_seeders || 0 }}-{{ feed.max_seeders > 0 ? feed.max_seeders : '∞' }}
              </span>
              <!-- 仅免费 -->
              <span v-if="feed.only_free" class="inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300">
                <SparklesIcon class="w-3.5 h-3.5 mr-1 hidden sm:inline" />
                免费
              </span>
              <!-- 排除 HR -->
              <span v-if="feed.exclude_hr" class="inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">
                <NoSymbolIcon class="w-3.5 h-3.5 mr-1 hidden sm:inline" />
                排除HR
              </span>
              <!-- 包含关键词 -->
              <span v-if="feed.include_keywords" class="inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 max-w-32 sm:max-w-none">
                <MagnifyingGlassIcon class="w-3.5 h-3.5 mr-1 flex-shrink-0 hidden sm:inline" />
                <span class="truncate">+{{ feed.include_keywords }}</span>
              </span>
              <!-- 排除关键词 -->
              <span v-if="feed.exclude_keywords" class="inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 max-w-32 sm:max-w-none">
                <XMarkIcon class="w-3.5 h-3.5 mr-1 flex-shrink-0 hidden sm:inline" />
                <span class="truncate">-{{ feed.exclude_keywords }}</span>
              </span>
              <!-- 无条件 -->
              <span v-if="!feed.only_free && !feed.exclude_hr && !feed.min_size && !feed.max_size && !feed.min_seeders && !feed.max_seeders && !feed.include_keywords && !feed.exclude_keywords" class="text-xs text-surface-400 dark:text-surface-500">
                无过滤条件
              </span>
            </div>
          </div>

          <!-- 选项行 -->
          <div class="flex flex-wrap gap-1.5 sm:gap-2">
            <span class="inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300">
              <ClockIcon class="w-3.5 h-3.5 mr-1" />
              {{ feed.fetch_interval }}s
            </span>
            <span class="inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-300">
              <ServerIcon class="w-3.5 h-3.5 mr-1" />
              {{ getDownloaderName(feed.downloader_id) }}
            </span>
            <span :class="[
              'inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium',
              feed.first_run_done
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
            ]">
              <CheckCircleIcon v-if="feed.first_run_done" class="w-3.5 h-3.5 mr-1" />
              <ExclamationCircleIcon v-else class="w-3.5 h-3.5 mr-1" />
              {{ feed.first_run_done ? '已初始化' : '待初始化' }}
            </span>
          </div>
        </div>

        <!-- 卡片底部 - 移动端优化 -->
        <div class="flex items-center justify-between px-3 sm:px-4 py-2.5 sm:py-3 border-t border-surface-100 dark:border-surface-700 bg-surface-50/50 dark:bg-surface-800/50">
          <div class="flex items-center space-x-1">
            <button
              @click="fetchFeed(feed)"
              :disabled="fetchingFeed === feed.id"
              class="p-2 rounded-lg text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700 disabled:opacity-50 transition-colors"
              title="抓取"
            >
              <ArrowPathIcon class="w-5 h-5" :class="{ 'animate-spin': fetchingFeed === feed.id }" />
            </button>
            <button
              @click="testFeed(feed)"
              :disabled="testingFeed === feed.id"
              class="p-2 rounded-lg text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700 disabled:opacity-50 transition-colors"
              title="测试"
            >
              <BeakerIcon class="w-5 h-5" />
            </button>
            <button
              @click="resetFeed(feed)"
              class="p-2 rounded-lg text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors"
              title="重置"
            >
              <ArrowUturnLeftIcon class="w-5 h-5" />
            </button>
          </div>
          <div class="flex items-center space-x-1">
            <button
              @click="openFeedModal(feed)"
              class="p-2 rounded-lg text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors"
              title="编辑"
            >
              <PencilIcon class="w-5 h-5" />
            </button>
            <button
              @click="deleteFeed(feed)"
              class="p-2 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="删除"
            >
              <TrashIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </Card>
    </div>

    <!-- 抓取记录 -->
    <Card :padding="false">
      <template #header>
        <div class="flex flex-col gap-3 w-full">
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <QueueListIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">抓取记录</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">共 {{ pagination.total }} 条记录，第 {{ pagination.page }}/{{ pagination.pages }} 页</p>
            </div>
          </div>
          <!-- 过滤器 - 移动端优化 -->
          <div class="flex flex-wrap items-center gap-2">
            <select v-model="recordFilter.feed_id" class="form-select text-sm py-1.5 flex-1 min-w-[120px] max-w-[200px]">
              <option :value="null">全部订阅</option>
              <option v-for="feed in feeds" :key="feed.id" :value="feed.id">{{ feed.name }}</option>
            </select>
            <select v-model="recordFilter.downloaded" class="form-select text-sm py-1.5 w-24">
              <option :value="null">全部</option>
              <option :value="true">已下载</option>
              <option :value="false">已跳过</option>
            </select>
            <Button variant="secondary" size="sm" @click="loadRecords" class="!px-2">
              <ArrowPathIcon class="w-4 h-4" />
            </Button>
          </div>
        </div>
      </template>

      <div v-if="records.length === 0" class="empty-state py-12">
        <div class="empty-state-icon !w-12 !h-12">
          <QueueListIcon class="w-full h-full" />
        </div>
        <p class="empty-state-title text-base">暂无记录</p>
        <p class="empty-state-description">RSS 抓取记录将显示在这里</p>
      </div>

      <!-- 桌面端表格 -->
      <div v-else class="hidden md:block overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>标题</th>
              <th class="w-24">大小</th>
              <th class="w-20">做种</th>
              <th class="w-28">状态</th>
              <th class="w-36">时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in records" :key="record.id" class="hover:bg-surface-50 dark:hover:bg-surface-800/50">
              <td class="max-w-xs">
                <p class="truncate font-medium text-surface-900 dark:text-white" :title="record.title">{{ record.title }}</p>
                <div class="flex space-x-1 mt-1">
                  <span v-if="record.is_free" class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300">FREE</span>
                  <span v-if="record.is_hr" class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">H&R</span>
                </div>
              </td>
              <td class="text-surface-500 dark:text-surface-400">{{ formatSize(record.size) }}</td>
              <td class="text-surface-500 dark:text-surface-400">{{ record.seeders }}</td>
              <td>
                <span
                  v-if="record.downloaded"
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
                >
                  <CheckCircleIcon class="w-3 h-3 mr-1" />
                  已下载
                </span>
                <span
                  v-else
                  class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-400"
                  :title="record.skip_reason"
                >
                  {{ record.skip_reason || '已跳过' }}
                </span>
              </td>
              <td class="text-xs text-surface-500 dark:text-surface-400">{{ formatTime(record.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 移动端卡片列表 -->
      <div v-if="records.length > 0" class="md:hidden divide-y divide-surface-100 dark:divide-surface-700">
        <div
          v-for="record in records"
          :key="record.id"
          class="p-4 space-y-2"
        >
          <div class="flex items-start justify-between gap-2">
            <p class="font-medium text-surface-900 dark:text-white text-sm line-clamp-2 flex-1">{{ record.title }}</p>
            <span
              v-if="record.downloaded"
              class="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
            >
              已下载
            </span>
            <span
              v-else
              class="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-400"
            >
              跳过
            </span>
          </div>
          <div class="flex items-center gap-3 text-xs text-surface-500 dark:text-surface-400">
            <span>{{ formatSize(record.size) }}</span>
            <span>{{ record.seeders }} 做种</span>
            <div class="flex space-x-1">
              <span v-if="record.is_free" class="px-1.5 py-0.5 rounded bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 font-medium">FREE</span>
              <span v-if="record.is_hr" class="px-1.5 py-0.5 rounded bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 font-medium">H&R</span>
            </div>
            <span class="ml-auto">{{ formatTime(record.created_at) }}</span>
          </div>
          <p v-if="!record.downloaded && record.skip_reason" class="text-xs text-orange-600 dark:text-orange-400">
            {{ record.skip_reason }}
          </p>
        </div>
      </div>

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
    </Card>

    <!-- 添加/编辑弹窗 -->
    <Modal v-model="feedModalOpen" :title="editingFeed ? '编辑订阅' : '添加订阅'" size="lg">
      <form @submit.prevent="saveFeed" class="space-y-5">
        <!-- 基本信息 -->
        <div>
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
            <InformationCircleIcon class="w-4 h-4 mr-2 text-surface-400" />
            基本信息
          </h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div class="sm:col-span-2 form-group">
              <label class="form-label">订阅名称</label>
              <input v-model="feedForm.name" type="text" required class="form-input" placeholder="我的订阅" />
            </div>
            <div class="sm:col-span-2 form-group">
              <label class="form-label">订阅地址</label>
              <input v-model="feedForm.url" type="url" required class="form-input" placeholder="https://..." />
            </div>
            <div class="form-group">
              <label class="form-label">下载器</label>
              <select v-model="feedForm.downloader_id" class="form-select">
                <option :value="null">自动分配</option>
                <option v-for="dl in downloaders" :key="dl.id" :value="dl.id">{{ dl.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">抓取间隔 (秒)</label>
              <input v-model.number="feedForm.fetch_interval" type="number" min="60" class="form-input" placeholder="300" />
            </div>
            <div class="sm:col-span-2 form-group">
              <label class="form-label">站点 Cookie</label>
              <textarea v-model="feedForm.site_cookie" rows="2" class="form-input" placeholder="可选，用于访问需要登录的 RSS"></textarea>
            </div>
          </div>
        </div>

        <!-- 过滤条件 -->
        <div>
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
            <FunnelIcon class="w-4 h-4 mr-2 text-surface-400" />
            过滤条件
          </h4>
          <div class="grid grid-cols-2 sm:grid-cols-2 gap-3 sm:gap-4">
            <div class="form-group">
              <label class="form-label">最小大小 (GB)</label>
              <input v-model.number="feedForm.min_size" type="number" step="0.1" min="0" class="form-input" placeholder="0" />
            </div>
            <div class="form-group">
              <label class="form-label">最大大小 (GB)</label>
              <input v-model.number="feedForm.max_size" type="number" step="0.1" min="0" class="form-input" placeholder="0=不限" />
            </div>
            <div class="form-group">
              <label class="form-label">最小做种数</label>
              <input v-model.number="feedForm.min_seeders" type="number" min="0" class="form-input" placeholder="0" />
            </div>
            <div class="form-group">
              <label class="form-label">最大做种数</label>
              <input v-model.number="feedForm.max_seeders" type="number" min="0" class="form-input" placeholder="0=不限" />
            </div>
            <div class="col-span-2 form-group">
              <label class="form-label">包含关键词</label>
              <input v-model="feedForm.include_keywords" type="text" class="form-input" placeholder="逗号分隔" />
            </div>
            <div class="col-span-2 form-group">
              <label class="form-label">排除关键词</label>
              <input v-model="feedForm.exclude_keywords" type="text" class="form-input" placeholder="逗号分隔" />
            </div>
          </div>
        </div>

        <!-- qBittorrent 设置 -->
        <div>
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
            <TagIcon class="w-4 h-4 mr-2 text-cyan-500" />
            qBittorrent 种子设置
          </h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="form-group">
              <label class="form-label">分类 (Category)</label>
              <input v-model="feedForm.qb_category" type="text" class="form-input" placeholder="例如: PT, RSS订阅" />
              <p class="text-xs text-surface-500 mt-1">下载的种子将自动分配到此分类</p>
            </div>
            <div class="form-group">
              <label class="form-label">标签 (Tags)</label>
              <input v-model="feedForm.qb_tags" type="text" class="form-input" placeholder="逗号分隔，例如: rss,auto" />
              <p class="text-xs text-surface-500 mt-1">下载的种子将自动添加这些标签</p>
            </div>
            <div class="sm:col-span-2 form-group">
              <label class="form-label">自定义保存路径</label>
              <input v-model="feedForm.qb_save_path" type="text" class="form-input" placeholder="留空使用下载器默认路径" />
              <p class="text-xs text-surface-500 mt-1">可选，指定种子下载保存位置</p>
            </div>
          </div>
        </div>

        <!-- 选项 -->
        <div>
          <h4 class="text-sm font-medium text-surface-900 dark:text-white mb-3 flex items-center">
            <Cog6ToothIcon class="w-4 h-4 mr-2 text-surface-400" />
            选项
          </h4>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
              <input v-model="feedForm.enabled" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
              <span class="text-sm text-surface-700 dark:text-surface-300">启用订阅</span>
            </label>
            <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
              <input v-model="feedForm.only_free" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
              <span class="text-sm text-surface-700 dark:text-surface-300">仅免费</span>
            </label>
            <label class="flex items-center space-x-2 p-3 rounded-xl bg-surface-50 dark:bg-surface-700/50 cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-700 transition-colors">
              <input v-model="feedForm.exclude_hr" type="checkbox" class="rounded text-primary-600 focus:ring-primary-500" />
              <span class="text-sm text-surface-700 dark:text-surface-300">排除 H&R</span>
            </label>
          </div>
        </div>
      </form>

      <template #footer>
        <Button variant="secondary" @click="feedModalOpen = false">取消</Button>
        <Button variant="primary" :loading="savingFeed" @click="saveFeed">
          <CheckIcon class="w-4 h-4" />
          保存
        </Button>
      </template>
    </Modal>

    <!-- 测试结果弹窗 -->
    <Modal v-model="testResultModal" title="RSS 测试结果" size="lg">
      <div v-if="testResult" class="space-y-4">
        <!-- 状态 -->
        <div :class="[
          'p-4 rounded-xl border',
          testResult.success
            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
            : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
        ]">
          <div class="flex items-center space-x-2">
            <CheckCircleIcon v-if="testResult.success" class="w-5 h-5 text-green-500" />
            <ExclamationCircleIcon v-else class="w-5 h-5 text-red-500" />
            <span :class="testResult.success ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'" class="font-medium">
              {{ testResult.success ? '解析成功' : '解析失败' }}
            </span>
          </div>
          <p v-if="testResult.success" class="mt-2 text-sm text-green-600 dark:text-green-400">
            共解析到 {{ testResult.total_entries }} 条记录
          </p>
          <p v-if="testResult.error" class="mt-2 text-sm text-red-600 dark:text-red-400">
            {{ testResult.error }}
          </p>
        </div>

        <!-- 请求信息 -->
        <div v-if="testResult.request_info" class="p-4 bg-surface-50 dark:bg-surface-700/50 rounded-xl">
          <h4 class="font-medium text-surface-900 dark:text-white mb-3">请求详情</h4>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div class="text-surface-500 dark:text-surface-400">状态码:</div>
            <div :class="testResult.request_info.status_code === 200 ? 'text-green-600' : 'text-red-600'">
              {{ testResult.request_info.status_code || 'N/A' }}
            </div>
            <div class="text-surface-500 dark:text-surface-400">内容类型:</div>
            <div class="text-surface-900 dark:text-white truncate">{{ testResult.request_info.content_type || 'N/A' }}</div>
            <div class="text-surface-500 dark:text-surface-400">内容大小:</div>
            <div class="text-surface-900 dark:text-white">{{ testResult.request_info.content_length || 0 }} bytes</div>
            <div v-if="testResult.request_info.is_cloudflare" class="col-span-2 text-orange-600 dark:text-orange-400 flex items-center">
              <ExclamationTriangleIcon class="w-4 h-4 mr-1" />
              检测到 CloudFlare 保护
            </div>
          </div>
          <div v-if="testResult.request_info.response_preview" class="mt-3">
            <div class="text-surface-500 dark:text-surface-400 text-xs mb-1">响应预览:</div>
            <pre class="text-xs bg-surface-100 dark:bg-surface-800 p-2 rounded-lg overflow-x-auto max-h-32">{{ testResult.request_info.response_preview }}</pre>
          </div>
          <div v-if="testResult.request_info.request_error" class="mt-2 text-red-600 dark:text-red-400 text-sm">
            请求错误: {{ testResult.request_info.request_error }}
          </div>
        </div>

        <!-- 首次运行提示 -->
        <div v-if="testResult.message" class="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
          <div class="flex items-start space-x-2">
            <ExclamationCircleIcon class="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p class="text-amber-700 dark:text-amber-300 font-medium">首次运行模式</p>
              <p class="text-sm text-amber-600 dark:text-amber-400 mt-1">{{ testResult.message }}</p>
            </div>
          </div>
        </div>

        <!-- 条目列表 -->
        <div v-if="testResult.entries && testResult.entries.length > 0" class="space-y-2">
          <h4 class="font-medium text-surface-900 dark:text-white">解析到的条目 (最多显示10条)</h4>
          <div class="max-h-80 sm:max-h-96 overflow-y-auto space-y-2">
            <div
              v-for="(entry, idx) in testResult.entries"
              :key="idx"
              class="p-3 bg-surface-50 dark:bg-surface-700/50 rounded-xl"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="flex-1 min-w-0">
                  <p class="font-medium text-surface-900 dark:text-white text-sm line-clamp-2">{{ entry.title }}</p>
                  <div class="flex flex-wrap gap-1.5 mt-2">
                    <span v-if="entry.size > 0" class="text-xs px-2 py-0.5 rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
                      {{ formatSize(entry.size) }}
                    </span>
                    <span v-if="entry.seeders > 0" class="text-xs px-2 py-0.5 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300">
                      {{ entry.seeders }} 做种
                    </span>
                    <span v-if="entry.is_free" class="text-xs px-2 py-0.5 rounded-lg bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300">
                      FREE
                    </span>
                    <span v-if="entry.is_hr" class="text-xs px-2 py-0.5 rounded-lg bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">
                      H&R
                    </span>
                  </div>
                </div>
                <span :class="[
                  'text-xs px-2 py-1 rounded-full flex-shrink-0',
                  entry.passed_filter
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                    : 'bg-surface-100 dark:bg-surface-600 text-surface-600 dark:text-surface-300'
                ]">
                  {{ entry.passed_filter ? '通过' : '跳过' }}
                </span>
              </div>
              <p v-if="entry.skip_reason" class="text-xs text-orange-600 dark:text-orange-400 mt-2">
                跳过原因: {{ entry.skip_reason }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { rssApi, downloadersApi } from '@/api'
import { formatSize, formatTime } from '@/utils/format'
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
  XMarkIcon,
  BeakerIcon,
  QueueListIcon,
  InformationCircleIcon,
  FunnelIcon,
  Cog6ToothIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  TagIcon,
} from '@heroicons/vue/24/outline'

dayjs.locale('zh-cn')

// PT站点信息映射
const PT_SITES = {
  // 国内PT站点
  'u2.dmhy.org': { name: 'U2', color: 'linear-gradient(135deg, #6366f1, #8b5cf6)', icon: 'https://u2.dmhy.org/favicon.ico' },
  'hdsky.me': { name: 'HDSky', color: 'linear-gradient(135deg, #0ea5e9, #06b6d4)', icon: 'https://hdsky.me/favicon.ico' },
  'pterclub.com': { name: 'PTer', color: 'linear-gradient(135deg, #f97316, #ef4444)', icon: 'https://pterclub.com/favicon.ico' },
  'audiences.me': { name: 'Audiences', color: 'linear-gradient(135deg, #22c55e, #16a34a)', icon: null },
  'hdhome.org': { name: 'HDHome', color: 'linear-gradient(135deg, #3b82f6, #2563eb)', icon: 'https://hdhome.org/favicon.ico' },
  'ourbits.club': { name: 'OurBits', color: 'linear-gradient(135deg, #a855f7, #7c3aed)', icon: 'https://ourbits.club/favicon.ico' },
  'chdbits.co': { name: 'CHDBits', color: 'linear-gradient(135deg, #ef4444, #dc2626)', icon: 'https://chdbits.co/favicon.ico' },
  'mteam.cc': { name: 'M-Team', color: 'linear-gradient(135deg, #eab308, #ca8a04)', icon: 'https://kp.m-team.cc/favicon.ico' },
  'hdcity.city': { name: 'HDCity', color: 'linear-gradient(135deg, #14b8a6, #0d9488)', icon: null },
  'beitai.pt': { name: '备胎', color: 'linear-gradient(135deg, #f472b6, #ec4899)', icon: null },
  'hdatmos.club': { name: 'HDAtmos', color: 'linear-gradient(135deg, #6366f1, #4f46e5)', icon: null },
  'hares.top': { name: '白兔', color: 'linear-gradient(135deg, #f43f5e, #e11d48)', icon: null },
  'haidan.video': { name: '海胆', color: 'linear-gradient(135deg, #0ea5e9, #0284c7)', icon: null },
  'hdzone.me': { name: 'HDZone', color: 'linear-gradient(135deg, #8b5cf6, #7c3aed)', icon: null },
  'leaves.red': { name: '红叶', color: 'linear-gradient(135deg, #ef4444, #b91c1c)', icon: null },
  'pttime.org': { name: 'PTTime', color: 'linear-gradient(135deg, #3b82f6, #1d4ed8)', icon: null },
  'pthome.net': { name: 'PTHome', color: 'linear-gradient(135deg, #22c55e, #15803d)', icon: null },
  'ssd.upxin.net': { name: 'SSD', color: 'linear-gradient(135deg, #6366f1, #4338ca)', icon: null },
  'hddolby.com': { name: 'HDDolby', color: 'linear-gradient(135deg, #0ea5e9, #0369a1)', icon: null },
  'tjupt.org': { name: 'TJUPT', color: 'linear-gradient(135deg, #6366f1, #4f46e5)', icon: null },
  'springsunday.net': { name: '春天', color: 'linear-gradient(135deg, #22c55e, #16a34a)', icon: null },
  'btschool.club': { name: 'BTSchool', color: 'linear-gradient(135deg, #3b82f6, #2563eb)', icon: null },
  'hdtime.org': { name: 'HDTime', color: 'linear-gradient(135deg, #f97316, #ea580c)', icon: null },
  'totheglory.im': { name: 'TTG', color: 'linear-gradient(135deg, #eab308, #ca8a04)', icon: null },
  'greatposterwall.com': { name: 'GPW', color: 'linear-gradient(135deg, #a855f7, #9333ea)', icon: null },
  'dicmusic.com': { name: 'DIC', color: 'linear-gradient(135deg, #6366f1, #4f46e5)', icon: null },
  'open.cd': { name: 'OpenCD', color: 'linear-gradient(135deg, #14b8a6, #0d9488)', icon: null },
  // 国际PT站点
  'passthepopcorn.me': { name: 'PTP', color: 'linear-gradient(135deg, #ef4444, #dc2626)', icon: null },
  'broadcasthe.net': { name: 'BTN', color: 'linear-gradient(135deg, #3b82f6, #2563eb)', icon: null },
  'empornium.is': { name: 'EMP', color: 'linear-gradient(135deg, #f472b6, #ec4899)', icon: null },
  'iptorrents.com': { name: 'IPT', color: 'linear-gradient(135deg, #22c55e, #16a34a)', icon: null },
  'torrentleech.org': { name: 'TL', color: 'linear-gradient(135deg, #0ea5e9, #0284c7)', icon: null },
  'filelist.io': { name: 'FL', color: 'linear-gradient(135deg, #6366f1, #4f46e5)', icon: null },
  'hdbits.org': { name: 'HDBits', color: 'linear-gradient(135deg, #3b82f6, #1d4ed8)', icon: null },
  'beyondhd.co': { name: 'BHD', color: 'linear-gradient(135deg, #8b5cf6, #7c3aed)', icon: null },
  'blutopia.cc': { name: 'BLU', color: 'linear-gradient(135deg, #0ea5e9, #06b6d4)', icon: null },
  'aither.cc': { name: 'Aither', color: 'linear-gradient(135deg, #a855f7, #9333ea)', icon: null },
  'orpheus.network': { name: 'OPS', color: 'linear-gradient(135deg, #22c55e, #15803d)', icon: null },
  'redacted.ch': { name: 'RED', color: 'linear-gradient(135deg, #ef4444, #b91c1c)', icon: null },
}

// 从URL获取站点域名
function getSiteDomain(url) {
  if (!url) return '未知'
  try {
    const urlObj = new URL(url)
    return urlObj.hostname
  } catch {
    return '未知'
  }
}

// 从URL获取站点信息
function getSiteInfo(url) {
  if (!url) return { name: 'RSS', color: 'linear-gradient(135deg, #f97316, #ea580c)', icon: null }
  try {
    const urlObj = new URL(url)
    const hostname = urlObj.hostname.toLowerCase()

    // 精确匹配
    if (PT_SITES[hostname]) {
      return PT_SITES[hostname]
    }

    // 模糊匹配（检查是否包含已知站点域名）
    for (const [domain, info] of Object.entries(PT_SITES)) {
      if (hostname.includes(domain.split('.')[0])) {
        return info
      }
    }

    // 默认返回
    return { name: getSiteDomain(url).split('.')[0].toUpperCase(), color: 'linear-gradient(135deg, #f97316, #ea580c)', icon: null }
  } catch {
    return { name: 'RSS', color: 'linear-gradient(135deg, #f97316, #ea580c)', icon: null }
  }
}

const feeds = ref([])
const records = ref([])
const downloaders = ref([])

const feedModalOpen = ref(false)
const editingFeed = ref(null)
const savingFeed = ref(false)
const fetchingFeed = ref(null)
const testingFeed = ref(null)
const testResult = ref(null)
const testResultModal = ref(false)

// 分页状态
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
  pages: 1
})

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
  qb_category: '',
  qb_tags: '',
  qb_save_path: '',
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
  if (!id) return '自动'
  return downloaderMap.value[id] || '未知'
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
      page: pagination.page,
      page_size: pagination.pageSize,
      ...(recordFilter.feed_id && { feed_id: recordFilter.feed_id }),
      ...(recordFilter.downloaded !== null && { downloaded: recordFilter.downloaded }),
    }
    const response = await rssApi.getRecords(params)
    records.value = response.data.items
    pagination.total = response.data.total
    pagination.pages = response.data.pages
  } catch (error) {
    console.error('Failed to load records:', error)
  }
}

function changePage(newPage) {
  if (newPage >= 1 && newPage <= pagination.pages) {
    pagination.page = newPage
    loadRecords()
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
    alert(error.response?.data?.detail || '保存失败')
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
  if (!confirm('确定要删除此订阅吗？')) return

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
    alert(`抓取完成：共 ${response.data.total} 条，下载 ${response.data.downloaded} 条`)
    await loadRecords()
  } catch (error) {
    console.error('Failed to fetch feed:', error)
    alert('抓取失败')
  } finally {
    fetchingFeed.value = null
  }
}

async function resetFeed(feed) {
  if (!confirm('确定要重置此订阅吗？将清除已抓取记录。')) return

  try {
    await rssApi.resetFeed(feed.id)
    await loadFeeds()
  } catch (error) {
    console.error('Failed to reset feed:', error)
  }
}

async function testFeed(feed) {
  testingFeed.value = feed.id
  try {
    const response = await rssApi.testFeed(feed.id)
    testResult.value = response.data
    testResultModal.value = true
  } catch (error) {
    console.error('Failed to test feed:', error)
    testResult.value = {
      success: false,
      error: error.response?.data?.detail || error.message || '测试失败'
    }
    testResultModal.value = true
  } finally {
    testingFeed.value = null
  }
}

watch(recordFilter, () => {
  pagination.page = 1  // 重置到第一页
  loadRecords()
})

onMounted(() => {
  loadFeeds()
  loadRecords()
  loadDownloaders()
})
</script>
