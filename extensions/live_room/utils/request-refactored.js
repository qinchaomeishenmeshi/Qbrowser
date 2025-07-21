/**
 * @file request-refactored.js
 * @description 重构后的请求工具文件，使用配置管理器替换硬编码配置
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
    console.log('✅ Request 配置加载完成');
  } catch (error) {
    console.error('❌ Request 配置加载失败:', error);
    // 使用默认配置
    config = getDefaultConfig();
  }
}

/**
 * 获取默认配置（备用）
 */
function getDefaultConfig() {
  return {
    http: {
      timeout: 30000,
      headers: {
        content_type_json: "application/json",
        user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
      },
      credentials: "same-origin"
    },
    urls: {
      commodity_detail_base: "https://haohuo.jinritemai.com/aweme/v2/shop/promotion/pack/detail/",
      referer_template: "https://haohuo.jinritemai.com/ecommerce/trade/detail/index.html?id={id}"
    },
    delays: {
      api_request: 500,
      random_min: 1000,
      random_max: 3000
    }
  };
}

// 初始化配置
initializeConfig();

// #endregion

// =================================================================================
// #region Error Handling
// =================================================================================

/**
 * 统一错误处理函数
 * @param {Error} error - 错误对象
 * @param {string} context - 错误上下文
 * @param {Object} additionalInfo - 额外信息
 */
function $handleError(error, context = '', additionalInfo = {}) {
  const errorInfo = {
    message: error.message || '未知错误',
    context,
    timestamp: new Date().toISOString(),
    stack: error.stack,
    ...additionalInfo
  };
  
  console.error(`[${context}] 错误:`, errorInfo);
  
  // 可以在这里添加错误上报逻辑
  // reportError(errorInfo);
  
  return errorInfo;
}

// #endregion

// =================================================================================
// #region HTTP Request Utilities
// =================================================================================

/**
 * 获取HTTP配置
 */
function getHttpConfig() {
  return config?.http || getDefaultConfig().http;
}

/**
 * 获取URL配置
 */
function getUrlConfig() {
  return config?.urls || getDefaultConfig().urls;
}

/**
 * 获取延迟配置
 */
function getDelayConfig() {
  return config?.delays || getDefaultConfig().delays;
}

/**
 * 生成随机延迟时间
 * @returns {number} 随机延迟时间（毫秒）
 */
