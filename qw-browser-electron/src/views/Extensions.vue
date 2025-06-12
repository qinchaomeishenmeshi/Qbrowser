<template>
  <div class="extensions">
    <div class="page-header">
      <h1 class="page-title">扩展管理</h1>
      <div class="page-actions">
        <button @click="installExtension" class="btn btn-primary">
          <span>📦</span>
          安装扩展
        </button>
        <button @click="refreshExtensions" class="btn btn-secondary" :disabled="isLoading">
          <span v-if="isLoading" class="loading"></span>
          <span v-else>🔄</span>
          刷新
        </button>
      </div>
    </div>

    <div class="extensions-content">
      <!-- 扩展统计 -->
      <div class="grid grid-4">
        <div class="card stat-card">
          <div class="card-body">
            <div class="stat-icon total">🧩</div>
            <div class="stat-info">
              <h3>总扩展数</h3>
              <p class="stat-number">{{ extensions.length }}</p>
            </div>
          </div>
        </div>
        
        <div class="card stat-card">
          <div class="card-body">
            <div class="stat-icon enabled">✅</div>
            <div class="stat-info">
              <h3>已启用</h3>
              <p class="stat-number text-success">{{ enabledExtensions }}</p>
            </div>
          </div>
        </div>
        
        <div class="card stat-card">
          <div class="card-body">
            <div class="stat-icon disabled">⏸️</div>
            <div class="stat-info">
              <h3>已禁用</h3>
              <p class="stat-number text-warning">{{ disabledExtensions }}</p>
            </div>
          </div>
        </div>
        
        <div class="card stat-card">
          <div class="card-body">
            <div class="stat-icon updates">🔄</div>
            <div class="stat-info">
              <h3>可更新</h3>
              <p class="stat-number text-info">{{ updatableExtensions }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 扩展列表 -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">已安装扩展</h2>
          <div class="extension-filters">
            <select v-model="statusFilter" class="form-select">
              <option value="">全部状态</option>
              <option value="enabled">已启用</option>
              <option value="disabled">已禁用</option>
            </select>
            <select v-model="categoryFilter" class="form-select">
              <option value="">全部分类</option>
              <option value="automation">自动化</option>
              <option value="productivity">效率工具</option>
              <option value="development">开发工具</option>
              <option value="security">安全工具</option>
            </select>
          </div>
        </div>
        <div class="card-body">
          <div v-if="filteredExtensions.length === 0" class="empty-state">
            <div class="empty-icon">🧩</div>
            <h3>暂无扩展</h3>
            <p>点击上方按钮安装第一个扩展</p>
          </div>
          <div v-else class="extensions-grid">
            <div 
              v-for="extension in filteredExtensions" 
              :key="extension.id"
              class="extension-card"
              :class="{ disabled: !extension.enabled }"
            >
              <div class="extension-header">
                <div class="extension-icon">
                  <img 
                    v-if="extension.icon" 
                    :src="extension.icon" 
                    :alt="extension.name"
                    @error="handleIconError"
                  >
                  <span v-else class="default-icon">🧩</span>
                </div>
                <div class="extension-info">
                  <h3 class="extension-name">{{ extension.name }}</h3>
                  <p class="extension-version">v{{ extension.version }}</p>
                </div>
                <div class="extension-status">
                  <div 
                    class="status-indicator" 
                    :class="extension.enabled ? 'enabled' : 'disabled'"
                    :title="extension.enabled ? '已启用' : '已禁用'"
                  ></div>
                </div>
              </div>
              
              <div class="extension-body">
                <p class="extension-description">{{ extension.description }}</p>
                
                <div class="extension-meta">
                  <span class="extension-category">{{ getCategoryText(extension.category) }}</span>
                  <span class="extension-author">作者: {{ extension.author }}</span>
                </div>
                
                <div v-if="extension.permissions && extension.permissions.length" class="extension-permissions">
                  <h4>权限要求:</h4>
                  <ul>
                    <li v-for="permission in extension.permissions" :key="permission">
                      {{ getPermissionText(permission) }}
                    </li>
                  </ul>
                </div>
              </div>
              
              <div class="extension-footer">
                <div class="extension-actions">
                  <button 
                    v-if="!extension.enabled"
                    @click="enableExtension(extension.id)"
                    class="btn btn-small btn-success"
                    :disabled="isOperating"
                  >
                    启用
                  </button>
                  <button 
                    v-if="extension.enabled"
                    @click="disableExtension(extension.id)"
                    class="btn btn-small btn-warning"
                    :disabled="isOperating"
                  >
                    禁用
                  </button>
                  <button 
                    @click="configureExtension(extension)"
                    class="btn btn-small btn-secondary"
                  >
                    配置
                  </button>
                  <button 
                    v-if="extension.hasUpdate"
                    @click="updateExtension(extension.id)"
                    class="btn btn-small btn-info"
                    :disabled="isOperating"
                  >
                    更新
                  </button>
                  <button 
                    @click="uninstallExtension(extension.id)"
                    class="btn btn-small btn-danger"
                    :disabled="isOperating || extension.enabled"
                  >
                    卸载
                  </button>
                </div>
                
                <div class="extension-stats">
                  <span class="install-date">安装于: {{ formatDate(extension.installDate) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 扩展安装模态框 -->
    <div v-if="showInstallModal" class="modal-overlay" @click="closeInstallModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>安装扩展</h3>
          <button @click="closeInstallModal" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="install-tabs">
            <button 
              v-for="tab in installTabs" 
              :key="tab.key"
              @click="activeInstallTab = tab.key"
              class="tab-button"
              :class="{ active: activeInstallTab === tab.key }"
            >
              {{ tab.label }}
            </button>
          </div>
          
          <!-- 从文件安装 -->
          <div v-if="activeInstallTab === 'file'" class="install-content">
            <div class="form-group">
              <label class="form-label">选择扩展文件</label>
              <input 
                type="file" 
                @change="handleFileSelect"
                accept=".zip,.crx,.xpi"
                class="form-input"
              >
              <small class="form-help">支持 .zip, .crx, .xpi 格式的扩展文件</small>
            </div>
          </div>
          
          <!-- 从URL安装 -->
          <div v-if="activeInstallTab === 'url'" class="install-content">
            <div class="form-group">
              <label class="form-label">扩展URL</label>
              <input 
                v-model="installForm.url" 
                type="url" 
                class="form-input"
                placeholder="https://example.com/extension.zip"
              >
            </div>
          </div>
          
          <!-- 从商店安装 -->
          <div v-if="activeInstallTab === 'store'" class="install-content">
            <div class="form-group">
              <label class="form-label">搜索扩展</label>
              <input 
                v-model="storeSearchQuery" 
                type="text" 
                class="form-input"
                placeholder="输入扩展名称或关键词"
                @input="searchStoreExtensions"
              >
            </div>
            
            <div v-if="storeExtensions.length" class="store-extensions">
              <div 
                v-for="ext in storeExtensions" 
                :key="ext.id"
                class="store-extension-item"
                @click="selectStoreExtension(ext)"
              >
                <div class="store-ext-icon">
                  <img v-if="ext.icon" :src="ext.icon" :alt="ext.name">
                  <span v-else>🧩</span>
                </div>
                <div class="store-ext-info">
                  <h4>{{ ext.name }}</h4>
                  <p>{{ ext.description }}</p>
                  <div class="store-ext-meta">
                    <span class="rating">⭐ {{ ext.rating }}</span>
                    <span class="downloads">{{ ext.downloads }} 下载</span>
                  </div>
                </div>
                <div class="store-ext-actions">
                  <button class="btn btn-small btn-primary">安装</button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="modal-actions">
            <button 
              @click="performInstall" 
              class="btn btn-primary"
              :disabled="isInstalling || !canInstall"
            >
              <span v-if="isInstalling" class="loading"></span>
              安装扩展
            </button>
            <button @click="closeInstallModal" class="btn btn-secondary">
              取消
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 扩展配置模态框 -->
    <div v-if="showConfigModal" class="modal-overlay" @click="closeConfigModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>配置扩展 - {{ configuringExtension?.name }}</h3>
          <button @click="closeConfigModal" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="configuringExtension" class="config-content">
            <div class="form-group">
              <label class="form-checkbox">
                <input v-model="extensionConfig.autoStart" type="checkbox">
                <span>随浏览器自动启动</span>
              </label>
            </div>
            
            <div class="form-group">
              <label class="form-checkbox">
                <input v-model="extensionConfig.allowInIncognito" type="checkbox">
                <span>允许在隐身模式下运行</span>
              </label>
            </div>
            
            <div class="form-group">
              <label class="form-label">扩展设置</label>
              <textarea 
                v-model="extensionConfig.customSettings" 
                class="form-textarea"
                placeholder="JSON格式的自定义设置"
                rows="6"
              ></textarea>
            </div>
          </div>
          
          <div class="modal-actions">
            <button @click="saveExtensionConfig" class="btn btn-primary" :disabled="isSaving">
              <span v-if="isSaving" class="loading"></span>
              保存配置
            </button>
            <button @click="closeConfigModal" class="btn btn-secondary">
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue';

export default {
  name: 'Extensions',
  setup() {
    const isLoading = ref(false);
    const isOperating = ref(false);
    const isInstalling = ref(false);
    const isSaving = ref(false);
    const extensions = ref([]);
    const statusFilter = ref('');
    const categoryFilter = ref('');
    const showInstallModal = ref(false);
    const showConfigModal = ref(false);
    const configuringExtension = ref(null);
    const activeInstallTab = ref('file');
    const storeSearchQuery = ref('');
    const storeExtensions = ref([]);
    
    // 安装表单
    const installForm = reactive({
      file: null,
      url: ''
    });
    
    // 扩展配置
    const extensionConfig = reactive({
      autoStart: false,
      allowInIncognito: false,
      customSettings: '{}'
    });
    
    // 安装选项卡
    const installTabs = [
      { key: 'file', label: '从文件安装' },
      { key: 'url', label: '从URL安装' },
      { key: 'store', label: '从商店安装' }
    ];
    
    // 计算属性
    const enabledExtensions = computed(() => {
      return extensions.value.filter(ext => ext.enabled).length;
    });
    
    const disabledExtensions = computed(() => {
      return extensions.value.filter(ext => !ext.enabled).length;
    });
    
    const updatableExtensions = computed(() => {
      return extensions.value.filter(ext => ext.hasUpdate).length;
    });
    
    const filteredExtensions = computed(() => {
      let filtered = extensions.value;
      
      if (statusFilter.value) {
        filtered = filtered.filter(ext => {
          if (statusFilter.value === 'enabled') return ext.enabled;
          if (statusFilter.value === 'disabled') return !ext.enabled;
          return true;
        });
      }
      
      if (categoryFilter.value) {
        filtered = filtered.filter(ext => ext.category === categoryFilter.value);
      }
      
      return filtered;
    });
    
    const canInstall = computed(() => {
      if (activeInstallTab.value === 'file') return installForm.file;
      if (activeInstallTab.value === 'url') return installForm.url;
      return false;
    });
    
    // 获取扩展列表
    const getExtensions = async () => {
      try {
        if (window.httpAPI) {
          const data = await window.httpAPI.get('/api/extensions');
          extensions.value = data.extensions || [];
        }
      } catch (error) {
        console.error('获取扩展列表失败:', error);
        extensions.value = [];
      }
    };
    
    // 刷新扩展
    const refreshExtensions = async () => {
      isLoading.value = true;
      try {
        await getExtensions();
      } finally {
        isLoading.value = false;
      }
    };
    
    // 启用扩展
    const enableExtension = async (extensionId) => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post(`/api/extensions/${extensionId}/enable`);
          await getExtensions();
        }
      } catch (error) {
        console.error('启用扩展失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 禁用扩展
    const disableExtension = async (extensionId) => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post(`/api/extensions/${extensionId}/disable`);
          await getExtensions();
        }
      } catch (error) {
        console.error('禁用扩展失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 更新扩展
    const updateExtension = async (extensionId) => {
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post(`/api/extensions/${extensionId}/update`);
          await getExtensions();
        }
      } catch (error) {
        console.error('更新扩展失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 卸载扩展
    const uninstallExtension = async (extensionId) => {
      if (!confirm('确定要卸载这个扩展吗？')) return;
      
      try {
        isOperating.value = true;
        if (window.httpAPI) {
          await window.httpAPI.delete(`/api/extensions/${extensionId}`);
          await getExtensions();
        }
      } catch (error) {
        console.error('卸载扩展失败:', error);
      } finally {
        isOperating.value = false;
      }
    };
    
    // 安装扩展
    const installExtension = () => {
      showInstallModal.value = true;
    };
    
    // 执行安装
    const performInstall = async () => {
      try {
        isInstalling.value = true;
        if (window.httpAPI) {
          let result;
          if (activeInstallTab.value === 'file' && installForm.file) {
            const formData = new FormData();
            formData.append('file', installForm.file);
            result = await window.httpAPI.post('/api/extensions/install/file', formData);
          } else if (activeInstallTab.value === 'url' && installForm.url) {
            result = await window.httpAPI.post('/api/extensions/install/url', {
              url: installForm.url
            });
          }
          
          if (result) {
            await getExtensions();
            closeInstallModal();
          }
        }
      } catch (error) {
        console.error('安装扩展失败:', error);
      } finally {
        isInstalling.value = false;
      }
    };
    
    // 配置扩展
    const configureExtension = (extension) => {
      configuringExtension.value = extension;
      // 加载现有配置
      Object.assign(extensionConfig, {
        autoStart: extension.config?.autoStart || false,
        allowInIncognito: extension.config?.allowInIncognito || false,
        customSettings: JSON.stringify(extension.config?.customSettings || {}, null, 2)
      });
      showConfigModal.value = true;
    };
    
    // 保存扩展配置
    const saveExtensionConfig = async () => {
      try {
        isSaving.value = true;
        if (window.httpAPI && configuringExtension.value) {
          const config = {
            autoStart: extensionConfig.autoStart,
            allowInIncognito: extensionConfig.allowInIncognito,
            customSettings: JSON.parse(extensionConfig.customSettings || '{}')
          };
          
          await window.httpAPI.put(
            `/api/extensions/${configuringExtension.value.id}/config`,
            config
          );
          
          await getExtensions();
          closeConfigModal();
        }
      } catch (error) {
        console.error('保存配置失败:', error);
      } finally {
        isSaving.value = false;
      }
    };
    
    // 搜索商店扩展
    const searchStoreExtensions = async () => {
      if (!storeSearchQuery.value.trim()) {
        storeExtensions.value = [];
        return;
      }
      
      try {
        if (window.httpAPI) {
          const data = await window.httpAPI.get('/api/extensions/store/search', {
            params: { q: storeSearchQuery.value }
          });
          storeExtensions.value = data.extensions || [];
        }
      } catch (error) {
        console.error('搜索扩展失败:', error);
        storeExtensions.value = [];
      }
    };
    
    // 选择商店扩展
    const selectStoreExtension = async (extension) => {
      try {
        isInstalling.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post('/api/extensions/install/store', {
            extensionId: extension.id
          });
          await getExtensions();
          closeInstallModal();
        }
      } catch (error) {
        console.error('安装扩展失败:', error);
      } finally {
        isInstalling.value = false;
      }
    };
    
    // 处理文件选择
    const handleFileSelect = (event) => {
      const file = event.target.files[0];
      installForm.file = file;
    };
    
    // 处理图标错误
    const handleIconError = (event) => {
      event.target.style.display = 'none';
      event.target.nextElementSibling.style.display = 'block';
    };
    
    // 关闭模态框
    const closeInstallModal = () => {
      showInstallModal.value = false;
      installForm.file = null;
      installForm.url = '';
      storeSearchQuery.value = '';
      storeExtensions.value = [];
    };
    
    const closeConfigModal = () => {
      showConfigModal.value = false;
      configuringExtension.value = null;
    };
    
    // 工具函数
    const getCategoryText = (category) => {
      const categoryMap = {
        'automation': '自动化',
        'productivity': '效率工具',
        'development': '开发工具',
        'security': '安全工具'
      };
      return categoryMap[category] || category;
    };
    
    const getPermissionText = (permission) => {
      const permissionMap = {
        'tabs': '访问标签页',
        'storage': '本地存储',
        'activeTab': '当前标签页',
        'background': '后台运行',
        'notifications': '桌面通知',
        'webRequest': '网络请求',
        'cookies': 'Cookie访问'
      };
      return permissionMap[permission] || permission;
    };
    
    const formatDate = (timestamp) => {
      if (!timestamp) return '-';
      const date = new Date(timestamp);
      return date.toLocaleDateString('zh-CN');
    };
    
    // 生命周期
    onMounted(() => {
      refreshExtensions();
    });
    
    return {
      isLoading,
      isOperating,
      isInstalling,
      isSaving,
      extensions,
      statusFilter,
      categoryFilter,
      showInstallModal,
      showConfigModal,
      configuringExtension,
      activeInstallTab,
      storeSearchQuery,
      storeExtensions,
      installForm,
      extensionConfig,
      installTabs,
      enabledExtensions,
      disabledExtensions,
      updatableExtensions,
      filteredExtensions,
      canInstall,
      refreshExtensions,
      enableExtension,
      disableExtension,
      updateExtension,
      uninstallExtension,
      installExtension,
      performInstall,
      configureExtension,
      saveExtensionConfig,
      searchStoreExtensions,
      selectStoreExtension,
      handleFileSelect,
      handleIconError,
      closeInstallModal,
      closeConfigModal,
      getCategoryText,
      getPermissionText,
      formatDate
    };
  }
};
</script>

<style scoped>
.extensions {
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

.extensions-content {
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

.stat-icon.enabled {
  background: linear-gradient(135deg, #4caf50, #45a049);
  color: white;
}

.stat-icon.disabled {
  background: linear-gradient(135deg, #ff9800, #f57c00);
  color: white;
}

.stat-icon.updates {
  background: linear-gradient(135deg, #2196f3, #1976d2);
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

.extension-filters {
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

/* 扩展网格 */
.extensions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.extension-card {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  background: white;
  transition: all 0.2s ease;
}

.extension-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.extension-card.disabled {
  opacity: 0.6;
  background: #f9f9f9;
}

.extension-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.extension-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.extension-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.default-icon {
  font-size: 24px;
}

.extension-info {
  flex: 1;
}

.extension-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #333;
}

.extension-version {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.extension-status {
  display: flex;
  align-items: center;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ccc;
}

.status-indicator.enabled {
  background: #4caf50;
}

.status-indicator.disabled {
  background: #f44336;
}

.extension-description {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  margin-bottom: 12px;
}

.extension-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.extension-category {
  padding: 4px 8px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.extension-author {
  font-size: 12px;
  color: #666;
}

.extension-permissions {
  margin-bottom: 16px;
}

.extension-permissions h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #333;
}

.extension-permissions ul {
  margin: 0;
  padding-left: 16px;
}

.extension-permissions li {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.extension-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.extension-actions {
  display: flex;
  gap: 8px;
}

.extension-stats {
  font-size: 12px;
  color: #666;
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
  max-width: 700px;
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

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

/* 安装选项卡 */
.install-tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
  margin-bottom: 20px;
}

.tab-button {
  padding: 12px 20px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.tab-button:hover {
  color: #333;
}

.tab-button.active {
  color: #1976d2;
  border-bottom-color: #1976d2;
}

.install-content {
  margin-bottom: 20px;
}

/* 商店扩展 */
.store-extensions {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.store-extension-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s ease;
}

.store-extension-item:hover {
  background: #f9f9f9;
}

.store-extension-item:last-child {
  border-bottom: none;
}

.store-ext-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.store-ext-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.store-ext-info {
  flex: 1;
}

.store-ext-info h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #333;
}

.store-ext-info p {
  font-size: 14px;
  color: #666;
  margin: 0 0 8px 0;
}

.store-ext-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.store-ext-actions {
  display: flex;
  gap: 8px;
}
</style>