import { defineStore } from 'pinia';

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    // 通用设置
    general: {
      language: 'zh-CN',
      theme: 'light',
      autoStart: false,
      minimizeToTray: true,
      closeToTray: false,
      checkUpdates: true,
      autoUpdate: false,
      telemetry: true,
      crashReports: true
    },
    
    // 浏览器设置
    browser: {
      defaultProfile: 'default',
      headless: false,
      userAgent: '',
      viewport: {
        width: 1920,
        height: 1080
      },
      timeout: {
        page: 30000,
        element: 5000,
        navigation: 30000
      },
      proxy: {
        enabled: false,
        type: 'http', // http, socks5
        host: '',
        port: '',
        username: '',
        password: ''
      },
      extensions: {
        allowedPaths: [],
        autoLoad: true,
        devMode: false
      },
      security: {
        allowInsecureContent: false,
        disableWebSecurity: false,
        ignoreCertificateErrors: false
      }
    },
    
    // 性能设置
    performance: {
      maxConcurrentBrowsers: 5,
      maxConcurrentTasks: 10,
      memoryLimit: 4096, // MB
      cpuLimit: 80, // %
      diskCacheSize: 1024, // MB
      enableGPU: true,
      enableHardwareAcceleration: true,
      processIsolation: true,
      resourceOptimization: {
        images: true,
        css: false,
        javascript: false,
        fonts: false
      }
    },
    
    // 安全设置
    security: {
      apiKey: '',
      allowedOrigins: ['http://localhost:*'],
      rateLimiting: {
        enabled: true,
        maxRequests: 100,
        windowMs: 60000
      },
      encryption: {
        enabled: false,
        algorithm: 'aes-256-gcm',
        keyRotation: 86400000 // 24 hours
      },
      authentication: {
        required: false,
        method: 'token', // token, basic, oauth
        tokenExpiry: 3600000 // 1 hour
      }
    },
    
    // 日志设置
    logging: {
      level: 'info', // debug, info, warn, error
      maxFileSize: 10, // MB
      maxFiles: 5,
      enableConsole: true,
      enableFile: true,
      enableRemote: false,
      remoteEndpoint: '',
      categories: {
        browser: true,
        scheduler: true,
        extensions: true,
        api: true,
        system: true
      }
    },
    
    // 网络设置
    network: {
      port: 8000,
      host: '127.0.0.1',
      cors: {
        enabled: true,
        origins: ['*'],
        methods: ['GET', 'POST', 'PUT', 'DELETE'],
        headers: ['Content-Type', 'Authorization']
      },
      ssl: {
        enabled: false,
        certPath: '',
        keyPath: '',
        passphrase: ''
      },
      compression: {
        enabled: true,
        level: 6,
        threshold: 1024
      }
    },
    
    // 存储设置
    storage: {
      dataPath: '',
      cachePath: '',
      logsPath: '',
      backupPath: '',
      autoBackup: {
        enabled: true,
        interval: 86400000, // 24 hours
        maxBackups: 7
      },
      cleanup: {
        enabled: true,
        interval: 604800000, // 7 days
        maxAge: 2592000000 // 30 days
      }
    },
    
    // 通知设置
    notifications: {
      enabled: true,
      sound: true,
      desktop: true,
      email: {
        enabled: false,
        smtp: {
          host: '',
          port: 587,
          secure: false,
          username: '',
          password: ''
        },
        from: '',
        to: []
      },
      webhook: {
        enabled: false,
        url: '',
        events: ['task_completed', 'task_failed', 'browser_crashed']
      }
    },
    
    // 开发者设置
    developer: {
      debugMode: false,
      devTools: false,
      hotReload: false,
      mockData: false,
      apiLogging: false,
      performanceMonitoring: false
    },
    
    // 加载状态
    loading: {
      general: false,
      browser: false,
      performance: false,
      security: false,
      logging: false,
      network: false,
      storage: false,
      notifications: false,
      developer: false
    },
    
    // 保存状态
    saving: false,
    
    // 重置状态
    resetting: false,
    
    // 设置变更历史
    changeHistory: [],
    
    // 导入/导出状态
    importing: false,
    exporting: false
  }),
  
  getters: {
    // 获取所有设置
    allSettings: (state) => {
      return {
        general: state.general,
        browser: state.browser,
        performance: state.performance,
        security: state.security,
        logging: state.logging,
        network: state.network,
        storage: state.storage,
        notifications: state.notifications,
        developer: state.developer
      };
    },
    
    // 检查是否有未保存的更改
    hasUnsavedChanges: (state) => {
      return state.changeHistory.some(change => !change.saved);
    },
    
    // 获取最近的更改
    recentChanges: (state) => {
      return state.changeHistory
        .filter(change => Date.now() - change.timestamp < 86400000) // 24 hours
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, 10);
    },
    
    // 检查设置是否有效
    isValidConfig: (state) => {
      // 基本验证
      if (state.network.port < 1 || state.network.port > 65535) return false;
      if (state.performance.maxConcurrentBrowsers < 1) return false;
      if (state.performance.memoryLimit < 512) return false;
      
      return true;
    },
    
    // 获取代理配置
    proxyConfig: (state) => {
      if (!state.browser.proxy.enabled) return null;
      
      return {
        type: state.browser.proxy.type,
        host: state.browser.proxy.host,
        port: state.browser.proxy.port,
        username: state.browser.proxy.username,
        password: state.browser.proxy.password
      };
    },
    
    // 获取CORS配置
    corsConfig: (state) => {
      return {
        enabled: state.network.cors.enabled,
        origin: state.network.cors.origins,
        methods: state.network.cors.methods,
        allowedHeaders: state.network.cors.headers
      };
    }
  },
  
  actions: {
    // 加载所有设置
    async loadAllSettings() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/settings');
          const settings = response.settings || {};
          
          // 合并设置，保持默认值
          Object.keys(settings).forEach(category => {
            if (this[category]) {
              this[category] = { ...this[category], ...settings[category] };
            }
          });
        }
      } catch (error) {
        console.error('加载设置失败:', error);
        throw error;
      }
    },
    
    // 加载特定分类的设置
    async loadCategorySettings(category) {
      try {
        this.loading[category] = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.get(`/api/settings/${category}`);
          const settings = response.settings || {};
          
          this[category] = { ...this[category], ...settings };
        }
      } catch (error) {
        console.error(`加载${category}设置失败:`, error);
        throw error;
      } finally {
        this.loading[category] = false;
      }
    },
    
    // 保存所有设置
    async saveAllSettings() {
      try {
        this.saving = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.put('/api/settings', this.allSettings);
          
          // 标记所有更改为已保存
          this.changeHistory.forEach(change => {
            change.saved = true;
          });
          
          return response;
        }
      } catch (error) {
        console.error('保存设置失败:', error);
        throw error;
      } finally {
        this.saving = false;
      }
    },
    
    // 保存特定分类的设置
    async saveCategorySettings(category) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.put(`/api/settings/${category}`, {
            settings: this[category]
          });
          
          // 记录更改
          this.recordChange(category, 'update', this[category]);
          
          return response;
        }
      } catch (error) {
        console.error(`保存${category}设置失败:`, error);
        throw error;
      }
    },
    
    // 重置所有设置
    async resetAllSettings() {
      try {
        this.resetting = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.delete('/api/settings');
          
          // 重新加载默认设置
          await this.loadAllSettings();
          
          // 记录重置操作
          this.recordChange('all', 'reset', null);
          
          return response;
        }
      } catch (error) {
        console.error('重置设置失败:', error);
        throw error;
      } finally {
        this.resetting = false;
      }
    },
    
    // 重置特定分类的设置
    async resetCategorySettings(category) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.delete(`/api/settings/${category}`);
          
          // 重新加载该分类的默认设置
          await this.loadCategorySettings(category);
          
          // 记录重置操作
          this.recordChange(category, 'reset', null);
          
          return response;
        }
      } catch (error) {
        console.error(`重置${category}设置失败:`, error);
        throw error;
      }
    },
    
    // 更新设置项
    updateSetting(category, key, value) {
      if (this[category] && this[category].hasOwnProperty(key)) {
        const oldValue = this[category][key];
        this[category][key] = value;
        
        // 记录更改
        this.recordChange(category, 'update', { key, oldValue, newValue: value });
      }
    },
    
    // 批量更新设置
    updateSettings(category, settings) {
      if (this[category]) {
        const oldSettings = { ...this[category] };
        this[category] = { ...this[category], ...settings };
        
        // 记录更改
        this.recordChange(category, 'batch_update', { oldSettings, newSettings: settings });
      }
    },
    
    // 记录设置更改
    recordChange(category, action, data) {
      const change = {
        id: Date.now() + Math.random(),
        category,
        action,
        data,
        timestamp: Date.now(),
        saved: false
      };
      
      this.changeHistory.unshift(change);
      
      // 限制历史记录数量
      if (this.changeHistory.length > 100) {
        this.changeHistory = this.changeHistory.slice(0, 100);
      }
    },
    
    // 导出设置
    async exportSettings(categories = null) {
      try {
        this.exporting = true;
        
        const settingsToExport = categories 
          ? Object.fromEntries(categories.map(cat => [cat, this[cat]]))
          : this.allSettings;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/settings/export', {
            settings: settingsToExport,
            timestamp: Date.now(),
            version: '1.0.0'
          });
          
          return response.exportData;
        }
      } catch (error) {
        console.error('导出设置失败:', error);
        throw error;
      } finally {
        this.exporting = false;
      }
    },
    
    // 导入设置
    async importSettings(settingsData, options = {}) {
      try {
        this.importing = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/settings/import', {
            settings: settingsData,
            options: {
              overwrite: options.overwrite || false,
              backup: options.backup !== false,
              validate: options.validate !== false
            }
          });
          
          // 重新加载设置
          await this.loadAllSettings();
          
          // 记录导入操作
          this.recordChange('all', 'import', settingsData);
          
          return response;
        }
      } catch (error) {
        console.error('导入设置失败:', error);
        throw error;
      } finally {
        this.importing = false;
      }
    },
    
    // 验证设置
    async validateSettings(settings = null) {
      try {
        const settingsToValidate = settings || this.allSettings;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/settings/validate', {
            settings: settingsToValidate
          });
          
          return response.validation;
        }
      } catch (error) {
        console.error('验证设置失败:', error);
        throw error;
      }
    },
    
    // 获取设置模式
    async getSettingsSchema() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/settings/schema');
          return response.schema;
        }
      } catch (error) {
        console.error('获取设置模式失败:', error);
        throw error;
      }
    },
    
    // 测试连接设置
    async testConnection(type, config) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/settings/test-connection', {
            type,
            config
          });
          
          return response.result;
        }
      } catch (error) {
        console.error('测试连接失败:', error);
        throw error;
      }
    },
    
    // 清理缓存
    async clearCache() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.delete('/api/cache');
          return response;
        }
      } catch (error) {
        console.error('清理缓存失败:', error);
        throw error;
      }
    },
    
    // 清理日志
    async clearLogs() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.delete('/api/logs');
          return response;
        }
      } catch (error) {
        console.error('清理日志失败:', error);
        throw error;
      }
    },
    
    // 检查更新
    async checkForUpdates() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/updates/check');
          return response.update;
        }
      } catch (error) {
        console.error('检查更新失败:', error);
        throw error;
      }
    },
    
    // 下载更新
    async downloadUpdate() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/updates/download');
          return response;
        }
      } catch (error) {
        console.error('下载更新失败:', error);
        throw error;
      }
    },
    
    // 安装更新
    async installUpdate() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/updates/install');
          return response;
        }
      } catch (error) {
        console.error('安装更新失败:', error);
        throw error;
      }
    },
    
    // 获取系统信息
    async getSystemInfo() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/system/info');
          return response.info;
        }
      } catch (error) {
        console.error('获取系统信息失败:', error);
        throw error;
      }
    },
    
    // 获取许可证信息
    async getLicenseInfo() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/license');
          return response.license;
        }
      } catch (error) {
        console.error('获取许可证信息失败:', error);
        throw error;
      }
    },
    
    // 应用主题
    applyTheme(theme) {
      this.general.theme = theme;
      document.documentElement.setAttribute('data-theme', theme);
      
      // 保存设置
      this.saveCategorySettings('general');
    },
    
    // 应用语言
    applyLanguage(language) {
      this.general.language = language;
      
      // 这里可以集成国际化库
      // i18n.locale = language;
      
      // 保存设置
      this.saveCategorySettings('general');
    },
    
    // 切换开发者模式
    toggleDeveloperMode() {
      this.developer.debugMode = !this.developer.debugMode;
      this.saveCategorySettings('developer');
    },
    
    // 重启应用
    async restartApplication() {
      try {
        if (window.electronAPI?.restartApp) {
          await window.electronAPI.restartApp();
        }
      } catch (error) {
        console.error('重启应用失败:', error);
        throw error;
      }
    }
  }
});