const eosHomePage = 'https://*.douyin.com/*'
const targetUrlPattern = /^https:\/\/eos\.douyin\.com\/data\/life\/live\/shelves\/anchor\//
// 存储请求ID和标签页ID的映射
const requestTabMap = {}

chrome.runtime.onInstalled.addListener(({ reason }) => {
  console.log('插件加载完成', reason)
})

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'SHELVES_ANCHOR_DATA') {
    console.log('接收货架主播数据:', request.data)
    // 统一数据处理逻辑
    handleShelvesData(request.data)
  }
  return true // 保持通道开放用于异步响应
})

// 新增数据处理函数
function handleShelvesData(data) {
  // 这里添加数据存储或转发逻辑
  console.log('处理货架数据:', {
    timestamp: data.timestamp,
    url: data.url,
    payload: data.payload
  })
}

function getDouyinTab() {
  return new Promise((resolve, reject) => {
    chrome.tabs.query({ url: eosHomePage }, async (tabs) => {
      console.log(tabs, 'tabs')
      if (tabs.length > 0) {
        const tab = tabs[0]
        try {
          await ensureScriptInjected(tab.id)
          if (!tab.active) {
            chrome.tabs.update(tab.id, { active: true })
          }
          resolve(tab)
        } catch (error) {
          console.log('检测脚本状态时出错:', error)
          reject(error.message)
        }
      } else {
        reject('未找到抖音tab')
      }
    })
  })
}

// 确保脚本注入逻辑的优化版
async function ensureScriptInjected(tabId) {
  try {
    const isInjected = await isScriptInjected(tabId)
    if (!isInjected) {
      console.log('脚本未注入，正在注入...')
      await injectContentScript(tabId)
    } else {
      console.log('脚本已注入')
    }
  } catch (error) {
    console.log('确保脚本注入时出错:', error)
    throw error
  }
}

// 检查脚本是否已注入
function isScriptInjected(tabId) {
  return new Promise((resolve, reject) => {
    chrome.scripting.executeScript(
      {
        target: { tabId: tabId },
        func: () => !!window.__scriptInjected // 检查标志变量
      },
      (results) => {
        if (chrome.runtime.lastError || !results || results.length === 0) {
          reject(chrome.runtime.lastError || '无法执行脚本')
        } else {
          resolve(results[0].result) // 返回标志变量的状态
        }
      }
    )
  })
}

// 注入内容脚本并返回一个Promise
function injectContentScript(tabId) {
  console.log(tabId, 'tabId')
  console.log('injectContentScript 脚本注入')
  return new Promise((resolve, reject) => {
    chrome.scripting.executeScript(
      {
        target: { tabId: tabId },
        files: ['utils/dom.js', 'utils/request.js', 'utils/setting.js']
      },
      () => {
        if (chrome.runtime.lastError) {
          console.log(chrome.runtime.lastError.message)
          reject(chrome.runtime.lastError.message)
        } else {
          resolve()
        }
      }
    )
  })
}

//监听所有请求
// chrome.webRequest.onBeforeRequest.addListener(
//     function (details) {
//         if (ws.readyState != ws.OPEN) {
//             return;
//         }
//         chrome.tabs.getSelected(null, function (tab) {
//             var tabUrl = tab.url;
//             var message = {"cmd": "url", "message": details.url, "tabUrl": tabUrl};
//             ws.send(JSON.stringify(message));
//             console.log(JSON.stringify(message));
//         });
//     },
//     {urls: ["<all_urls>"]},
//     ["blocking"]
// )

getDouyinTab()
