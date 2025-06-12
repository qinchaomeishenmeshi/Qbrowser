import { defineStore } from 'pinia';

export const useAppStore = defineStore('app', {
  state: () => ({
    // 应用基本信息
    appInfo: {
      name: 'QW Browser',
      version: '1.0.0',
      buildDate: null,
      electronVersion: null,
      nodeVersion: null,
      chromeVersion: null
    },
    
    // 后端服务状态
    backendStatus: {
      isRunning: false,
      port: 8000,
      pid: null,
      startTime: null,
      lastCheck: null,
      error: null
    },
    
    // 系统状态
    systemInfo: {
      platform: null,
      arch: null,
      memory: {
        total: 0,
        used: 0,
        free: 0
      },
      cpu: {
        usage: 0,
        cores: 0
      }
    },
    
    // UI状态
    ui: {
      sidebarCollapsed: false,
      theme: 'light',
      language: 'zh-CN',
      loading: false,
      notifications: []
    },
    
    // 连接状态
    connection: {
      isOnline: true,
      lastPing: null,
      retryCount: 0,
      maxRetries: 3
    }
  }),
  
  getters: {
    // 是否已连接到后端
    isConnected: (state) => {
      return state.backendStatus.isRunning && state.connection.isOnline;
    },
    
    // 内存使用率
    memoryUsage: (state) => {
      const { total, used } = state.systemInfo.memory;
      return total > 0 ? Math.round((used / total) * 100) : 0;
    },
    
    // 应用运行时间
    uptime: (state) => {
      if (!state.backendStatus.startTime) return 0;
      return Date.now() - state.backendStatus.startTime;
    },
    
    // 格式化的运行时间
    formattedUptime: (state) => {
      const uptime = state.backendStatus.startTime 
        ? Date.now() - state.backendStatus.startTime 
        : 0;
      
      const seconds = Math.floor(uptime / 1000) % 60;
      const minutes = Math.floor(uptime / (1000 * 60)) % 60;
      const hours = Math.floor(uptime / (1000 * 60 * 60)) % 24;
      const days = Math.floor(uptime / (1000 * 60 * 60 * 24));
      
      if (days > 0) {
        return `${days}天 ${hours}小时 ${minutes}分钟`;
      } else if (hours > 0) {
        return `${hours}小时 ${minutes}分钟`;
      } else if (minutes > 0) {
        return `${minutes}分钟 ${seconds}秒`;
      } else {
        return `${seconds}秒`;
      }
    },
    
    // 未读通知数量
    unreadNotifications: (state) => {
      return state.ui.notifications.filter(n => !n.read).length;
    }
  },
  
  actions: {
    // 初始化应用
    async initializeApp() {
      try {
        this.ui.loading = true;
        
        // 获取应用信息
        await this.getAppInfo();
        
        // 获取系统信息
        await this.getSystemInfo();
        
        // 检查后端状态
        await this.checkBackendStatus();
        
        // 加载用户设置
        await this.loadUserSettings();
        
      } catch (error) {
        console.error('应用初始化失败:', error);
        this.addNotification({
          type: 'error',
          title: '初始化失败',
          message: '应用初始化时发生错误',
          duration: 5000
        });
      } finally {
        this.ui.loading = false;
      }
    },
    
    // 获取应用信息
    async getAppInfo() {
      try {
        if (window.electronAPI?.getAppInfo) {
          const info = await window.electronAPI.getAppInfo();
          this.appInfo = { ...this.appInfo, ...info };
        }
      } catch (error) {
        console.error('获取应用信息失败:', error);
      }
    },
    
    // 获取系统信息
    async getSystemInfo() {
      try {
        if (window.electronAPI?.getSystemInfo) {
          const info = await window.electronAPI.getSystemInfo();
          this.systemInfo = { ...this.systemInfo, ...info };
        }
      } catch (error) {
        console.error('获取系统信息失败:', error);
      }
    },
    
    // 检查后端状态
    async checkBackendStatus() {
      try {
        this.backendStatus.lastCheck = Date.now();
        
        if (window.electronAPI?.getBackendStatus) {
          const status = await window.electronAPI.getBackendStatus();
          this.updateBackendStatus(status);
          
          // 如果后端运行中，测试连接
          if (status.isRunning) {
            await this.pingBackend();
          }
        }
      } catch (error) {
        console.error('检查后端状态失败:', error);
        this.backendStatus.error = error.message;
        this.connection.isOnline = false;
      }
    },
    
    // 更新后端状态
    updateBackendStatus(status) {
      this.backendStatus = {
        ...this.backendStatus,
        ...status,
        lastCheck: Date.now()
      };
      
      // 重置连接重试计数
      if (status.isRunning) {
        this.connection.retryCount = 0;
      }
    },
    
    // Ping后端服务
    async pingBackend() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/health');
          this.connection.isOnline = response.status === 'ok';
          this.connection.lastPing = Date.now();
          this.connection.retryCount = 0;
        }
      } catch (error) {
        this.connection.isOnline = false;
        this.connection.retryCount++;
        
        // 如果重试次数超过限制，显示错误通知
        if (this.connection.retryCount >= this.connection.maxRetries) {
          this.addNotification({
            type: 'error',
            title: '连接失败',
            message: '无法连接到后端服务，请检查服务状态',
            duration: 5000
          });
        }
      }
    },
    
    // 重启后端服务
    async restartBackend() {
      try {
        this.ui.loading = true;
        
        if (window.electronAPI?.restartBackend) {
          await window.electronAPI.restartBackend();
          
          // 等待服务启动
          await new Promise(resolve => setTimeout(resolve, 3000));
          
          // 重新检查状态
          await this.checkBackendStatus();
          
          this.addNotification({
            type: 'success',
            title: '重启成功',
            message: '后端服务已重新启动',
            duration: 3000
          });
        }
      } catch (error) {
        console.error('重启后端失败:', error);
        this.addNotification({
          type: 'error',
          title: '重启失败',
          message: '后端服务重启失败: ' + error.message,
          duration: 5000
        });
      } finally {
        this.ui.loading = false;
      }
    },
    
    // 加载用户设置
    async loadUserSettings() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/settings/ui');
          const settings = response.settings || {};
          
          // 应用UI设置
          if (settings.theme) this.ui.theme = settings.theme;
          if (settings.language) this.ui.language = settings.language;
          if (typeof settings.sidebarCollapsed === 'boolean') {
            this.ui.sidebarCollapsed = settings.sidebarCollapsed;
          }
        }
      } catch (error) {
        console.error('加载用户设置失败:', error);
      }
    },
    
    // 保存用户设置
    async saveUserSettings() {
      try {
        if (window.httpAPI) {
          await window.httpAPI.post('/api/settings/ui', {
            theme: this.ui.theme,
            language: this.ui.language,
            sidebarCollapsed: this.ui.sidebarCollapsed
          });
        }
      } catch (error) {
        console.error('保存用户设置失败:', error);
      }
    },
    
    // 切换侧边栏
    toggleSidebar() {
      this.ui.sidebarCollapsed = !this.ui.sidebarCollapsed;
      this.saveUserSettings();
    },
    
    // 设置主题
    setTheme(theme) {
      this.ui.theme = theme;
      this.saveUserSettings();
      
      // 应用主题到DOM
      document.documentElement.setAttribute('data-theme', theme);
    },
    
    // 设置语言
    setLanguage(language) {
      this.ui.language = language;
      this.saveUserSettings();
    },
    
    // 添加通知
    addNotification(notification) {
      const id = Date.now() + Math.random();
      const newNotification = {
        id,
        type: 'info',
        title: '',
        message: '',
        duration: 3000,
        read: false,
        timestamp: Date.now(),
        ...notification
      };
      
      this.ui.notifications.unshift(newNotification);
      
      // 自动移除通知
      if (newNotification.duration > 0) {
        setTimeout(() => {
          this.removeNotification(id);
        }, newNotification.duration);
      }
      
      // 限制通知数量
      if (this.ui.notifications.length > 50) {
        this.ui.notifications = this.ui.notifications.slice(0, 50);
      }
    },
    
    // 移除通知
    removeNotification(id) {
      const index = this.ui.notifications.findIndex(n => n.id === id);
      if (index > -1) {
        this.ui.notifications.splice(index, 1);
      }
    },
    
    // 标记通知为已读
    markNotificationAsRead(id) {
      const notification = this.ui.notifications.find(n => n.id === id);
      if (notification) {
        notification.read = true;
      }
    },
    
    // 清除所有通知
    clearAllNotifications() {
      this.ui.notifications = [];
    },
    
    // 标记所有通知为已读
    markAllNotificationsAsRead() {
      this.ui.notifications.forEach(n => n.read = true);
    },
    
    // 开始定期检查
    startPeriodicCheck() {
      // 每30秒检查一次后端状态
      setInterval(() => {
        this.checkBackendStatus();
      }, 30000);
      
      // 每5分钟更新一次系统信息
      setInterval(() => {
        this.getSystemInfo();
      }, 300000);
    },
    
    // 处理应用错误
    handleError(error, context = '') {
      console.error(`应用错误 [${context}]:`, error);
      
      this.addNotification({
        type: 'error',
        title: '应用错误',
        message: context ? `${context}: ${error.message}` : error.message,
        duration: 5000
      });
    }
  }
});