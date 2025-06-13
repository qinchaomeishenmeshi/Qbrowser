<template>
  <div id="main-app" :class="{ 'dark-theme': isDarkTheme }" class="app-container">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: !sidebarExpanded }">
      <div class="sidebar-header">
        <div class="logo">
          <img src="./assets/icon.png" alt="全网直播浏览器" class="logo-icon">
        </div>
        <span v-show="sidebarExpanded" class="logo-text">全网直播浏览器</span>
        <button
                class="sidebar-toggle"
                @click="toggleSidebar"
                :title="sidebarExpanded ? '收起侧边栏' : '展开侧边栏'">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M3 4.5h10v1H3v-1zm0 3h10v1H3v-1zm0 3h10v1H3v-1z" />
          </svg>
        </button>
      </div>

      <nav class="sidebar-nav nav-menu">
        <router-link to="/" class="nav-item" exact-active-class="active">
          <svg class="nav-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 1l7 6v8H1V7l7-6zm0 1.5L2.5 7.5V14h3V9h5v5h3V7.5L8 2.5z" />
          </svg>
          <span v-show="sidebarExpanded" class="nav-text">仪表盘</span>
        </router-link>

        <router-link to="/browser" class="nav-item" active-class="active">
          <svg class="nav-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M1 3a1 1 0 011-1h12a1 1 0 011 1v10a1 1 0 01-1 1H2a1 1 0 01-1-1V3zm1 1v9h12V4H2zm1 1h10v1H3V5z" />
          </svg>
          <span v-show="sidebarExpanded" class="nav-text">浏览器管理</span>
        </router-link>

        <router-link to="/scheduler" class="nav-item" active-class="active">
          <svg class="nav-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M3 1a1 1 0 00-1 1v12a1 1 0 001 1h10a1 1 0 001-1V2a1 1 0 00-1-1H3zm0 1h10v12H3V2zm2 2v1h6V4H5zm0 2v1h6V6H5zm0 2v1h4V8H5z" />
          </svg>
          <span v-show="sidebarExpanded" class="nav-text">定时任务</span>
        </router-link>

        <router-link to="/extensions" class="nav-item" active-class="active">
          <svg class="nav-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 1a7 7 0 100 14A7 7 0 008 1zM2 8a6 6 0 1112 0A6 6 0 012 8zm6-3a1 1 0 00-1 1v4a1 1 0 002 0V6a1 1 0 00-1-1z" />
          </svg>
          <span v-show="sidebarExpanded" class="nav-text">扩展管理</span>
        </router-link>

        <router-link to="/settings" class="nav-item" active-class="active">
          <svg class="nav-icon" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 4.754a3.246 3.246 0 100 6.492 3.246 3.246 0 000-6.492zM5.754 8a2.246 2.246 0 114.492 0 2.246 2.246 0 01-4.492 0z" />
            <path
                  d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 01-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 01-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 01.52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 011.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 011.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 01.52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 01-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 01-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 002.693 1.115l.292-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 001.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 00-1.115 2.693l.16.292c.415.764-.42 1.6-1.185 1.184l-.292-.159a1.873 1.873 0 00-2.692 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 00-2.693-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.292A1.873 1.873 0 001.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 003.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 002.692-1.116l.094-.318z" />
          </svg>
          <span v-show="sidebarExpanded" class="nav-text">系统设置</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="status-indicator" :class="backendStatus.isRunning ? 'online' : 'offline'">
          <div class="status-dot"></div>
          <span v-show="sidebarExpanded" class="status-text">
            {{ backendStatusText }}
          </span>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <div class="top-bar-left">
          <h1 class="page-title">{{ pageTitle }}</h1>
        </div>

        <div class="top-bar-right">
          <!-- 主题切换 -->
          <button class="icon-button" @click="toggleTheme" :title="isDarkTheme ? '切换到浅色主题' : '切换到深色主题'">
            <svg v-if="isDarkTheme" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zM2 8a6 6 0 1112 0A6 6 0 012 8z" />
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path
                    d="M6 .278a.768.768 0 01.08.858 7.208 7.208 0 00-.878 3.46c0 4.021 3.278 7.277 7.318 7.277.527 0 1.04-.055 1.533-.16a.787.787 0 01.81.316.733.733 0 01-.031.893A8.349 8.349 0 018.344 16C3.734 16 0 12.286 0 7.71 0 4.266 2.114 1.312 5.124.06A.752.752 0 016 .278z" />
            </svg>
          </button>
        </div>
      </header>

      <!-- 路由视图 -->
      <div class="content-area">
        <router-view />
      </div>
    </main>


  </div>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAppStore } from './store/modules/app.js'

export default {
  name: 'App',
  data() {
    return {
      statusCheckInterval: null
    }
  },

  computed: {
    ...mapState(useAppStore, [
      'backendStatus'
    ]),

    sidebarExpanded() {
      const appStore = useAppStore()
      return !appStore.ui?.sidebarCollapsed
    },

    isDarkTheme() {
      const appStore = useAppStore()
      return appStore.ui?.theme === 'dark'
    },

    pageTitle() {
      const routeTitles = {
        '/': '仪表盘',
        '/browser': '浏览器管理',
        '/scheduler': '定时任务',
        '/extensions': '扩展管理',
        '/settings': '系统设置'
      }
      return routeTitles[this.$route.path] || '全网直播浏览器'
    },

    backendStatusText() {
      return this.backendStatus.isRunning ? '后端在线' : '后端离线'
    }
  },

  methods: {
    ...mapActions(useAppStore, [
      'initializeApp',
      'checkBackendStatus',
      'restartBackend',
      'setTheme',
      'toggleSidebar'
    ]),

    toggleTheme() {
      const appStore = useAppStore()
      const newTheme = appStore.ui?.theme === 'dark' ? 'light' : 'dark'
      this.setTheme(newTheme)
    },




  },

  async mounted() {
    // 初始化应用
    await this.initializeApp()

    // 定期检查后端状态
    this.statusCheckInterval = setInterval(() => {
      this.checkBackendStatus()
    }, 5000)

    // 监听后端状态变化
    if (window.electronAPI) {
      window.electronAPI.onBackendStatusChange((event, status) => {
        this.backendStatus.isRunning = status.status === 'running'
        this.backendStatus.pid = status.pid
      })
    }
  },

  beforeUnmount() {
    if (this.statusCheckInterval) {
      clearInterval(this.statusCheckInterval)
    }
  },


}
</script>

