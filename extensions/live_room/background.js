// 抖音域名匹配模式
const DOUYIN_DOMAINS = [
  "https://haohuo.jinritemai.com/*",
  "https://www.douyin.com/*",
  "https://eos.douyin.com/*",
  "https://buyin.jinritemai.com/*",
];

// 新增数据处理函数

function getDouyinTab() {
  return new Promise((resolve, reject) => {
    // 使用正确的URL匹配模式
    chrome.tabs.query({ url: DOUYIN_DOMAINS }, async (tabs) => {
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

// 确保脚本注入逻辑的优化版
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

// 检查脚本是否已注入
function isScriptInjected(tabId) {
  return new Promise((resolve, reject) => {
    chrome.scripting.executeScript(
      {
        target: { tabId: tabId },
        func: () => !!window.__scriptInjected, // 检查标志变量
      },
      (results) => {
        if (chrome.runtime.lastError || !results || results.length === 0) {
          reject(chrome.runtime.lastError || "无法执行脚本");
        } else {
          resolve(results[0].result); // 返回标志变量的状态
        }
      }
    );
  });
}

// 注入内容脚本并返回一个Promise
function injectContentScript(tabId) {
  console.log(tabId, "tabId");
  console.log("injectContentScript 脚本注入");
  return new Promise((resolve, reject) => {
    chrome.scripting.executeScript(
      {
        target: { tabId: tabId },
        files: ["utils/dom.js", "utils/request.js", "utils/setting.js"],
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

// 计算下一个"今天 9:30"或"明天 9:30"的时间戳（毫秒）
function computeNext930() {
  const now = new Date();
  const next = new Date();
  next.setHours(9, 30, 0, 0);
  if (next.getTime() <= now.getTime()) {
    next.setDate(next.getDate() + 1);
  }
  return next.getTime();
}

// 计算下一个"下个整点"的时间戳（毫秒）
// 例如当前 9:17 → 返回今天 10:00；当前 10:00:00.100 → 返回 11:00
function computeNextHour() {
  const now = new Date();
  const next = new Date(now);
  next.setMinutes(0, 0, 0); // 先设置到本小时的 0 分 0 秒 0 毫秒
  if (next.getTime() <= now.getTime()) {
    next.setHours(next.getHours() + 1);
  }
  return next.getTime();
}

// 业务函数：每天早上 9:30 要执行的逻辑
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

// 业务函数：每小时执行的逻辑
async function doHourlyTask() {
  console.log("执行整点任务");
  try {
    // 这里添加整点特有的任务逻辑
    // 如果暂时没有特殊逻辑，可以调用日常任务
    await doDailyTask();
  } catch (error) {
    console.error("执行整点任务失败:", error);
  }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log(request, "onMessage:request");
  if (
    request.action === "FETCH_EC_PRODUCT_LIST" ||
    request.action === "FETCH_PRODUCT_DETAIL"
  ) {
    const { url, options = {} } = request.data || {}; // Provide defaults

    if (!url) {
      console.error("Invalid request format: URL is missing.", request);
      sendResponse({
        success: false,
        error: "Invalid request format: URL is missing.",
      });
      return true;
    }

    fetch(url, {
      method: options.method || "POST",
      headers: options.headers || {
        "Content-Type": "application/json",
      },
      body: options.body,
      credentials: options.credentials || "same-origin",
    })
      .then((response) => response.json())
      .then((data) => {
        sendResponse({ success: true, data });
      })
      .catch((error) => {
        console.error(
          "Fetch error:",
          error.toString(),
          "URL:",
          url,
          "Options:",
          options
        );
        sendResponse({ success: false, error: error.message });
      });
    return true; // Indicates that the response is sent asynchronously
  }

  if (request.action === "CLOSE_TAB_BY_URL") {
    const targetUrl = request.data.url;

    // 查询所有标签页
    chrome.tabs.query({}, (tabs) => {
      try {
        let found = false;
        // 遍历所有标签页
        tabs.forEach((tab) => {
          // 检查标签页URL是否匹配目标URL
          if (tab.url.includes(targetUrl)) {
            // 关闭匹配的标签页
            chrome.tabs.remove(tab.id);
            found = true;
          }
        });

        // 发送响应
        sendResponse({
          success: true,
          message: found ? "标签页已关闭" : "未找到匹配的标签页",
        });
      } catch (error) {
        sendResponse({
          success: false,
          error: error.message,
        });
      }
    });

    // 返回true表示将异步发送响应
    return true;
  }

  return true; // 保持通道开放用于异步响应
});

// 安装或更新时注册两个 Alarm
chrome.runtime.onInstalled.addListener(() => {
  // 清除已有的 alarm
  chrome.alarms.clearAll(() => {
    // 每天 9:30
    chrome.alarms.create("daily930", {
      when: computeNext930(),
      periodInMinutes: 24 * 60,
    });
    // 每个整点
    chrome.alarms.create("hourlyTop", {
      when: computeNextHour(),
      periodInMinutes: 60,
    });
    console.log("Alarm 已注册：daily930, hourlyTop");
  });
});

// 当扩展启动（例如浏览器重启）时，同步注册（可选，保证不会漏掉）
chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create("daily930", {
    when: computeNext930(),
    periodInMinutes: 24 * 60,
  });
  chrome.alarms.create("hourlyTop", {
    when: computeNextHour(),
    periodInMinutes: 60,
  });
  console.log("onStartup 同步 Alarm：daily930, hourlyTop");
});

// 监听 Alarm 触发
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "daily930") {
    doDailyTask().catch((error) => {
      console.error("daily930任务执行失败:", error);
    });
  } else if (alarm.name === "hourlyTop") {
    doHourlyTask().catch((error) => {
      console.error("hourlyTop任务执行失败:", error);
    });
  }
});
