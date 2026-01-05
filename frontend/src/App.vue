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
import { ref, onMounted, onUnmounted, watch } from 'vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useAppStore, useBrowserStore } from '@/stores'
import { useBrowserSocket, destroyBrowserSocket } from '@/composables/useBrowserSocket'

const appStore = useAppStore()
const browserStore = useBrowserStore()

const sidebarCollapsed = ref(false)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 初始化 Browser WebSocket 连接

// 监听连接状态，自动初始化 WebSocket
watch(
  () => appStore.backendConnected,
  (connected) => {
    if (connected) {
      const socket = useBrowserSocket()
      if (socket.status.value === 'CLOSED') {
        console.log('🔄 重新激活 Browser WebSocket...')
        socket.open()
      }
    }
  },
  { immediate: true }
)

onMounted(async () => {
  // 初始化：检查后端连接状态
  await appStore.checkBackendHealth()
  await appStore.loadSettings()

  // 加载初始数据
  if (appStore.backendConnected) {
    await browserStore.refresh()
  }

  // 应用主题
  if (appStore.settings.theme === 'dark') {
    document.documentElement.classList.add('dark')
  }
})

onUnmounted(() => {
  // 清理 WebSocket 连接
  destroyBrowserSocket()
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
