<template>
  <aside class="w-72 flex-shrink-0 p-4 pl-0">
    <div class="bg-white/90 backdrop-blur-xl rounded-[28px] p-6 shadow-xl shadow-slate-200/50 border border-white/60 h-full">
      <!-- 用户头像区域 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-3">
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/30">
            <span class="text-white font-bold text-xl">R</span>
          </div>
          <div>
            <p class="text-sm font-semibold text-slate-800">连接数</p>
            <p class="text-xs text-slate-400">@个人数据</p>
          </div>
        </div>
        <button class="w-8 h-8 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center transition-all cursor-pointer">
          <PencilIcon class="w-4 h-4" />
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="relative mb-8">
        <input
          type="text"
          placeholder="添加入"
          class="w-full pl-4 pr-12 py-3 bg-slate-50/80 border border-slate-200/60 rounded-2xl text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
        />
        <button class="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-xl bg-white shadow-sm flex items-center justify-center text-slate-400 hover:text-slate-600 cursor-pointer transition-colors">
          <MagnifyingGlassIcon class="w-4 h-4" />
        </button>
      </div>

      <!-- PT总览 -->
      <div class="space-y-6">
        <h3 class="text-sm font-semibold text-slate-800">PT总览</h3>

        <!-- 总上传 -->
        <div class="space-y-1.5">
          <p class="text-xs text-slate-400 font-medium">总上传</p>
          <p class="text-3xl font-bold text-slate-800 tracking-tight">{{ formatSizeCompact(stats.total_uploaded || 0) }}</p>
        </div>

        <!-- 总下载 -->
        <div class="space-y-1.5">
          <p class="text-xs text-slate-400 font-medium">总下载</p>
          <p class="text-3xl font-bold text-slate-800 tracking-tight">{{ formatSizeCompact(stats.total_downloaded || 0) }}</p>
        </div>

        <!-- 分享率 -->
        <div class="space-y-1.5">
          <p class="text-xs text-slate-400 font-medium">分享率</p>
          <p class="text-3xl font-bold text-slate-800 tracking-tight">{{ shareRatio }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { PencilIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline'
import { useDashboardStore } from '@/stores/dashboard'

const dashboardStore = useDashboardStore()

const stats = computed(() => dashboardStore.stats)

const shareRatio = computed(() => {
  const uploaded = stats.value?.total_uploaded || 0
  const downloaded = stats.value?.total_downloaded || 1
  if (downloaded === 0) return uploaded > 0 ? '∞' : '0.00'
  return (uploaded / downloaded).toFixed(2)
})

function formatSizeCompact(bytes) {
  if (!bytes || bytes === 0) return '0B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const value = bytes / Math.pow(k, i)
  return value.toFixed(1) + units[i]
}
</script>
