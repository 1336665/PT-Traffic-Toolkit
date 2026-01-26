<template>
  <aside class="w-20 flex flex-col items-center py-6 bg-white/80 backdrop-blur-xl rounded-3xl m-4 shadow-xl border border-white/50">
    <!-- 添加按钮 -->
    <button
      @click="showAddMenu = !showAddMenu"
      class="w-12 h-12 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center mb-8 hover:scale-110 transition-transform duration-200 shadow-lg shadow-purple-200/50 cursor-pointer relative"
    >
      <PlusIcon class="w-6 h-6 text-blue-600" />

      <!-- 添加菜单下拉 -->
      <transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="transform opacity-0 scale-95"
        enter-to-class="transform opacity-100 scale-100"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="transform opacity-100 scale-100"
        leave-to-class="transform opacity-0 scale-95"
      >
        <div
          v-if="showAddMenu"
          class="absolute left-full ml-3 top-0 w-48 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50"
        >
          <router-link
            to="/downloaders"
            @click="showAddMenu = false"
            class="flex items-center px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 cursor-pointer"
          >
            <ServerStackIcon class="w-5 h-5 text-blue-500 mr-3" />
            添加下载器
          </router-link>
          <router-link
            to="/rss"
            @click="showAddMenu = false"
            class="flex items-center px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 cursor-pointer"
          >
            <RssIcon class="w-5 h-5 text-orange-500 mr-3" />
            添加RSS订阅
          </router-link>
          <router-link
            to="/delete-rules"
            @click="showAddMenu = false"
            class="flex items-center px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 cursor-pointer"
          >
            <TrashIcon class="w-5 h-5 text-red-500 mr-3" />
            添加删种规则
          </router-link>
        </div>
      </transition>
    </button>

    <!-- 导航菜单 -->
    <nav class="flex-1 flex flex-col items-center space-y-2">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        v-slot="{ isExactActive }"
        custom
      >
        <button
          @click="$router.push(item.path)"
          class="w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-200 cursor-pointer group relative"
          :class="[
            isExactActive
              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30'
              : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
          ]"
          :title="item.label"
        >
          <component :is="item.icon" class="w-6 h-6" />
          <!-- Tooltip -->
          <span class="absolute left-full ml-3 px-3 py-1.5 bg-slate-800 text-white text-sm rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50">
            {{ item.label }}
          </span>
        </button>
      </router-link>
    </nav>

    <!-- 底部设置按钮 -->
    <router-link to="/settings" v-slot="{ isExactActive }" custom>
      <button
        @click="$router.push('/settings')"
        class="w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-200 cursor-pointer group relative"
        :class="[
          isExactActive
            ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30'
            : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
        ]"
        title="设置"
      >
        <Cog6ToothIcon class="w-6 h-6" />
        <span class="absolute left-full ml-3 px-3 py-1.5 bg-slate-800 text-white text-sm rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50">
          系统设置
        </span>
      </button>
    </router-link>
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
