<template>
  <div class="settings">
    <div class="page-header">
      <div class="page-actions">
        <button @click="saveAllSettings" class="btn btn-primary" :disabled="isSaving">
          <span v-if="isSaving" class="loading"></span>
          <span v-else>[SAVE]</span>
          保存设置
        </button>
        <button @click="resetSettings" class="btn btn-secondary">
          <span>[RESET]</span>
          重置默认
        </button>
      </div>
    </div>

    <div class="settings-content">
      <div class="settings-sidebar">
        <nav class="settings-nav">
          <button
                  v-for="section in settingSections"
                  :key="section.key"
                  @click="activeSection = section.key"
                  class="nav-item"
                  :class="{ active: activeSection === section.key }">
            <span class="nav-icon">{{ section.icon }}</span>
            <span class="nav-label">{{ section.label }}</span>
          </button>
        </nav>
      </div>

      <div class="settings-main">
        <!-- 通用设置 -->
        <div v-if="activeSection === 'general'" class="setting-section">
          <h2 class="section-title">通用设置</h2>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">应用配置</h3>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-label">应用语言</label>
                <select v-model="settings.general.language" class="form-select">
                  <option value="zh-CN">简体中文</option>
                  <option value="en-US">English</option>
                  <option value="ja-JP">日本語</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">主题模式</label>
                <select v-model="settings.general.theme" class="form-select">
                  <option value="light">浅色模式</option>
                  <option value="dark">深色模式</option>
                  <option value="auto">跟随系统</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.general.autoStart" type="checkbox">
                  <span>开机自动启动</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.general.minimizeToTray" type="checkbox">
                  <span>最小化到系统托盘</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.general.closeToTray" type="checkbox">
                  <span>关闭时最小化到托盘</span>
                </label>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">更新设置</h3>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.general.autoUpdate" type="checkbox">
                  <span>自动检查更新</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-label">更新频率</label>
                <select v-model="settings.general.updateFrequency" class="form-select">
                  <option value="daily">每天</option>
                  <option value="weekly">每周</option>
                  <option value="monthly">每月</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- 浏览器设置 -->
        <div v-if="activeSection === 'browser'" class="setting-section">
          <h2 class="section-title">浏览器设置</h2>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">默认配置</h3>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-label">默认浏览器类型</label>
                <select v-model="settings.browser.defaultType" class="form-select">
                  <option value="chrome">Chrome</option>
                  <option value="firefox">Firefox</option>
                  <option value="edge">Edge</option>
                  <option value="safari">Safari</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">默认窗口大小</label>
                <div class="form-row">
                  <input
                         v-model.number="settings.browser.defaultWidth"
                         type="number"
                         class="form-input"
                         placeholder="宽度">
                  <span class="form-separator">×</span>
                  <input
                         v-model.number="settings.browser.defaultHeight"
                         type="number"
                         class="form-input"
                         placeholder="高度">
                </div>
              </div>

              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.browser.headless" type="checkbox">
                  <span>默认无头模式</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.browser.disableImages" type="checkbox">
                  <span>禁用图片加载</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.browser.disableJavaScript" type="checkbox">
                  <span>禁用JavaScript</span>
                </label>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">代理设置</h3>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.browser.useProxy" type="checkbox">
                  <span>启用代理</span>
                </label>
              </div>

              <div v-if="settings.browser.useProxy" class="proxy-config">
                <div class="form-group">
                  <label class="form-label">代理类型</label>
                  <select v-model="settings.browser.proxyType" class="form-select">
                    <option value="http">HTTP</option>
                    <option value="https">HTTPS</option>
                    <option value="socks5">SOCKS5</option>
                  </select>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label">代理地址</label>
                    <input
                           v-model="settings.browser.proxyHost"
                           type="text"
                           class="form-input"
                           placeholder="127.0.0.1">
                  </div>

                  <div class="form-group">
                    <label class="form-label">端口</label>
                    <input
                           v-model.number="settings.browser.proxyPort"
                           type="number"
                           class="form-input"
                           placeholder="8080">
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label">用户名（可选）</label>
                    <input
                           v-model="settings.browser.proxyUsername"
                           type="text"
                           class="form-input">
                  </div>

                  <div class="form-group">
                    <label class="form-label">密码（可选）</label>
                    <input
                           v-model="settings.browser.proxyPassword"
                           type="password"
                           class="form-input">
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 性能设置 -->
        <div v-if="activeSection === 'performance'" class="setting-section">
          <h2 class="section-title">性能设置</h2>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">资源限制</h3>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-label">最大并发浏览器数量</label>
                <input
                       v-model.number="settings.performance.maxBrowsers"
                       type="number"
                       class="form-input"
                       min="1"
                       max="20">
                <small class="form-help">同时运行的浏览器实例数量上限</small>
              </div>

              <div class="form-group">
                <label class="form-label">内存使用限制 (MB)</label>
                <input
                       v-model.number="settings.performance.memoryLimit"
                       type="number"
                       class="form-input"
                       min="512"
                       step="256">
                <small class="form-help">单个浏览器实例的内存使用上限</small>
              </div>

              <div class="form-group">
                <label class="form-label">CPU使用限制 (%)</label>
                <input
                       v-model.number="settings.performance.cpuLimit"
                       type="number"
                       class="form-input"
                       min="10"
                       max="100">
                <small class="form-help">应用程序的CPU使用率上限</small>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">缓存设置</h3>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.performance.enableCache" type="checkbox">
                  <span>启用缓存</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-label">缓存大小限制 (MB)</label>
                <input
                       v-model.number="settings.performance.cacheSize"
                       type="number"
                       class="form-input"
                       min="100"
                       step="100">
              </div>

              <div class="form-group">
                <button @click="clearCache" class="btn btn-warning">
                  <span>[删除]</span>
                  清理缓存
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 安全设置 -->
        <div v-if="activeSection === 'security'" class="setting-section">
          <h2 class="section-title">安全设置</h2>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">访问控制</h3>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.security.requireAuth" type="checkbox">
                  <span>启用身份验证</span>
                </label>
              </div>

              <div v-if="settings.security.requireAuth" class="auth-config">
                <div class="form-group">
                  <label class="form-label">用户名</label>
                  <input
                         v-model="settings.security.username"
                         type="text"
                         class="form-input"
                         required>
                </div>

                <div class="form-group">
                  <label class="form-label">密码</label>
                  <input
                         v-model="settings.security.password"
                         type="password"
                         class="form-input"
                         required>
                </div>
              </div>

              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.security.enableHttps" type="checkbox">
                  <span>强制HTTPS</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-label">允许的IP地址</label>
                <textarea
                          v-model="settings.security.allowedIPs"
                          class="form-textarea"
                          placeholder="127.0.0.1\n192.168.1.0/24"
                          rows="4"></textarea>
                <small class="form-help">每行一个IP地址或CIDR网段，留空表示允许所有</small>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">数据保护</h3>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.security.encryptData" type="checkbox">
                  <span>加密存储数据</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.security.autoBackup" type="checkbox">
                  <span>自动备份数据</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-label">备份保留天数</label>
                <input
                       v-model.number="settings.security.backupRetentionDays"
                       type="number"
                       class="form-input"
                       min="1"
                       max="365">
              </div>
            </div>
          </div>
        </div>

        <!-- 日志设置 -->
        <div v-if="activeSection === 'logging'" class="setting-section">
          <h2 class="section-title">日志设置</h2>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">日志配置</h3>
            </div>
            <div class="card-body">
              <div class="form-group">
                <label class="form-label">日志级别</label>
                <select v-model="settings.logging.level" class="form-select">
                  <option value="debug">调试 (DEBUG)</option>
                  <option value="info">信息 (INFO)</option>
                  <option value="warning">警告 (WARNING)</option>
                  <option value="error">错误 (ERROR)</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-checkbox">
                  <input v-model="settings.logging.enableFileLog" type="checkbox">
                  <span>保存到文件</span>
                </label>
              </div>

              <div class="form-group">
                <label class="form-label">日志文件大小限制 (MB)</label>
                <input
                       v-model.number="settings.logging.maxFileSize"
                       type="number"
                       class="form-input"
                       min="1"
                       max="1000">
              </div>

              <div class="form-group">
                <label class="form-label">日志文件保留数量</label>
                <input
                       v-model.number="settings.logging.maxFiles"
                       type="number"
                       class="form-input"
                       min="1"
                       max="100">
              </div>

              <div class="form-group">
                <button @click="clearLogs" class="btn btn-warning">
                  <span>[删除]</span>
                  清理日志
                </button>
                <button @click="exportLogs" class="btn btn-secondary">
                  <span>📤</span>
                  导出日志
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 关于 -->
        <div v-if="activeSection === 'about'" class="setting-section">
          <h2 class="section-title">关于</h2>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">应用信息</h3>
            </div>
            <div class="card-body">
              <div class="about-info">
                <div class="app-logo">
                  <span class="logo-icon">🌐</span>
                  <h3>QW Browser</h3>
                </div>

                <div class="app-details">
                  <div class="detail-item">
                    <span class="detail-label">版本:</span>
                    <span class="detail-value">{{ appInfo.version }}</span>
                  </div>

                  <div class="detail-item">
                    <span class="detail-label">构建时间:</span>
                    <span class="detail-value">{{ appInfo.buildDate }}</span>
                  </div>

                  <div class="detail-item">
                    <span class="detail-label">Electron版本:</span>
                    <span class="detail-value">{{ appInfo.electronVersion }}</span>
                  </div>

                  <div class="detail-item">
                    <span class="detail-label">Node.js版本:</span>
                    <span class="detail-value">{{ appInfo.nodeVersion }}</span>
                  </div>

                  <div class="detail-item">
                    <span class="detail-label">Chrome版本:</span>
                    <span class="detail-value">{{ appInfo.chromeVersion }}</span>
                  </div>
                </div>

                <div class="app-actions">
                  <button @click="checkUpdates" class="btn btn-primary" :disabled="isCheckingUpdates">
                    <span v-if="isCheckingUpdates" class="loading"></span>
                    <span v-else>🔄</span>
                    检查更新
                  </button>

                  <button @click="openLicense" class="btn btn-secondary">
                    <span>[DOC]</span>
                    许可证
                  </button>

                  <button @click="openHomepage" class="btn btn-secondary">
                    <span>[WEB]</span>
                    官网
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue';

