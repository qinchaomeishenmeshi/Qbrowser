/**
 * @file config-validator.js
 * @description 配置验证和测试脚本
 */

// =================================================================================
// #region Configuration Schema Definition
// =================================================================================

/**
 * 配置文件的JSON Schema定义
 */
const CONFIG_SCHEMA = {
  type: 'object',
  required: ['domains', 'urls', 'timeouts', 'delays', 'selectors', 'ui', 'http', 'business'],
  properties: {
    domains: {
      type: 'object',
      required: ['douyin', 'target_domains'],
      properties: {
        douyin: {
          type: 'array',
          items: { type: 'string', format: 'uri' },
          minItems: 1
        },
        target_domains: {
          type: 'array',
          items: { type: 'string' },
          minItems: 1
        }
      }
    },
    urls: {
      type: 'object',
      required: ['commodity_detail_base', 'punish_list_api', 'buyin_create_url'],
      properties: {
        commodity_detail_base: { type: 'string', format: 'uri' },
        punish_list_api: { type: 'string', format: 'uri' },
        buyin_create_url: { type: 'string', format: 'uri' },
        referer_template: { type: 'string' }
      }
    },
    timeouts: {
      type: 'object',
      required: ['element_wait', 'api_request', 'page_load'],
      properties: {
        element_wait: { type: 'number', minimum: 1000, maximum: 60000 },
        api_request: { type: 'number', minimum: 1000, maximum: 60000 },
        page_load: { type: 'number', minimum: 1000, maximum: 30000 }
      }
    },
    delays: {
      type: 'object',
      required: ['dom_operation', 'page_load', 'api_request', 'ui_animation'],
      properties: {
        dom_operation: { type: 'number', minimum: 0, maximum: 5000 },
        page_load: { type: 'number', minimum: 0, maximum: 10000 },
        api_request: { type: 'number', minimum: 0, maximum: 2000 },
        ui_animation: { type: 'number', minimum: 0, maximum: 1000 },
        random_min: { type: 'number', minimum: 0 },
        random_max: { type: 'number', minimum: 0 }
      }
    },
    selectors: {
      type: 'object',
      required: ['sync_button_container', 'account_panel'],
      properties: {
        sync_button_container: { type: 'string', minLength: 1 },
        account_panel: { type: 'string', minLength: 1 },
        product_list: { type: 'string', minLength: 1 },
        modal_content: { type: 'string', minLength: 1 }
      }
    },
    ui: {
      type: 'object',
      required: ['texts', 'styles'],
      properties: {
        texts: {
          type: 'object',
          required: ['sync_button', 'sync_success', 'sync_error'],
          properties: {
            sync_button: { type: 'string', minLength: 1 },
            sync_success: { type: 'string', minLength: 1 },
            sync_error: { type: 'string', minLength: 1 }
          }
        },
        styles: {
          type: 'object',
          required: ['sync_button', 'notification'],
          properties: {
            sync_button: {
              type: 'object',
              properties: {
                background_color: { type: 'string', pattern: '^#[0-9a-fA-F]{6}$' },
                text_color: { type: 'string', pattern: '^#[0-9a-fA-F]{6}$' },
                border_radius: { type: 'string' }
              }
            },
            notification: {
              type: 'object',
              properties: {
                success_color: { type: 'string', pattern: '^#[0-9a-fA-F]{6}$' },
                error_color: { type: 'string', pattern: '^#[0-9a-fA-F]{6}$' },
                warning_color: { type: 'string', pattern: '^#[0-9a-fA-F]{6}$' },
                auto_close_delay: { type: 'number', minimum: 1000, maximum: 10000 }
              }
            }
          }
        }
      }
    },
    http: {
      type: 'object',
      required: ['timeout', 'headers', 'credentials'],
      properties: {
        timeout: { type: 'number', minimum: 5000, maximum: 60000 },
        headers: {
          type: 'object',
          required: ['content_type_json', 'user_agent'],
          properties: {
            content_type_json: { type: 'string' },
            user_agent: { type: 'string', minLength: 10 }
          }
        },
        credentials: { type: 'string', enum: ['same-origin', 'include', 'omit'] }
      }
    },
    business: {
      type: 'object',
      required: ['default_account_info', 'task_types', 'daily_task_time'],
      properties: {
        default_account_info: {
          type: 'object',
          properties: {
            dy_account_no: { type: 'string' },
            dy_account_name: { type: 'string' }
          }
        },
        task_types: {
          type: 'object',
          properties: {
            SYNC_ACCOUNT: { type: 'string' },
            SYNC_PRODUCTS: { type: 'string' },
            SYNC_PUNISH: { type: 'string' },
            DAILY_TASK: { type: 'string' }
          }
        },
        daily_task_time: {
          type: 'object',
          required: ['hour', 'minute'],
          properties: {
            hour: { type: 'number', minimum: 0, maximum: 23 },
            minute: { type: 'number', minimum: 0, maximum: 59 }
          }
        }
      }
    }
  }
};