<style scoped>
/* CSS 变量定义 - 移到最前面确保优先加载 */
:root {
  --primary-color: #667eea;
  --primary-bg: rgba(102, 126, 234, 0.1);
  --bg-color: #ffffff;
  --content-bg: #f8fafc;
  --sidebar-bg: #ffffff;
  --header-bg: #ffffff;
  --panel-bg: #ffffff;
  --text-color: #1f2937;
  --text-secondary: #6b7280;
  --border-color: #e5e7eb;
  --hover-bg: #f3f4f6;
}

.dark-theme {
  --primary-color: #667eea;
  --primary-bg: rgba(102, 126, 234, 0.2);
  --bg-color: #111827;
  --content-bg: #1f2937;
  --sidebar-bg: #1f2937;
  --header-bg: #1f2937;
  --panel-bg: #1f2937;
  --text-color: #f9fafb;
  --text-secondary: #9ca3af;
  --border-color: #374151;
  --hover-bg: #374151;
}

.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏样式 */
.sidebar {
  width: 250px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  transition: all 0.3s ease;
  overflow: hidden;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar.collapsed .sidebar-header {
  padding: 20px 10px;
  justify-content: center;
}

.sidebar-toggle {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
  margin-left: auto;
}

.sidebar-toggle:hover {
  background: var(--hover-bg);
  color: var(--text-color);
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
}

.sidebar.collapsed .logo-text {
  opacity: 0;
  width: 0;
}

.logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 14px;
}

.logo>img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
}

.sidebar.collapsed .app-title {
  opacity: 0;
  width: 0;
}

.nav-menu {
  padding: 20px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
  border: none;
  background: none;
  width: 100%;
  text-align: left;
}

.sidebar.collapsed .nav-item {
  padding: 12px 18px;
  justify-content: center;
}

.nav-item:hover {
  background: var(--hover-bg);
  color: var(--primary-color);
}

.sidebar-nav .nav-item.active,
.sidebar-nav .nav-item.router-link-active,
.sidebar-nav .nav-item.router-link-exact-active {
  background: var(--primary-bg, rgba(102, 126, 234, 0.1)) !important;
  color: var(--primary-color, #667eea) !important;
  border-right: 3px solid var(--primary-color, #667eea) !important;
}

.nav-icon {
  width: 20px;
  height: 20px;
  margin-right: 12px;
  flex-shrink: 0;
}

.sidebar.collapsed .nav-icon {
  margin-right: 0;
}

.nav-text {
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
}

.sidebar.collapsed .nav-text {
  opacity: 0;
  width: 0;
}

.sidebar-footer {
  margin-top: auto;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.sidebar.collapsed .sidebar-footer {
  padding: 16px 10px;
}

.sidebar.collapsed .status-text {
  opacity: 0;
  width: 0;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部栏样式 */
.top-bar {
  height: 60px;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toggle-sidebar {
  background: none;
  border: none;
  color: var(--text-color);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.toggle-sidebar:hover {
  background: var(--hover-bg);
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-color);
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-button {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-button:hover {
  background: var(--hover-bg);
  color: var(--text-color);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 12px;
  padding: 4px 8px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-indicator.online {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.status-indicator.offline {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.top-bar-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
  position: relative;
}

.top-bar-btn:hover {
  background: var(--hover-bg);
  color: var(--text-color);
}

.notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

/* 内容区域 */
.content-area {
  flex: 1;
  overflow: auto;
  background: var(--content-bg);
  padding: 20px;
}

/* 通知面板样式 */
.notification-panel {
  position: fixed;
  top: 60px;
  right: 0;
  width: 350px;
  height: calc(100vh - 60px);
  background: var(--panel-bg);
  border-left: 1px solid var(--border-color);
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.notification-panel.show {
  transform: translateX(0);
}

.notification-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.notification-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.notification-actions {
  display: flex;
  gap: 8px;
}

.notification-list {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.notification-item {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.3s ease;
  cursor: pointer;
}

.notification-item:hover {
  background: var(--hover-bg);
}

.notification-item.unread {
  background: var(--primary-bg, rgba(102, 126, 234, 0.1));
  border-left: 3px solid var(--primary-color, #667eea);
}

.notification-content {
  margin-bottom: 8px;
}

.notification-message {
  font-size: 14px;
  color: var(--text-color);
  margin-bottom: 4px;
}

.notification-type {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-weight: 500;
}

.notification-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.empty-notifications {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-secondary);
}

/* 重复的 CSS 变量定义已移到文件开头 */

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 1001;
    transform: translateX(-100%);
  }

  .sidebar.show {
    transform: translateX(0);
  }

  .main-content {
    width: 100%;
  }

  .notification-panel {
    width: 100%;
  }
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: var(--bg-color);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notification-item {
  animation: fadeIn 0.3s ease;
}

/* 加载状态 */
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: var(--text-secondary);
}

.loading::after {
  content: '';
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-left: 10px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}
</style>