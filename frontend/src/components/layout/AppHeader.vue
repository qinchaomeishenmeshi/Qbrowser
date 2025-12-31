<template>
  <el-header class="app-header glass-effect">
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
  height: var(--header-height);
  padding: 0 24px;
  position: relative;

  /* 底部装饰边 */
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 5%;
    width: 90%;
    height: 1px;
    background: linear-gradient(
      90deg,
      transparent 0%,
      var(--border-color) 20%,
      var(--border-color) 80%,
      transparent 100%
    );
  }
}

.header-left {
  display: flex;
  align-items: center;

  :deep(.el-breadcrumb) {
    font-size: 14px;

    .el-breadcrumb__inner {
      font-weight: 500;
      transition: color 0.2s ease;
    }

    .el-breadcrumb__item:last-child .el-breadcrumb__inner {
      color: var(--text-color);
      font-weight: 600;
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(245, 108, 108, 0.1);
  color: var(--danger-color);
  transition: all 0.3s ease;
  cursor: default;

  .el-icon {
    transition: transform 0.3s ease;
  }

  &.connected {
    background: rgba(16, 185, 129, 0.1);
    color: var(--success-color);

    .el-icon {
      animation: statusPulse 2s ease-in-out infinite;
    }
  }

  &:hover .el-icon {
    transform: scale(1.2);
  }
}

@keyframes statusPulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.8;
  }
}

/* 工具按钮悬停效果 */
:deep(.el-button.is-circle) {
  transition: all 0.25s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}
</style>
