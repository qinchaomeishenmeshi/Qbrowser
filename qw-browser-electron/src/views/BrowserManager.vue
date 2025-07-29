<template>
  <div class="browser-manager">
    <div class="page-header">
      <div class="page-actions">
        <button @click="createBrowser" class="btn btn-primary">
          <span>[+]</span>
          创建浏览器实例
        </button>
        <button @click="refreshBrowsers" class="btn btn-secondary" :disabled="isLoading">
          <span v-if="isLoading" class="loading"></span>
          <span v-else>[REFRESH]</span>
          刷新
        </button>
      </div>
    </div>

    <div class="browser-content">
      <!-- 浏览器实例列表 -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">浏览器实例</h2>
          <div class="browser-stats">
            <span class="stat-item">
              <span class="stat-label">总数:</span>
              <span class="stat-value">{{ browsers.length }}</span>
            </span>
            <span class="stat-item">
              <span class="stat-label">运行中:</span>
              <span class="stat-value text-success">{{ activeBrowsers }}</span>
            </span>
          </div>
        </div>
        <div class="card-body">
          <div v-if="browsers.length === 0" class="empty-state">
            <div class="empty-icon">[BROWSER]</div>
            <h3>暂无浏览器实例</h3>
            <p>点击上方按钮创建第一个浏览器实例</p>
          </div>
          <div v-else class="browser-table-container">
            <table class="browser-table">
              <thead>
                <tr>
                  <th>用户ID</th>
                  <th>状态</th>
                  <th>端口</th>
                  <th>创建时间</th>
                  <th>最后活动</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="browser in browsers" :key="browser.user_id" :class="{ 'active-row': browser.status === 'running' }">
                  <td class="browser-id">
                    <div class="id-cell">
                      <span class="id-text">{{ browser.user_id || 'undefined' }}</span>
                    </div>
                  </td>
                  <td class="browser-status">
                    <div class="status-badge" :class="browser.status">
                      <span class="status-dot"></span>
                      {{ getStatusText(browser.status) }}
                    </div>
                  </td>
                  <td class="browser-port">
                    <span class="port-text">{{ browser.port || '-' }}</span>
                  </td>
                  <td class="browser-created">
                    <span class="time-text">{{ formatTime(browser.createdAt) }}</span>
                  </td>
                  <td class="browser-activity">
                    <span class="time-text">{{ formatTime(browser.lastActivity) }}</span>
                  </td>
                  <td class="browser-actions">
                    <div class="action-buttons">
                      <button
                              v-if="browser.status !== 'running'"
                              @click="startBrowser(browser.user_id)"
                              class="btn btn-small btn-success"
                              :disabled="isOperating"
                              title="启动浏览器">
                        [PLAY]
                      </button>
                      <button
                              v-if="browser.status === 'running'"
                              @click="stopBrowser(browser.user_id)"
                              class="btn btn-small btn-warning"
                              :disabled="isOperating"
                              title="停止浏览器">
                        [PAUSE]
                      </button>
                      <button
                              @click="deleteBrowser(browser.user_id)"
                              class="btn btn-small btn-danger"
                              :disabled="isOperating"
                              title="删除浏览器">
                        [DELETE]
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>


    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue';

