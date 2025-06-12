import { defineStore } from 'pinia';

export const useSchedulerStore = defineStore('scheduler', {
  state: () => ({
    // 任务列表
    tasks: [],
    
    // 任务模板
    templates: [],
    
    // 当前选中的任务
    selectedTask: null,
    
    // 任务统计信息
    stats: {
      total: 0,
      running: 0,
      scheduled: 0,
      paused: 0,
      completed: 0,
      failed: 0
    },
    
    // 加载状态
    loading: {
      tasks: false,
      templates: false,
      creating: false,
      updating: false,
      executing: false
    },
    
    // 过滤和排序
    filters: {
      status: 'all', // all, running, scheduled, paused, completed, failed
      type: 'all', // all, once, recurring
      search: '',
      sortBy: 'created_at',
      sortOrder: 'desc'
    },
    
    // 批量操作
    selectedTasks: [],
    
    // 执行历史
    executionHistory: [],
    
    // 实时监控
    monitoring: {
      enabled: false,
      interval: 10000,
      data: {}
    },
    
    // 调度器状态
    schedulerStatus: {
      isRunning: false,
      nextExecution: null,
      activeTasks: 0,
      queueSize: 0
    }
  }),
  
  getters: {
    // 过滤后的任务列表
    filteredTasks: (state) => {
      let tasks = [...state.tasks];
      
      // 状态过滤
      if (state.filters.status !== 'all') {
        tasks = tasks.filter(task => task.status === state.filters.status);
      }
      
      // 类型过滤
      if (state.filters.type !== 'all') {
        tasks = tasks.filter(task => task.type === state.filters.type);
      }
      
      // 搜索过滤
      if (state.filters.search) {
        const search = state.filters.search.toLowerCase();
        tasks = tasks.filter(task => 
          task.name.toLowerCase().includes(search) ||
          task.description.toLowerCase().includes(search) ||
          (task.tags && task.tags.some(tag => tag.toLowerCase().includes(search)))
        );
      }
      
      // 排序
      tasks.sort((a, b) => {
        const aValue = a[state.filters.sortBy];
        const bValue = b[state.filters.sortBy];
        
        if (state.filters.sortOrder === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });
      
      return tasks;
    },
    
    // 运行中的任务
    runningTasks: (state) => {
      return state.tasks.filter(task => task.status === 'running');
    },
    
    // 已调度的任务
    scheduledTasks: (state) => {
      return state.tasks.filter(task => task.status === 'scheduled');
    },
    
    // 获取任务by ID
    getTaskById: (state) => (id) => {
      return state.tasks.find(task => task.id === id);
    },
    
    // 获取模板by ID
    getTemplateById: (state) => (id) => {
      return state.templates.find(template => template.id === id);
    },
    
    // 是否有选中的任务
    hasSelectedTasks: (state) => {
      return state.selectedTasks.length > 0;
    },
    
    // 选中任务的状态统计
    selectedTasksStats: (state) => {
      const stats = { running: 0, scheduled: 0, paused: 0, completed: 0, failed: 0 };
      state.selectedTasks.forEach(id => {
        const task = state.tasks.find(t => t.id === id);
        if (task) {
          stats[task.status] = (stats[task.status] || 0) + 1;
        }
      });
      return stats;
    },
    
    // 下次执行时间最近的任务
    nextTask: (state) => {
      const scheduledTasks = state.tasks.filter(task => 
        task.status === 'scheduled' && task.next_run
      );
      
      if (scheduledTasks.length === 0) return null;
      
      return scheduledTasks.reduce((earliest, current) => {
        return new Date(current.next_run) < new Date(earliest.next_run) ? current : earliest;
      });
    },
    
    // 今日执行的任务数
    todayExecutions: (state) => {
      const today = new Date().toDateString();
      return state.executionHistory.filter(execution => 
        new Date(execution.start_time).toDateString() === today
      ).length;
    },
    
    // 成功率
    successRate: (state) => {
      const total = state.stats.completed + state.stats.failed;
      return total > 0 ? Math.round((state.stats.completed / total) * 100) : 0;
    }
  },
  
  actions: {
    // 加载任务列表
    async loadTasks() {
      try {
        this.loading.tasks = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/scheduler/tasks');
          this.tasks = response.tasks || [];
          this.updateStats();
        }
      } catch (error) {
        console.error('加载任务列表失败:', error);
        throw error;
      } finally {
        this.loading.tasks = false;
      }
    },
    
    // 加载任务模板
    async loadTemplates() {
      try {
        this.loading.templates = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/scheduler/templates');
          this.templates = response.templates || [];
        }
      } catch (error) {
        console.error('加载任务模板失败:', error);
        throw error;
      } finally {
        this.loading.templates = false;
      }
    },
    
    // 加载执行历史
    async loadExecutionHistory(options = {}) {
      try {
        if (window.httpAPI) {
          const params = new URLSearchParams(options).toString();
          const response = await window.httpAPI.get(`/api/scheduler/executions?${params}`);
          this.executionHistory = response.executions || [];
        }
      } catch (error) {
        console.error('加载执行历史失败:', error);
        throw error;
      }
    },
    
    // 获取调度器状态
    async getSchedulerStatus() {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get('/api/scheduler/status');
          this.schedulerStatus = response.status;
        }
      } catch (error) {
        console.error('获取调度器状态失败:', error);
        throw error;
      }
    },
    
    // 创建任务
    async createTask(taskData) {
      try {
        this.loading.creating = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post('/api/scheduler/tasks', taskData);
          const newTask = response.task;
          
          // 添加到列表
          this.tasks.unshift(newTask);
          this.updateStats();
          
          return newTask;
        }
      } catch (error) {
        console.error('创建任务失败:', error);
        throw error;
      } finally {
        this.loading.creating = false;
      }
    },
    
    // 更新任务
    async updateTask(taskId, updates) {
      try {
        this.loading.updating = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.put(`/api/scheduler/tasks/${taskId}`, updates);
          
          // 更新任务
          const task = this.getTaskById(taskId);
          if (task) {
            Object.assign(task, response.task);
            this.updateStats();
          }
          
          return response.task;
        }
      } catch (error) {
        console.error('更新任务失败:', error);
        throw error;
      } finally {
        this.loading.updating = false;
      }
    },
    
    // 删除任务
    async deleteTask(taskId) {
      try {
        if (window.httpAPI) {
          await window.httpAPI.delete(`/api/scheduler/tasks/${taskId}`);
          
          // 从列表中移除
          const index = this.tasks.findIndex(task => task.id === taskId);
          if (index > -1) {
            this.tasks.splice(index, 1);
            this.updateStats();
          }
          
          // 从选中列表中移除
          this.removeFromSelection(taskId);
        }
      } catch (error) {
        console.error('删除任务失败:', error);
        throw error;
      }
    },
    
    // 启动任务
    async startTask(taskId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/scheduler/tasks/${taskId}/start`);
          
          // 更新任务状态
          const task = this.getTaskById(taskId);
          if (task) {
            Object.assign(task, response.task);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('启动任务失败:', error);
        throw error;
      }
    },
    
    // 停止任务
    async stopTask(taskId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/scheduler/tasks/${taskId}/stop`);
          
          // 更新任务状态
          const task = this.getTaskById(taskId);
          if (task) {
            Object.assign(task, response.task);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('停止任务失败:', error);
        throw error;
      }
    },
    
    // 暂停任务
    async pauseTask(taskId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/scheduler/tasks/${taskId}/pause`);
          
          // 更新任务状态
          const task = this.getTaskById(taskId);
          if (task) {
            Object.assign(task, response.task);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('暂停任务失败:', error);
        throw error;
      }
    },
    
    // 恢复任务
    async resumeTask(taskId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/scheduler/tasks/${taskId}/resume`);
          
          // 更新任务状态
          const task = this.getTaskById(taskId);
          if (task) {
            Object.assign(task, response.task);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('恢复任务失败:', error);
        throw error;
      }
    },
    
    // 立即执行任务
    async executeTask(taskId) {
      try {
        this.loading.executing = true;
        
        if (window.httpAPI) {
          const response = await window.httpAPI.post(`/api/scheduler/tasks/${taskId}/execute`);
          
          // 更新任务状态
          const task = this.getTaskById(taskId);
          if (task) {
            Object.assign(task, response.task);
            this.updateStats();
          }
          
          return response;
        }
      } catch (error) {
        console.error('执行任务失败:', error);
        throw error;
      } finally {
        this.loading.executing = false;
      }
    },
    
    // 获取任务详情
    async getTaskDetails(taskId) {
      try {
        if (window.httpAPI) {
          const response = await window.httpAPI.get(`/api/scheduler/tasks/${taskId}`);
          return response.task;
        }
      } catch (error) {
        console.error('获取任务详情失败:', error);
        throw error;
      }
    },
    
    // 获取任务日志
    async getTaskLogs(taskId, options = {}) {
      try {
        if (window.httpAPI) {
          const params = new URLSearchParams(options).toString();
          const response = await window.httpAPI.get(`/api/scheduler/tasks/${taskId}/logs?${params}`);
          return response.logs;
        }
      } catch (error) {
        console.error('获取任务日志失败:', error);
        throw error;
      }
    },
    
    // 获取任务执行历史
    async getTaskExecutions(taskId, options = {}) {
      try {
        if (window.httpAPI) {
          const params = new URLSearchParams(options).toString();
          const response = await window.httpAPI.get(`/api/scheduler/tasks/${taskId}/executions?${params}`);
          return response.executions;
        }
      } catch (error) {
        console.error('获取任务执行历史失败:', error);
        throw error;
      }
    },
    
    // 批量启动任务
    async startSelectedTasks() {
      const promises = this.selectedTasks.map(id => this.startTask(id));
      await Promise.allSettled(promises);
    },
    
    // 批量停止任务
    async stopSelectedTasks() {
      const promises = this.selectedTasks.map(id => this.stopTask(id));
      await Promise.allSettled(promises);
    },
    
    // 批量暂停任务
    async pauseSelectedTasks() {
      const promises = this.selectedTasks.map(id => this.pauseTask(id));
      await Promise.allSettled(promises);
    },
    
    // 批量删除任务
    async deleteSelectedTasks() {
      const promises = this.selectedTasks.map(id => this.deleteTask(id));
      await Promise.allSettled(promises);
      this.selectedTasks = [];
    },
    
    // 更新统计信息
    updateStats() {
      this.stats = {
        total: this.tasks.length,
        running: this.tasks.filter(t => t.status === 'running').length,
        scheduled: this.tasks.filter(t => t.status === 'scheduled').length,
        paused: this.tasks.filter(t => t.status === 'paused').length,
        completed: this.tasks.filter(t => t.status === 'completed').length,
        failed: this.tasks.filter(t => t.status === 'failed').length
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
        type: 'all',
        search: '',
        sortBy: 'created_at',
        sortOrder: 'desc'
      };
    },
    
    // 选择任务
    selectTask(taskId) {
      if (!this.selectedTasks.includes(taskId)) {
        this.selectedTasks.push(taskId);
      }
    },
    
    // 取消选择任务
    deselectTask(taskId) {
      const index = this.selectedTasks.indexOf(taskId);
      if (index > -1) {
        this.selectedTasks.splice(index, 1);
      }
    },
    
    // 切换任务选择状态
    toggleTaskSelection(taskId) {
      if (this.selectedTasks.includes(taskId)) {
        this.deselectTask(taskId);
      } else {
        this.selectTask(taskId);
      }
    },
    
    // 全选/取消全选
    toggleSelectAll() {
      if (this.selectedTasks.length === this.filteredTasks.length) {
        this.selectedTasks = [];
      } else {
        this.selectedTasks = this.filteredTasks.map(task => task.id);
      }
    },
    
    // 从选择列表中移除
    removeFromSelection(taskId) {
      this.deselectTask(taskId);
    },
    
    // 清空选择
    clearSelection() {
      this.selectedTasks = [];
    },
    
    // 设置当前选中任务
    setSelectedTask(task) {
      this.selectedTask = task;
    },
    
    // 开始监控
    startMonitoring() {
      if (this.monitoring.enabled) return;
      
      this.monitoring.enabled = true;
      
      const monitor = async () => {
        if (!this.monitoring.enabled) return;
        
        try {
          // 更新调度器状态
          await this.getSchedulerStatus();
          
          // 更新运行中任务的状态
          const runningIds = this.runningTasks.map(t => t.id);
          if (runningIds.length > 0) {
            const response = await window.httpAPI.post('/api/scheduler/tasks/status', {
              task_ids: runningIds
            });
            
            // 更新任务状态
            response.tasks.forEach(updatedTask => {
              const task = this.getTaskById(updatedTask.id);
              if (task) {
                Object.assign(task, updatedTask);
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
    
    // 刷新任务状态
    async refreshTaskStatus(taskId) {
      try {
        const response = await window.httpAPI.get(`/api/scheduler/tasks/${taskId}/status`);
        const task = this.getTaskById(taskId);
        if (task) {
          Object.assign(task, response.task);
          this.updateStats();
        }
      } catch (error) {
        console.error('刷新任务状态失败:', error);
        throw error;
      }
    },
    
    // 导出任务配置
    async exportTaskConfig(taskId) {
      try {
        const response = await window.httpAPI.get(`/api/scheduler/tasks/${taskId}/export`);
        return response.config;
      } catch (error) {
        console.error('导出任务配置失败:', error);
        throw error;
      }
    },
    
    // 导入任务配置
    async importTaskConfig(config) {
      try {
        const response = await window.httpAPI.post('/api/scheduler/tasks/import', config);
        
        // 添加导入的任务
        if (response.tasks) {
          this.tasks.unshift(...response.tasks);
          this.updateStats();
        }
        
        return response;
      } catch (error) {
        console.error('导入任务配置失败:', error);
        throw error;
      }
    },
    
    // 清理完成的任务
    async cleanupCompletedTasks(olderThanDays = 30) {
      try {
        const response = await window.httpAPI.delete('/api/scheduler/tasks/cleanup', {
          older_than_days: olderThanDays
        });
        
        // 重新加载任务列表
        await this.loadTasks();
        
        return response;
      } catch (error) {
        console.error('清理完成任务失败:', error);
        throw error;
      }
    }
  }
});