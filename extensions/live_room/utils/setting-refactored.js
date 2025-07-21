/**
 * @file setting-refactored.js
 * @description 重构后的设置文件，使用配置管理器替换硬编码配置
 */

// =================================================================================
// #region Configuration Manager Integration
// =================================================================================

// 全局配置管理器实例
let config = null;

/**
 * 初始化配置
 */
async function initializeConfig() {
  try {
    // 确保配置管理器已加载
    if (typeof configManager === 'undefined') {
      const configUrl = chrome.runtime.getURL('utils/config-manager.js');
      await import(configUrl);
    }
    
    // 加载配置
    config = await configManager.loadConfig();
    console.log('✅ Setting 配置加载完成');
  } catch (error) {
    console.error('❌ Setting 配置加载失败:', error);
    // 使用默认配置
    config = getDefaultConfig();
  }
}

/**
 * 获取默认配置（备用）
 */
function getDefaultConfig() {
  return {
    delays: {
      dom_operation: 1000,
      page_load: 2000,
      api_request: 500,
      ui_animation: 300
    },
    business: {
      task_types: {
        SYNC_ACCOUNT: 'SYNC_ACCOUNT',
        SYNC_PRODUCTS: 'SYNC_PRODUCTS',
        SYNC_PUNISH: 'SYNC_PUNISH',
        DAILY_TASK: 'DAILY_TASK'
      }
    },
    api: {
      base_url: 'http://localhost:3000/api',
      endpoints: {
        get_task: '/task/get',
        sync_account: '/account/sync',
        save_products: '/products/save',
        save_punish: '/punish/save',
        get_punish_list: '/punish/list'
      }
    },
    pages: {
      douyin_creator: 'https://creator.douyin.com'
    }
  };
}

// 初始化配置
initializeConfig();

// #endregion

// =================================================================================
// #region Configuration Getters
// =================================================================================

/**
 * 获取延迟配置
 */
function getDelayConfig() {
  return config?.delays || getDefaultConfig().delays;
}

/**
 * 获取任务类型枚举
 */
function getTaskTypeEnums() {
  return config?.business?.task_types || getDefaultConfig().business.task_types;
}

/**
 * 获取API配置
 */
function getApiConfig() {
  const defaultApi = getDefaultConfig().api;
  const configApi = config?.api || {};
  
  return {
    base_url: configApi.base_url || defaultApi.base_url,
    endpoints: { ...defaultApi.endpoints, ...configApi.endpoints }
  };
}

/**
 * 获取页面配置
 */
function getPageConfig() {
  return config?.pages || getDefaultConfig().pages;
}

// #endregion

// =================================================================================
// #region Legacy Compatibility (保持向后兼容)
// =================================================================================

/**
 * 延迟配置对象（保持原有接口）
 */
const DELAY = new Proxy({}, {
  get(target, prop) {
    const delays = getDelayConfig();
    // 映射原有的属性名到新的配置结构
    const mapping = {
      DOM_OPERATION: 'dom_operation',
      PAGE_LOAD: 'page_load',
      API_REQUEST: 'api_request',
      UI_ANIMATION: 'ui_animation'
    };
    
    const configKey = mapping[prop] || prop.toLowerCase();
    return delays[configKey] || delays.dom_operation; // 默认值
  }
});

/**
 * 任务类型枚举（保持原有接口）
 */
const taskTypeEnums = new Proxy({}, {
  get(target, prop) {
    const taskTypes = getTaskTypeEnums();
    return taskTypes[prop] || prop;
  }
});

/**
 * API配置对象（保持原有接口）
 */
const API = new Proxy({}, {
  get(target, prop) {
    const apiConfig = getApiConfig();
    
    // 处理完整URL的构建
    if (prop in apiConfig.endpoints) {
      return `${apiConfig.base_url}${apiConfig.endpoints[prop]}`;
    }
    
    // 处理直接的URL配置
    const urlMapping = {
      GET_TASK: 'get_task',
      SYNC_ACCOUNT: 'sync_account',
      SAVE_PRODUCTS_LIST: 'save_products',
      SAVE_PUNISH_INFO: 'save_punish',
      GET_PUNISH_LIST: 'get_punish_list'
    };
    
    const endpointKey = urlMapping[prop];
    if (endpointKey && apiConfig.endpoints[endpointKey]) {
      return `${apiConfig.base_url}${apiConfig.endpoints[endpointKey]}`;
    }
    
    // 返回原始配置或默认值
    return apiConfig[prop] || `${apiConfig.base_url}/${prop.toLowerCase()}`;
  }
});

