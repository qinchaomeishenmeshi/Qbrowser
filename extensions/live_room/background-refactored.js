/**
 * @file background-refactored.js
 * @description 重构后的后台脚本，使用配置管理器替换硬编码配置
 */

// =================================================================================
// #region Configuration & Initialization
// =================================================================================

// 全局配置管理器实例
let config = null;

/**
 * 初始化配置
 */
async function initializeConfig() {
  try {
    // 加载配置管理器
    const configUrl = chrome.runtime.getURL('utils/config-manager.js');
    await import(configUrl);
    
    // 加载配置
    config = await configManager.loadConfig();
    console.log('✅ Background script 配置加载完成');
  } catch (error) {
    console.error('❌ Background script 配置加载失败:', error);
    // 使用默认配置
    config = getDefaultConfig();
  }
}

/**
 * 获取默认配置（备用）
 */
function getDefaultConfig() {
  return {
    domains: {
      douyin: [
        "https://haohuo.jinritemai.com/*",
        "https://www.douyin.com/*",
        "https://eos.douyin.com/*",
        "https://buyin.jinritemai.com/*"
      ]
    },
    business: {
      daily_task_time: {
        hour: 9,
        minute: 30
      }
    },
    http: {
      headers: {
        content_type_json: "application/json"
      },
      credentials: "same-origin"
    }
  };
}

// 初始化配置
initializeConfig();

// #endregion

// =================================================================================
// #region Tab Management Functions
// =================================================================================

/**
 * 获取抖音标签页
 */
function getDouyinTab() {
  return new Promise((resolve, reject) => {
    const domains = config?.domains?.douyin || getDefaultConfig().domains.douyin;
    
    chrome.tabs.query({ url: domains }, async (tabs) => {
      console.log("查找到的抖音标签页:", tabs);
      if (tabs.length > 0) {
        const tab = tabs[0];
        try {
          await ensureScriptInjected(tab.id);
          if (!tab.active) {
            await chrome.tabs.update(tab.id, { active: true });
          }
          resolve(tab);
        } catch (error) {
          console.error("检测脚本状态时出错:", error);
          reject(error);
        }
      } else {
        reject(new Error("未找到抖音标签页"));
      }
    });
  });
}

/**
 * 确保脚本注入
 */
async function ensureScriptInjected(tabId) {
  try {
    const isInjected = await isScriptInjected(tabId);
    if (!isInjected) {
      console.log("脚本未注入，正在注入...");
      await injectContentScript(tabId);
    } else {
      console.log("脚本已注入");
    }
  } catch (error) {
    console.log("确保脚本注入时出错:", error);
    throw error;
  }
}

/**
 * 检查脚本是否已注入
 */
function isScriptInjected(tabId) {
  return new Promise((resolve, reject) => {
    const storageKeys = config?.storage_keys || { script_injected_flag: '__scriptInjected' };
    
    chrome.scripting.executeScript(
      {
        target: { tabId: tabId },
        func: (flagKey) => !!window[flagKey],
        args: [storageKeys.script_injected_flag]
      },
      (results) => {
        if (chrome.runtime.lastError || !results || results.length === 0) {
          reject(chrome.runtime.lastError || "无法执行脚本");
        } else {
          resolve(results[0].result);
        }
      }
    );
  });
}

/**
 * 注入内容脚本
 */
function injectContentScript(tabId) {
  console.log(tabId, "tabId");
  console.log("injectContentScript 脚本注入");
  return new Promise((resolve, reject) => {
    chrome.scripting.executeScript(
      {
        target: { tabId: tabId },
        files: [
          "utils/config-manager.js",
          "utils/dom.js", 
          "utils/request.js", 
          "utils/setting.js"
        ],
      },
      () => {
        if (chrome.runtime.lastError) {
          console.log(chrome.runtime.lastError.message);
          reject(chrome.runtime.lastError.message);
        } else {
          resolve();
        }
      }
    );
  });
}

// #endregion

// =================================================================================
// #region Scheduled Tasks
// =================================================================================

/**
 * 计算下一个指定时间的时间戳
 */
function computeNextScheduledTime(hour = 9, minute = 30) {
  const now = new Date();
  const next = new Date();
  next.setHours(hour, minute, 0, 0);
  if (next.getTime() <= now.getTime()) {
    next.setDate(next.getDate() + 1);
  }
  return next.getTime();
}

/**
 * 计算下一个整点时间
 */
function computeNextHour() {
  const now = new Date();
  const next = new Date(now);
  next.setMinutes(0, 0, 0);
  if (next.getTime() <= now.getTime()) {
    next.setHours(next.getHours() + 1);
  }
  return next.getTime();
}

/**
 * 计算下一个9:30的时间戳
 */
function computeNext930() {
  const taskTime = config?.business?.daily_task_time || { hour: 9, minute: 30 };
  return computeNextScheduledTime(taskTime.hour, taskTime.minute);
}

/**
 * 执行每日任务
 */
async function doDailyTask() {
  console.log("执行每日任务");
  try {
    const tab = await getDouyinTab();
    await chrome.tabs.sendMessage(tab.id, {
      action: "DO_DAILY_TASK",
      data: {},
      url: "",
    });
    console.log("每日任务消息已发送");
  } catch (error) {
    console.error("执行每日任务失败:", error);
  }
}

