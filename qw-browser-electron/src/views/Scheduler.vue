<template>
  <div class="scheduler">
    <div class="page-header">
      <h1 class="page-title">定时任务</h1>
      <div class="page-actions">
        <button @click="createTask" class="btn btn-primary">
          <span>➕</span>
          创建任务
        </button>
        <button @click="refreshTasks" class="btn btn-secondary" :disabled="isLoading">
          <span v-if="isLoading" class="loading"></span>
          <span v-else>🔄</span>
          刷新
        </button>
      </div>
    </div>

    <div class="scheduler-content">
      <!-- 任务统计 -->
      <div class="grid grid-4">
        <div class="card stat-card">
          <div class="card-body">
            <div class="stat-icon total">📋</div>
            <div class="stat-info">
              <h3>总任务数</h3>
              <p class="stat-number">{{ tasks.length }}</p>
            </div>
          </div>
        </div>
        
        <div class="card stat-card">
          <div class="card-body">
            <div class="stat-icon running">▶️</div>
            <div class="stat-info">
              <h3>运行中</h3>
              <p class="stat-number text-success">{{ runningTasks }}</p>
            </div>
          </div>
        </div>
        
        <div class="card stat-card">
          <div class="card-body">
            <div class="stat-icon scheduled">⏰</div>
            <div class="stat-info">
              <h3>已调度</h3>
              <p class="stat-number text-info">{{ scheduledTasks }}</p>
            </div>
          </div>
        </div>
        
        <div class="card stat-card">
          <div class="card-body">
            <div class="stat-icon failed">❌</div>
            <div class="stat-info">
              <h3>失败</h3>
              <p class="stat-number text-danger">{{ failedTasks }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 任务列表 -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">任务列表</h2>
          <div class="task-filters">
            <select v-model="statusFilter" class="form-select">
              <option value="">全部状态</option>
              <option value="running">运行中</option>
              <option value="scheduled">已调度</option>
              <option value="stopped">已停止</option>
              <option value="failed">失败</option>
            </select>
          </div>
        </div>
        <div class="card-body">
          <div v-if="filteredTasks.length === 0" class="empty-state">
            <div class="empty-icon">📋</div>
            <h3>暂无任务</h3>
            <p>点击上方按钮创建第一个定时任务</p>
          </div>
          <div v-else class="task-table">
            <table class="table">
              <thead>
                <tr>
                  <th>任务名称</th>
                  <th>类型</th>
                  <th>状态</th>
                  <th>调度规则</th>
                  <th>下次执行</th>
                  <th>最后执行</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="task in filteredTasks" :key="task.id">
                  <td>
                    <div class="task-name">
                      <strong>{{ task.name }}</strong>
                      <small v-if="task.description">{{ task.description }}</small>
                    </div>
                  </td>
                  <td>
                    <span class="task-type">{{ getTaskTypeText(task.type) }}</span>
                  </td>
                  <td>
                    <div class="task-status" :class="task.status">
                      <span class="status-dot"></span>
                      {{ getStatusText(task.status) }}
                    </div>
                  </td>
                  <td>
                    <code class="cron-expression">{{ task.cronExpression || '-' }}</code>
                  </td>
                  <td>
                    <span class="time-text">{{ formatTime(task.nextRun) }}</span>
                  </td>
                  <td>
                    <span class="time-text">{{ formatTime(task.lastRun) }}</span>
                  </td>
                  <td>
                    <div class="task-actions">
                      <button 
                        v-if="task.status === 'stopped'"
                        @click="startTask(task.id)"
                        class="btn btn-small btn-success"
                        :disabled="isOperating"
                      >
                        ▶️
                      </button>
                      <button 
                        v-if="task.status === 'running' || task.status === 'scheduled'"
                        @click="stopTask(task.id)"
                        class="btn btn-small btn-warning"
                        :disabled="isOperating"
                      >
                        ⏸️
                      </button>
                      <button 
                        @click="editTask(task)"
                        class="btn btn-small btn-secondary"
                      >
                        ✏️
                      </button>
                      <button 
                        @click="deleteTask(task.id)"
                        class="btn btn-small btn-danger"
                        :disabled="isOperating || task.status === 'running'"
                      >
                        🗑️
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

    <!-- 任务创建/编辑模态框 -->
    <div v-if="showTaskModal" class="modal-overlay" @click="closeTaskModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingTask ? '编辑任务' : '创建任务' }}</h3>
          <button @click="closeTaskModal" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="saveTask">
            <div class="form-group">
              <label class="form-label">任务名称</label>
              <input 
                v-model="taskForm.name" 
                type="text" 
                class="form-input"
                required
                placeholder="输入任务名称"
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">任务描述</label>
              <textarea 
                v-model="taskForm.description" 
                class="form-textarea"
                placeholder="输入任务描述（可选）"
              ></textarea>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">任务类型</label>
                <select v-model="taskForm.type" class="form-select" required>
                  <option value="">选择任务类型</option>
                  <option value="browser_automation">浏览器自动化</option>
                  <option value="data_collection">数据采集</option>
                  <option value="content_processing">内容处理</option>
                  <option value="system_maintenance">系统维护</option>
                </select>
              </div>
              
              <div class="form-group">
                <label class="form-label">调度规则 (Cron)</label>
                <input 
                  v-model="taskForm.cronExpression" 
                  type="text" 
                  class="form-input"
                  required
                  placeholder="0 */5 * * * *"
                >
                <small class="form-help">例: 0 */5 * * * * (每5分钟执行一次)</small>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">执行脚本/命令</label>
              <textarea 
                v-model="taskForm.script" 
                class="form-textarea"
                required
                placeholder="输入要执行的脚本或命令"
                rows="4"
              ></textarea>
            </div>
            
            <div class="form-group">
              <label class="form-checkbox">
                <input v-model="taskForm.enabled" type="checkbox">
                <span>启用任务</span>
              </label>
            </div>
            
            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="isSaving">
                <span v-if="isSaving" class="loading"></span>
                {{ editingTask ? '更新任务' : '创建任务' }}
              </button>
              <button type="button" @click="closeTaskModal" class="btn btn-secondary">
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue';

export default {
  name: 'Scheduler',
  setup() {
    const isLoading = ref(false);
    const isOperating = ref(false);
    const isSaving = ref(false);
    const tasks = ref([]);
    const statusFilter = ref('');
    const showTaskModal = ref(false);
    const editingTask = ref(null);
    
    // 任务表单
    const taskForm = reactive({
      name: '',
      description: '',
      type: '',
      cronExpression: '',
      script: '',
      enabled: true
    });
    
    // 计算属性
    const runningTasks = computed(() => {
      return tasks.value.filter(t => t.status === 'running').length;
    });
    
    const scheduledTasks = computed(() => {
      return tasks.value.filter(t => t.status === 'scheduled').length;
    });
    
    const failedTasks = computed(() => {
      return tasks.value.filter(t => t.status === 'failed').length;
    });
    
    const filteredTasks = computed(() => {
      if (!statusFilter.value) return tasks.value;
      return tasks.value.filter(t => t.status === statusFilter.value);
    });
    
    // 获取任务列表
    const getTasks = async () => {
      try {
        if (window.httpAPI) {
          const data = await window.httpAPI.get('/api/scheduler/tasks');
          tasks.value = data.tasks || [];
        }
      } catch (error) {
        console.error('获取任务列表失败:', error);
        tasks.value = [];
      }
    };
    
    // 刷新任务
    const refreshTasks = async () => {
      isLoading.value = true;
      try {
        await getTasks();
      } finally {
        isLoading.value = false;
      }
    };
    
    // 创建任务
    const createTask = () => {
      editingTask.value = null;
      resetTaskForm();
      showTaskModal.value = true;
    };
    
    // 编辑任务
    const editTask = (task) => {
      editingTask.value = task;
      Object.assign(taskForm, {
        name: task.name,
        description: task.description || '',
        type: task.type,
        cronExpression: task.cronExpression,
        script: task.script || '',
        enabled: task.enabled !== false
      });
      showTaskModal.value = true;
    };
    
    // 保存任务
    const saveTask = async () => {
      try {
        isSaving.value = true;
        if (window.httpAPI) {
          if (editingTask.value) {
            await window.httpAPI.put(`/api/scheduler/tasks/${editingTask.value.id}`, taskForm);
          } else {
            await window.httpAPI.post('/api/scheduler/tasks', taskForm);
          }
          await getTasks();
          closeTaskModal();
        }
      } catch (error) {
        console.error('保存任务失败:', error);
      } finally {
        isSaving.value = false;
      }
    };
    
    // 启动任务
    const startTask = async (taskId) => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post(`/api/scheduler/tasks/${taskId}/start`);
          await getTasks();
        }
      } catch (error) {
        console.error('启动任务失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 停止任务
    const stopTask = async (taskId) => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post(`/api/scheduler/tasks/${taskId}/stop`);
          await getTasks();
        }
      } catch (error) {
        console.error('停止任务失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 删除任务
    const deleteTask = async (taskId) => {
      if (!confirm('确定要删除这个任务吗？')) return;
      
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.delete(`/api/scheduler/tasks/${taskId}`);
          await getTasks();
        }
      } catch (error) {
        console.error('删除任务失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 关闭模态框
    const closeTaskModal = () => {
      showTaskModal.value = false;
      editingTask.value = null;
      resetTaskForm();
    };
    
    // 重置表单
    const resetTaskForm = () => {
      Object.assign(taskForm, {
        name: '',
        description: '',
        type: '',
        cronExpression: '',
        script: '',
        enabled: true
      });
    };
    
    // 工具函数
    const getTaskTypeText = (type) => {
      const typeMap = {
        'browser_automation': '浏览器自动化',
        'data_collection': '数据采集',
        'content_processing': '内容处理',
        'system_maintenance': '系统维护'
      };
      return typeMap[type] || type;
    };
    
    const getStatusText = (status) => {
      const statusMap = {
        'running': '运行中',
        'scheduled': '已调度',
        'stopped': '已停止',
        'failed': '失败',
        'completed': '已完成'
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
      refreshTasks();
    });
    
    return {
      isLoading,
      isOperating,
      isSaving,
      tasks,
      statusFilter,
      showTaskModal,
      editingTask,
      taskForm,
      runningTasks,
      scheduledTasks,
      failedTasks,
      filteredTasks,
      refreshTasks,
      createTask,
      editTask,
      saveTask,
      startTask,
      stopTask,
      deleteTask,
      closeTaskModal,
      getTaskTypeText,
      getStatusText,
      formatTime
    };
  }
};
</script>

<style scoped>
.scheduler {
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

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin: 0;
}

.page-actions {
  display: flex;
  gap: 12px;
}

.scheduler-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 统计卡片 */
.stat-card .card-body {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: #f5f5f5;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.stat-icon.running {
  background: linear-gradient(135deg, #4caf50, #45a049);
  color: white;
}

.stat-icon.scheduled {
  background: linear-gradient(135deg, #2196f3, #1976d2);
  color: white;
}

.stat-icon.failed {
  background: linear-gradient(135deg, #f44336, #d32f2f);
  color: white;
}

.stat-info h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #333;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  color: #333;
}

.task-filters {
  display: flex;
  gap: 12px;
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

.task-table {
  overflow-x: auto;
}

.task-name strong {
  display: block;
  font-size: 14px;
  color: #333;
}

.task-name small {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.task-type {
  padding: 4px 8px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.task-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.task-status.running {
  background: #e8f5e8;
  color: #2e7d32;
}

.task-status.scheduled {
  background: #e3f2fd;
  color: #1976d2;
}

.task-status.stopped {
  background: #f5f5f5;
  color: #666;
}

.task-status.failed {
  background: #ffebee;
  color: #c62828;
}

.cron-expression {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 4px;
}

.time-text {
  font-size: 12px;
  color: #666;
}

.task-actions {
  display: flex;
  gap: 4px;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.modal-close:hover {
  background: #f5f5f5;
}

.modal-body {
  padding: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-help {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}
</style>