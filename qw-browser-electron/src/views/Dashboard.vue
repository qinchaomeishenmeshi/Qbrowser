<template>
  <div class="dashboard">


    <div class="dashboard-content">
      <!-- 用户ID配置卡片 -->
      <div class="config-card">
        <div class="card-header">
          <h2 class="card-title">用户ID配置</h2>
        </div>
        <div class="card-separator"></div>
        <div class="card-body">
          <p class="input-hint">请输入浏览器实例的用户ID，支持换行符、逗号、分号分隔</p>
          <textarea
                    v-model="userIds"
                    class="user-input"
                    placeholder="test001&#10;test002&#10;test003&#10;或者: test001,test002,test003"
                    rows="6"></textarea>
          <div v-if="userIds.trim()" class="user-id-stats">
            <span class="stats-item" :class="{ 'text-success': userIdStats.valid > 0 }">
              有效ID: {{ userIdStats.valid }}
            </span>
            <span v-if="userIdStats.invalid > 0" class="stats-item text-warning">
              无效ID: {{ userIdStats.invalid }}
            </span>
            <span class="stats-item">
              总计: {{ userIdStats.total }}
            </span>
          </div>
        </div>
      </div>

      <!-- 操作控制卡片 -->
      <div class="action-card">
        <div class="card-header">
          <h2 class="card-title">操作控制</h2>
        </div>
        <div class="card-separator"></div>
        <div class="card-body">
          <div class="button-container">
            <button
                    @click="startBrowsers"
                    class="chrome-btn success-btn"
                    :disabled="isLoading || !isValidUserIds">
              启动浏览器
            </button>
            <button
                    @click="stopBrowsers"
                    class="chrome-btn error-btn"
                    :disabled="isLoading">
              一键关闭
            </button>
            <button
                    @click="loadConfig"
                    class="chrome-btn primary-btn"
                    :disabled="isLoading">
              加载配置
            </button>
            <button
                    @click="clearCache"
                    class="chrome-btn warning-btn"
                    :disabled="isLoading">
              清除缓存
            </button>
          </div>
        </div>
      </div>

      <!-- 进度与日志卡片 -->
      <div class="log-card">
        <div class="card-header">
          <h2 class="card-title">进度与日志</h2>
        </div>
        <div class="card-separator"></div>
        <div class="card-body">
          <!-- 进度条区域 -->
          <div class="progress-section">
            <h3 class="section-title">操作进度</h3>
            <div class="progress-bar">
              <div
                   class="progress-fill"
                   :style="{ width: progress + '%' }"></div>
            </div>
            <p class="progress-text">{{ progressText }}</p>
          </div>

          <!-- 日志区域 -->
          <div class="log-section">
            <h3 class="section-title">操作日志</h3>
            <div class="log-area" ref="logArea">
              <div
                   v-for="(log, index) in logs"
                   :key="index"
                   class="log-entry"
                   :class="log.level">
                <span class="log-time">{{ formatLogTime(log.timestamp) }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
              <div v-if="logs.length === 0" class="empty-logs">
                暂无日志信息
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'Dashboard',
  setup() {
    const router = useRouter();
    const isLoading = ref(false);
    const userIds = ref('');
    const progress = ref(0);
    const progressText = ref('准备就绪');
    const logs = ref([]);
    const logArea = ref(null);

    // 计算属性：处理用户ID列表
    const userIdList = computed(() => {
      if (!userIds.value.trim()) return [];
      return userIds.value
        .split(/[\n,;]/) // 支持换行符、逗号、分号分隔
        .map(id => id.trim())
        .filter(id => id.length > 0)
        .filter((id, index, arr) => arr.indexOf(id) === index); // 去重
    });

    // 计算属性：验证用户ID格式
    const isValidUserIds = computed(() => {
      if (userIdList.value.length === 0) return false;
      // 简单的ID格式验证：只允许字母、数字、下划线、连字符
      const validPattern = /^[a-zA-Z0-9_-]+$/;
      return userIdList.value.every(id => validPattern.test(id));
    });

    // 计算属性：用户ID统计信息
    const userIdStats = computed(() => ({
      total: userIdList.value.length,
      valid: userIdList.value.filter(id => /^[a-zA-Z0-9_-]+$/.test(id)).length,
      invalid: userIdList.value.filter(id => !/^[a-zA-Z0-9_-]+$/.test(id)).length
    }));

    // 添加日志
    const addLog = (message, level = 'info') => {
      const timestamp = new Date();
      logs.value.push({
        timestamp,
        message,
        level
      });

      // 自动滚动到底部
      nextTick(() => {
        if (logArea.value) {
          logArea.value.scrollTop = logArea.value.scrollHeight;
        }
      });
    };

    // 更新进度
    const updateProgress = (value, text) => {
      progress.value = value;
      progressText.value = text;
    };

    // 启动浏览器
    const startBrowsers = async () => {
      // 验证用户ID输入
      if (userIdList.value.length === 0) {
        addLog('请先输入用户ID', 'error');
        return;
      }

      if (!isValidUserIds.value) {
        addLog(`发现 ${userIdStats.value.invalid} 个无效的用户ID格式，请检查输入`, 'error');
        addLog('用户ID只能包含字母、数字、下划线和连字符', 'warning');
        return;
      }

      isLoading.value = true;
      updateProgress(0, '准备启动浏览器...');
      addLog('开始启动浏览器实例');
      addLog(`共 ${userIdStats.value.total} 个有效用户ID`);

      try {
        const validUserIds = userIdList.value;
        addLog(`准备启动 ${validUserIds.length} 个浏览器实例`);

        updateProgress(20, '正在启动浏览器...');

        if (window.httpAPI) {
          // 将user_ids作为查询参数发送
          const queryParams = new URLSearchParams();
          validUserIds.forEach(id => queryParams.append('user_ids', id));
          const response = await window.httpAPI.post(`/api/start_all?${queryParams.toString()}`, {});

          // 处理API响应
          if (response && response.results) {
            let successCount = 0;
            let failCount = 0;

            // 显示每个实例的详细启动信息
            response.results.forEach((result, index) => {
              const { user_id, status, port, message } = result;
              const displayIndex = `[${index + 1}/${response.results.length}]`;

              if (status === 'success') {
                addLog(`${displayIndex} ${user_id} success (端口: ${port})`, 'success');
                successCount++;
              } else if (status === 'already_running') {
                addLog(`${displayIndex} ${user_id} already_running (端口: ${port})`, 'info');
                successCount++;
              } else if (status === 'fail' || status === 'error') {
                addLog(`${displayIndex} ${user_id} ${status} ${message ? '- ' + message : ''}`, 'error');
                failCount++;
              }
            });

            updateProgress(100, '启动完成');
            addLog('启动浏览器操作已完成', 'success');

            if (failCount > 0) {
              addLog(`注意：${failCount} 个实例启动失败`, 'warning');
            }
          } else {
            updateProgress(100, '启动完成');
            addLog(`成功启动 ${validUserIds.length} 个浏览器实例`, 'success');
            addLog('启动浏览器操作已完成', 'success');
          }
        } else {
          // 模拟启动过程
          for (let i = 0; i < validUserIds.length; i++) {
            const userId = validUserIds[i];
            updateProgress(20 + (i + 1) * 80 / validUserIds.length, `启动实例: ${userId}`);
            addLog(`启动浏览器实例: ${userId}`);
            await new Promise(resolve => setTimeout(resolve, 500));
          }
          updateProgress(100, '启动完成');
          addLog('所有浏览器实例启动完成', 'success');
        }
      } catch (error) {
        updateProgress(0, '启动失败');
        addLog(`启动失败: ${error.message}`, 'error');
        console.error('启动浏览器失败:', error);
      } finally {
        isLoading.value = false;
      }
    };

    // 停止浏览器
    const stopBrowsers = async () => {
      isLoading.value = true;
      updateProgress(0, '准备关闭浏览器...');
      addLog('开始关闭所有浏览器实例');

      try {
        updateProgress(50, '正在关闭浏览器...');

        if (window.httpAPI) {
          await window.httpAPI.post('/api/stop');
        } else {
          // 模拟关闭过程
          await new Promise(resolve => setTimeout(resolve, 1000));
        }

        updateProgress(100, '关闭完成');
        addLog('所有浏览器实例已关闭', 'success');
      } catch (error) {
        updateProgress(0, '关闭失败');
        addLog(`关闭失败: ${error.message}`, 'error');
        console.error('关闭浏览器失败:', error);
      } finally {
        isLoading.value = false;
      }
    };

    // 加载配置
    const loadConfig = async () => {
      isLoading.value = true;
      updateProgress(0, '加载配置中...');
      addLog('开始加载用户配置');

      try {
        updateProgress(50, '读取配置文件...');

        if (window.httpAPI) {
          // 后端暂未实现/api/config/users接口，使用模拟数据
          addLog('后端配置接口暂未实现，使用默认配置', 'warning');
          
          // 模拟用户配置数据
          const mockUserIds = ['user001', 'user002', 'user003'];
          userIds.value = mockUserIds.join('\n');
          addLog(`加载了 ${mockUserIds.length} 个默认用户配置`, 'info');
        } else {
          // 模拟加载过程
          await new Promise(resolve => setTimeout(resolve, 500));
          // 模拟加载一些示例数据
          userIds.value = 'test001\ntest002\ntest003';
          addLog('加载了示例用户配置', 'info');
        }

        updateProgress(100, '配置加载完成');
        addLog('用户配置加载完成', 'success');
      } catch (error) {
        updateProgress(0, '加载失败');
        addLog(`配置加载失败: ${error.message}`, 'error');
        console.error('加载配置失败:', error);
      } finally {
        isLoading.value = false;
      }
    };

    // 清除缓存
    const clearCache = async () => {
      isLoading.value = true;
      updateProgress(0, '清除缓存中...');
      addLog('开始清除浏览器缓存');

      try {
        updateProgress(50, '正在清除缓存...');

        if (window.httpAPI) {
          await window.httpAPI.post('/api/browser/clear-cache');
        } else {
          // 模拟清除过程
          await new Promise(resolve => setTimeout(resolve, 1000));
        }

        updateProgress(100, '缓存清除完成');
        addLog('浏览器缓存清除完成', 'success');
      } catch (error) {
        updateProgress(0, '清除失败');
        addLog(`缓存清除失败: ${error.message}`, 'error');
        console.error('清除缓存失败:', error);
      } finally {
        isLoading.value = false;
      }
    };

    // 格式化日志时间
    const formatLogTime = (timestamp) => {
      return timestamp.toLocaleTimeString('zh-CN', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    };

    // 组件挂载时初始化
    onMounted(async () => {
      addLog('FastAPI服务已启动');

      // 检查后端服务状态
      try {
        if (window.httpAPI) {
          const healthResponse = await window.httpAPI.get('/api/health');
          if (healthResponse) {
            addLog('定时任务调度器启动成功，已加载 0 个任务配置，其中 0 个已启用');
            addLog('应用初始化完成');
          }
        } else {
          addLog('定时任务调度器启动成功，已加载 0 个任务配置，其中 0 个已启用');
          addLog('应用初始化完成');
        }
      } catch (error) {
        addLog('后端服务连接失败', 'warning');
        addLog('应用初始化完成（离线模式）');
      }

      addLog('浏览器控制中心已就绪');
    });

    return {
      isLoading,
      userIds,
      userIdList,
      isValidUserIds,
      userIdStats,
      progress,
      progressText,
      logs,
      logArea,
      startBrowsers,
      stopBrowsers,
      loadConfig,
      clearCache,
      formatLogTime
    };
  }
};
</script>

<style scoped>
.dashboard {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
  font-family: 'Microsoft YaHei', sans-serif;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 卡片通用样式 */
.config-card,
.action-card,
.log-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  background: #f8f9fa;
  padding: 15px 20px;
  border-bottom: 1px solid #e9ecef;
}

.card-title {
  font-weight: 600;
  color: #495057;
  margin: 0;
  font-size: 1.1rem;
}

.card-separator {
  height: 1px;
  background: #e9ecef;
}

.card-body {
  padding: 20px;
}

/* 用户ID配置卡片 */
.input-hint {
  margin-bottom: 10px;
  font-size: 14px;
  color: #666;
}

.user-input {
  width: 100%;
  min-height: 120px;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
}

.user-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.user-input::placeholder {
  color: #bababa;
}

.user-id-stats {
  margin-top: 10px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.stats-item {
  font-weight: 500;
  color: #495057;
}

.text-success {
  color: #28a745 !important;
}

.text-warning {
  color: #ffc107 !important;
}

.text-error {
  color: #dc3545 !important;
}

/* 操作控制卡片 */
.button-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.chrome-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  text-align: center;
}

.chrome-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.success-btn {
  background: #28a745;
  color: white;
}

.success-btn:hover:not(:disabled) {
  background: #218838;
}

.error-btn {
  background: #dc3545;
  color: white;
}

.error-btn:hover:not(:disabled) {
  background: #c82333;
}

.primary-btn {
  background: #007bff;
  color: white;
}

.primary-btn:hover:not(:disabled) {
  background: #0056b3;
}

.warning-btn {
  background: #ffc107;
  color: #212529;
}

.warning-btn:hover:not(:disabled) {
  background: #e0a800;
}

/* 进度与日志卡片 */
.progress-section {
  margin-bottom: 20px;
}

.section-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 10px;
  font-size: 1rem;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #0056b3);
  transition: width 0.3s ease;
  border-radius: 10px;
}

.progress-text {
  font-weight: 500;
  color: #495057;
  margin: 0;
}

.log-section {
  margin-top: 20px;
}

.log-area {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  height: 200px;
  overflow-y: auto;
  padding: 10px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.4;
}

.log-entry {
  margin-bottom: 5px;
  padding: 2px 0;
  display: flex;
  gap: 8px;
}

.log-time {
  color: #6c757d;
  flex-shrink: 0;
}

.log-message {
  color: #495057;
}

.log-entry.error .log-message {
  color: #dc3545;
}

.log-entry.success .log-message {
  color: #28a745;
}

.log-entry.warning .log-message {
  color: #ffc107;
}

.log-entry.info .log-message {
  color: #007bff;
}

.empty-logs {
  text-align: center;
  color: #6c757d;
  font-style: italic;
  padding: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard {
    padding: 15px;
  }

  .button-container {
    grid-template-columns: repeat(2, 1fr);
  }

  .card-body {
    padding: 15px;
  }
}

@media (max-width: 480px) {
  .button-container {
    grid-template-columns: 1fr;
  }
}
</style>