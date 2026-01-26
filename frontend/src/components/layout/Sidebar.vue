<template>
  <aside class="w-[88px] flex flex-col items-center py-6 m-4">
    <div class="bg-white/90 backdrop-blur-xl rounded-[28px] p-4 shadow-xl shadow-slate-200/50 border border-white/60 h-full flex flex-col items-center">
      <!-- 添加按钮 -->
      <button
        @click="showAddMenu = !showAddMenu"
        class="w-14 h-14 rounded-full bg-gradient-to-br from-blue-100 via-blue-50 to-purple-100 flex items-center justify-center mb-8 hover:scale-105 transition-all duration-300 shadow-lg shadow-blue-200/60 cursor-pointer relative group"
      >
        <PlusIcon class="w-7 h-7 text-blue-500 group-hover:rotate-90 transition-transform duration-300" />

        <!-- 添加菜单下拉 -->
        <transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="transform opacity-0 scale-95 -translate-x-2"
          enter-to-class="transform opacity-100 scale-100 translate-x-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="transform opacity-100 scale-100"
          leave-to-class="transform opacity-0 scale-95"
        >
          <div
            v-if="showAddMenu"
            class="absolute left-full ml-4 top-0 w-52 bg-white rounded-2xl shadow-2xl shadow-slate-200/60 border border-slate-100 py-2 z-50"
          >
            <router-link
              to="/downloaders"
              @click="showAddMenu = false"
              class="flex items-center px-4 py-3 text-sm text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <div class="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center mr-3">
                <ServerStackIcon class="w-4 h-4 text-blue-500" />
              </div>
              添加下载器
            </router-link>
            <router-link
              to="/rss"
              @click="showAddMenu = false"
              class="flex items-center px-4 py-3 text-sm text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <div class="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center mr-3">
                <RssIcon class="w-4 h-4 text-orange-500" />
              </div>
              添加RSS订阅
            </router-link>
            <router-link
              to="/delete-rules"
              @click="showAddMenu = false"
              class="flex items-center px-4 py-3 text-sm text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <div class="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center mr-3">
                <TrashIcon class="w-4 h-4 text-red-500" />
              </div>
              添加删种规则
            </router-link>
          </div>
        </transition>
      </button>

      <!-- 导航菜单 -->
      <nav class="flex-1 flex flex-col items-center space-y-3">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          v-slot="{ isExactActive }"
          custom
        >
          <button
            @click="$router.push(item.path)"
            class="w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 cursor-pointer group relative"
            :class="[
              isExactActive
                ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/40'
                : 'text-slate-400 hover:text-blue-500 hover:bg-blue-50'
            ]"
            :title="item.label"
          >
            <component :is="item.icon" class="w-5 h-5" />
            <!-- Tooltip -->
            <span class="absolute left-full ml-4 px-3 py-2 bg-slate-800 text-white text-xs font-medium rounded-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50 shadow-lg">
              {{ item.label }}
              <span class="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-2 h-2 bg-slate-800 rotate-45"></span>
            </span>
          </button>
        </router-link>
      </nav>

      <!-- 底部设置按钮 -->
      <router-link to="/settings" v-slot="{ isExactActive }" custom>
        <button
          @click="$router.push('/settings')"
          class="w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 cursor-pointer group relative mt-4"
          :class="[
            isExactActive
              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/40'
              : 'text-slate-400 hover:text-blue-500 hover:bg-blue-50'
          ]"
          title="设置"
        >
          <Cog6ToothIcon class="w-5 h-5" />
          <span class="absolute left-full ml-4 px-3 py-2 bg-slate-800 text-white text-xs font-medium rounded-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50 shadow-lg">
            系统设置
            <span class="absolute left-0 top-1/2 -translate-x-1 -translate-y-1/2 w-2 h-2 bg-slate-800 rotate-45"></span>
          </span>
        </button>
      </router-link>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import {
  PlusIcon,
  HomeIcon,
  Squares2X2Icon,
  ChartBarIcon,
  CircleStackIcon,
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon,
  ServerStackIcon,
  RssIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline'

const showAddMenu = ref(false)

const navItems = [
  { label: '首页', path: '/', icon: HomeIcon },
  { label: '下载器', path: '/downloaders', icon: Squares2X2Icon },
  { label: '数据统计', path: '/statistics', icon: ChartBarIcon },
  { label: 'RSS订阅', path: '/rss', icon: CircleStackIcon },
  { label: '系统日志', path: '/logs', icon: ChatBubbleLeftRightIcon },
]

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  if (showAddMenu.value && !event.target.closest('aside')) {
    showAddMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
