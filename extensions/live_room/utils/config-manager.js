/**
 * @file config-manager.js
 * @description 配置管理器，用于加载和管理应用配置
 */

class ConfigManager {
  constructor() {
    this.config = null;
    this.isLoaded = false;
  }

  /**
   * 异步加载配置文件
   * @returns {Promise<Object>} 配置对象
   */
  async loadConfig() {
    if (this.isLoaded && this.config) {
      return this.config;
    }

    try {
      const configUrl = chrome.runtime.getURL('config/app-config.json');
      const response = await fetch(configUrl);
      
      if (!response.ok) {
        throw new Error(`Failed to load config: ${response.status}`);
      }
      
      this.config = await response.json();
      this.isLoaded = true;
      console.log('✅ 配置文件加载成功');
      return this.config;
    } catch (error) {
      console.error('❌ 配置文件加载失败:', error);
      // 返回默认配置以防止应用崩溃
      return this.getDefaultConfig();
    }
  }

  /**
   * 获取配置项
   * @param {string} path - 配置路径，支持点号分隔的嵌套路径
   * @param {*} defaultValue - 默认值
   * @returns {*} 配置值
   */
  get(path, defaultValue = null) {
    if (!this.config) {
      console.warn('配置未加载，返回默认值');
      return defaultValue;
    }

    const keys = path.split('.');
    let value = this.config;
    
    for (const key of keys) {
      if (value && typeof value === 'object' && key in value) {
        value = value[key];
      } else {
        return defaultValue;
      }
    }
    
    return value;
  }

  /**
   * 获取域名配置
   * @returns {Object} 域名配置
   */
  getDomains() {
    return this.get('domains', {});
  }

  /**
   * 获取URL配置
   * @returns {Object} URL配置
   */
  getUrls() {
    return this.get('urls', {});
  }

  /**
   * 获取超时配置
   * @returns {Object} 超时配置
   */
  getTimeouts() {
    return this.get('timeouts', {});
  }

  /**
   * 获取延迟配置
   * @returns {Object} 延迟配置
   */
  getDelays() {
    return this.get('delays', {});
  }

  /**
   * 获取选择器配置
   * @returns {Object} 选择器配置
   */
  getSelectors() {
    return this.get('selectors', {});
  }

  /**
   * 获取UI配置
   * @returns {Object} UI配置
   */
  getUI() {
    return this.get('ui', {});
  }

  /**
   * 获取HTTP配置
   * @returns {Object} HTTP配置
   */
  getHttp() {
    return this.get('http', {});
  }

  /**
   * 获取业务配置
   * @returns {Object} 业务配置
   */
  getBusiness() {
    return this.get('business', {});
  }

  /**
   * 获取消息配置
   * @returns {Object} 消息配置
   */
  getMessages() {
    return this.get('messages', {});
  }

  /**
   * 获取存储键配置
   * @returns {Object} 存储键配置
   */
  getStorageKeys() {
    return this.get('storage_keys', {});
  }

  /**
   * 格式化消息模板
   * @param {string} template - 消息模板
   * @param {Object} params - 参数对象
   * @returns {string} 格式化后的消息
   */
  formatMessage(template, params = {}) {
    if (!template) return '';
    
    return template.replace(/\{(\w+)\}/g, (match, key) => {
      return params[key] !== undefined ? params[key] : match;
    });
  }

  /**
   * 获取格式化的提示消息
   * @param {string} key - 消息键
   * @param {Object} params - 参数对象
   * @returns {string} 格式化后的消息
   */
  getTip(key, params = {}) {
    const template = this.get(`messages.tips.${key}`, key);
    return this.formatMessage(template, params);
  }

  /**
   * 检查是否为目标域名
   * @param {string} hostname - 主机名
   * @param {string} target - 目标类型 (eos, buyin, haohuo)
   * @returns {boolean} 是否匹配
   */
  isTargetHostname(hostname, target) {
    const targetHostname = this.get(`domains.target_hostnames.${target}`);
    return hostname === targetHostname;
  }

  /**
   * 获取默认配置（备用）
   * @returns {Object} 默认配置
   */
  getDefaultConfig() {
    return {
      domains: {
        douyin: [
          "https://haohuo.jinritemai.com/*",
          "https://www.douyin.com/*",
          "https://eos.douyin.com/*",
          "https://buyin.jinritemai.com/*"
        ],
        target_hostnames: {
          eos: "eos.douyin.com",
          buyin: "buyin.jinritemai.com",
          haohuo: "haohuo.jinritemai.com"
        }
      },
      timeouts: {
        account_observer: 10000,
        save_plan_button_observer: 30000,
        sync_container_delay: 3000
      },
      delays: {
        dom_delay: 500,
        page_delay: 3000
      },
      ui: {
        sync_button: {
          text: {
            default: "同步混剪系统",
            loading: "同步中...",
            success: "同步成功",
            error: "同步失败",
            reload: "重新同步"
          }
        }
      },
      messages: {
        tips: {
          account_loading_timeout: "账号信息加载超时，请手动刷新页面",
          sync_complete: "所有商品已处理完毕"
        }
      }
    };
  }

  /**
   * 重新加载配置
   * @returns {Promise<Object>} 新的配置对象
   */
  async reload() {
    this.isLoaded = false;
    this.config = null;
    return await this.loadConfig();
  }

  /**
   * 验证配置完整性
   * @returns {boolean} 配置是否有效
   */
  validateConfig() {
    if (!this.config) return false;
    
    const requiredKeys = ['domains', 'timeouts', 'selectors', 'ui'];
    return requiredKeys.every(key => key in this.config);
  }
}

// 创建全局配置管理器实例
const configManager = new ConfigManager();

// 导出配置管理器
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ConfigManager, configManager };
} else if (typeof window !== 'undefined') {
  window.ConfigManager = ConfigManager;
  window.configManager = configManager;
}