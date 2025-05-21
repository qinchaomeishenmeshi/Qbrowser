const eosHomePage = 'https://*.douyin.com/*'
const targetUrlPattern = /^https:\/\/eos\.douyin\.com\/data\/life\/live\/shelves\/anchor\//
// 存储请求ID和标签页ID的映射
const requestTabMap = {}

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

// background.js


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
        chrome.tabs.query({url: eosHomePage}, async (tabs) => {
            console.log(tabs, 'tabs')
            if (tabs.length > 0) {
                const tab = tabs[0]
                try {
                    await ensureScriptInjected(tab.id)
                    if (!tab.active) {
                        chrome.tabs.update(tab.id, {active: true})
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

getDouyinTab()

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
                target: {tabId: tabId},
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
                target: {tabId: tabId},
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


// 计算下一个“今天 9:30”或“明天 9:30”的时间戳（毫秒）
function computeNext930() {
    const now = new Date();
    const next = new Date();
    next.setHours(9, 30, 0, 0);
    if (next.getTime() <= now.getTime()) {
        next.setDate(next.getDate() + 1);
    }
    return next.getTime();
}

// 计算下一个“下个整点”的时间戳（毫秒）
// 例如当前 9:17 → 返回今天 10:00；当前 10:00:00.100 → 返回 11:00
function computeNextHour() {
    const now = new Date();
    const next = new Date(now);
    next.setMinutes(0, 0, 0);       // 先设置到本小时的 0 分 0 秒 0 毫秒
    if (next.getTime() <= now.getTime()) {
        next.setHours(next.getHours() + 1);
    }
    return next.getTime();
}

// 业务函数：每天早上 9:30 要执行的逻辑
function doDailyTask() {
    console.log('执行每日任务');
//    发送消息给content.js 执行任务
    chrome.tabs.query({url: eosHomePage}, (tabs) => {
        if (tabs.length > 0) {
            const tab = tabs[0]
            chrome.tabs.sendMessage(tab.id, {action: 'DO_DAILY_TASK', data: {}, url: ''}, (response) => {
                console.log('发送消息给content.js执行任务', response)
            })
        }
    })
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'SHELVES_ANCHOR_DATA') {
        console.log('接收货架主播数据:', request.data)
        // 统一数据处理逻辑
        handleShelvesData(request.data)
    }

    if (request.action === 'CLOSE_TAB_BY_URL') {
        const targetUrl = request.data.url;
        
        // 查询所有标签页
        chrome.tabs.query({}, (tabs) => {
            try {
                let found = false;
                // 遍历所有标签页
                tabs.forEach(tab => {
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
                    message: found ? '标签页已关闭' : '未找到匹配的标签页'
                });
            } catch (error) {
                sendResponse({
                    success: false,
                    error: error.message
                });
            }
        });
        
        // 返回true表示将异步发送响应
        return true;
    }
    return true // 保持通道开放用于异步响应
})


// 安装或更新时注册两个 Alarm
chrome.runtime.onInstalled.addListener(() => {
    // 清除已有的 alarm
    chrome.alarms.clearAll(() => {
        // 每天 9:30
        chrome.alarms.create('daily930', {
            when: computeNext930(),
            periodInMinutes: 24 * 60
        });
        // 每个整点
        chrome.alarms.create('hourlyTop', {
            when: computeNextHour(),
            periodInMinutes: 60
        });
        console.log('Alarm 已注册：daily930, hourlyTop');
    });
});

// 当扩展启动（例如浏览器重启）时，同步注册（可选，保证不会漏掉）
chrome.runtime.onStartup.addListener(() => {
    chrome.alarms.create('daily930', {
        when: computeNext930(),
        periodInMinutes: 24 * 60
    });
    chrome.alarms.create('hourlyTop', {
        when: computeNextHour(),
        periodInMinutes: 60
    });
    console.log('onStartup 同步 Alarm：daily930, hourlyTop');
});

// 监听 Alarm 触发
chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'daily930') {
        doDailyTask();
    } else if (alarm.name === 'hourlyTop') {
        doDailyTask();
    }
});
