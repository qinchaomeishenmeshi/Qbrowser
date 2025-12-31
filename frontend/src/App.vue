<template>
  <el-container class="app-container">
    <AppSidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />

    <el-container direction="vertical">
      <AppHeader />

      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useAppStore, useBrowserStore } from '@/stores'

const appStore = useAppStore()
const browserStore = useBrowserStore()

const sidebarCollapsed = ref(false)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

onMounted(async () => {
  // 初始化：检查后端连接状态
  await appStore.checkBackendHealth()
  await appStore.loadSettings()

  // 加载浏览器状态
  if (appStore.backendConnected) {
    await browserStore.refresh()
  }

  // 应用主题
  if (appStore.settings.theme === 'dark') {
    document.documentElement.classList.add('dark')
  }
})
</script>

<style lang="scss">
.app-container {
  height: 100vh;
  overflow: hidden;
}

.app-main {
  background-color: var(--bg-color);
  overflow-y: auto;
  padding: 0;
}
</style>