export default {
  name: 'BrowserManager',
  setup() {
    const isLoading = ref(false);
    const isOperating = ref(false);
    const browsers = ref([]);
    const isSaving = ref(false);

    // 计算属性
    const activeBrowsers = computed(() => {
      return browsers.value.filter(b => b.status === 'running').length;
    });

    // 获取浏览器列表
    const getBrowsers = async () => {
      try {
        if (window.httpAPI) {
          const data = await window.httpAPI.get('/api/active_instances');
          // 将active_instances转换为browsers格式
          if (data.active_instances && Array.isArray(data.active_instances)) {
            browsers.value = data.active_instances.map((userId, index) => ({
              user_id: userId,
              status: 'running',
              port: 9222 + index, // 模拟端口信息
              createdAt: new Date(Date.now() - Math.random() * 86400000).toISOString(), // 模拟创建时间
              lastActivity: new Date().toISOString() // 当前时间作为最后活动时间
            }));
          } else {
            browsers.value = [];
          }
        }
      } catch (error) {
        console.error('获取浏览器列表失败:', error);
        browsers.value = [];
      }
    };

    // 刷新浏览器列表
    const refreshBrowsers = async () => {
      isLoading.value = true;
      try {
        await getBrowsers();
      } finally {
        isLoading.value = false;
      }
    };

    // 创建浏览器 - 使用现有的start接口
    const createBrowser = async () => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          // 使用测试用户ID启动接口
          const userId = prompt('请输入用户ID', 'test001');
          if (userId) {
            await window.httpAPI.post(`/api/start/${userId}`);
            await getBrowsers();
          }
        }
      } catch (error) {
        console.error('创建浏览器失败:', error);
      } finally {
        isOperating.value = false;
      }
    };

    // 启动浏览器 - 使用现有的start接口
    const startBrowser = async (browserId) => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post(`/api/start/${browserId}`);
          await getBrowsers();
        }
      } catch (error) {
        console.error('启动浏览器失败:', error);
      } finally {
        isOperating.value = false;
      }
    };

    // 停止浏览器 - 目前只支持停止所有浏览器
    const stopBrowser = async (browserId) => {
      if (!confirm('当前只支持停止所有浏览器，确定要继续吗？')) return;
      
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post('/api/stop');
          await getBrowsers();
        }
      } catch (error) {
        console.error('停止浏览器失败:', error);
      } finally {
        isOperating.value = false;
      }
    };

    // 删除浏览器 - 目前只支持停止所有浏览器
    const deleteBrowser = async (browserId) => {
      if (!confirm('当前只支持停止所有浏览器，确定要继续吗？')) return;

      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post('/api/stop');
          await getBrowsers();
        }
      } catch (error) {
        console.error('删除浏览器失败:', error);
      } finally {
        isOperating.value = false;
      }
    };



    // 工具函数
    const getStatusText = (status) => {
      const statusMap = {
        'running': '运行中',
        'stopped': '已停止',
        'starting': '启动中',
        'stopping': '停止中',
        'error': '错误'
      };
      return statusMap[status] || status;
    };

    const formatTime = (timestamp) => {
      if (!timestamp) return '-';
      const date = new Date(timestamp);
      return date.toLocaleString('zh-CN');
    };

    // 生命周期
    onMounted(() => {
      refreshBrowsers();
    });

    return {
      isLoading,
      isOperating,
      browsers,
      activeBrowsers,
      isSaving,
      refreshBrowsers,
      createBrowser,
      startBrowser,
      stopBrowser,
      deleteBrowser,
      getStatusText,
      formatTime
    };
  }
};
</script>

<style scoped>
.browser-manager {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}



.page-actions {
  display: flex;
  gap: 12px;
}

.browser-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.browser-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 8px;
}

.empty-state p {
  color: #666;
}

/* 表格容器 */
.browser-table-container {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

/* 表格样式 */
.browser-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.browser-table th {
  background: #f5f5f5;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e0e0e0;
  font-size: 14px;
}

.browser-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
}

.browser-table tbody tr:hover {
  background: #f9f9f9;
}

.browser-table tbody tr.active-row {
  background: #f0f8f0;
}

.browser-table tbody tr.active-row:hover {
  background: #e8f5e8;
}

/* 用户ID列 */
.browser-id .id-cell {
  display: flex;
  align-items: center;
}

.browser-id .id-text {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
}

/* 状态列 */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  min-width: 80px;
  justify-content: center;
}

.status-badge.running {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-badge.stopped {
  background: #ffebee;
  color: #c62828;
}

.status-badge.starting,
.status-badge.stopping {
  background: #fff3e0;
  color: #ef6c00;
}

.status-badge.error {
  background: #ffebee;
  color: #d32f2f;
}

/* 操作按钮组 */
.browser-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 60px;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-btn:active {
  transform: translateY(0);
}

.action-btn.start {
  background: #4caf50;
  color: white;
}

.action-btn.start:hover {
  background: #45a049;
}

.action-btn.stop {
  background: #ff9800;
  color: white;
}

.action-btn.stop:hover {
  background: #f57c00;
}

.action-btn.delete {
  background: #f44336;
  color: white;
}

.action-btn.delete:hover {
  background: #d32f2f;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.action-btn:disabled:hover {
  transform: none;
  box-shadow: none;
}

/* 端口信息 */
.port-info {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: #666;
  background: #f8f8f8;
  padding: 2px 6px;
  border-radius: 3px;
}

/* 时间信息 */
.time-info {
  font-size: 12px;
  color: #888;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .browser-table-container {
    font-size: 12px;
  }
  
  .browser-table th,
  .browser-table td {
    padding: 8px 12px;
  }
  
  .action-btn {
    padding: 4px 8px;
    font-size: 11px;
    min-width: 50px;
  }
}


</style>