import { defineStore } from 'pinia';

export const useExtensionStore = defineStore('extension', {
  state: () => ({
    // 扩展列表
    extensions: [],
    
    // 扩展商店列表
    storeExtensions: [],
    
    // 当前选中的扩展
    selectedExtension: null,
    
    // 扩展统计信息
    stats: {
      total: 0,
      enabled: 0,
      disabled: 0,
      updateAvailable: 0,
      installed: 0
    },
    
    // 加载状态
    loading: {
      extensions: false,
      store: false,
      installing: false,
      updating: false,
      configuring: false
    },
    
    // 过滤和排序
    filters: {
      status: 'all', // all, enabled, disabled, update_available
      category: 'all', // all, automation, scraping, utility, development
      search: '',
      sortBy: 'name',
      sortOrder: 'asc'
    },
    
    // 批量操作
    selectedExtensions: [],
    
    // 扩展配置
    extensionConfigs: {},
    
    // 安装进度
    installProgress: {},
    
    // 扩展商店配置
    storeConfig: {
      url: 'https://extensions.qw-browser.com',
      enabled: true,
      autoUpdate: false
    }
  }),
  
  getters: {
    // 过滤后的扩展列表
    filteredExtensions: (state) => {
      let extensions = [...state.extensions];
      
      // 状态过滤
      if (state.filters.status !== 'all') {
        if (state.filters.status === 'update_available') {
          extensions = extensions.filter(ext => ext.update_available);
        } else {
          extensions = extensions.filter(ext => ext.status === state.filters.status);
        }
      }
      
      // 分类过滤
      if (state.filters.category !== 'all') {
        extensions = extensions.filter(ext => ext.category === state.filters.category);
      }
      
      // 搜索过滤
      if (state.filters.search) {
        const search = state.filters.search.toLowerCase();
        extensions = extensions.filter(ext => 
          ext.name.toLowerCase().includes(search) ||
          ext.description.toLowerCase().includes(search) ||
          ext.author.toLowerCase().includes(search) ||
          (ext.tags && ext.tags.some(tag => tag.toLowerCase().includes(search)))
        );
      }
      
      // 排序
      extensions.sort((a, b) => {
        const aValue = a[state.filters.sortBy];
        const bValue = b[state.filters.sortBy];
        
        if (state.filters.sortOrder === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });
      
      return extensions;
    },
    
    // 已启用的扩展
    enabledExtensions: (state) => {
      return state.extensions.filter(ext => ext.status === 'enabled');
    },
    
    // 可更新的扩展
    updatableExtensions: (state) => {
      return state.extensions.filter(ext => ext.update_available);
    },
    
    // 获取扩展by ID
    getExtensionById: (state) => (id) => {
      return state.extensions.find(ext => ext.id === id);
    },
    
    // 获取扩展配置
    getExtensionConfig: (state) => (id) => {
      return state.extensionConfigs[id] || {};
    },
    
    // 是否有选中的扩展
    hasSelectedExtensions: (state) => {
      return state.selectedExtensions.length > 0;
    },
    
    // 选中扩展的状态统计
    selectedExtensionsStats: (state) => {
      const stats = { enabled: 0, disabled: 0, updateAvailable: 0 };
      state.selectedExtensions.forEach(id => {
        const ext = state.extensions.find(e => e.id === id);
        if (ext) {
          stats[ext.status] = (stats[ext.status] || 0) + 1;
          if (ext.update_available) {
            stats.updateAvailable++;
          }
        }
      });
      return stats;
    },
    
    // 扩展分类列表
    categories: (state) => {
      const categories = new Set();
      state.extensions.forEach(ext => {
        if (ext.category) categories.add(ext.category);
      });
      return Array.from(categories).sort();
    },
    
    // 安装进度
    getInstallProgress: (state) => (id) => {
      return state.installProgress[id] || { progress: 0, status: 'idle' };
    }
  },
  
  actions: {
    // 加载扩展列表
    async loadExtensions() {
      try {
        this.loading.extensions = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/extensions');
          this.extensions = response.extensions || [];
          this.updateStats();
        }
      } catch (error) {
        console.error('加载扩展列表失败:', error);
        throw error;
      } finally {
        this.loading.extensions = false;
      }
    },
    
    // 加载扩展商店
    async loadStore() {
      try {
        this.loading.store = true;
        
        if (window.httpAPI && this.storeConfig.enabled) {
          const response = await window.httpAPI.get('/api/extensions/store');
          this.storeExtensions = response.extensions || [];
        }
      } catch (error) {
        console.error('加载扩展商店失败:', error);
        throw error;
      } finally {
        this.loading.store = false;
      }
    },
    
    // 安装扩展
    async installExtension(source, options = {}) {
      try {
        this.loading.installing = true;
        
        const installId = Date.now().toString();
        this.installProgress[installId] = { progress: 0, status: 'downloading' };
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/extensions/install', {
            source,
            options,
            install_id: installId
          });
          
          const newExtension = response.extension;
          
          // 添加到列表
          this.extensions.unshift(newExtension);
          this.updateStats();
          
          // 清理安装进度
          delete this.installProgress[installId];
          
          return newExtension;
        }
      } catch (error) {
        console.error('安装扩展失败:', error);
        throw error;
      } finally {
        this.loading.installing = false;
      }
    },
    
    // 卸载扩展
    async uninstallExtension(extensionId) {
      try {
        if (window.httpAPI) {
          await window.httpAPI.delete(`/api/extensions/${extensionId}`);
          
          // 从列表中移除
          const index = this.extensions.findIndex(ext => ext.id === extensionId);
          if (index > -1) {
            this.extensions.splice(index, 1);
            this.updateStats();
          }
          
          // 清理配置
          delete this.extensionConfigs[extensionId];
          
          // 从选中列表中移除
          this.removeFromSelection(extensionId);
        }
      } catch (error) {
        console.error('卸载扩展失败:', error);
        throw error;
      }
    },
    
    // 启用扩展
    async enableExtension(extensionId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/extensions/${extensionId}/enable`);
          
          // 更新扩展状态
          const extension = this.getExtensionById(extensionId);
          if (extension) {
            Object.assign(extension, response.extension);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('启用扩展失败:', error);
        throw error;
      }
    },
    
    // 禁用扩展
    async disableExtension(extensionId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/extensions/${extensionId}/disable`);
          
          // 更新扩展状态
          const extension = this.getExtensionById(extensionId);
          if (extension) {
            Object.assign(extension, response.extension);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('禁用扩展失败:', error);
        throw error;
      }
    },
    
    // 更新扩展
    async updateExtension(extensionId) {
      try {
        this.loading.updating = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/extensions/${extensionId}/update`);
          
          // 更新扩展信息
          const extension = this.getExtensionById(extensionId);
          if (extension) {
            Object.assign(extension, response.extension);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('更新扩展失败:', error);
        throw error;
      } finally {
        this.loading.updating = false;
      }
    },
    
    // 检查扩展更新
    async checkUpdates() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/extensions/check-updates');
          
          // 更新扩展信息
          response.updates.forEach(update => {
            const extension = this.getExtensionById(update.id);
            if (extension) {
              extension.update_available = true;
              extension.latest_version = update.latest_version;
            }
          });
          
          this.updateStats();
          return response.updates;
        }
      } catch (error) {
        console.error('检查扩展更新失败:', error);
        throw error;
      }
    },
    
    // 批量更新扩展
    async updateAllExtensions() {
      const updatableIds = this.updatableExtensions.map(ext => ext.id);
      const promises = updatableIds.map(id => this.updateExtension(id));
      await Promise.allSettled(promises);
    },
    
    // 获取扩展详情
    async getExtensionDetails(extensionId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get(`/api/extensions/${extensionId}`);
          return response.extension;
        }
      } catch (error) {
        console.error('获取扩展详情失败:', error);
        throw error;
      }
    },
    
    // 获取扩展配置
    async loadExtensionConfig(extensionId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get(`/api/extensions/${extensionId}/config`);
          this.extensionConfigs[extensionId] = response.config || {};
          return response.config;
        }
      } catch (error) {
        console.error('获取扩展配置失败:', error);
        throw error;
      }
    },
    
    // 保存扩展配置
    async saveExtensionConfig(extensionId, config) {
      try {
        this.loading.configuring = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.put(`/api/extensions/${extensionId}/config`, config);
          this.extensionConfigs[extensionId] = response.config;
          
          return response;
        }
      } catch (error) {
        console.error('保存扩展配置失败:', error);
        throw error;
      } finally {
        this.loading.configuring = false;
      }
    },
    
    // 重置扩展配置
    async resetExtensionConfig(extensionId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.delete(`/api/extensions/${extensionId}/config`);
          this.extensionConfigs[extensionId] = response.config || {};
          
          return response;
        }
      } catch (error) {
        console.error('重置扩展配置失败:', error);
        throw error;
      }
    },
    
    // 获取扩展日志
    async getExtensionLogs(extensionId, options = {}) {
      try {
        if (window.httpAPI) {
          const params = new URLSearchParams(options).toString();
          const response = await window.httpAPI.get(`/api/extensions/${extensionId}/logs?${params}`);
          return response.logs;
        }
      } catch (error) {
        console.error('获取扩展日志失败:', error);
        throw error;
      }
    },
    
    // 批量启用扩展
    async enableSelectedExtensions() {
      const promises = this.selectedExtensions.map(id => this.enableExtension(id));
      await Promise.allSettled(promises);
    },
    
    // 批量禁用扩展
    async disableSelectedExtensions() {
      const promises = this.selectedExtensions.map(id => this.disableExtension(id));
      await Promise.allSettled(promises);
    },
    
    // 批量更新扩展
    async updateSelectedExtensions() {
      const updatableSelected = this.selectedExtensions.filter(id => {
        const ext = this.getExtensionById(id);
        return ext && ext.update_available;
      });
      
      const promises = updatableSelected.map(id => this.updateExtension(id));
      await Promise.allSettled(promises);
    },
    
    // 批量卸载扩展
    async uninstallSelectedExtensions() {
      const promises = this.selectedExtensions.map(id => this.uninstallExtension(id));
      await Promise.allSettled(promises);
      this.selectedExtensions = [];
    },
    
    // 更新统计信息
    updateStats() {
      this.stats = {
        total: this.extensions.length,
        enabled: this.extensions.filter(ext => ext.status === 'enabled').length,
        disabled: this.extensions.filter(ext => ext.status === 'disabled').length,
        updateAvailable: this.extensions.filter(ext => ext.update_available).length,
        installed: this.extensions.length
      };
    },
    
    // 设置过滤器
    setFilter(key, value) {
      this.filters[key] = value;
    },
    
    // 重置过滤器
    resetFilters() {
      this.filters = {
        status: 'all',
        category: 'all',
        search: '',
        sortBy: 'name',
        sortOrder: 'asc'
      };
    },
    
    // 选择扩展
    selectExtension(extensionId) {
      if (!this.selectedExtensions.includes(extensionId)) {
        this.selectedExtensions.push(extensionId);
      }
    },
    
    // 取消选择扩展
    deselectExtension(extensionId) {
      const index = this.selectedExtensions.indexOf(extensionId);
      if (index > -1) {
        this.selectedExtensions.splice(index, 1);
      }
    },
    
    // 切换扩展选择状态
    toggleExtensionSelection(extensionId) {
      if (this.selectedExtensions.includes(extensionId)) {
        this.deselectExtension(extensionId);
      } else {
        this.selectExtension(extensionId);
      }
    },
    
    // 全选/取消全选
    toggleSelectAll() {
      if (this.selectedExtensions.length === this.filteredExtensions.length) {
        this.selectedExtensions = [];
      } else {
        this.selectedExtensions = this.filteredExtensions.map(ext => ext.id);
      }
    },
    
    // 从选择列表中移除
    removeFromSelection(extensionId) {
      this.deselectExtension(extensionId);
    },
    
    // 清空选择
    clearSelection() {
      this.selectedExtensions = [];
    },
    
    // 设置当前选中扩展
    setSelectedExtension(extension) {
      this.selectedExtension = extension;
    },
    
    // 更新安装进度
    updateInstallProgress(installId, progress, status) {
      if (this.installProgress[installId]) {
        this.installProgress[installId] = { progress, status };
      }
    },
    
    // 搜索扩展商店
    async searchStore(query, options = {}) {
      try {
        if (window.httpAPI && this.storeConfig.enabled) {
          const params = new URLSearchParams({ query, ...options }).toString();
          const response = await window.httpAPI.get(`/api/extensions/store/search?${params}`);
          return response.extensions || [];
        }
      } catch (error) {
        console.error('搜索扩展商店失败:', error);
        throw error;
      }
    },
    
    // 获取扩展商店分类
    async getStoreCategories() {
      try {
        if (window.httpAPI && this.storeConfig.enabled) {
          const response = await window.httpAPI.get('/api/extensions/store/categories');
          return response.categories || [];
        }
      } catch (error) {
        console.error('获取扩展商店分类失败:', error);
        throw error;
      }
    },
    
    // 从文件安装扩展
    async installFromFile(filePath) {
      try {
        this.loading.installing = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/extensions/install-file', {
            file_path: filePath
          });
          
          const newExtension = response.extension;
          
          // 添加到列表
          this.extensions.unshift(newExtension);
          this.updateStats();
          
          return newExtension;
        }
      } catch (error) {
        console.error('从文件安装扩展失败:', error);
        throw error;
      } finally {
        this.loading.installing = false;
      }
    },
    
    // 从URL安装扩展
    async installFromUrl(url) {
      try {
        this.loading.installing = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/extensions/install-url', {
            url
          });
          
          const newExtension = response.extension;
          
          // 添加到列表
          this.extensions.unshift(newExtension);
          this.updateStats();
          
          return newExtension;
        }
      } catch (error) {
        console.error('从URL安装扩展失败:', error);
        throw error;
      } finally {
        this.loading.installing = false;
      }
    },
    
    // 导出扩展
    async exportExtension(extensionId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get(`/api/extensions/${extensionId}/export`);
          return response.package;
        }
      } catch (error) {
        console.error('导出扩展失败:', error);
        throw error;
      }
    },
    
    // 设置商店配置
    setStoreConfig(config) {
      this.storeConfig = { ...this.storeConfig, ...config };
    },
    
    // 清理扩展缓存
    async clearExtensionCache() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.delete('/api/extensions/cache');
          return response;
        }
      } catch (error) {
        console.error('清理扩展缓存失败:', error);
        throw error;
      }
    }
  }
});