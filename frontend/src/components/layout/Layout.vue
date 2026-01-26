<template>
  <div class="min-h-screen flex bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20">
    <!-- 左侧导航栏 -->
    <Sidebar />

    <!-- 主内容区域 -->
    <div class="flex-1 flex min-w-0">
      <!-- 中间主内容 -->
      <div class="flex-1 flex flex-col min-w-0">
        <!-- Header - 仅在非Dashboard页面显示 -->
        <Header v-if="!isDashboard" />

        <!-- Page content -->
        <main class="flex-1 overflow-y-auto" :class="isDashboard ? 'p-6' : 'p-4 lg:p-6'">
          <router-view />
        </main>
      </div>

      <!-- 右侧边栏 - 仅在Dashboard显示 -->
      <RightSidebar v-if="isDashboard" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import RightSidebar from './RightSidebar.vue'

const route = useRoute()

// 判断是否为首页Dashboard
const isDashboard = computed(() => route.path === '/')
</script>
