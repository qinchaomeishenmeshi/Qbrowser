<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1 class="dashboard-title">仪表盘</h1>
      <div class="dashboard-actions">
        <button @click="refreshData" class="btn btn-primary" :disabled="isLoading">
          <span v-if="isLoading" class="loading"></span>
          <span v-else>🔄</span>
          刷新数据
        </button>
      </div>
    </div>

    <div class="dashboard-content">
      <!-- 系统状态卡片 -->
      <div class="grid grid-4">
        <div class="card status-card">
          <div class="card-body">
            <div class="status-icon backend" :class="{ online: systemStatus.backend }">
              🖥️
            </div>
            <div class="status-info">
              <h3>后端服务</h3>
              <p :class="systemStatus.backend ? 'text-success' : 'text-danger'">
                {{ systemStatus.backend ? '运行中' : '已停止' }}
              </p>
            </div>
          </div>
        </div>

        <div class="card status-card">
          <div class="card-body">
            <div class="status-icon browser" :class="{ online: systemStatus.browser }">
              🌐
            </div>
            <div class="status-info">
              <h3>浏览器实例</h3>
              <p class="text-info">{{ browserStats.active }}/{{ browserStats.total }} 活跃</p>
            </div>
          </div>
        </div>

        <div class="card status-card">
          <div class="card-body">
            <div class="status-icon tasks" :class="{ online: taskStats.running > 0 }">
              ⏰
            </div>
            <div class="status-info">
              <h3>定时任务</h3>
              <p class="text-info">{{ taskStats.running }} 个运行中</p>
            </div>
          </div>
        </div>

        <div class="card status-card">
          <div class="card-body">
            <div class="status-icon extensions" :class="{ online: extensionStats.enabled > 0 }">
              🧩
            </div>
            <div class="status-info">
              <h3>扩展插件</h3>
              <p class="text-info">{{ extensionStats.enabled }}/{{ extensionStats.total }} 启用</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 快速操作 -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">快速操作</h2>
        </div>
        <div class="card-body">
          <div class="quick-actions">
            <button @click="startBrowser" class="action-btn" :disabled="!systemStatus.backend">
              <div class="action-icon">🚀</div>
              <div class="action-text">
                <h4>启动浏览器</h4>
                <p>创建新的浏览器实例</p>
              </div>
            </button>

            <button @click="openScheduler" class="action-btn">
              <div class="action-icon">📅</div>
              <div class="action-text">
                <h4>管理任务</h4>
                <p>配置和监控定时任务</p>
              </div>
            </button>

            <button @click="viewLogs" class="action-btn">
              <div class="action-icon">📋</div>
              <div class="action-text">
                <h4>查看日志</h4>
                <p>检查系统运行日志</p>
              </div>
            </button>

            <button @click="openSettings" class="action-btn">
              <div class="action-icon">⚙️</div>
              <div class="action-text">
                <h4>系统设置</h4>
                <p>配置应用参数</p>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- 最近活动 -->
      <div class="grid grid-2">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title">最近任务</h2>
          </div>
          <div class="card-body">
            <div v-if="recentTasks.length === 0" class="empty-state">
              <p>暂无最近任务</p>
            </div>
            <div v-else class="task-list">
              <div v-for="task in recentTasks" :key="task.id" class="task-item">
                <div class="task-info">
                  <h4>{{ task.name }}</h4>
                  <p class="task-time">{{ formatTime(task.lastRun) }}</p>
                </div>
                <div class="task-status" :class="task.status">
                  {{ getStatusText(task.status) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title">系统日志</h2>
          </div>
          <div class="card-body">
            <div v-if="systemLogs.length === 0" class="empty-state">
              <p>暂无系统日志</p>
            </div>
            <div v-else class="log-list">
              <div v-for="log in systemLogs" :key="log.id" class="log-item" :class="log.level">
                <div class="log-time">{{ formatTime(log.timestamp) }}</div>
                <div class="log-message">{{ log.message }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'Dashboard',
  setup() {
    const router = useRouter();
    const isLoading = ref(false);
    
    // 系统状态
    const systemStatus = reactive({
      backend: false,
      browser: false
    });
    
    // 统计数据
    const browserStats = reactive({
      active: 0,
      total: 0
    });
    
    const taskStats = reactive({
      running: 0,
      total: 0
    });
    
    const extensionStats = reactive({
      enabled: 0,
      total: 0
    });
    
    // 最近任务和日志
    const recentTasks = ref([]);
    const systemLogs = ref([]);
    
    let refreshInterval = null;
    
    // 获取系统状态
    const getSystemStatus = async () => {
      try {
        if (window.electronAPI) {
          const status = await window.electronAPI.getBackendStatus();
          systemStatus.backend = status.isRunning;
        }
        
        if (systemStatus.backend && window.httpAPI) {
          // 获取浏览器状态
          try {
            const browserData = await window.httpAPI.get('/api/browser/status');
            browserStats.active = browserData.active || 0;
            browserStats.total = browserData.total || 0;
            systemStatus.browser = browserStats.total > 0;
          } catch (error) {
            console.warn('获取浏览器状态失败:', error);
          }
          
          // 获取任务状态
          try {
            const taskData = await window.httpAPI.get('/api/scheduler/status');
            taskStats.running = taskData.running || 0;
            taskStats.total = taskData.total || 0;
          } catch (error) {
            console.warn('获取任务状态失败:', error);
          }
          
          // 获取扩展状态
          try {
            const extensionData = await window.httpAPI.get('/api/extensions/status');
            extensionStats.enabled = extensionData.enabled || 0;
            extensionStats.total = extensionData.total || 0;
          } catch (error) {
            console.warn('获取扩展状态失败:', error);
          }
        }
      } catch (error) {
        console.error('获取系统状态失败:', error);
      }
    };
    
    // 获取最近任务
    const getRecentTasks = async () => {
      try {
        if (systemStatus.backend && window.httpAPI) {
          const data = await window.httpAPI.get('/api/scheduler/recent');
          recentTasks.value = data.tasks || [];
        }
      } catch (error) {
        console.warn('获取最近任务失败:', error);
        recentTasks.value = [];
      }
    };
    
    // 获取系统日志
    const getSystemLogs = async () => {
      try {
        if (systemStatus.backend && window.httpAPI) {
          const data = await window.httpAPI.get('/api/system/logs?limit=10');
          systemLogs.value = data.logs || [];
        }
      } catch (error) {
        console.warn('获取系统日志失败:', error);
        systemLogs.value = [];
      }
    };
    
    // 刷新所有数据
    const refreshData = async () => {
      isLoading.value = true;
      try {
        await Promise.all([
          getSystemStatus(),
          getRecentTasks(),
          getSystemLogs()
        ]);
      } finally {
        isLoading.value = false;
      }
    };
    
    // 快速操作
    const startBrowser = async () => {
      try {
        if (window.httpAPI) {
          await window.httpAPI.post('/api/browser/start');
          await getSystemStatus();
        }
      } catch (error) {
        console.error('启动浏览器失败:', error);
      }
    };
    
    const openScheduler = () => {
      router.push('/scheduler');
    };
    
    const viewLogs = () => {
      // 可以打开日志查看器或跳转到日志页面
      console.log('查看日志');
    };
    
    const openSettings = () => {
      router.push('/settings');
    };
    
    // 工具函数
    const formatTime = (timestamp) => {
      if (!timestamp) return '-';
      const date = new Date(timestamp);
      return date.toLocaleString('zh-CN');
    };
    
    const getStatusText = (status) => {
      const statusMap = {
        'success': '成功',
        'running': '运行中',
        'failed': '失败',
        'pending': '等待中'
      };
      return statusMap[status] || status;
    };
    
    // 生命周期
    onMounted(async () => {
      await refreshData();
      
      // 设置定时刷新
      refreshInterval = setInterval(refreshData, 30000); // 每30秒刷新一次
    });
    
    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    });
    
    return {
      isLoading,
      systemStatus,
      browserStats,
      taskStats,
      extensionStats,
      recentTasks,
      systemLogs,
      refreshData,
      startBrowser,
      openScheduler,
      viewLogs,
      openSettings,
      formatTime,
      getStatusText
    };
  }
};
</script>