function getRandomDelay() {
  const delayConfig = getDelayConfig();
  const min = delayConfig.random_min;
  const max = delayConfig.random_max;
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * 延迟执行函数
 * @param {number} ms - 延迟时间（毫秒）
 * @returns {Promise} Promise对象
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 通用AJAX请求函数
 * @param {Object} options - 请求选项
 * @returns {Promise} 请求结果
 */
async function $ajax(options = {}) {
  const httpConfig = getHttpConfig();
  
  const defaultOptions = {
    method: 'GET',
    headers: {
      'Content-Type': httpConfig.headers.content_type_json,
      'User-Agent': httpConfig.headers.user_agent
    },
    timeout: httpConfig.timeout,
    credentials: httpConfig.credentials
  };
  
  const finalOptions = { ...defaultOptions, ...options };
  
  try {
    // 添加请求前延迟
    const delayConfig = getDelayConfig();
    await delay(delayConfig.api_request);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), finalOptions.timeout);
    
    const response = await fetch(finalOptions.url, {
      ...finalOptions,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return { success: true, data };
    
  } catch (error) {
    const errorInfo = $handleError(error, 'AJAX请求', {
      url: finalOptions.url,
      method: finalOptions.method,
      options: finalOptions
    });
    
    return { success: false, error: errorInfo };
  }
}

/**
 * Chrome扩展消息请求函数
 * @param {Object} requestData - 请求数据
 * @returns {Promise} 请求结果
 */
function $Request(requestData) {
  return new Promise((resolve, reject) => {
    try {
      chrome.runtime.sendMessage(requestData, (response) => {
        if (chrome.runtime.lastError) {
          const error = new Error(chrome.runtime.lastError.message);
          const errorInfo = $handleError(error, 'Chrome消息请求', { requestData });
          reject(errorInfo);
        } else if (response && response.success) {
          resolve(response.data);
        } else {
          const error = new Error(response?.error || '请求失败');
          const errorInfo = $handleError(error, 'Chrome消息响应', { 
            requestData, 
            response 
          });
          reject(errorInfo);
        }
      });
    } catch (error) {
      const errorInfo = $handleError(error, 'Chrome消息发送', { requestData });
      reject(errorInfo);
    }
  });
}

// #endregion

// =================================================================================
// #region Business API Functions
// =================================================================================

/**
 * 获取商品详情
 * @param {string} productId - 商品ID
 * @param {Object} options - 额外选项
 * @returns {Promise} 商品详情数据
 */
async function getCommodityDetail(productId, options = {}) {
  if (!productId) {
    throw new Error('商品ID不能为空');
  }
  
  const urlConfig = getUrlConfig();
  const httpConfig = getHttpConfig();
  
  const url = `${urlConfig.commodity_detail_base}${productId}`;
  const referer = urlConfig.referer_template.replace('{id}', productId);
  
  const requestOptions = {
    method: 'GET',
    headers: {
      'Content-Type': httpConfig.headers.content_type_json,
      'User-Agent': httpConfig.headers.user_agent,
      'Referer': referer,
      ...options.headers
    },
    url,
    ...options
  };
  
  try {
    // 添加随机延迟以避免频率限制
    const randomDelay = getRandomDelay();
    await delay(randomDelay);
    
    const result = await $ajax(requestOptions);
    
    if (result.success) {
      console.log(`✅ 成功获取商品详情: ${productId}`);
      return result.data;
    } else {
      throw new Error(result.error.message || '获取商品详情失败');
    }
    
  } catch (error) {
    $handleError(error, '获取商品详情', { productId, options });
    throw error;
  }
}

/**
 * 获取产品详情（通过Chrome扩展消息）
 * @param {string} productId - 产品ID
 * @param {Object} options - 额外选项
 * @returns {Promise} 产品详情数据
 */
async function getProductDetail(productId, options = {}) {
  if (!productId) {
    throw new Error('产品ID不能为空');
  }
  
  const urlConfig = getUrlConfig();
  const httpConfig = getHttpConfig();
  
  const url = `${urlConfig.commodity_detail_base}${productId}`;
  const referer = urlConfig.referer_template.replace('{id}', productId);
  
  const requestData = {
    action: "FETCH_PRODUCT_DETAIL",
    data: {
      url,
      options: {
        method: 'GET',
        headers: {
          'Content-Type': httpConfig.headers.content_type_json,
          'User-Agent': httpConfig.headers.user_agent,
          'Referer': referer,
          ...options.headers
        },
        credentials: httpConfig.credentials,
        ...options
      }
    }
  };
  
  try {
    // 添加随机延迟
    const randomDelay = getRandomDelay();
    await delay(randomDelay);
    
    const result = await $Request(requestData);
    console.log(`✅ 成功获取产品详情: ${productId}`);
    return result;
    
  } catch (error) {
    $handleError(error, '获取产品详情', { productId, options });
    throw error;
  }
}

/**
 * 批量获取产品详情
 * @param {Array} productIds - 产品ID数组
 * @param {Object} options - 选项
 * @returns {Promise} 产品详情数组
 */
async function getProductDetailsBatch(productIds, options = {}) {
  if (!Array.isArray(productIds) || productIds.length === 0) {
    throw new Error('产品ID数组不能为空');
  }
  
  const {
    concurrency = 3, // 并发数
    retryCount = 2,  // 重试次数
    onProgress = null // 进度回调
  } = options;
  
  const results = [];
  const errors = [];
  
  // 分批处理
  for (let i = 0; i < productIds.length; i += concurrency) {
    const batch = productIds.slice(i, i + concurrency);
    
    const batchPromises = batch.map(async (productId, index) => {
      let lastError = null;
      
      // 重试逻辑
      for (let retry = 0; retry <= retryCount; retry++) {
        try {
          const result = await getProductDetail(productId);
          return { productId, data: result, success: true };
        } catch (error) {
          lastError = error;
          if (retry < retryCount) {
            // 重试前等待
            await delay(1000 * (retry + 1));
          }
        }
      }
      
      return { productId, error: lastError, success: false };
    });
    
    const batchResults = await Promise.all(batchPromises);
    
    batchResults.forEach(result => {
      if (result.success) {
        results.push(result);
      } else {
        errors.push(result);
      }
    });
    
    // 进度回调
    if (onProgress) {
      onProgress({
        completed: i + batch.length,
        total: productIds.length,
        successCount: results.length,
        errorCount: errors.length
      });
    }
    
    // 批次间延迟
    if (i + concurrency < productIds.length) {
      await delay(getRandomDelay());
    }
  }
  
  return {
    success: results,
    errors,
    total: productIds.length,
    successCount: results.length,
    errorCount: errors.length
  };
}

// #endregion

// =================================================================================
// #region Configuration Helpers
// =================================================================================

/**
 * 更新HTTP配置
 * @param {Object} newConfig - 新的HTTP配置
 */
function updateHttpConfig(newConfig) {
  if (config && config.http) {
    config.http = { ...config.http, ...newConfig };
  }
}

/**
 * 获取当前配置
 * @returns {Object} 当前配置对象
 */
function getCurrentConfig() {
  return config || getDefaultConfig();
}

/**
 * 重新加载配置
 */
async function reloadConfig() {
  try {
    config = await configManager.loadConfig();
    console.log('✅ Request 配置重新加载完成');
    return true;
  } catch (error) {
    console.error('❌ Request 配置重新加载失败:', error);
    return false;
  }
}

// #endregion

// =================================================================================
// #region Exports
// =================================================================================

// 导出函数（保持向后兼容）
if (typeof module !== 'undefined' && module.exports) {
  // Node.js 环境
  module.exports = {
    $handleError,
    $ajax,
    $Request,
    getCommodityDetail,
    getProductDetail,
    getProductDetailsBatch,
    delay,
    getRandomDelay,
    updateHttpConfig,
    getCurrentConfig,
    reloadConfig,
    getHttpConfig,
    getUrlConfig,
    getDelayConfig
  };
} else {
  // 浏览器环境 - 将函数添加到全局作用域
  window.$handleError = $handleError;
  window.$ajax = $ajax;
  window.$Request = $Request;
  window.getCommodityDetail = getCommodityDetail;
  window.getProductDetail = getProductDetail;
  window.getProductDetailsBatch = getProductDetailsBatch;
  window.delay = delay;
  window.getRandomDelay = getRandomDelay;
  window.updateHttpConfig = updateHttpConfig;
  window.getCurrentConfig = getCurrentConfig;
  window.reloadConfig = reloadConfig;
  window.getHttpConfig = getHttpConfig;
  window.getUrlConfig = getUrlConfig;
  window.getDelayConfig = getDelayConfig;
}

// #endregion