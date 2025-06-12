<template>
  <div class="browser-manager">
    <div class="page-header">
      <h1 class="page-title">浏览器管理</h1>
      <div class="page-actions">
        <button @click="createBrowser" class="btn btn-primary">
          <span>➕</span>
          创建浏览器实例
        </button>
        <button @click="refreshBrowsers" class="btn btn-secondary" :disabled="isLoading">
          <span v-if="isLoading" class="loading"></span>
          <span v-else>🔄</span>
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
            <div class="empty-icon">🌐</div>
            <h3>暂无浏览器实例</h3>
            <p>点击上方按钮创建第一个浏览器实例</p>
          </div>
          <div v-else class="browser-grid">
            <div 
              v-for="browser in browsers" 
              :key="browser.id" 
              class="browser-card"
              :class="{ active: browser.status === 'running' }"
            >
              <div class="browser-header">
                <div class="browser-info">
                  <h3 class="browser-name">{{ browser.name || `浏览器 ${browser.id}` }}</h3>
                  <div class="browser-status" :class="browser.status">
                    <span class="status-dot"></span>
                    {{ getStatusText(browser.status) }}
                  </div>
                </div>
                <div class="browser-actions">
                  <button 
                    v-if="browser.status === 'stopped'"
                    @click="startBrowser(browser.id)"
                    class="btn btn-small btn-success"
                    :disabled="isOperating"
                  >
                    ▶️ 启动
                  </button>
                  <button 
                    v-if="browser.status === 'running'"
                    @click="stopBrowser(browser.id)"
                    class="btn btn-small btn-warning"
                    :disabled="isOperating"
                  >
                    ⏸️ 停止
                  </button>
                  <button 
                    @click="deleteBrowser(browser.id)"
                    class="btn btn-small btn-danger"
                    :disabled="isOperating || browser.status === 'running'"
                  >
                    🗑️ 删除
                  </button>
                </div>
              </div>
              
              <div class="browser-details">
                <div class="detail-item">
                  <span class="detail-label">用户数据目录:</span>
                  <span class="detail-value">{{ browser.userDataDir || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">端口:</span>
                  <span class="detail-value">{{ browser.port || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">创建时间:</span>
                  <span class="detail-value">{{ formatTime(browser.createdAt) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">最后活动:</span>
                  <span class="detail-value">{{ formatTime(browser.lastActivity) }}</span>
                </div>
              </div>
              
              <div v-if="browser.status === 'running'" class="browser-tabs">
                <h4>活跃标签页 ({{ browser.tabs?.length || 0 }})</h4>
                <div v-if="browser.tabs?.length" class="tab-list">
                  <div v-for="tab in browser.tabs.slice(0, 3)" :key="tab.id" class="tab-item">
                    <span class="tab-title">{{ tab.title || tab.url }}</span>
                  </div>
                  <div v-if="browser.tabs.length > 3" class="tab-more">
                    +{{ browser.tabs.length - 3 }} 更多
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 浏览器配置 -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">浏览器配置</h2>
        </div>
        <div class="card-body">
          <form @submit.prevent="saveBrowserConfig" class="config-form">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">默认用户代理</label>
                <input 
                  v-model="config.userAgent" 
                  type="text" 
                  class="form-input"
                  placeholder="留空使用默认用户代理"
                >
              </div>
              <div class="form-group">
                <label class="form-label">窗口大小</label>
                <div class="size-inputs">
                  <input 
                    v-model.number="config.windowWidth" 
                    type="number" 
                    class="form-input"
                    placeholder="宽度"
                    min="800"
                  >
                  <span>×</span>
                  <input 
                    v-model.number="config.windowHeight" 
                    type="number" 
                    class="form-input"
                    placeholder="高度"
                    min="600"
                  >
                </div>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="config.headless" type="checkbox">
                  <span>无头模式</span>
                </label>
              </div>
              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="config.disableImages" type="checkbox">
                  <span>禁用图片加载</span>
                </label>
              </div>
              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="config.disableJavaScript" type="checkbox">
                  <span>禁用JavaScript</span>
                </label>
              </div>
            </div>
            
            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="isSaving">
                <span v-if="isSaving" class="loading"></span>
                保存配置
              </button>
              <button type="button" @click="resetConfig" class="btn btn-secondary">
                重置
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
  name: 'BrowserManager',
  setup() {
    const isLoading = ref(false);
    const isOperating = ref(false);
    const isSaving = ref(false);
    const browsers = ref([]);
    
    // 浏览器配置
    const config = reactive({
      userAgent: '',
      windowWidth: 1920,
      windowHeight: 1080,
      headless: false,
      disableImages: false,
      disableJavaScript: false
    });
    
    // 计算属性
    const activeBrowsers = computed(() => {
      return browsers.value.filter(b => b.status === 'running').length;
    });
    
    // 获取浏览器列表
    const getBrowsers = async () => {
      try {
        if (window.httpAPI) {
          const data = await window.httpAPI.get('/api/browser/list');
          browsers.value = data.browsers || [];
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
    
    // 创建浏览器
    const createBrowser = async () => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post('/api/browser/create', config);
          await getBrowsers();
        }
      } catch (error) {
        console.error('创建浏览器失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 启动浏览器
    const startBrowser = async (browserId) => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post(`/api/browser/${browserId}/start`);
          await getBrowsers();
        }
      } catch (error) {
        console.error('启动浏览器失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 停止浏览器
    const stopBrowser = async (browserId) => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post(`/api/browser/${browserId}/stop`);
          await getBrowsers();
        }
      } catch (error) {
        console.error('停止浏览器失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 删除浏览器
    const deleteBrowser = async (browserId) => {
      if (!confirm('确定要删除这个浏览器实例吗？')) return;
      
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.delete(`/api/browser/${browserId}`);
          await getBrowsers();
        }
      } catch (error) {
        console.error('删除浏览器失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 保存配置
    const saveBrowserConfig = async () => {
      try {
        isSaving.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post('/api/browser/config', config);
          console.log('配置保存成功');
        }
      } catch (error) {
        console.error('保存配置失败:', error);
      } finally {
        isSaving.value = false;
      }
    };
    
    // 重置配置
    const resetConfig = () => {
      Object.assign(config, {
        userAgent: '',
        windowWidth: 1920,
        windowHeight: 1080,
        headless: false,
        disableImages: false,
        disableJavaScript: false
      });
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
      isSaving,
      browsers,
      config,
      activeBrowsers,
      refreshBrowsers,
      createBrowser,
      startBrowser,
      stopBrowser,
      deleteBrowser,
      saveBrowserConfig,
      resetConfig,
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

.browser-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.browser-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  background: white;
  transition: all 0.3s ease;
}

.browser-card.active {
  border-color: #4caf50;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.15);
}

.browser-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.browser-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.browser-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.browser-status.running {
  background: #e8f5e8;
  color: #2e7d32;
}

.browser-status.stopped {
  background: #ffebee;
  color: #c62828;
}

.browser-status.starting,
.browser-status.stopping {
  background: #fff3e0;
  color: #ef6c00;
}

.browser-actions {
  display: flex;
  gap: 8px;
}

.browser-details {
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 14px;
}

.detail-label {
  color: #666;
  font-weight: 500;
}

.detail-value {
  color: #333;
  font-family: monospace;
}

.browser-tabs h4 {
  font-size: 14px;
  color: #333;
  margin: 0 0 8px 0;
}

.tab-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tab-item {
  padding: 4px 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.tab-title {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tab-more {
  padding: 4px 8px;
  background: #e0e0e0;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  text-align: center;
}

.config-form {
  max-width: 600px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.size-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.size-inputs input {
  flex: 1;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}
</style>