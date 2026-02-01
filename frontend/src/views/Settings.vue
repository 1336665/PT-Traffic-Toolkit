<template>
  <div class="space-y-6">
    <!-- 页头 -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center space-x-3">
        <div class="p-2.5 rounded-xl shadow-lg shadow-surface-500/30"
             style="background: var(--gradient-primary)">
          <Cog6ToothIcon class="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-white">系统设置</h2>
          <p class="text-sm text-surface-500 dark:text-surface-400">管理个人账户和系统配置</p>
        </div>
      </div>
    </div>

    <!-- 选项卡 -->
    <div class="border-b border-surface-200 dark:border-surface-700">
      <nav class="-mb-px flex space-x-8">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            activeTab === tab.id
              ? 'border-primary-500 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-surface-500 dark:text-surface-400 hover:text-surface-700 dark:hover:text-surface-300 hover:border-surface-300',
            'group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors'
          ]"
        >
          <component
            :is="tab.icon"
            :class="[
              activeTab === tab.id
                ? 'text-primary-500'
                : 'text-surface-400 group-hover:text-surface-500',
              '-ml-0.5 mr-2 h-5 w-5'
            ]"
          />
          {{ tab.name }}
        </button>
      </nav>
    </div>

    <!-- 个人设置 -->
    <div v-show="activeTab === 'profile'" class="space-y-6">
      <!-- 头像和基本信息 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
              <UserCircleIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">个人信息</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">管理您的账户信息</p>
            </div>
          </div>
        </template>

        <div class="flex items-center space-x-6 mb-6">
          <div class="flex-shrink-0">
            <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/30">
              <span class="text-white text-3xl font-bold">
                {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
              </span>
            </div>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-surface-900 dark:text-white">
              {{ authStore.user?.username || 'User' }}
            </h3>
            <p class="text-sm text-surface-500 dark:text-surface-400">管理员账户</p>
            <p class="text-xs text-surface-400 dark:text-surface-500 mt-1">
              创建于 {{ formatDate(authStore.user?.created_at) }}
            </p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input
              v-model="profileForm.username"
              type="text"
              class="form-input"
              placeholder="用户名"
            />
          </div>
          <div class="form-group">
            <label class="form-label">邮箱</label>
            <input
              v-model="profileForm.email"
              type="email"
              class="form-input"
              placeholder="可选"
            />
          </div>
        </div>

        <div class="flex justify-end mt-4">
          <Button variant="primary" @click="saveProfile" :loading="savingProfile">
            <CheckIcon class="w-4 h-4" />
            保存信息
          </Button>
        </div>
      </Card>

      <!-- 修改密码 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/30">
              <KeyIcon class="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">修改密码</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">更新您的登录密码</p>
            </div>
          </div>
        </template>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="form-group">
            <label class="form-label">当前密码</label>
            <input
              v-model="passwordForm.currentPassword"
              type="password"
              class="form-input"
              placeholder="输入当前密码"
            />
          </div>
          <div class="form-group">
            <label class="form-label">新密码</label>
            <input
              v-model="passwordForm.newPassword"
              type="password"
              class="form-input"
              placeholder="至少6位字符"
            />
          </div>
          <div class="form-group">
            <label class="form-label">确认新密码</label>
            <input
              v-model="passwordForm.confirmPassword"
              type="password"
              class="form-input"
              placeholder="再次输入新密码"
            />
          </div>
        </div>

        <div v-if="passwordError" class="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
          {{ passwordError }}
        </div>

        <div class="flex justify-end mt-4">
          <Button variant="primary" @click="changePassword" :loading="changingPassword">
            <KeyIcon class="w-4 h-4" />
            修改密码
          </Button>
        </div>
      </Card>
    </div>

    <!-- 通知设置 -->
    <div v-show="activeTab === 'notifications'" class="space-y-6">
      <!-- Telegram 配置 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <PaperAirplaneIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">Telegram 通知</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">配置 Telegram Bot 接收系统通知</p>
            </div>
          </div>
        </template>

        <div class="space-y-4">
          <!-- 启用开关 -->
          <div class="flex items-center justify-between p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-lg bg-surface-100 dark:bg-surface-600">
                <BellIcon class="w-5 h-5 text-surface-600 dark:text-surface-300" />
              </div>
              <div>
                <p class="font-medium text-surface-900 dark:text-white">启用 Telegram 通知</p>
                <p class="text-sm text-surface-500 dark:text-surface-400">开启后将通过 Telegram 发送系统通知</p>
              </div>
            </div>
            <button
              @click="telegramForm.enabled = !telegramForm.enabled"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                telegramForm.enabled ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  telegramForm.enabled ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>

          <!-- Bot Token -->
          <div class="form-group">
            <label class="form-label">Bot Token</label>
            <input
              v-model="telegramForm.bot_token"
              type="password"
              class="form-input font-mono"
              placeholder="从 @BotFather 获取的 Token"
            />
            <p class="text-xs text-surface-500 dark:text-surface-400 mt-1">
              通过 Telegram 的 @BotFather 创建 Bot 并获取 Token
            </p>
          </div>

          <!-- Chat ID -->
          <div class="form-group">
            <label class="form-label">Chat ID</label>
            <input
              v-model="telegramForm.chat_id"
              type="text"
              class="form-input font-mono"
              placeholder="您的 Telegram Chat ID"
            />
            <p class="text-xs text-surface-500 dark:text-surface-400 mt-1">
              可以通过 @userinfobot 获取您的 Chat ID
            </p>
          </div>

          <!-- 测试结果 -->
          <div v-if="telegramTestResult" :class="[
            'p-4 rounded-xl',
            telegramTestResult.success
              ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
              : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
          ]">
            <div class="flex items-center space-x-2">
              <CheckIcon v-if="telegramTestResult.success" class="w-5 h-5" />
              <ExclamationTriangleIcon v-else class="w-5 h-5" />
              <span>{{ telegramTestResult.message }}</span>
            </div>
          </div>

          <div class="flex justify-end space-x-3">
            <Button variant="secondary" @click="testTelegram" :loading="testingTelegram">
              <PaperAirplaneIcon class="w-4 h-4" />
              测试连接
            </Button>
            <Button variant="primary" @click="saveTelegramSettings" :loading="savingTelegram">
              <CheckIcon class="w-4 h-4" />
              保存设置
            </Button>
          </div>
        </div>
      </Card>

      <!-- 通知类型 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
              <BellIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">通知类型</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">选择要接收的通知类型</p>
            </div>
          </div>
        </template>

        <div class="space-y-3">
          <div class="flex items-center justify-between p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <div>
              <p class="font-medium text-surface-900 dark:text-white">RSS 下载通知</p>
              <p class="text-sm text-surface-500 dark:text-surface-400">新种子下载时发送通知</p>
            </div>
            <button
              @click="notificationToggles.notify_rss_download = !notificationToggles.notify_rss_download"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                notificationToggles.notify_rss_download ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  notificationToggles.notify_rss_download ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>

          <div class="flex items-center justify-between p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <div>
              <p class="font-medium text-surface-900 dark:text-white">删除规则通知</p>
              <p class="text-sm text-surface-500 dark:text-surface-400">种子被删除时发送通知</p>
            </div>
            <button
              @click="notificationToggles.notify_delete = !notificationToggles.notify_delete"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                notificationToggles.notify_delete ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  notificationToggles.notify_delete ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>

          <div class="flex items-center justify-between p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <div>
              <p class="font-medium text-surface-900 dark:text-white">限速汇报通知</p>
              <p class="text-sm text-surface-500 dark:text-surface-400">限速状态汇报时发送通知</p>
            </div>
            <button
              @click="notificationToggles.notify_speed_limit = !notificationToggles.notify_speed_limit"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                notificationToggles.notify_speed_limit ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  notificationToggles.notify_speed_limit ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>

          <div class="flex items-center justify-between p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <div>
              <p class="font-medium text-surface-900 dark:text-white">错误警报</p>
              <p class="text-sm text-surface-500 dark:text-surface-400">系统错误时发送通知</p>
            </div>
            <button
              @click="notificationToggles.notify_error = !notificationToggles.notify_error"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                notificationToggles.notify_error ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  notificationToggles.notify_error ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>

          <div class="flex items-center justify-between p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <div>
              <p class="font-medium text-surface-900 dark:text-white">磁盘空间警告</p>
              <p class="text-sm text-surface-500 dark:text-surface-400">磁盘空间不足时发送通知</p>
            </div>
            <button
              @click="notificationToggles.notify_low_disk = !notificationToggles.notify_low_disk"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                notificationToggles.notify_low_disk ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  notificationToggles.notify_low_disk ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>
        </div>

        <div class="flex justify-end mt-4">
          <Button variant="primary" @click="saveTelegramSettings" :loading="savingTelegram">
            <CheckIcon class="w-4 h-4" />
            保存设置
          </Button>
        </div>
      </Card>
    </div>

    <!-- 系统设置 -->
    <div v-show="activeTab === 'system'" class="space-y-6">
      <!-- 网站设置 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
              <GlobeAltIcon class="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">网站设置</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">自定义网站名称和介绍</p>
            </div>
          </div>
        </template>

        <div class="space-y-4">
          <div class="form-group">
            <label class="form-label">网站名称</label>
            <input
              v-model="siteForm.site_name"
              type="text"
              class="form-input"
              placeholder="PT Manager"
            />
            <p class="text-xs text-surface-500 dark:text-surface-400 mt-1">
              显示在浏览器标题和侧边栏的名称
            </p>
          </div>

          <div class="form-group">
            <label class="form-label">网站介绍</label>
            <textarea
              v-model="siteForm.site_description"
              rows="2"
              class="form-input"
              placeholder="PT 流量管理工具"
            ></textarea>
            <p class="text-xs text-surface-500 dark:text-surface-400 mt-1">
              显示在登录页面和侧边栏的描述
            </p>
          </div>

          <div class="flex justify-end">
            <Button variant="primary" @click="saveSiteSettings" :loading="savingSite">
              <CheckIcon class="w-4 h-4" />
              保存设置
            </Button>
          </div>
        </div>
      </Card>

      <!-- 外观设置 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
              <SwatchIcon class="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">外观设置</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">自定义界面显示</p>
            </div>
          </div>
        </template>

        <div class="space-y-4">
          <!-- 深色模式 -->
          <div class="flex items-center justify-between p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-lg bg-surface-100 dark:bg-surface-600">
                <MoonIcon class="w-5 h-5 text-surface-600 dark:text-surface-300" />
              </div>
              <div>
                <p class="font-medium text-surface-900 dark:text-white">深色模式</p>
                <p class="text-sm text-surface-500 dark:text-surface-400">启用深色主题减少眼睛疲劳</p>
              </div>
            </div>
            <button
              @click="settingsStore.toggleDarkMode"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                settingsStore.darkMode ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  settingsStore.darkMode ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>

          <!-- 侧边栏折叠 -->
          <div class="flex items-center justify-between p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <div class="flex items-center space-x-3">
              <div class="p-2 rounded-lg bg-surface-100 dark:bg-surface-600">
                <Bars3BottomLeftIcon class="w-5 h-5 text-surface-600 dark:text-surface-300" />
              </div>
              <div>
                <p class="font-medium text-surface-900 dark:text-white">紧凑侧边栏</p>
                <p class="text-sm text-surface-500 dark:text-surface-400">折叠侧边栏以获得更多空间</p>
              </div>
            </div>
            <button
              @click="settingsStore.toggleSidebar"
              :class="[
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none',
                settingsStore.sidebarCollapsed ? 'bg-primary-600' : 'bg-surface-200 dark:bg-surface-600'
              ]"
            >
              <span
                :class="[
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                  settingsStore.sidebarCollapsed ? 'translate-x-5' : 'translate-x-0'
                ]"
              />
            </button>
          </div>
        </div>
      </Card>

      <!-- 系统信息 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <InformationCircleIcon class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">系统信息</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">查看系统版本和状态</p>
            </div>
          </div>
        </template>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div class="p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <p class="text-sm text-surface-500 dark:text-surface-400">版本号</p>
            <p class="text-lg font-semibold text-surface-900 dark:text-white mt-1">v1.0.0</p>
          </div>
          <div class="p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <p class="text-sm text-surface-500 dark:text-surface-400">前端框架</p>
            <p class="text-lg font-semibold text-surface-900 dark:text-white mt-1">Vue 3 + Vite</p>
          </div>
          <div class="p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <p class="text-sm text-surface-500 dark:text-surface-400">UI框架</p>
            <p class="text-lg font-semibold text-surface-900 dark:text-white mt-1">Tailwind CSS</p>
          </div>
        </div>
      </Card>

      <!-- 数据管理 -->
      <Card>
        <template #header>
          <div class="flex items-center space-x-3">
            <div class="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
              <ExclamationTriangleIcon class="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h3 class="font-semibold text-surface-900 dark:text-white">数据管理</h3>
              <p class="text-xs text-surface-500 dark:text-surface-400">管理系统数据和缓存</p>
            </div>
          </div>
        </template>

        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 rounded-xl bg-surface-50 dark:bg-surface-700/30">
            <div>
              <p class="font-medium text-surface-900 dark:text-white">清除本地缓存</p>
              <p class="text-sm text-surface-500 dark:text-surface-400">清除浏览器中存储的临时数据</p>
            </div>
            <Button variant="secondary" size="sm" @click="clearLocalCache">
              <TrashIcon class="w-4 h-4" />
              清除缓存
            </Button>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { authApi, settingsApi } from '@/api'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import {
  Cog6ToothIcon,
  UserCircleIcon,
  KeyIcon,
  SwatchIcon,
  MoonIcon,
  Bars3BottomLeftIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  TrashIcon,
  CheckIcon,
  BellIcon,
  PaperAirplaneIcon,
  GlobeAltIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const tabs = [
  { id: 'profile', name: '个人设置', icon: UserCircleIcon },
  { id: 'notifications', name: '通知设置', icon: BellIcon },
  { id: 'system', name: '系统设置', icon: Cog6ToothIcon },
]

const activeTab = ref(route.query.tab || 'profile')
const savingProfile = ref(false)
const changingPassword = ref(false)
const passwordError = ref('')
const savingTelegram = ref(false)
const testingTelegram = ref(false)
const telegramTestResult = ref(null)
const savingSite = ref(false)

const profileForm = reactive({
  username: authStore.user?.username || '',
  email: authStore.user?.email || '',
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const telegramForm = reactive({
  bot_token: '',
  chat_id: '',
  enabled: false,
})

const notificationToggles = reactive({
  notify_rss_download: true,
  notify_delete: true,
  notify_speed_limit: true,
  notify_error: true,
  notify_low_disk: true,
})

const siteForm = reactive({
  site_name: 'PT Manager',
  site_description: 'PT 流量管理工具',
})

function formatDate(dateStr) {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

async function saveProfile() {
  savingProfile.value = true
  try {
    // TODO: 实现保存个人信息的 API 调用
    await new Promise(resolve => setTimeout(resolve, 500))
    alert('个人信息保存成功')
  } catch (error) {
    console.error('Failed to save profile:', error)
    alert('保存失败')
  } finally {
    savingProfile.value = false
  }
}

async function changePassword() {
  passwordError.value = ''

  if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
    passwordError.value = '请填写所有密码字段'
    return
  }

  if (passwordForm.newPassword.length < 6) {
    passwordError.value = '新密码至少需要6位字符'
    return
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }

  changingPassword.value = true
  try {
    await authApi.changePassword(passwordForm.currentPassword, passwordForm.newPassword)
    alert('密码修改成功')
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (error) {
    passwordError.value = error.response?.data?.detail || '密码修改失败'
  } finally {
    changingPassword.value = false
  }
}

function clearLocalCache() {
  if (confirm('确定要清除本地缓存吗？这将清除所有本地存储的数据。')) {
    localStorage.clear()
    sessionStorage.clear()
    alert('缓存已清除，页面将刷新')
    window.location.reload()
  }
}

async function loadTelegramSettings() {
  try {
    const response = await settingsApi.getNotifications()
    const data = response.data
    telegramForm.bot_token = data.telegram.bot_token
    telegramForm.chat_id = data.telegram.chat_id
    telegramForm.enabled = data.telegram.enabled
    notificationToggles.notify_rss_download = data.notify_rss_download
    notificationToggles.notify_delete = data.notify_delete
    notificationToggles.notify_speed_limit = data.notify_speed_limit
    notificationToggles.notify_error = data.notify_error
    notificationToggles.notify_low_disk = data.notify_low_disk
  } catch (error) {
    console.error('Failed to load notification settings:', error)
  }
}

async function saveTelegramSettings() {
  savingTelegram.value = true
  try {
    await settingsApi.updateNotifications({
      telegram: {
        bot_token: telegramForm.bot_token,
        chat_id: telegramForm.chat_id,
        enabled: telegramForm.enabled,
      },
      notify_rss_download: notificationToggles.notify_rss_download,
      notify_delete: notificationToggles.notify_delete,
      notify_speed_limit: notificationToggles.notify_speed_limit,
      notify_error: notificationToggles.notify_error,
      notify_low_disk: notificationToggles.notify_low_disk,
    })
    alert('通知设置保存成功')
  } catch (error) {
    console.error('Failed to save telegram settings:', error)
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    savingTelegram.value = false
  }
}

async function testTelegram() {
  testingTelegram.value = true
  telegramTestResult.value = null
  try {
    // First save the current settings
    await settingsApi.updateTelegram({
      bot_token: telegramForm.bot_token,
      chat_id: telegramForm.chat_id,
      enabled: telegramForm.enabled,
    })
    // Then test
    const response = await settingsApi.testTelegram()
    telegramTestResult.value = response.data
  } catch (error) {
    console.error('Failed to test telegram:', error)
    telegramTestResult.value = {
      success: false,
      message: error.response?.data?.detail || error.message,
    }
  } finally {
    testingTelegram.value = false
  }
}

async function loadSiteSettings() {
  try {
    const response = await settingsApi.getSite()
    siteForm.site_name = response.data.site_name
    siteForm.site_description = response.data.site_description
  } catch (error) {
    console.error('Failed to load site settings:', error)
  }
}

async function saveSiteSettings() {
  savingSite.value = true
  try {
    await settingsApi.updateSite({
      site_name: siteForm.site_name,
      site_description: siteForm.site_description,
    })
    // Update document title
    document.title = siteForm.site_name
    // Update settings store to refresh sidebar
    const settingsStore = useSettingsStore()
    settingsStore.siteName = siteForm.site_name
    settingsStore.siteDescription = siteForm.site_description
    // Also update localStorage
    localStorage.setItem('siteName', siteForm.site_name)
    localStorage.setItem('siteDescription', siteForm.site_description)
    alert('网站设置保存成功')
  } catch (error) {
    console.error('Failed to save site settings:', error)
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    savingSite.value = false
  }
}

onMounted(() => {
  if (route.query.tab) {
    activeTab.value = route.query.tab
  }
  loadTelegramSettings()
  loadSiteSettings()
})
</script>