/**
 * 页面配置对象（保持原有接口）
 */
const PAGE = new Proxy({}, {
  get(target, prop) {
    const pageConfig = getPageConfig();
    
    // 映射原有的属性名
    const mapping = {
      DOUYIN_CREATOR: 'douyin_creator'
    };
    
    const configKey = mapping[prop] || prop.toLowerCase();
    return pageConfig[configKey] || pageConfig.douyin_creator;
  }
});

// #endregion

// =================================================================================
// #region Enhanced Configuration Functions
// =================================================================================

/**
 * 获取配置值的通用函数
 * @param {string} path - 配置路径，如 'delays.dom_operation'
 * @param {*} defaultValue - 默认值
 * @returns {*} 配置值
 */
function getConfigValue(path, defaultValue = null) {
  if (!config) return defaultValue;
  
  const keys = path.split('.');
  let value = config;
  
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
 * 构建完整的API URL
 * @param {string} endpoint - 端点名称
 * @param {Object} params - URL参数
 * @returns {string} 完整的URL
 */
function buildApiUrl(endpoint, params = {}) {
  const apiConfig = getApiConfig();
  let url = `${apiConfig.base_url}${apiConfig.endpoints[endpoint] || `/${endpoint}`}`;
  
  // 添加查询参数
  if (Object.keys(params).length > 0) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }
  
  return url;
}

/**
 * 获取延迟时间
 * @param {string} type - 延迟类型
 * @returns {number} 延迟时间（毫秒）
 */
function getDelay(type) {
  const delays = getDelayConfig();
  return delays[type] || delays.dom_operation;
}

/**
 * 检查是否为目标页面
 * @param {string} url - 当前页面URL
 * @param {string} pageType - 页面类型
 * @returns {boolean} 是否匹配
 */
function isTargetPage(url, pageType) {
  const pageConfig = getPageConfig();
  const targetUrl = pageConfig[pageType];
  
  if (!targetUrl) return false;
  
  return url.includes(targetUrl) || url.startsWith(targetUrl);
}

/**
 * 重新加载配置
 */
async function reloadConfig() {
  try {
    config = await configManager.loadConfig();
    console.log('✅ 配置重新加载完成');
    return true;
  } catch (error) {
    console.error('❌ 配置重新加载失败:', error);
    return false;
  }
}

// #endregion

// =================================================================================
// #region Data Storage Variables (保持原有变量)
// =================================================================================

// 这些变量保持原有的定义方式，用于数据存储
let topicNames = [];
let currentPage = 1;
let maxPage = 1;
let currentAccountList = [];
let accountList = [];

// #endregion

// =================================================================================
// #region Exports
// =================================================================================

// 导出配置对象和函数（保持向后兼容）
if (typeof module !== 'undefined' && module.exports) {
  // Node.js 环境
  module.exports = {
    DELAY,
    taskTypeEnums,
    API,
    PAGE,
    getConfigValue,
    buildApiUrl,
    getDelay,
    isTargetPage,
    reloadConfig,
    getDelayConfig,
    getTaskTypeEnums,
    getApiConfig,
    getPageConfig,
    topicNames,
    currentPage,
    maxPage,
    currentAccountList,
    accountList
  };
} else {
  // 浏览器环境 - 将对象添加到全局作用域
  window.DELAY = DELAY;
  window.taskTypeEnums = taskTypeEnums;
  window.API = API;
  window.PAGE = PAGE;
  window.getConfigValue = getConfigValue;
  window.buildApiUrl = buildApiUrl;
  window.getDelay = getDelay;
  window.isTargetPage = isTargetPage;
  window.reloadConfig = reloadConfig;
  window.getDelayConfig = getDelayConfig;
  window.getTaskTypeEnums = getTaskTypeEnums;
  window.getApiConfig = getApiConfig;
  window.getPageConfig = getPageConfig;
  
  // 数据存储变量
  window.topicNames = topicNames;
  window.currentPage = currentPage;
  window.maxPage = maxPage;
  window.currentAccountList = currentAccountList;
  window.accountList = accountList;
}

// #endregion