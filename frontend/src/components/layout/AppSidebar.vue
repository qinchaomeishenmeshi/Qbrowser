<template>
  <el-aside :width="collapsed ? '64px' : '220px'" class="app-sidebar">
    <div class="logo">
      <el-icon :size="28" color="#409eff">
        <Monitor />
      </el-icon>
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
  background-color: var(--bg-color-light);
  border-right: 1px solid var(--border-color);
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  height: 60px;
  border-bottom: 1px solid var(--border-color);

  .logo-text {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-color);
    white-space: nowrap;
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