export default {
  name: 'Settings',
  setup() {
    const isSaving = ref(false);
    const isCheckingUpdates = ref(false);
    const activeSection = ref('general');

    // 设置分类
    const settingSections = [
      { key: 'general', label: '通用', icon: '[SETTINGS]' },
      { key: 'browser', label: '浏览器', icon: '[BROWSER]' },
      { key: 'performance', label: '性能', icon: '[PERF]' },
      { key: 'security', label: '安全', icon: '[LOCK]' },
      { key: 'logging', label: '日志', icon: '[LOG]' },
      { key: 'about', label: '关于', icon: '[INFO]' }
    ];

    // 设置数据
    const settings = reactive({
      general: {
        language: 'zh-CN',
        theme: 'light',
        autoStart: false,
        minimizeToTray: true,
        closeToTray: false,
        autoUpdate: true,
        updateFrequency: 'weekly'
      },
      browser: {
        defaultType: 'chrome',
        defaultWidth: 1280,
        defaultHeight: 720,
        headless: false,
        disableImages: false,
        disableJavaScript: false,
        useProxy: false,
        proxyType: 'http',
        proxyHost: '',
        proxyPort: 8080,
        proxyUsername: '',
        proxyPassword: ''
      },
      performance: {
        maxBrowsers: 5,
        memoryLimit: 2048,
        cpuLimit: 80,
        enableCache: true,
        cacheSize: 500
      },
      security: {
        requireAuth: false,
        username: '',
        password: '',
        enableHttps: false,
        allowedIPs: '',
        encryptData: false,
        autoBackup: true,
        backupRetentionDays: 30
      },
      logging: {
        level: 'info',
        enableFileLog: true,
        maxFileSize: 10,
        maxFiles: 5
      }
    });

    // 应用信息
    const appInfo = reactive({
      version: '1.0.0',
      buildDate: '2024-01-01',
      electronVersion: '28.0.0',
      nodeVersion: '18.20.0',
      chromeVersion: '120.0.0'
    });

    // 加载设置
    const loadSettings = async () => {
      try {
        if (window.httpAPI) {
          const data = await window.httpAPI.get('/api/settings');
          Object.assign(settings, data.settings || {});
        }
      } catch (error) {
        console.error('加载设置失败:', error);
      }
    };

    // 保存所有设置
    const saveAllSettings = async () => {
      try {
        isSaving.value = true;
        if (window.httpAPI) {
          await window.httpAPI.post('/api/settings', settings);
          // 显示成功提示
          if (window.electronAPI?.showNotification) {
            window.electronAPI.showNotification('设置已保存', '所有设置已成功保存');
          }
        }
      } catch (error) {
        console.error('保存设置失败:', error);
        // 显示错误提示
        if (window.electronAPI?.showNotification) {
          window.electronAPI.showNotification('保存失败', '设置保存时发生错误');
        }
      } finally {
        isSaving.value = false;
      }
    };

    // 重置设置
    const resetSettings = async () => {
      if (!confirm('确定要重置所有设置到默认值吗？')) return;

      try {
        if (window.httpAPI) {
          await window.httpAPI.post('/api/settings/reset');
          await loadSettings();
        }
      } catch (error) {
        console.error('重置设置失败:', error);
      }
    };

    // 清理缓存
    const clearCache = async () => {
      if (!confirm('确定要清理所有缓存吗？')) return;

      try {
        if (window.httpAPI) {
          await window.httpAPI.post('/api/cache/clear');
          if (window.electronAPI?.showNotification) {
            window.electronAPI.showNotification('缓存已清理', '所有缓存文件已被删除');
          }
        }
      } catch (error) {
        console.error('清理缓存失败:', error);
      }
    };

    // 清理日志
    const clearLogs = async () => {
      if (!confirm('确定要清理所有日志吗？')) return;

      try {
        if (window.httpAPI) {
          await window.httpAPI.post('/api/logs/clear');
          if (window.electronAPI?.showNotification) {
            window.electronAPI.showNotification('日志已清理', '所有日志文件已被删除');
          }
        }
      } catch (error) {
        console.error('清理日志失败:', error);
      }
    };

    // 导出日志
    const exportLogs = async () => {
      try {
        if (window.electronAPI?.showSaveDialog) {
          const result = await window.electronAPI.showSaveDialog({
            title: '导出日志',
            defaultPath: `logs_${new Date().toISOString().split('T')[0]}.zip`,
            filters: [
              { name: 'ZIP文件', extensions: ['zip'] }
            ]
          });

          if (!result.canceled && result.filePath) {
            if (window.httpAPI) {
              await window.httpAPI.post('/api/logs/export', {
                filePath: result.filePath
              });

              if (window.electronAPI?.showNotification) {
                window.electronAPI.showNotification('导出成功', `日志已导出到 ${result.filePath}`);
              }
            }
          }
        }
      } catch (error) {
        console.error('导出日志失败:', error);
      }
    };

    // 检查更新
    const checkUpdates = async () => {
      try {
        isCheckingUpdates.value = true;
        if (window.httpAPI) {
          const result = await window.httpAPI.get('/api/updates/check');
          if (result.hasUpdate) {
            if (confirm(`发现新版本 ${result.version}，是否立即更新？`)) {
              await window.httpAPI.post('/api/updates/install');
            }
          } else {
            if (window.electronAPI?.showNotification) {
              window.electronAPI.showNotification('已是最新版本', '当前版本已是最新版本');
            }
          }
        }
      } catch (error) {
        console.error('检查更新失败:', error);
      } finally {
        isCheckingUpdates.value = false;
      }
    };

    // 打开许可证
    const openLicense = () => {
      if (window.electronAPI?.openExternal) {
        window.electronAPI.openExternal('https://github.com/your-repo/LICENSE');
      }
    };

    // 打开官网
    const openHomepage = () => {
      if (window.electronAPI?.openExternal) {
        window.electronAPI.openExternal('https://your-website.com');
      }
    };

    // 获取应用信息
    const getAppInfo = async () => {
      try {
        if (window.electronAPI?.getAppInfo) {
          const info = await window.electronAPI.getAppInfo();
          Object.assign(appInfo, info);
        }
      } catch (error) {
        console.error('获取应用信息失败:', error);
      }
    };

    // 生命周期
    onMounted(() => {
      loadSettings();
      getAppInfo();
    });

    return {
      isSaving,
      isCheckingUpdates,
      activeSection,
      settingSections,
      settings,
      appInfo,
      saveAllSettings,
      resetSettings,
      clearCache,
      clearLogs,
      exportLogs,
      checkUpdates,
      openLicense,
      openHomepage
    };
  }
};
</script>