<style scoped>
.dashboard {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dashboard-title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 状态卡片 */
.status-card .card-body {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: #f5f5f5;
  transition: all 0.3s ease;
}

.status-icon.online {
  background: linear-gradient(135deg, #4caf50, #45a049);
  color: white;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.status-info h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #333;
}

.status-info p {
  font-size: 14px;
  margin: 0;
  font-weight: 500;
}

.text-success { color: #4caf50; }
.text-danger { color: #f44336; }
.text-info { color: #2196f3; }

/* 快速操作 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.action-btn:hover:not(:disabled) {
  border-color: #1976d2;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(25, 118, 210, 0.15);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.action-text h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #333;
}

.action-text p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

/* 任务和日志列表 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.task-list,
.log-list {
  max-height: 300px;
  overflow-y: auto;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.task-item:last-child {
  border-bottom: none;
}

.task-info h4 {
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 4px 0;
  color: #333;
}

.task-time {
  font-size: 12px;
  color: #666;
  margin: 0;
}

.task-status {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.task-status.success {
  background: #e8f5e8;
  color: #2e7d32;
}

.task-status.running {
  background: #e3f2fd;
  color: #1976d2;
}

.task-status.failed {
  background: #ffebee;
  color: #c62828;
}

.task-status.pending {
  background: #fff3e0;
  color: #ef6c00;
}

.log-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.log-message {
  font-size: 14px;
  color: #333;
}

.log-item.error .log-message {
  color: #f44336;
}

.log-item.warning .log-message {
  color: #ff9800;
}

.log-item.info .log-message {
  color: #2196f3;
}
</style>