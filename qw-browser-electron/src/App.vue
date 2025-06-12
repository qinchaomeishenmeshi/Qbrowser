<template>
  <div id="main-app" :class="{ 'dark-theme': isDarkTheme }">
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

      <nav class="sidebar-nav">
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

    <!-- 通知面板 -->
    <div v-if="showNotificationPanel" class="notification-panel" @click.self="hideNotifications">
      <div class="notification-content">
        <div class="notification-header">
          <h3>通知</h3>
          <button @click="hideNotifications" class="close-button">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path
                    d="M4.646 4.646a.5.5 0 01.708 0L8 7.293l2.646-2.647a.5.5 0 01.708.708L8.707 8l2.647 2.646a.5.5 0 01-.708.708L8 8.707l-2.646 2.647a.5.5 0 01-.708-.708L7.293 8 4.646 5.354a.5.5 0 010-.708z" />
            </svg>
          </button>
        </div>

        <div class="notification-list">
          <div v-if="notifications.length === 0" class="no-notifications">
            暂无通知
          </div>

          <div
               v-for="notification in notifications"
               :key="notification.id"
               class="notification-item"
               :class="{ unread: !notification.read }"
               @click="markAsRead(notification.id)">
            <div class="notification-icon" :class="notification.type">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path v-if="notification.type === 'success'"
                      d="M13.854 3.646a.5.5 0 010 .708l-7 7a.5.5 0 01-.708 0l-3.5-3.5a.5.5 0 11.708-.708L6.5 10.293l6.646-6.647a.5.5 0 01.708 0z" />
                <path v-else-if="notification.type === 'error'"
                      d="M4.646 4.646a.5.5 0 01.708 0L8 7.293l2.646-2.647a.5.5 0 01.708.708L8.707 8l2.647 2.646a.5.5 0 01-.708.708L8 8.707l-2.646 2.647a.5.5 0 01-.708-.708L7.293 8 4.646 5.354a.5.5 0 010-.708z" />
                <path v-else-if="notification.type === 'warning'"
                      d="M8.982 1.566a1.13 1.13 0 00-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 01-1.1 0L7.1 5.995A.905.905 0 018 5zm.002 6a1 1 0 100 2 1 1 0 000-2z" />
                <path v-else d="M8 1a7 7 0 100 14A7 7 0 008 1zM7 4a1 1 0 112 0v3a1 1 0 11-2 0V4zm1.5 6.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
              </svg>
            </div>

            <div class="notification-body">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
            </div>
          </div>
        </div>

        <div class="notification-actions">
          <button @click="markAllAsRead" class="btn btn-secondary">全部标记为已读</button>
          <button @click="clearAllNotifications" class="btn btn-danger">清空通知</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useAppStore } from './store/modules/app'
import { mapState, mapActions } from 'pinia'

export default {
  name: 'App',
  data() {
    return {
      sidebarExpanded: true,
      notifications: [],
      statusCheckInterval: null
    }
  },

  computed: {
    ...mapState(useAppStore, [
      'backendStatus',
      'notifications as storeNotifications'
    ]),

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
      'toggleSidebar',
      'addNotification',
      'markNotificationAsRead',
      'clearNotifications'
    ]),

    toggleTheme() {
      const appStore = useAppStore()
      const newTheme = appStore.ui?.theme === 'dark' ? 'light' : 'dark'
      this.setTheme(newTheme)
    },



    markAsRead(notificationId) {
      const notification = this.notifications.find(n => n.id === notificationId)
      if (notification) {
        notification.read = true
        this.markNotificationAsRead(notificationId)
      }
    },

    markAllAsRead() {
      this.notifications.forEach(n => {
        n.read = true
        this.markNotificationAsRead(n.id)
      })
    },

    clearAllNotifications() {
      this.notifications = []
      this.clearNotifications()
      this.hideNotifications()
    },

    formatTime(timestamp) {
      const now = new Date()
      const time = new Date(timestamp)
      const diff = now - time

      if (diff < 60000) { // 1分钟内
        return '刚刚'
      } else if (diff < 3600000) { // 1小时内
        return `${Math.floor(diff / 60000)}分钟前`
      } else if (diff < 86400000) { // 24小时内
        return `${Math.floor(diff / 3600000)}小时前`
      } else {
        return time.toLocaleDateString()
      }
    },

    addTestNotification() {
      const types = ['success', 'error', 'warning', 'info']
      const type = types[Math.floor(Math.random() * types.length)]

      this.addNotification({
        type,
        title: '测试通知',
        message: `这是一个${type}类型的测试通知`,
        timestamp: Date.now()
      })
    }
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

        // 添加状态变化通知
        this.addNotification({
          type: status.status === 'running' ? 'success' : 'error',
          title: '后端状态变化',
          message: status.status === 'running' ? '后端服务已启动' : '后端服务已停止',
          timestamp: Date.now()
        })
      })
    }

    // 初始化通知数据
    this.notifications = this.storeNotifications || []
  },

  beforeUnmount() {
    if (this.statusCheckInterval) {
      clearInterval(this.statusCheckInterval)
    }
  },

  watch: {
    storeNotifications: {
      handler(newNotifications) {
        this.notifications = newNotifications || []
      },
      deep: true
    }
  }
}
</script>

<style scoped>
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

.nav-item.active {
  background: var(--primary-bg);
  color: var(--primary-color);
  border-right: 3px solid var(--primary-color);
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
.content {
  flex: 1;
  overflow: auto;
  background: var(--content-bg);
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
  background: var(--primary-bg);
  border-left: 3px solid var(--primary-color);
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

/* CSS 变量定义 */
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