<style scoped>
.settings {
  padding: 24px;
  height: 100%;
  overflow: hidden;
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

.settings-content {
  display: flex;
  height: calc(100% - 80px);
  gap: 24px;
}

.settings-sidebar {
  width: 240px;
  flex-shrink: 0;
}

.settings-nav {
  background: white;
  border-radius: 12px;
  padding: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  background: none;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  margin-bottom: 4px;
}

.nav-item:hover {
  background: #f5f5f5;
}

.nav-item.active {
  background: #e3f2fd;
  color: #1976d2;
}

.nav-icon {
  font-size: 18px;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

.settings-main {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
}

.setting-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-separator {
  font-size: 16px;
  color: #666;
}

.form-help {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.proxy-config,
.auth-config {
  margin-top: 16px;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
}

/* 关于页面 */
.about-info {
  text-align: center;
}

.app-logo {
  margin-bottom: 32px;
}

.logo-icon {
  font-size: 64px;
  display: block;
  margin-bottom: 16px;
}

.app-logo h3 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.app-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 32px;
  text-align: left;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-label {
  font-weight: 500;
  color: #666;
}

.detail-value {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  color: #333;
}

.app-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* 滚动条样式 */
.settings-main::-webkit-scrollbar {
  width: 6px;
}

.settings-main::-webkit-scrollbar-track {
  background: transparent;
}

.settings-main::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.settings-main::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>