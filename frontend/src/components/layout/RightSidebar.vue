<template>
  <aside class="w-64 flex-shrink-0 p-4">
    <div class="bg-white/80 backdrop-blur-xl rounded-3xl p-5 shadow-xl border border-white/50 h-full">
      <!-- 用户区域 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/30">
            <span class="text-white font-bold text-lg">R</span>
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-800">连接数</p>
            <p class="text-xs text-slate-400">@个人数据</p>
          </div>
        </div>
        <button class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer">
          <PencilIcon class="w-4 h-4" />
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="relative mb-6">
        <input
          type="text"
          placeholder="添加入"
          class="w-full pl-4 pr-10 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
        />
        <button class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-slate-600 cursor-pointer">
          <MagnifyingGlassIcon class="w-4 h-4" />
        </button>
      </div>

      <!-- PT总览 -->
      <div class="space-y-4">
        <h3 class="text-sm font-semibold text-slate-800">PT总览</h3>

        <!-- 总上传 -->
        <div class="space-y-1">
          <p class="text-xs text-slate-400">总上传</p>
          <p class="text-2xl font-bold text-slate-800">{{ formatSize(stats.total_uploaded || 0) }}</p>
        </div>

        <!-- 总下载 -->
        <div class="space-y-1">
          <p class="text-xs text-slate-400">总下载</p>
          <p class="text-2xl font-bold text-slate-800">{{ formatSize(stats.total_downloaded || 0) }}</p>
        </div>

        <!-- 分享率 -->
        <div class="space-y-1">
          <p class="text-xs text-slate-400">分享率</p>
          <p class="text-2xl font-bold text-slate-800">{{ shareRatio }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { PencilIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline'
import { useDashboardStore } from '@/stores/dashboard'
import { formatSize } from '@/utils/format'

const dashboardStore = useDashboardStore()

const stats = computed(() => dashboardStore.stats)

const shareRatio = computed(() => {
  const uploaded = stats.value?.total_uploaded || 0
  const downloaded = stats.value?.total_downloaded || 1
  if (downloaded === 0) return uploaded > 0 ? '∞' : '0.00'
  return (uploaded / downloaded).toFixed(2)
})
</script>
