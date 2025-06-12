import { defineStore } from 'pinia';

export const useBrowserStore = defineStore('browser', {
  state: () => ({
    // 浏览器实例列表
    instances: [],
    
    // 浏览器配置模板
    templates: [],
    
    // 当前选中的实例
    selectedInstance: null,
    
    // 浏览器统计信息
    stats: {
      total: 0,
      running: 0,
      stopped: 0,
      error: 0
    },
    
    // 加载状态
    loading: {
      instances: false,
      templates: false,
      creating: false,
      starting: false,
      stopping: false
    },
    
    // 过滤和排序
    filters: {
      status: 'all', // all, running, stopped, error
      search: '',
      sortBy: 'created_at',
      sortOrder: 'desc'
    },
    
    // 批量操作
    selectedInstances: [],
    
    // 实时监控数据
    monitoring: {
      enabled: false,
      interval: 5000,
      data: {}
    }
  }),
  
  getters: {
    // 过滤后的实例列表
    filteredInstances: (state) => {
      let instances = [...state.instances];
      
      // 状态过滤
      if (state.filters.status !== 'all') {
        instances = instances.filter(instance => instance.status === state.filters.status);
      }
      
      // 搜索过滤
      if (state.filters.search) {
        const search = state.filters.search.toLowerCase();
        instances = instances.filter(instance => 
          instance.name.toLowerCase().includes(search) ||
          instance.profile.toLowerCase().includes(search) ||
          (instance.tags && instance.tags.some(tag => tag.toLowerCase().includes(search)))
        );
      }
      
      // 排序
      instances.sort((a, b) => {
        const aValue = a[state.filters.sortBy];
        const bValue = b[state.filters.sortBy];
        
        if (state.filters.sortOrder === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });
      
      return instances;
    },
    
    // 运行中的实例
    runningInstances: (state) => {
      return state.instances.filter(instance => instance.status === 'running');
    },
    
    // 获取实例by ID
    getInstanceById: (state) => (id) => {
      return state.instances.find(instance => instance.id === id);
    },
    
    // 获取模板by ID
    getTemplateById: (state) => (id) => {
      return state.templates.find(template => template.id === id);
    },
    
    // 是否有选中的实例
    hasSelectedInstances: (state) => {
      return state.selectedInstances.length > 0;
    },
    
    // 选中实例的状态统计
    selectedInstancesStats: (state) => {
      const stats = { running: 0, stopped: 0, error: 0 };
      state.selectedInstances.forEach(id => {
        const instance = state.instances.find(i => i.id === id);
        if (instance) {
          stats[instance.status] = (stats[instance.status] || 0) + 1;
        }
      });
      return stats;
    }
  },
  
  actions: {
    // 加载浏览器实例列表
    async loadInstances() {
      try {
        this.loading.instances = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/browser/instances');
          this.instances = response.instances || [];
          this.updateStats();
        }
      } catch (error) {
        console.error('加载浏览器实例失败:', error);
        throw error;
      } finally {
        this.loading.instances = false;
      }
    },
    
    // 加载配置模板
    async loadTemplates() {
      try {
        this.loading.templates = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/browser/templates');
          this.templates = response.templates || [];
        }
      } catch (error) {
        console.error('加载配置模板失败:', error);
        throw error;
      } finally {
        this.loading.templates = false;
      }
    },
    
    // 创建浏览器实例
    async createInstance(config) {
      try {
        this.loading.creating = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/browser/instances', config);
          const newInstance = response.instance;
          
          // 添加到列表
          this.instances.unshift(newInstance);
          this.updateStats();
          
          return newInstance;
        }
      } catch (error) {
        console.error('创建浏览器实例失败:', error);
        throw error;
      } finally {
        this.loading.creating = false;
      }
    },
    
    // 启动浏览器实例
    async startInstance(instanceId) {
      try {
        this.loading.starting = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/browser/instances/${instanceId}/start`);
          
          // 更新实例状态
          const instance = this.getInstanceById(instanceId);
          if (instance) {
            Object.assign(instance, response.instance);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('启动浏览器实例失败:', error);
        throw error;
      } finally {
        this.loading.starting = false;
      }
    },
    
    // 停止浏览器实例
    async stopInstance(instanceId) {
      try {
        this.loading.stopping = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/browser/instances/${instanceId}/stop`);
          
          // 更新实例状态
          const instance = this.getInstanceById(instanceId);
          if (instance) {
            Object.assign(instance, response.instance);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('停止浏览器实例失败:', error);
        throw error;
      } finally {
        this.loading.stopping = false;
      }
    },
    
    // 重启浏览器实例
    async restartInstance(instanceId) {
      await this.stopInstance(instanceId);
      await new Promise(resolve => setTimeout(resolve, 2000));
      await this.startInstance(instanceId);
    },
    
    // 删除浏览器实例
    async deleteInstance(instanceId) {
      try {
        if (window.httpAPI) {
          await window.httpAPI.delete(`/api/browser/instances/${instanceId}`);
          
          // 从列表中移除
          const index = this.instances.findIndex(instance => instance.id === instanceId);
          if (index > -1) {
            this.instances.splice(index, 1);
            this.updateStats();
          }
          
          // 从选中列表中移除
          this.removeFromSelection(instanceId);
        }
      } catch (error) {
        console.error('删除浏览器实例失败:', error);
        throw error;
      }
    },
    
    // 更新浏览器实例
    async updateInstance(instanceId, updates) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.put(`/api/browser/instances/${instanceId}`, updates);
          
          // 更新实例
          const instance = this.getInstanceById(instanceId);
          if (instance) {
            Object.assign(instance, response.instance);
          }
          
          return response.instance;
        }
      } catch (error) {
        console.error('更新浏览器实例失败:', error);
        throw error;
      }
    },
    
    // 获取实例详情
    async getInstanceDetails(instanceId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get(`/api/browser/instances/${instanceId}`);
          return response.instance;
        }
      } catch (error) {
        console.error('获取实例详情失败:', error);
        throw error;
      }
    },
    
    // 获取实例日志
    async getInstanceLogs(instanceId, options = {}) {
      try {
        if (window.httpAPI) {
          const params = new URLSearchParams(options).toString();
          const response = await window.httpAPI.get(`/api/browser/instances/${instanceId}/logs?${params}`);
          return response.logs;
        }
      } catch (error) {
        console.error('获取实例日志失败:', error);
        throw error;
      }
    },
    
    // 批量启动实例
    async startSelectedInstances() {
      const promises = this.selectedInstances.map(id => this.startInstance(id));
      await Promise.allSettled(promises);
    },
    
    // 批量停止实例
    async stopSelectedInstances() {
      const promises = this.selectedInstances.map(id => this.stopInstance(id));
      await Promise.allSettled(promises);
    },
    
    // 批量删除实例
    async deleteSelectedInstances() {
      const promises = this.selectedInstances.map(id => this.deleteInstance(id));
      await Promise.allSettled(promises);
      this.selectedInstances = [];
    },
    
    // 更新统计信息
    updateStats() {
      this.stats = {
        total: this.instances.length,
        running: this.instances.filter(i => i.status === 'running').length,
        stopped: this.instances.filter(i => i.status === 'stopped').length,
        error: this.instances.filter(i => i.status === 'error').length
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
        search: '',
        sortBy: 'created_at',
        sortOrder: 'desc'
      };
    },
    
    // 选择实例
    selectInstance(instanceId) {
      if (!this.selectedInstances.includes(instanceId)) {
        this.selectedInstances.push(instanceId);
      }
    },
    
    // 取消选择实例
    deselectInstance(instanceId) {
      const index = this.selectedInstances.indexOf(instanceId);
      if (index > -1) {
        this.selectedInstances.splice(index, 1);
      }
    },
    
    // 切换实例选择状态
    toggleInstanceSelection(instanceId) {
      if (this.selectedInstances.includes(instanceId)) {
        this.deselectInstance(instanceId);
      } else {
        this.selectInstance(instanceId);
      }
    },
    
    // 全选/取消全选
    toggleSelectAll() {
      if (this.selectedInstances.length === this.filteredInstances.length) {
        this.selectedInstances = [];
      } else {
        this.selectedInstances = this.filteredInstances.map(instance => instance.id);
      }
    },
    
    // 从选择列表中移除
    removeFromSelection(instanceId) {
      this.deselectInstance(instanceId);
    },
    
    // 清空选择
    clearSelection() {
      this.selectedInstances = [];
    },
    
    // 设置当前选中实例
    setSelectedInstance(instance) {
      this.selectedInstance = instance;
    },
    
    // 开始监控
    startMonitoring() {
      if (this.monitoring.enabled) return;
      
      this.monitoring.enabled = true;
      
      const monitor = async () => {
        if (!this.monitoring.enabled) return;
        
        try {
          // 更新运行中实例的状态
          const runningIds = this.runningInstances.map(i => i.id);
          if (runningIds.length > 0) {
            const response = await window.httpAPI.post('/api/browser/instances/status', {
              instance_ids: runningIds
            });
            
            // 更新实例状态
            response.instances.forEach(updatedInstance => {
              const instance = this.getInstanceById(updatedInstance.id);
              if (instance) {
                Object.assign(instance, updatedInstance);
              }
            });
            
            this.updateStats();
          }
        } catch (error) {
          console.error('监控更新失败:', error);
        }
        
        // 继续下一次监控
        if (this.monitoring.enabled) {
          setTimeout(monitor, this.monitoring.interval);
        }
      };
      
      // 开始监控
      setTimeout(monitor, this.monitoring.interval);
    },
    
    // 停止监控
    stopMonitoring() {
      this.monitoring.enabled = false;
    },
    
    // 设置监控间隔
    setMonitoringInterval(interval) {
      this.monitoring.interval = interval;
    },
    
    // 刷新实例状态
    async refreshInstanceStatus(instanceId) {
      try {
        const response = await window.httpAPI.get(`/api/browser/instances/${instanceId}/status`);
        const instance = this.getInstanceById(instanceId);
        if (instance) {
          Object.assign(instance, response.instance);
          this.updateStats();
        }
      } catch (error) {
        console.error('刷新实例状态失败:', error);
        throw error;
      }
    },
    
    // 导出实例配置
    async exportInstanceConfig(instanceId) {
      try {
        const response = await window.httpAPI.get(`/api/browser/instances/${instanceId}/export`);
        return response.config;
      } catch (error) {
        console.error('导出实例配置失败:', error);
        throw error;
      }
    },
    
    // 导入实例配置
    async importInstanceConfig(config) {
      try {
        const response = await window.httpAPI.post('/api/browser/instances/import', config);
        
        // 添加导入的实例
        if (response.instances) {
          this.instances.unshift(...response.instances);
          this.updateStats();
        }
        
        return response;
      } catch (error) {
        console.error('导入实例配置失败:', error);
        throw error;
      }
    }
  }
});