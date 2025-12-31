<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="currentRoute.meta?.title">
          {{ currentRoute.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="header-right">
      <!-- 连接状态 -->
      <div class="connection-status" :class="{ connected: appStore.backendConnected }">
        <el-icon :size="14">
          <component :is="appStore.backendConnected ? 'SuccessFilled' : 'CircleCloseFilled'" />
        </el-icon>
        <span>{{ appStore.backendConnected ? '已连接' : '未连接' }}</span>
      </div>

      <!-- 刷新按钮 -->
      <el-tooltip content="刷新数据" placement="bottom">
        <el-button :icon="Refresh" circle size="small" @click="handleRefresh" />
      </el-tooltip>

      <!-- 主题切换 -->
      <el-tooltip content="切换主题" placement="bottom">
        <el-button
          :icon="appStore.isDarkTheme ? Sunny : Moon"
          circle
          size="small"
          @click="toggleTheme"
        />
      </el-tooltip>
    </div>
  </el-header>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAppStore, useBrowserStore } from '@/stores'
import { Refresh, Sunny, Moon } from '@element-plus/icons-vue'

const currentRoute = useRoute()
const appStore = useAppStore()
const browserStore = useBrowserStore()

const handleRefresh = async () => {
  await Promise.all([appStore.checkBackendHealth(), browserStore.refresh()])
}

const toggleTheme = () => {
  appStore.setTheme(appStore.isDarkTheme ? 'light' : 'dark')
}
</script>

<style scoped lang="scss">
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 24px;
  background-color: var(--bg-color-light);
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  background: rgba(245, 108, 108, 0.1);
  color: var(--danger-color);

  &.connected {
    background: rgba(103, 194, 58, 0.1);
    color: var(--success-color);
  }
}
</style>
