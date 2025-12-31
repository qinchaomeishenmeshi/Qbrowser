<template>
  <el-aside :width="collapsed ? '64px' : '220px'" class="app-sidebar glass-effect">
    <div class="logo">
      <img src="/app-icon.png" class="logo-icon" alt="Logo" />
      <span v-show="!collapsed" class="logo-text">QW-Browser</span>
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
  /* background-color: var(--bg-color-light); */
  background: transparent; /* 使用父级或自身 glass */
  border-right: 1px solid var(--border-color); /* 保留极细边框或移除 */
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  z-index: 10; /* 确保在内容之上 */
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px; /* 增加左右内边距 */
  height: var(--header-height);
  border-bottom: 1px solid var(--border-color);

  .logo-icon {
    width: 28px;
    height: 28px;
    object-fit: contain;
  }

  .logo-text {
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: var(--text-color);
    white-space: nowrap;
    background: linear-gradient(120deg, var(--primary-color), #60a5fa);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }
}

.sidebar-menu {
  flex: 1;
  border: none;

  .el-menu-item {
    &.is-active {
      background-color: rgba(64, 158, 255, 0.1);
    }

    &:hover {
      background-color: rgba(64, 158, 255, 0.05);
    }
  }
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: center;
}
</style>