// #endregion

// =================================================================================
// #region Validation Functions
// =================================================================================

/**
 * 简单的JSON Schema验证器
 */
class SimpleValidator {
  /**
   * 验证数据是否符合schema
   * @param {*} data - 要验证的数据
   * @param {Object} schema - JSON Schema
   * @param {string} path - 当前路径（用于错误信息）
   * @returns {Object} 验证结果
   */
  validate(data, schema, path = '') {
    const errors = [];
    
    try {
      this._validateType(data, schema, path, errors);
      this._validateRequired(data, schema, path, errors);
      this._validateProperties(data, schema, path, errors);
      this._validateArray(data, schema, path, errors);
      this._validateString(data, schema, path, errors);
      this._validateNumber(data, schema, path, errors);
    } catch (error) {
      errors.push({
        path,
        message: `验证过程中发生错误: ${error.message}`
      });
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  _validateType(data, schema, path, errors) {
    if (schema.type) {
      const actualType = Array.isArray(data) ? 'array' : typeof data;
      if (actualType !== schema.type) {
        errors.push({
          path,
          message: `类型错误: 期望 ${schema.type}, 实际 ${actualType}`
        });
      }
    }
  }
  
  _validateRequired(data, schema, path, errors) {
    if (schema.required && schema.type === 'object') {
      for (const requiredField of schema.required) {
        if (!(requiredField in data)) {
          errors.push({
            path: `${path}.${requiredField}`,
            message: `缺少必需字段: ${requiredField}`
          });
        }
      }
    }
  }
  
  _validateProperties(data, schema, path, errors) {
    if (schema.properties && typeof data === 'object' && !Array.isArray(data)) {
      for (const [key, value] of Object.entries(data)) {
        if (schema.properties[key]) {
          const result = this.validate(value, schema.properties[key], `${path}.${key}`);
          errors.push(...result.errors);
        }
      }
    }
  }
  
  _validateArray(data, schema, path, errors) {
    if (Array.isArray(data)) {
      if (schema.minItems && data.length < schema.minItems) {
        errors.push({
          path,
          message: `数组长度不足: 最少需要 ${schema.minItems} 个元素`
        });
      }
      
      if (schema.items) {
        data.forEach((item, index) => {
          const result = this.validate(item, schema.items, `${path}[${index}]`);
          errors.push(...result.errors);
        });
      }
    }
  }
  
  _validateString(data, schema, path, errors) {
    if (typeof data === 'string') {
      if (schema.minLength && data.length < schema.minLength) {
        errors.push({
          path,
          message: `字符串长度不足: 最少需要 ${schema.minLength} 个字符`
        });
      }
      
      if (schema.pattern) {
        const regex = new RegExp(schema.pattern);
        if (!regex.test(data)) {
          errors.push({
            path,
            message: `字符串格式不正确: 不匹配模式 ${schema.pattern}`
          });
        }
      }
      
      if (schema.format === 'uri') {
        try {
          new URL(data);
        } catch {
          errors.push({
            path,
            message: `无效的URI格式: ${data}`
          });
        }
      }
      
      if (schema.enum && !schema.enum.includes(data)) {
        errors.push({
          path,
          message: `值不在允许的枚举中: ${data}, 允许的值: ${schema.enum.join(', ')}`
        });
      }
    }
  }
  
  _validateNumber(data, schema, path, errors) {
    if (typeof data === 'number') {
      if (schema.minimum !== undefined && data < schema.minimum) {
        errors.push({
          path,
          message: `数值过小: ${data} < ${schema.minimum}`
        });
      }
      
      if (schema.maximum !== undefined && data > schema.maximum) {
        errors.push({
          path,
          message: `数值过大: ${data} > ${schema.maximum}`
        });
      }
    }
  }
}

// #endregion

// =================================================================================
// #region Test Functions
// =================================================================================

/**
 * 配置验证器类
 */
class ConfigValidator {
  constructor() {
    this.validator = new SimpleValidator();
  }
  
  /**
   * 验证配置文件
   * @param {Object} config - 配置对象
   * @returns {Object} 验证结果
   */
  validateConfig(config) {
    console.log('🔍 开始验证配置文件...');
    
    const result = this.validator.validate(config, CONFIG_SCHEMA);
    
    if (result.valid) {
      console.log('✅ 配置文件验证通过');
    } else {
      console.log('❌ 配置文件验证失败:');
      result.errors.forEach(error => {
        console.log(`  - ${error.path}: ${error.message}`);
      });
    }
    
    return result;
  }
  
  /**
   * 验证配置完整性
   * @param {Object} config - 配置对象
   * @returns {Object} 验证结果
   */
  validateCompleteness(config) {
    console.log('🔍 检查配置完整性...');
    
    const issues = [];
    
    // 检查URL的可访问性（模拟）
    const urls = this._extractUrls(config);
    urls.forEach(url => {
      if (!this._isValidUrl(url)) {
        issues.push(`无效的URL: ${url}`);
      }
    });
    
    // 检查CSS选择器格式
    const selectors = config.selectors || {};
    Object.entries(selectors).forEach(([key, selector]) => {
      if (!this._isValidCssSelector(selector)) {
        issues.push(`无效的CSS选择器 ${key}: ${selector}`);
      }
    });
    
    // 检查颜色值格式
    const colors = this._extractColors(config);
    colors.forEach(({ path, color }) => {
      if (!this._isValidColor(color)) {
        issues.push(`无效的颜色值 ${path}: ${color}`);
      }
    });
    
    // 检查时间配置的合理性
    this._validateTimeConfig(config, issues);
    
    if (issues.length === 0) {
      console.log('✅ 配置完整性检查通过');
    } else {
      console.log('⚠️ 配置完整性检查发现问题:');
      issues.forEach(issue => {
        console.log(`  - ${issue}`);
      });
    }
    
    return {
      valid: issues.length === 0,
      issues
    };
  }
  
  /**
   * 性能测试
   * @param {Object} config - 配置对象
   * @returns {Object} 测试结果
   */
  performanceTest(config) {
    console.log('🚀 开始性能测试...');
    
    const results = {};
    
    // 测试配置加载时间
    const loadStart = performance.now();
    const configStr = JSON.stringify(config);
    const parsedConfig = JSON.parse(configStr);
    const loadTime = performance.now() - loadStart;
    
    results.loadTime = loadTime;
    results.configSize = new Blob([configStr]).size;
    
    // 测试配置访问性能
    const accessStart = performance.now();
    for (let i = 0; i < 1000; i++) {
      const _ = parsedConfig.domains.douyin[0];
      const __ = parsedConfig.ui.texts.sync_button;
      const ___ = parsedConfig.timeouts.api_request;
    }
    const accessTime = performance.now() - accessStart;
    
    results.accessTime = accessTime;
    
    console.log('📊 性能测试结果:');
    console.log(`  - 配置大小: ${results.configSize} bytes`);
    console.log(`  - 加载时间: ${results.loadTime.toFixed(2)} ms`);
    console.log(`  - 访问性能: ${results.accessTime.toFixed(2)} ms (1000次访问)`);
    
    // 性能评估
    const performance_issues = [];
    if (results.configSize > 50000) {
      performance_issues.push('配置文件过大，可能影响加载性能');
    }
    if (results.loadTime > 10) {
      performance_issues.push('配置加载时间过长');
    }
    
    if (performance_issues.length > 0) {
      console.log('⚠️ 性能问题:');
      performance_issues.forEach(issue => {
        console.log(`  - ${issue}`);
      });
    } else {
      console.log('✅ 性能测试通过');
    }
    
    return {
      ...results,
      issues: performance_issues
    };
  }
  
  /**
   * 运行所有测试
   * @param {Object} config - 配置对象
   * @returns {Object} 综合测试结果
   */
  runAllTests(config) {
    console.log('🧪 开始配置文件综合测试...');
    console.log('='.repeat(50));
    
    const results = {
      schema: this.validateConfig(config),
      completeness: this.validateCompleteness(config),
      performance: this.performanceTest(config)
    };
    
    console.log('='.repeat(50));
    
    const allValid = results.schema.valid && 
                    results.completeness.valid && 
                    results.performance.issues.length === 0;
    
    if (allValid) {
      console.log('🎉 所有测试通过！配置文件可以安全使用。');
    } else {
      console.log('❌ 测试发现问题，请检查并修复后重新测试。');
    }
    
    return {
      ...results,
      overall: allValid
    };
  }
  
  // 辅助方法
  _extractUrls(config) {
    const urls = [];
    
    if (config.domains?.douyin) {
      urls.push(...config.domains.douyin);
    }
    
    if (config.urls) {
      Object.values(config.urls).forEach(url => {
        if (typeof url === 'string') {
          urls.push(url);
        }
      });
    }
    
    return urls;
  }
  
  _extractColors(config) {
    const colors = [];
    
    const extractFromObject = (obj, path = '') => {
      for (const [key, value] of Object.entries(obj)) {
        const currentPath = path ? `${path}.${key}` : key;
        
        if (typeof value === 'string' && key.includes('color')) {
          colors.push({ path: currentPath, color: value });
        } else if (typeof value === 'object' && value !== null) {
          extractFromObject(value, currentPath);
        }
      }
    };
    
    if (config.ui?.styles) {
      extractFromObject(config.ui.styles, 'ui.styles');
    }
    
    return colors;
  }
  
  _isValidUrl(url) {
    try {
      new URL(url.replace('*', ''));
      return true;
    } catch {
      return false;
    }
  }
  
  _isValidCssSelector(selector) {
    try {
      document.querySelector(selector);
      return true;
    } catch {
      // 在Node.js环境中，简单检查格式
      return selector.length > 0 && !selector.includes('  ');
    }
  }
  
  _isValidColor(color) {
    return /^#[0-9a-fA-F]{6}$/.test(color);
  }
  
  _validateTimeConfig(config, issues) {
    const timeouts = config.timeouts || {};
    const delays = config.delays || {};
    
    // 检查超时时间是否合理
    if (timeouts.api_request && timeouts.api_request < 5000) {
      issues.push('API请求超时时间过短，可能导致请求失败');
    }
    
    if (timeouts.element_wait && timeouts.element_wait > 60000) {
      issues.push('元素等待超时时间过长，可能影响用户体验');
    }
    
    // 检查延迟时间是否合理
    if (delays.random_min && delays.random_max && delays.random_min >= delays.random_max) {
      issues.push('随机延迟配置错误: random_min 应该小于 random_max');
    }
    
    // 检查每日任务时间
    const dailyTask = config.business?.daily_task_time;
    if (dailyTask) {
      if (dailyTask.hour < 0 || dailyTask.hour > 23) {
        issues.push('每日任务小时配置错误: 应该在0-23之间');
      }
      if (dailyTask.minute < 0 || dailyTask.minute > 59) {
        issues.push('每日任务分钟配置错误: 应该在0-59之间');
      }
    }
  }
}

// #endregion

// =================================================================================
// #region Main Function
// =================================================================================

/**
 * 主函数 - 加载并验证配置文件
 */
async function main() {
  try {
    // 加载配置文件
    let config;
    
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      // Chrome扩展环境
      const configUrl = chrome.runtime.getURL('app-config.json');
      const response = await fetch(configUrl);
      config = await response.json();
    } else if (typeof require !== 'undefined') {
      // Node.js环境
      const fs = require('fs');
      const path = require('path');
      const configPath = path.join(__dirname, 'app-config.json');
      const configContent = fs.readFileSync(configPath, 'utf8');
      config = JSON.parse(configContent);
    } else {
      throw new Error('不支持的运行环境');
    }
    
    // 运行验证
    const validator = new ConfigValidator();
    const results = validator.runAllTests(config);
    
    return results;
    
  } catch (error) {
    console.error('❌ 配置验证失败:', error);
    return {
      error: error.message,
      overall: false
    };
  }
}

// #endregion

// =================================================================================
// #region Exports
// =================================================================================

if (typeof module !== 'undefined' && module.exports) {
  // Node.js环境
  module.exports = {
    ConfigValidator,
    CONFIG_SCHEMA,
    main
  };
} else {
  // 浏览器环境
  window.ConfigValidator = ConfigValidator;
  window.CONFIG_SCHEMA = CONFIG_SCHEMA;
  window.validateConfig = main;
}

// 如果直接运行此脚本
if (typeof require !== 'undefined' && require.main === module) {
  main().then(results => {
    process.exit(results.overall ? 0 : 1);
  });
}

// #endregion