/**
 * 执行整点任务
 */
async function doHourlyTask() {
  console.log("执行整点任务");
  try {
    await doDailyTask();
  } catch (error) {
    console.error("执行整点任务失败:", error);
  }
}

// #endregion

// =================================================================================
// #region Message Handlers
// =================================================================================

/**
 * 处理HTTP请求
 */
async function handleHttpRequest(request, sendResponse) {
  const { url, options = {} } = request.data || {};

  if (!url) {
    console.error("Invalid request format: URL is missing.", request);
    sendResponse({
      success: false,
      error: "Invalid request format: URL is missing.",
    });
    return;
  }

  const httpConfig = config?.http || getDefaultConfig().http;
  
  try {
    const response = await fetch(url, {
      method: options.method || "POST",
      headers: options.headers || {
        "Content-Type": httpConfig.headers.content_type_json,
      },
      body: options.body,
      credentials: options.credentials || httpConfig.credentials,
    });
    
    const data = await response.json();
    sendResponse({ success: true, data });
  } catch (error) {
    console.error(
      "Fetch error:",
      error.toString(),
      "URL:",
      url,
      "Options:",
      options
    );
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * 处理关闭标签页请求
 */
function handleCloseTabRequest(request, sendResponse) {
  const targetUrl = request.data.url;

  chrome.tabs.query({}, (tabs) => {
    try {
      let found = false;
      tabs.forEach((tab) => {
        if (tab.url.includes(targetUrl)) {
          chrome.tabs.remove(tab.id);
          found = true;
        }
      });
      
      if (found) {
        console.log(`成功关闭包含URL "${targetUrl}" 的标签页`);
        sendResponse({ success: true, message: "标签页已关闭" });
      } else {
        console.log(`未找到包含URL "${targetUrl}" 的标签页`);
        sendResponse({ success: false, message: "未找到匹配的标签页" });
      }
    } catch (error) {
      console.error("关闭标签页时出错:", error);
      sendResponse({ success: false, error: error.message });
    }
  });
}

/**
 * 主消息监听器
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log(request, "onMessage:request");
  
  // 确保配置已加载
  if (!config) {
    initializeConfig().then(() => {
      handleMessage(request, sender, sendResponse);
    });
    return true;
  }
  
  return handleMessage(request, sender, sendResponse);
});

/**
 * 处理消息的核心逻辑
 */
function handleMessage(request, sender, sendResponse) {
  if (
    request.action === "FETCH_EC_PRODUCT_LIST" ||
    request.action === "FETCH_PRODUCT_DETAIL"
  ) {
    handleHttpRequest(request, sendResponse);
    return true;
  }

  if (request.action === "CLOSE_TAB_BY_URL") {
    handleCloseTabRequest(request, sendResponse);
    return true;
  }

  // 处理其他消息类型
  console.log("未处理的消息类型:", request.action);
  sendResponse({ success: false, error: "未知的消息类型" });
  return false;
}

// #endregion

// =================================================================================
// #region Extension Lifecycle
// =================================================================================

/**
 * 设置定时任务
 */
function setupAlarms() {
  // 清除现有的定时任务
  chrome.alarms.clearAll();
  
  // 设置每日9:30任务
  const next930 = computeNext930();
  chrome.alarms.create("daily-task", {
    when: next930,
    periodInMinutes: 24 * 60, // 每24小时重复
  });
  
  // 设置整点任务
  const nextHour = computeNextHour();
  chrome.alarms.create("hourly-task", {
    when: nextHour,
    periodInMinutes: 60, // 每小时重复
  });
  
  console.log("定时任务已设置:");
  console.log(`- 每日任务: ${new Date(next930).toLocaleString()}`);
  console.log(`- 整点任务: ${new Date(nextHour).toLocaleString()}`);
}

/**
 * 扩展安装时的处理
 */
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log("扩展已安装/更新:", details.reason);
  
  // 确保配置已加载
  await initializeConfig();
  
  // 设置定时任务
  setupAlarms();
});

/**
 * 扩展启动时的处理
 */
chrome.runtime.onStartup.addListener(async () => {
  console.log("扩展已启动");
  
  // 确保配置已加载
  await initializeConfig();
  
  // 重新设置定时任务
  setupAlarms();
});

/**
 * 定时任务触发处理
 */
chrome.alarms.onAlarm.addListener(async (alarm) => {
  console.log("定时任务触发:", alarm.name);
  
  try {
    switch (alarm.name) {
      case "daily-task":
        await doDailyTask();
        break;
      case "hourly-task":
        await doHourlyTask();
        break;
      default:
        console.log("未知的定时任务:", alarm.name);
    }
  } catch (error) {
    console.error(`执行定时任务 ${alarm.name} 时出错:`, error);
  }
});

// #endregion

// =================================================================================
// #region Utility Functions
// =================================================================================

/**
 * 获取配置值的辅助函数
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
 * 日志记录辅助函数
 */
function logWithTimestamp(level, message, ...args) {
  const timestamp = new Date().toISOString();
  console[level](`[${timestamp}] ${message}`, ...args);
}

// #endregion