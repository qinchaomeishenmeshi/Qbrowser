<template>
  <el-aside :width="collapsed ? '64px' : '220px'" class="app-sidebar glass-effect">
    <div class="logo">
      <img src="/app-icon.png" class="logo-icon" alt="Logo" />
      <span v-show="!collapsed" class="logo-text">清简浏览器</span>
    </div>

    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      :router="true"
      class="sidebar-menu"
      background-color="transparent"
      text-color="var(--text-color)"
      active-text-color="#409eff"
    >
      <el-menu-item index="/">
        <el-icon><Monitor /></el-icon>
        <template #title>仪表盘</template>
      </el-menu-item>

      <el-menu-item index="/browsers">
        <el-icon><ChromeFilled /></el-icon>
        <template #title>浏览器管理</template>
      </el-menu-item>

      <el-menu-item index="/extensions">
        <el-icon><Opportunity /></el-icon>
        <template #title>扩展管理</template>
      </el-menu-item>

      <el-menu-item index="/logs">
        <el-icon><Document /></el-icon>
        <template #title>系统日志</template>
      </el-menu-item>

      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <template #title>系统设置</template>
      </el-menu-item>
    </el-menu>

    <div class="sidebar-footer">
      <el-button :icon="collapsed ? Expand : Fold" circle size="small" @click="$emit('toggle')" />
    </div>
  </el-aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Monitor,
  ChromeFilled,
  Opportunity,
  Document,
  Setting,
  Expand,
  Fold
} from '@element-plus/icons-vue'

defineProps<{
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
}>()

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped lang="scss">
.app-sidebar {
  display: flex;
  flex-direction: column;
  background: transparent;
  border-right: 1px solid var(--border-color);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  z-index: 10;
  position: relative;

  /* 侧边装饰线 */
  &::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 1px;
    height: 100%;
    background: linear-gradient(180deg, transparent 0%, var(--primary-color) 50%, transparent 100%);
    opacity: 0.3;
  }
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  height: var(--header-height);
  border-bottom: 1px solid var(--border-color);
  transition: all 0.3s ease;

  .logo-icon {
    width: 32px;
    height: 32px;
    object-fit: contain;
    transition: transform 0.3s ease;

    &:hover {
      transform: rotate(-10deg) scale(1.1);
    }
  }

  .logo-text {
    font-size: 17px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: var(--text-color);
    white-space: nowrap;
    background: linear-gradient(120deg, var(--primary-color), #60a5fa);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 3s ease infinite;
  }
}

@keyframes gradientShift {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.sidebar-menu {
  flex: 1;
  border: none;
  padding: 12px 8px;

  :deep(.el-menu-item) {
    margin: 4px 0;
    border-radius: 10px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;

    /* 悬停背景动画 */
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
      transform: translateX(-100%);
      transition: transform 0.3s ease;
    }

    &:hover {
      background-color: transparent;

      &::before {
        transform: translateX(0);
      }

      .el-icon {
        transform: scale(1.1);
        color: var(--primary-color);
      }
    }

    &.is-active {
      background: linear-gradient(
        90deg,
        rgba(59, 130, 246, 0.15) 0%,
        rgba(59, 130, 246, 0.05) 100%
      );
      color: var(--primary-color);
      font-weight: 600;

      /* 激活指示条 */
      &::after {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 24px;
        background: linear-gradient(180deg, var(--primary-color) 0%, #60a5fa 100%);
        border-radius: 0 3px 3px 0;
      }
    }

    .el-icon {
      transition: all 0.25s ease;
    }
  }
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: center;

  .el-button {
    transition: all 0.3s ease;

    &:hover {
      transform: rotate(180deg);
      background: var(--bg-color-soft);
    }
  }
}
</style>
