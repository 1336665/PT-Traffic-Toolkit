<template>
  <header class="h-16 bg-white/80 dark:bg-surface-900/80 backdrop-blur-xl border-b border-surface-200/80 dark:border-surface-700/50 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-40">
    <!-- Left side -->
    <div class="flex items-center space-x-4">
      <!-- Mobile menu button -->
      <button
        class="lg:hidden p-2 rounded-xl text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors cursor-pointer"
        @click="mobileMenuOpen = true"
      >
        <Bars3Icon class="h-6 w-6" />
      </button>

      <!-- Breadcrumb / Page title -->
      <div class="flex items-center space-x-2">
        <div class="hidden sm:flex items-center text-sm">
          <HomeIcon class="w-4 h-4 text-surface-400" />
          <ChevronRightIcon class="w-4 h-4 text-surface-300 mx-1" />
        </div>
        <h1 class="text-lg font-bold text-surface-900 dark:text-white">
          {{ currentPageTitle }}
        </h1>
      </div>
    </div>

    <!-- Right side -->
    <div class="flex items-center space-x-2">
      <!-- 搜索按钮 -->
      <button
        @click="openSearch"
        class="hidden sm:flex items-center gap-2 px-3 py-2 rounded-xl text-surface-500 bg-surface-100/80 dark:bg-surface-800/80 hover:bg-surface-200 dark:hover:bg-surface-700 transition-all cursor-pointer group"
      >
        <MagnifyingGlassIcon class="h-4 w-4" />
        <span class="text-sm text-surface-400 group-hover:text-surface-600 dark:group-hover:text-surface-300">搜索...</span>
        <kbd class="hidden md:inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-medium text-surface-400 bg-surface-200/80 dark:bg-surface-700 rounded">
          <span>⌘</span>K
        </kbd>
      </button>

      <!-- 通知按钮 -->
      <div class="relative">
        <button
          class="relative p-2.5 rounded-xl text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors cursor-pointer"
          @click="toggleNotifications"
        >
          <BellIcon class="h-5 w-5" />
          <!-- 通知数量徽章 -->
          <transition
            enter-active-class="transition-all duration-300"
            enter-from-class="scale-0 opacity-0"
            enter-to-class="scale-100 opacity-100"
          >
            <span
              v-if="totalUnread > 0"
              class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center px-1 text-[10px] font-bold text-white rounded-full ring-2 ring-white dark:ring-surface-900"
              :class="hasErrors ? 'bg-red-500' : 'bg-primary-500'"
            >
              {{ totalUnread > 99 ? '99+' : totalUnread }}
            </span>
          </transition>
        </button>

        <!-- 通知面板 -->
        <transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="transform opacity-0 scale-95 -translate-y-2"
          enter-to-class="transform opacity-100 scale-100 translate-y-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="transform opacity-100 scale-100 translate-y-0"
          leave-to-class="transform opacity-0 scale-95 -translate-y-2"
        >
          <div
            v-if="notificationOpen"
            class="fixed inset-x-4 top-16 sm:absolute sm:inset-x-auto sm:left-auto sm:right-0 sm:mt-2 sm:w-96 rounded-2xl bg-white dark:bg-surface-800 shadow-2xl shadow-surface-900/20 dark:shadow-black/40 ring-1 ring-surface-200/50 dark:ring-surface-700/50 z-50 overflow-hidden"
          >
            <!-- 通知头部 -->
            <div class="px-4 py-3 border-b border-surface-100 dark:border-surface-700 bg-gradient-to-r from-surface-50 to-white dark:from-surface-800 dark:to-surface-800/80">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <div class="p-1.5 rounded-lg bg-gradient-to-br from-primary-100 to-primary-200/50 dark:from-primary-900/50 dark:to-primary-800/30">
                    <BellIcon class="w-4 h-4 text-primary-600 dark:text-primary-400" />
                  </div>
                  <span class="text-sm font-semibold text-surface-900 dark:text-white">通知中心</span>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    v-if="totalUnread > 0"
                    @click="markAllAsRead"
                    class="text-xs text-primary-500 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer font-medium"
                  >
                    全部已读
                  </button>
                  <button
                    class="p-1 rounded-lg text-surface-400 hover:text-surface-600 hover:bg-surface-100 dark:hover:bg-surface-700 dark:hover:text-surface-300 cursor-pointer transition-colors"
                    @click="notificationOpen = false"
                  >
                    <XMarkIcon class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <!-- 通知分类标签 -->
            <div class="px-4 py-2 border-b border-surface-100 dark:border-surface-700 flex gap-1">
              <button
                v-for="tab in notificationTabs"
                :key="tab.key"
                @click="activeNotificationTab = tab.key"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all cursor-pointer"
                :class="[
                  activeNotificationTab === tab.key
                    ? 'bg-primary-500 text-white shadow-md shadow-primary-500/30'
                    : 'text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-700'
                ]"
              >
                {{ tab.label }}
                <span
                  v-if="tab.count > 0"
                  class="ml-1 px-1.5 py-0.5 text-[10px] rounded-full"
                  :class="[
                    activeNotificationTab === tab.key
                      ? 'bg-white/20 text-white'
                      : 'bg-surface-200 dark:bg-surface-600 text-surface-600 dark:text-surface-300'
                  ]"
                >
                  {{ tab.count }}
                </span>
              </button>
            </div>

            <!-- 通知内容 -->
            <div class="max-h-80 overflow-y-auto">
              <div v-if="loadingNotifications" class="p-8 text-center">
                <div class="w-8 h-8 rounded-full border-2 border-primary-200 border-t-primary-600 animate-spin mx-auto mb-2"></div>
                <p class="text-sm text-surface-500">加载中...</p>
              </div>

              <div v-else-if="currentNotifications.length === 0" class="p-8 text-center">
                <div class="w-14 h-14 rounded-2xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mx-auto mb-3">
                  <CheckCircleIcon class="w-7 h-7 text-emerald-500" />
                </div>
                <p class="text-sm font-medium text-surface-700 dark:text-surface-300">暂无新通知</p>
                <p class="text-xs text-surface-400 mt-1">所有事务运行正常</p>
              </div>

              <ul v-else class="divide-y divide-surface-100 dark:divide-surface-700">
                <li
                  v-for="notification in currentNotifications"
                  :key="notification.id"
                  class="px-4 py-3 hover:bg-surface-50 dark:hover:bg-surface-700/50 transition-colors cursor-pointer relative group"
                  :class="{ 'bg-primary-50/50 dark:bg-primary-900/10': !notification.read }"
                  @click="handleNotificationClick(notification)"
                >
                  <!-- 未读指示器 -->
                  <div
                    v-if="!notification.read"
                    class="absolute left-1.5 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-primary-500"
                  ></div>

                  <div class="flex gap-3">
                    <!-- 图标 -->
                    <div
                      class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
                      :class="getNotificationIconClass(notification.type)"
                    >
                      <component :is="getNotificationIcon(notification.type)" class="w-4 h-4" />
                    </div>

                    <!-- 内容 -->
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-surface-900 dark:text-white line-clamp-2">
                        {{ notification.title }}
                      </p>
                      <p v-if="notification.message" class="text-xs text-surface-500 dark:text-surface-400 mt-0.5 line-clamp-1">
                        {{ notification.message }}
                      </p>
                      <p class="text-[10px] text-surface-400 mt-1 flex items-center">
                        <ClockIcon class="w-3 h-3 mr-1" />
                        {{ formatNotificationTime(notification.timestamp) }}
                        <span v-if="notification.module" class="ml-2">· {{ notification.module }}</span>
                      </p>
                    </div>

                    <!-- 删除按钮 -->
                    <button
                      @click.stop="dismissNotification(notification)"
                      class="flex-shrink-0 p-1 rounded-lg opacity-0 group-hover:opacity-100 text-surface-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all cursor-pointer"
                    >
                      <XMarkIcon class="w-4 h-4" />
                    </button>
                  </div>
                </li>
              </ul>
            </div>

            <!-- 底部操作 -->
            <div class="px-4 py-3 border-t border-surface-100 dark:border-surface-700 bg-surface-50/50 dark:bg-surface-900/30 flex items-center justify-between">
              <button
                @click="goToLogs"
                class="text-xs text-primary-500 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer font-medium flex items-center gap-1"
              >
                <DocumentTextIcon class="w-3.5 h-3.5" />
                查看系统日志
              </button>
              <button
                v-if="notifications.length > 0"
                @click="clearAllNotifications"
                class="text-xs text-surface-400 hover:text-red-500 cursor-pointer flex items-center gap-1"
              >
                <TrashIcon class="w-3.5 h-3.5" />
                清空通知
              </button>
            </div>
          </div>
        </transition>
      </div>

      <!-- Dark mode toggle -->
      <button
        @click="settingsStore.toggleDarkMode"
        class="p-2.5 rounded-xl text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-all duration-200 cursor-pointer"
      >
        <SunIcon v-if="settingsStore.darkMode" class="h-5 w-5 text-amber-500" />
        <MoonIcon v-else class="h-5 w-5" />
      </button>

      <!-- Divider -->
      <div class="hidden sm:block w-px h-8 bg-surface-200 dark:bg-surface-700"></div>

      <!-- User menu -->
      <Menu as="div" class="relative">
        <MenuButton class="flex items-center space-x-3 p-1.5 pr-3 rounded-xl hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors cursor-pointer">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/20 overflow-hidden"
               style="background: var(--gradient-primary)">
            <span class="text-white text-sm font-bold">
              {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
            </span>
          </div>
          <div class="hidden sm:flex flex-col items-start">
            <span class="text-sm font-medium text-surface-700 dark:text-surface-200">
              {{ authStore.user?.username || 'User' }}
            </span>
            <span class="text-xs text-surface-500 dark:text-surface-400">管理员</span>
          </div>
          <ChevronDownIcon class="hidden sm:block h-4 w-4 text-surface-400" />
        </MenuButton>

        <transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="transform opacity-0 scale-95 -translate-y-2"
          enter-to-class="transform opacity-100 scale-100 translate-y-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="transform opacity-100 scale-100 translate-y-0"
          leave-to-class="transform opacity-0 scale-95 -translate-y-2"
        >
          <MenuItems class="absolute right-0 mt-2 w-56 origin-top-right bg-white dark:bg-surface-800 rounded-2xl shadow-xl shadow-surface-900/10 dark:shadow-black/30 ring-1 ring-surface-200/50 dark:ring-surface-700/50 focus:outline-none z-50 p-1.5 overflow-hidden">
            <div class="px-3 py-2.5 border-b border-surface-100 dark:border-surface-700 mb-1.5">
              <p class="text-sm font-medium text-surface-900 dark:text-white">{{ authStore.user?.username }}</p>
              <p class="text-xs text-surface-500 dark:text-surface-400">admin@ptmanager.local</p>
            </div>
            <MenuItem v-slot="{ active }">
              <button
                @click="goToSettings('profile')"
                class="w-full flex items-center space-x-2 px-3 py-2.5 text-sm rounded-xl transition-colors cursor-pointer"
                :class="[
                  active ? 'bg-surface-100 dark:bg-surface-700' : '',
                  'text-surface-700 dark:text-surface-300'
                ]"
              >
                <UserCircleIcon class="w-4 h-4" />
                <span>个人设置</span>
              </button>
            </MenuItem>
            <MenuItem v-slot="{ active }">
              <button
                @click="goToSettings('system')"
                class="w-full flex items-center space-x-2 px-3 py-2.5 text-sm rounded-xl transition-colors cursor-pointer"
                :class="[
                  active ? 'bg-surface-100 dark:bg-surface-700' : '',
                  'text-surface-700 dark:text-surface-300'
                ]"
              >
                <Cog6ToothIcon class="w-4 h-4" />
                <span>系统设置</span>
              </button>
            </MenuItem>
            <div class="border-t border-surface-100 dark:border-surface-700 mt-1.5 pt-1.5">
              <MenuItem v-slot="{ active }">
                <button
                  @click="showLogoutConfirm = true"
                  class="w-full flex items-center space-x-2 px-3 py-2.5 text-sm rounded-xl transition-colors cursor-pointer"
                  :class="[
                    active ? 'bg-red-50 dark:bg-red-900/20' : '',
                    'text-red-600 dark:text-red-400'
                  ]"
                >
                  <ArrowRightOnRectangleIcon class="w-4 h-4" />
                  <span>退出登录</span>
                </button>
              </MenuItem>
            </div>
          </MenuItems>
        </transition>
      </Menu>
    </div>
  </header>

  <!-- 搜索弹窗 -->
  <TransitionRoot appear :show="searchOpen" as="template">
    <Dialog as="div" @close="searchOpen = false" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-200 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-150 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-surface-900/60 dark:bg-black/70 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto p-4 pt-[15vh]">
        <TransitionChild
          as="template"
          enter="duration-200 ease-out"
          enter-from="opacity-0 scale-95 -translate-y-4"
          enter-to="opacity-100 scale-100 translate-y-0"
          leave="duration-150 ease-in"
          leave-from="opacity-100 scale-100 translate-y-0"
          leave-to="opacity-0 scale-95 -translate-y-4"
        >
          <DialogPanel class="mx-auto max-w-xl transform overflow-hidden rounded-2xl bg-white dark:bg-surface-800 shadow-2xl ring-1 ring-surface-200/50 dark:ring-surface-700/50 transition-all">
            <!-- 搜索输入 -->
            <div class="relative">
              <MagnifyingGlassIcon class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
              <input
                ref="searchInput"
                v-model="searchQuery"
                type="text"
                placeholder="搜索页面、功能或设置..."
                class="w-full pl-12 pr-4 py-4 text-base bg-transparent border-0 border-b border-surface-200 dark:border-surface-700 text-surface-900 dark:text-white placeholder-surface-400 focus:outline-none focus:ring-0"
                @keydown.enter="handleSearchSelect(filteredSearchResults[selectedSearchIndex])"
                @keydown.up.prevent="selectedSearchIndex = Math.max(0, selectedSearchIndex - 1)"
                @keydown.down.prevent="selectedSearchIndex = Math.min(filteredSearchResults.length - 1, selectedSearchIndex + 1)"
                @keydown.esc="searchOpen = false"
              />
              <div class="absolute right-4 top-1/2 -translate-y-1/2">
                <kbd class="px-2 py-1 text-xs font-medium text-surface-400 bg-surface-100 dark:bg-surface-700 rounded">ESC</kbd>
              </div>
            </div>

            <!-- 搜索结果 -->
            <div class="max-h-80 overflow-y-auto py-2">
              <div v-if="searchQuery && filteredSearchResults.length === 0" class="px-4 py-8 text-center">
                <p class="text-sm text-surface-500">未找到匹配的结果</p>
              </div>

              <template v-else>
                <div v-if="!searchQuery" class="px-4 py-2">
                  <p class="text-xs font-medium text-surface-400 uppercase tracking-wider">快速导航</p>
                </div>
                <ul class="px-2">
                  <li
                    v-for="(item, index) in filteredSearchResults"
                    :key="item.path"
                    @click="handleSearchSelect(item)"
                    @mouseenter="selectedSearchIndex = index"
                    class="px-3 py-2.5 rounded-xl cursor-pointer flex items-center gap-3 transition-colors"
                    :class="[
                      index === selectedSearchIndex
                        ? 'bg-primary-500 text-white'
                        : 'text-surface-700 dark:text-surface-300 hover:bg-surface-100 dark:hover:bg-surface-700'
                    ]"
                  >
                    <div
                      class="w-9 h-9 rounded-xl flex items-center justify-center"
                      :class="[
                        index === selectedSearchIndex
                          ? 'bg-white/20'
                          : 'bg-surface-100 dark:bg-surface-700'
                      ]"
                    >
                      <component :is="item.icon" class="w-5 h-5" />
                    </div>
                    <div class="flex-1">
                      <p class="text-sm font-medium">{{ item.name }}</p>
                      <p
                        class="text-xs mt-0.5"
                        :class="index === selectedSearchIndex ? 'text-white/70' : 'text-surface-400'"
                      >
                        {{ item.description }}
                      </p>
                    </div>
                    <ChevronRightIcon
                      class="w-4 h-4"
                      :class="index === selectedSearchIndex ? 'text-white/70' : 'text-surface-300'"
                    />
                  </li>
                </ul>
              </template>
            </div>

            <!-- 底部提示 -->
            <div class="px-4 py-2.5 border-t border-surface-200 dark:border-surface-700 bg-surface-50/50 dark:bg-surface-900/30 flex items-center gap-4 text-xs text-surface-400">
              <span class="flex items-center gap-1">
                <kbd class="px-1.5 py-0.5 bg-surface-200 dark:bg-surface-700 rounded">↑</kbd>
                <kbd class="px-1.5 py-0.5 bg-surface-200 dark:bg-surface-700 rounded">↓</kbd>
                导航
              </span>
              <span class="flex items-center gap-1">
                <kbd class="px-1.5 py-0.5 bg-surface-200 dark:bg-surface-700 rounded">↵</kbd>
                选择
              </span>
              <span class="flex items-center gap-1">
                <kbd class="px-1.5 py-0.5 bg-surface-200 dark:bg-surface-700 rounded">ESC</kbd>
                关闭
              </span>
            </div>
          </DialogPanel>
        </TransitionChild>
      </div>
    </Dialog>
  </TransitionRoot>

  <!-- Mobile menu -->
  <TransitionRoot as="template" :show="mobileMenuOpen">
    <Dialog as="div" class="relative z-50 lg:hidden" @close="mobileMenuOpen = false">
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-300"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-surface-900/80 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 flex">
        <TransitionChild
          as="template"
          enter="transition ease-in-out duration-300 transform"
          enter-from="-translate-x-full"
          enter-to="translate-x-0"
          leave="transition ease-in-out duration-300 transform"
          leave-from="translate-x-0"
          leave-to="-translate-x-full"
        >
          <DialogPanel class="relative mr-16 flex w-full max-w-xs flex-1">
            <!-- Close button -->
            <TransitionChild
              as="template"
              enter="ease-in-out duration-300"
              enter-from="opacity-0"
              enter-to="opacity-100"
              leave="ease-in-out duration-300"
              leave-from="opacity-100"
              leave-to="opacity-0"
            >
              <div class="absolute left-full top-0 flex w-16 justify-center pt-5">
                <button type="button" class="-m-2.5 p-2.5 cursor-pointer" @click="mobileMenuOpen = false">
                  <XMarkIcon class="h-6 w-6 text-white" />
                </button>
              </div>
            </TransitionChild>

            <div class="flex grow flex-col overflow-y-auto bg-white dark:bg-surface-900 px-6 pb-4">
              <div class="flex h-16 shrink-0 items-center">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30 overflow-hidden"
                       style="background: var(--gradient-primary)">
                    <span class="text-white font-bold text-lg">PT</span>
                  </div>
                  <div>
                    <span class="font-bold text-surface-900 dark:text-white">Manager Pro</span>
                    <p class="text-xs text-surface-500 dark:text-surface-400">PT 管理系统</p>
                  </div>
                </div>
              </div>
              <nav class="flex flex-1 flex-col mt-6">
                <ul role="list" class="flex flex-1 flex-col gap-y-2">
                  <li v-for="item in navItems" :key="item.path">
                    <router-link
                      :to="item.path"
                      @click="mobileMenuOpen = false"
                      class="group flex items-center gap-x-3 rounded-xl p-3 text-sm font-medium transition-colors"
                      :class="[
                        $route.path === item.path
                          ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400'
                          : 'text-surface-700 dark:text-surface-300 hover:bg-surface-50 dark:hover:bg-surface-800'
                      ]"
                    >
                      <div
                        class="flex items-center justify-center w-9 h-9 rounded-xl transition-colors"
                        :class="[
                          $route.path === item.path
                            ? 'text-white shadow-lg shadow-primary-500/30'
                            : 'bg-surface-100 dark:bg-surface-800 group-hover:bg-surface-200 dark:group-hover:bg-surface-700'
                        ]"
                        :style="$route.path === item.path ? { background: 'var(--gradient-primary)' } : {}"
                      >
                        <component :is="item.icon" class="h-5 w-5 shrink-0" />
                      </div>
                      {{ item.name }}
                    </router-link>
                  </li>
                </ul>
              </nav>
            </div>
          </DialogPanel>
        </TransitionChild>
      </div>
    </Dialog>
  </TransitionRoot>

  <!-- 退出确认对话框 -->
  <TransitionRoot appear :show="showLogoutConfirm" as="template">
    <Dialog as="div" @close="showLogoutConfirm = false" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-surface-900/60 dark:bg-black/70 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full max-w-sm transform overflow-hidden rounded-2xl bg-white dark:bg-surface-800 p-6 text-left align-middle shadow-2xl transition-all">
              <div class="flex items-center justify-center w-14 h-14 mx-auto rounded-2xl bg-red-100 dark:bg-red-900/30 mb-4">
                <ArrowRightOnRectangleIcon class="w-7 h-7 text-red-600 dark:text-red-400" />
              </div>
              <DialogTitle as="h3" class="text-lg font-semibold text-center text-surface-900 dark:text-white">
                确认退出登录
              </DialogTitle>
              <div class="mt-2">
                <p class="text-sm text-center text-surface-500 dark:text-surface-400">
                  您确定要退出登录吗？退出后需要重新输入账号密码。
                </p>
              </div>

              <div class="mt-6 flex space-x-3">
                <button
                  type="button"
                  class="flex-1 btn-secondary cursor-pointer"
                  :disabled="loggingOut"
                  @click="showLogoutConfirm = false"
                >
                  取消
                </button>
                <button
                  type="button"
                  class="flex-1 btn-danger cursor-pointer flex items-center justify-center gap-2"
                  :disabled="loggingOut"
                  @click="confirmLogout"
                >
                  <svg v-if="loggingOut" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {{ loggingOut ? '退出中...' : '确认退出' }}
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import {
  Bars3Icon,
  SunIcon,
  MoonIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  HomeIcon,
  ServerIcon,
  RssIcon,
  TrashIcon,
  BoltIcon,
  SparklesIcon,
  DocumentTextIcon,
  ChartBarIcon,
  XMarkIcon,
  BellIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
  SignalIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { logsApi } from '@/api'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import { getToast } from '@/composables/useToast'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const toast = getToast()

// Ensure consistent timestamp parsing (backend returns naive UTC datetimes)
dayjs.extend(utc)
dayjs.extend(timezone)
const localTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone

const mobileMenuOpen = ref(false)
const notificationOpen = ref(false)
const showLogoutConfirm = ref(false)
const loggingOut = ref(false)
const loadingNotifications = ref(false)
const notifications = ref([])
const activeNotificationTab = ref('all')

// 搜索相关
const searchOpen = ref(false)
const searchQuery = ref('')
const searchInput = ref(null)
const selectedSearchIndex = ref(0)

let notificationIntervalId

const navItems = [
  { name: '仪表盘', path: '/', icon: HomeIcon, description: '系统概览和实时数据' },
  { name: '下载器', path: '/downloaders', icon: ServerIcon, description: '管理 qBittorrent 等下载器' },
  { name: 'RSS订阅', path: '/rss', icon: RssIcon, description: '自动订阅和下载种子' },
  { name: '删种规则', path: '/delete-rules', icon: TrashIcon, description: '自动清理过期种子' },
  { name: '动态限速', path: '/speed-limit', icon: BoltIcon, description: '智能速度限制规则' },
  { name: 'U2追魔', path: '/u2-magic', icon: SparklesIcon, description: 'U2 魔力值自动追踪' },
  { name: 'Netcup监控', path: '/netcup', icon: SignalIcon, description: 'Netcup 服务器监控' },
  { name: '数据统计', path: '/statistics', icon: ChartBarIcon, description: '流量和数据分析' },
  { name: '系统日志', path: '/logs', icon: DocumentTextIcon, description: '查看系统运行日志' },
  { name: '系统设置', path: '/settings', icon: Cog6ToothIcon, description: '配置系统参数' },
]

const currentPageTitle = computed(() => {
  const item = navItems.find(i => i.path === route.path)
  return item?.name || 'PT Manager'
})

// 搜索结果过滤
const filteredSearchResults = computed(() => {
  if (!searchQuery.value) {
    return navItems
  }
  const query = searchQuery.value.toLowerCase()
  return navItems.filter(item =>
    item.name.toLowerCase().includes(query) ||
    item.description.toLowerCase().includes(query)
  )
})

// 监听搜索结果变化重置选中索引
watch(searchQuery, () => {
  selectedSearchIndex.value = 0
})

// 通知分类
const notificationTabs = computed(() => [
  { key: 'all', label: '全部', count: notifications.value.filter(n => !n.read).length },
  { key: 'error', label: '错误', count: notifications.value.filter(n => n.type === 'error' && !n.read).length },
  { key: 'warning', label: '警告', count: notifications.value.filter(n => n.type === 'warning' && !n.read).length },
  { key: 'info', label: '信息', count: notifications.value.filter(n => n.type === 'info' && !n.read).length },
])

// 当前分类的通知
const currentNotifications = computed(() => {
  if (activeNotificationTab.value === 'all') {
    return notifications.value
  }
  return notifications.value.filter(n => n.type === activeNotificationTab.value)
})

// 未读总数
const totalUnread = computed(() => notifications.value.filter(n => !n.read).length)

// 是否有错误
const hasErrors = computed(() => notifications.value.some(n => n.type === 'error' && !n.read))

function goToSettings(tab) {
  router.push({ path: '/settings', query: { tab } })
}

function goToLogs() {
  notificationOpen.value = false
  router.push('/logs')
}

async function confirmLogout() {
  loggingOut.value = true
  try {
    await authStore.logout()
    toast.success('已退出登录')
    showLogoutConfirm.value = false
    router.push('/login')
  } catch (e) {
    toast.error('退出登录失败')
  } finally {
    loggingOut.value = false
  }
}

function formatNotificationTime(timestamp) {
  if (!timestamp) return ''
  // Parse backend timestamps as UTC and convert to local timezone
  const date = dayjs.utc(timestamp).tz(localTimezone)
  const now = dayjs()
  const diff = now.valueOf() - date.valueOf()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`

  return date.format('MM-DD HH:mm')
}

function getNotificationIcon(type) {
  const icons = {
    error: ExclamationCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,
    success: CheckCircleIcon,
  }
  return icons[type] || InformationCircleIcon
}

function getNotificationIconClass(type) {
  const classes = {
    error: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    warning: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
    info: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
    success: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
  }
  return classes[type] || classes.info
}

// 已读通知ID存储key
const READ_NOTIFICATIONS_KEY = 'pt_manager_read_notifications'
const DISMISSED_NOTIFICATIONS_KEY = 'pt_manager_dismissed_notifications'

// 获取已读通知ID列表
function getReadNotificationIds() {
  try {
    const stored = localStorage.getItem(READ_NOTIFICATIONS_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

// 保存已读通知ID
function saveReadNotificationIds(ids) {
  try {
    // 只保留最近100条
    const trimmed = ids.slice(-100)
    localStorage.setItem(READ_NOTIFICATIONS_KEY, JSON.stringify(trimmed))
  } catch (e) {
    console.error('Failed to save read notifications:', e)
  }
}

// 获取已删除通知ID列表
function getDismissedNotificationIds() {
  try {
    const stored = localStorage.getItem(DISMISSED_NOTIFICATIONS_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

// 保存已删除通知ID
function saveDismissedNotificationIds(ids) {
  try {
    // 只保留最近100条
    const trimmed = ids.slice(-100)
    localStorage.setItem(DISMISSED_NOTIFICATIONS_KEY, JSON.stringify(trimmed))
  } catch (e) {
    console.error('Failed to save dismissed notifications:', e)
  }
}

async function loadNotifications() {
  loadingNotifications.value = true
  try {
    // 加载错误日志作为通知
    const response = await logsApi.getLogs({ limit: 20 })
    const logs = response.data || []

    // 获取已读和已删除的通知ID
    const readIds = getReadNotificationIds()
    const dismissedIds = getDismissedNotificationIds()

    // 转换日志为通知格式，过滤已删除的，并恢复已读状态
    notifications.value = logs
      .filter(log => !dismissedIds.includes(log.id?.toString()))
      .map((log, index) => {
        const id = log.id?.toString() || `log_${index}`
        return {
          id,
          type: log.level?.toLowerCase() === 'error' ? 'error'
              : log.level?.toLowerCase() === 'warning' ? 'warning'
              : 'info',
          title: log.message?.substring(0, 100) || '系统通知',
          message: log.message?.length > 100 ? log.message : '',
          module: log.module,
          timestamp: log.timestamp,
          read: readIds.includes(id),
        }
      })
  } catch (error) {
    console.error('Failed to load notifications:', error)
  } finally {
    loadingNotifications.value = false
  }
}

async function toggleNotifications() {
  notificationOpen.value = !notificationOpen.value
  if (notificationOpen.value) {
    await loadNotifications()
  }
}

function handleNotificationClick(notification) {
  notification.read = true
  // 保存已读状态
  const readIds = getReadNotificationIds()
  if (!readIds.includes(notification.id)) {
    readIds.push(notification.id)
    saveReadNotificationIds(readIds)
  }
}

function dismissNotification(notification) {
  const index = notifications.value.findIndex(n => n.id === notification.id)
  if (index > -1) {
    notifications.value.splice(index, 1)
    // 保存已删除状态
    const dismissedIds = getDismissedNotificationIds()
    if (!dismissedIds.includes(notification.id)) {
      dismissedIds.push(notification.id)
      saveDismissedNotificationIds(dismissedIds)
    }
  }
}

function markAllAsRead() {
  const readIds = getReadNotificationIds()
  notifications.value.forEach(n => {
    n.read = true
    if (!readIds.includes(n.id)) {
      readIds.push(n.id)
    }
  })
  saveReadNotificationIds(readIds)
}

function clearAllNotifications() {
  // 保存所有当前通知为已删除
  const dismissedIds = getDismissedNotificationIds()
  notifications.value.forEach(n => {
    if (!dismissedIds.includes(n.id)) {
      dismissedIds.push(n.id)
    }
  })
  saveDismissedNotificationIds(dismissedIds)
  notifications.value = []
  toast.success('通知已清空')
}

// 搜索功能
function openSearch() {
  searchOpen.value = true
  searchQuery.value = ''
  selectedSearchIndex.value = 0
  nextTick(() => {
    searchInput.value?.focus()
  })
}

function handleSearchSelect(item) {
  if (item) {
    router.push(item.path)
    searchOpen.value = false
  }
}

// 键盘快捷键
function handleKeydown(e) {
  // Cmd/Ctrl + K 打开搜索
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    openSearch()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  // 定期刷新通知计数
  notificationIntervalId = setInterval(loadNotifications, 120000)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (notificationIntervalId) {
    clearInterval(notificationIntervalId)
  }
})
</script>
