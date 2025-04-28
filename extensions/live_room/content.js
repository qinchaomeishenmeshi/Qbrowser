// 获取抖音账号信息
let dyAccountNo = null

// 连接socket
let socketWs = null
let reconnectStartTime = null // 记录重连的起始时间

// 保存规则配置后启动定时器
let timerId = null
let isTimerRunning = false;

// 评论相关
let comment = {}
// 商品列表相关
let cacheData = ''
let productsList = []
let syncBtnLoading = false
let syncBtnLoadingText = '同步中...'
let syncBtnSuccessText = '同步成功'
let syncBtnErrorText = '同步失败'
let syncBtnReloadText = '重新同步'
let syncBtnText = '同步混剪系统'
// 顶部提示相关
let fixedTipBox = null

// 监听消息
chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    console.log('request', request)
    console.log('sender', sender)
    console.log('sendResponse', sendResponse)
    const {word, url} = request.data
    if (request.action === 'send_input_message') {
        // 发送常用词
        sendMessage(url, word, {}, sendResponse)
    } else if (request.action === 'send_comment') {
        // 发送评论
        sendMessage(url, word, {}, sendResponse)
    } else if (request.action === 'DO_DAILY_TASK') {
        console.log('DO_DAILY_TASK___执行每日任务')
        get_punish_list().then((res) => {
            console.log('punish_list', res)
        })

    } else {
        console.log('其他消息', request)
    }
})

// 监听直播间变化
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成 DOMContentLoaded')
    let timeoutId = null
    // 使用 MutationObserver 替代 setTimeout
    const observer = new MutationObserver((mutations, obs) => {
        const accountPanel = document.querySelector("div[class*='dropdown-panel-']")
        if (accountPanel) {
            console.log('检测到账号面板元素已加载')
            obs.disconnect() // 停止观察
            getDyAccountNo()
            timeoutId && clearTimeout(timeoutId) // 新增：清理超时定时器
        }
    })

    // 开始观察整个文档变化
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: false,
        characterData: false
    })

    // 设置超时回退（10秒）
    timeoutId = setTimeout(() => {
        observer.disconnect()
        createTopTips('账号信息加载超时，请手动刷新页面')
        console.error('账号面板元素加载超时')
    }, 10000)
    // 立即注入拦截器
    injectFetchInterceptor()
    // 立即同步一次
    syncPunishList();


})


// 复用已有的接口拦截逻辑（需修改匹配规则）
function injectFetchInterceptor() {
    console.log('注入拦截器')
    // 使用扩展资源路径代替内联脚本
    const scriptURL = chrome.runtime.getURL('fetch-interceptor.js')

    // 防止重复注入
    if (!document.querySelector('script[data-fetch-interceptor]')) {
        const scriptElement = document.createElement('script')
        scriptElement.setAttribute('data-fetch-interceptor', 'true')
        scriptElement.src = scriptURL
        document.head.appendChild(scriptElement)
    }
}

// 优化事件监听处理
window.addEventListener('fetchResponse', (event) => {
    const {url, status, body} = event.detail
    console.log('接口监听-test:', url, status, body)
    // if (url.includes('/data/life/live/shelves/anchor/') && status === 200) {
    if (url.includes('/data/life/live/plan/detail/') && status === 200) {
        try {
            const data = JSON.parse(body)
            console.log('直播商品列表数据:', data.data)
            cacheData = JSON.stringify(data.data)
            if (cacheData) {
                console.log('缓存数据:', cacheData)
                setTimeout(() => {
                    createSyncContainer()
                }, 3000)
            }
        } catch (e) {
            console.error('数据解析失败:', e)
        }
    }

    if (url.includes('/data/life/live/case/agreement/get') && status === 200) {
        try {
            // 用浏览器自带的 URL API 解析查询参数
            const userId = new URL(url, window.location.origin).searchParams.get('user_id');
            if (userId) {
                localStorage.setItem('agreement_user_id', userId);
                console.log('✅ 已保存 user_id 到 localStorage:', userId);
            } else {
                console.warn('⚠️ URL 中没有找到 user_id 参数');
            }
        } catch (e) {
            console.error('解析 user_id 或存储时出错:', e);
        }
    }
})


function createSyncContainer() {
    // 移除已有的同步容器（关键修复）
    const existingContainer = document.querySelector('.sync_wj');
    if (existingContainer) {
        existingContainer.remove();
    }

    // 查找父容器
    const tabGuide = document.querySelector(
        "div.okee-app-live-loading.okee-app-live-loading-block>div>div:nth-last-child(1) button:nth-child(1)"
    );
    if (!tabGuide || !tabGuide.parentElement) {
        console.error('未找到目标容器，无法创建同步按钮');
        return;
    }

    // 创建新容器和按钮
    const syncContainer = document.createElement('div');
    const syncButton = document.createElement('button');
    syncContainer.classList.add('sync_wj');
    // syncButton 添加样式
    syncButton.style.background = 'linear-gradient(to right bottom, #7db1ff, #004EFE) border-box border-box'
    syncButton.style.border = '1px solid transparent'
    syncButton.style.borderRadius = '6px'
    syncButton.style.color = '#fff'
    syncButton.style.fontSize = '14px'
    syncButton.style.height = '36px'
    syncButton.style.lineHeight = '22px'
    syncButton.style.minWidth = '80px'
    syncButton.style.padding = '6px 16px'
    syncButton.style.textAlign = 'center'
    syncButton.style.marginLeft = '10px'
    syncButton.style.cursor = 'pointer'
    syncButton.textContent = syncBtnText
    //
    tabGuide.parentElement.appendChild(syncContainer)
    syncContainer.appendChild(syncButton)

    // 配置按钮点击事件
    syncButton.addEventListener('click', () => {
        if (syncBtnLoading) {
            return
        }
        // 添加loading状态样式
        syncBtnLoading = true
        syncButton.style.opacity = '0.7'
        syncButton.style.cursor = 'not-allowed'
        syncButton.textContent = syncBtnLoadingText
        // 发送商品数据到后台
        try {
            handleShelvesData(JSON.parse(cacheData))
                .then((res) => {
                    console.log('发送商品数据到后台', res)
                    syncButton.textContent = syncBtnSuccessText
                    createTopTips('所有商品处理完成，请在混剪系统中查看')
                    setTimeout(() => {
                        syncButton.textContent = syncBtnText
                    }, 3000)

                })
                .catch((error) => {
                    console.error('发送商品数据到后台失败', error)
                    createTopTips(error)
                    syncButton.textContent = syncBtnErrorText
                    setTimeout(() => {
                        syncButton.textContent = syncBtnReloadText
                    }, 3000)
                })
                .finally(() => {
                    // 移除loading状态
                    syncBtnLoading = false;
                    syncButton.style.opacity = '1';
                    syncButton.style.cursor = 'pointer';
                })
        } catch (e) {
            console.error('发送商品数据到后台失败:', e)
            syncButton.textContent = syncBtnErrorText
            syncButton.style.opacity = '1'
            syncButton.style.cursor = 'pointer'
            syncBtnLoading = false
        }
    })
}

// 处理数据
async function handleShelvesData(data) {
    return new Promise((resolve, reject) => {
        try {
            // 新增延时函数
            const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
            // 生成随机延时
            const getRandomDelay = () => Math.floor(Math.random() * 2000) + 3000

            // productsList = data.card_list
            productsList = data.info || []
            console.log('待处理商品数量:', productsList.length)

            // 创建带延时的请求任务链
            const processProduct = async (productId) => {
                try {
                    // 第一阶段请求
                    console.log(`开始处理商品 ${productId} 的commodityDetail`)
                    await getCommodityDetail(productId)
                    await delay(getRandomDelay())

                    // 第二阶段请求（增加间隔）
                    console.log(`开始处理商品 ${productId} 的productDetail`)
                    await getProductDetail(productId)
                    await delay(getRandomDelay())
                } catch (error) {
                    console.error(`商品 ${productId} 处理失败:`, error)
                }
            }

            let currentIndex = 0
            let queueDelay = 0
            const queueInterval = 3000
            productsList.forEach((product) => {
                const productId = product.product_base_info.product_id
                const productName = product.product_base_info.name

                setTimeout(() => {
                    processProduct(productId).finally(async () => {
                        currentIndex++
                        console.log(`商品 ${productName}处理完成 ...`)
                        if (currentIndex >= productsList.length) {
                            const res = await sendProductsListToBackground()
                            console.log('发送商品数据到后台', res)
                            resolve(res)
                        }
                    })
                }, queueDelay)
                queueDelay = getRandomDelay() // 队列间隔递增
            })
        } catch (e) {
            console.error('处理数据失败:', e)
            reject(e)
        }
    })
}

// 获取commodityDetail信息
async function getCommodityDetail(productId) {
    // 添加随机延时（0-2秒）
    await delay(Math.random() * 2000)
    const baseUrl = `https://eos.douyin.com/life/alliance/v2/goods/product/commodity/detail/get?from_type=5&product_id=${productId}`
    return fetch(baseUrl)
        .then((response) => response.json())
        .then((data) => {
            console.log('获取commodityDetail信息成功:', data)
            // 找到对应的商品 ，然后更新productsList的数据
            const product = productsList.find(
                (product) => product.product_base_info.product_id === productId
            )
            if (product) {
                product.commodity_info = data.commodity_info || {}
                product.use_rule_info = data.use_rule_info || {}
            }
        })
        .catch((error) => {
            console.error('获取commodityDetail信息失败:', error)
            window.alert('获取commodityDetail信息失败' + JSON.stringify(error))
        })
}

// 获取商品详情数据
async function getProductDetail(productId) {
    window.scrollBy({
        top: Math.random() * 100,
        behavior: 'smooth'
    })
    const baseUrl = `https://eos.douyin.com/life/alliance/v2/goods/product/detail/get?from_type=5&image_size=%7B%22width%22:750%7D&product_id=${productId}`
    return fetch(baseUrl)
        .then((response) => response.json())
        .then((data) => {
            console.log('获取商品详情成功:', data)
            // 找到对应的商品 ，然后更新productsList的数据
            const product = productsList.find(
                (product) => product.product_base_info.product_id === productId
            )
            if (product) {
                product.product_info = data.product_info || {}
                product.poi_nearest = data.poi_nearest || {}
            }
        })
        .catch((error) => {
            console.error('获取商品详情失败:', error)
            window.alert('获取商品详情失败' + JSON.stringify(error))
        })
}

// 将组装好的productsList数据发送到后台
async function sendProductsListToBackground() {
    const params = {
        attr: '1',
        dyAccountNo: dyAccountNo,
        planContent: cacheData,
        products: productsList.map((product, index) => {
            return {
                ...product,
                fromType: '5',
                sort: index + 1
            }
        })
    }

    console.log('发送商品数据到后台', params)
    return await $Request(API.saveProductListApi, {params})
}


// 启动定时器
function startTimer() {
    if (isTimerRunning) return; // 已运行则直接返回
    stopTimer(); // 清理旧定时器（仅在首次启动时生效）

    timerId = setInterval(() => {
        getActiveCommentData().then(data => {
            console.log('定时任务执行成功:', data)
            const commentReply = data?.commentReply || ''
            createTopTips('评论区回复消息:', commentReply)
            if (commentReply) {
                // 评论区回复消息
                sendMessage(window.location.href, commentReply, data, (result) => {
                    console.log('评论区回复消息发送成功的返回结果' + JSON.stringify(result))
                })
            }
        }).catch(error => {
            console.error('定时任务执行失败:', error);
        });
    }, 10000);

    isTimerRunning = true;
    console.log('定时器已启动');
}

// 停止定时器
function stopTimer() {
    if (!isTimerRunning) return; // 未运行则直接返回
    clearInterval(timerId);
    timerId = null;
    isTimerRunning = false;
    console.log('定时器已停止');
}

// 每5秒检查一次是否在直播
setInterval(() => {
    const currentUrl = new URL(window.location.href);
    const pathName = currentUrl.pathname;
    const modal_wrapper = document.querySelector('.okee-main-modal-wrapper .okee-main-modal-body .okee-main-content-container .okee-main-content-header.okee-main-modal-content-header');
    console.log(modal_wrapper, '弹窗存在')
    if (modal_wrapper) {
        getModalText()
    }
    let isLiving = false;
    try {
        const liveMenus = document.querySelectorAll('.okee-main-menu-line-title');
        isLiving = Array.from(liveMenus).some(menu =>
            menu.textContent.includes('正在直播')
        );
    } catch (e) {
        isLiving = false;
        console.error('获取直播状态失败:', e);
    }

    const shouldStart = (pathName === '/livesite/live/current') && isLiving;
    console.log('当前直播状态:', shouldStart)
    if (shouldStart && !isTimerRunning) {
        startTimer();
    } else if (!shouldStart && isTimerRunning) {
        stopTimer();
    }
}, 3000);

// 每个小时同步一次违规记录
async function syncPunishList() {
    console.log('每个小时同步一次违规记录')
    try {
        const res = await get_punish_list();
    } catch (error) {
        console.error('Error syncing punish list:', error);
    }
}


// 设置定时器，每小时同步一次
setInterval(() => {
    console.log('定时器执行')
    syncPunishList();
}, 3600000);


// 获取主动评论数据
let debounceTimeout = null;

async function getModalText() {
    // 找到弹窗内容
    const spans = document.querySelectorAll('span');

    // 2. 过滤出文本里包含 “违规原因” 的元素
    const targetSpans = Array.from(spans).filter(span =>
        span.textContent.includes('处罚原因')
    );

    // 3. 如果只需要第一个匹配项，可以：
    const firstSpan = targetSpans[0] || null;

    if (firstSpan) {
        const modal_span_text = firstSpan.textContent
        console.log(modal_span_text, '弹窗内容')
        const pattern = /处罚原因：(.+?)\s*违规时间：([\d-]+\s[\d:]+)\s*处罚方式：(.+?)(?:\s|$)/s;

        const match = modal_span_text.match(pattern);

        const result = match
            ? {
                violationReason: match[1].trim(),
                violationTime: match[2].trim(),
                punishmentType: match[3].trim(),
                dyAccountNo: localStorage.getItem('dyAccountNo')
            }
            : {};

        console.log(result);
        const dyAccountNo = localStorage.getItem('dyAccountNo')
        const roomName = localStorage.getItem('dyRoomName')
        const params = {
            violationReason: result['violationReason'],
            violationTime: result['violationTime'],
            punishmentType: result['punishmentType'],
            name: roomName,
            dyAccountNo
        }
        if (!result['violationTime']) {
            createTopTips('弹窗内容获取失败')
            return
        }
        console.log('params', params)
        await $Request(API.liveviolationrecordsdealSaveApi, {params});
        createTopTips(`账号：${dyAccountNo},违规记录保存成功`)
    }

}

async function get_punish_list() {
    console.log('每天执行一次');
    createTopTips('同步违规记录——开始');

    const agreementUserId = localStorage.getItem('agreement_user_id');
    const dyAccountNo = localStorage.getItem('dyAccountNo');
    const dyRoomName = localStorage.getItem('dyRoomName');

    if (!agreementUserId) {
        console.warn('❌ 未找到 agreement_user_id，终止同步');
        createTopTips('同步失败：缺少 user_id');
        return;
    }

    // —— 动态计算四个日期 ——
    const today = new Date();
    const periodDays = 30;             // 周期天数
    const fmt = d => d.toISOString().slice(0, 10);

    // end_date = 今天
    const end_date = fmt(today);

    // begin_date = 今天往前推 (periodDays - 1) 天
    const begin = new Date(today);
    begin.setDate(begin.getDate() - (periodDays - 1));
    const begin_date = fmt(begin);

    // compare_end_date = begin_date 的前一天
    const cmpEnd = new Date(begin);
    cmpEnd.setDate(cmpEnd.getDate() - 1);
    const compare_end_date = end_date;

    // compare_begin_date = compare_end_date 再往前推 (periodDays - 1) 天
    const cmpBegin = new Date(cmpEnd);
    cmpBegin.setDate(cmpBegin.getDate() - (periodDays - 1));
    const compare_begin_date = begin_date;

    try {
        const res = await fetch(
            'https://eos.douyin.com/life/api/live_screen/v4/replay/punish_list',
            {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    user_id: agreementUserId,
                    begin_date,
                    end_date,
                    compare_begin_date,
                    compare_end_date
                })
            }
        );
        console.log(`接口状态 ${res.status}`);
        const {data: list = []} = await res.json();

        if (list.length === 0) {
            createTopTips('同步完成：无违规记录');
            console.log('ℹ️ 当天无违规记录');
            return;
        }

        for (const item of list) {
            try {
                const params = {
                    violationReason: item.violation_reason,
                    violationTime: item.time,
                    punishmentType: item.punish_result,
                    dyAccountNo,
                    name: dyRoomName
                };
                console.log('保存参数：', params);
                await $Request(API.liveviolationrecordsdealSaveApi, {params});
            } catch (e) {
                console.error('⚠️ 单条保存失败：', e, item);
            }
        }

        createTopTips('同步违规记录——完成');
        console.log('✅ 全部记录已处理完毕');
    } catch (err) {
        console.error('❌ 同步过程出错：', err);
        createTopTips(`同步失败：${err.message || '未知错误'}`);
    }
}


function getActiveCommentData() {
    return new Promise(async (resolve, reject) => {
        // 防抖逻辑：500ms内仅执行一次
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(async () => {
            try {
                const params = {
                    roomNo: localStorage.getItem('dyAccountNo'),
                    roomName: localStorage.getItem('dyRoomName')
                };
                const result = await $Request(API.pullAdminComment + '?roomNo=' + localStorage.getItem('dyAccountNo'), {params});
                console.log('主动评论数据', result)
                resolve(result);
            } catch (error) {
                reject(error);
            }
        }, 500); // 500ms防抖
    });
}

// 发送消息
function sendMessage(url, word, data, sendResponse) {
    // 查找输入框元素
    if (url.startsWith('https://live.kuaishou.com/')) {
        const textarea = document.querySelector('textarea.box-boder')
        if (textarea) {
            // 输入框塞数据
            textarea.value = word
            // 触发输入事件
            const inputEvent = new Event('input', {bubbles: true})
            textarea.dispatchEvent(inputEvent)
            // 触发发送
            const send_btn = document.querySelector('.submit-button')
            // 创建一个 mouseclick 事件
            const mouseEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window,
                button: 0 // 左键点击
            })
            send_btn.dispatchEvent(mouseEvent)
            sendResponse({action: 'send_input_message', data: data, status: 1})
        } else {
            sendResponse({action: 'send_input_message', data: data, status: 0})
        }
    } else if (url.startsWith('https://live.douyin.com/')) {
        const textarea = document.querySelector('textarea.webcast-chatroom___textarea')
        if (textarea) {
            // 输入框塞数据
            textarea.value = word
            // 触发输入事件
            const inputEvent = new Event('input', {bubbles: true})
            textarea.dispatchEvent(inputEvent)
            // 触发发送
            const svg_send = document.querySelector('.webcast-chatroom___send-btn')
            // 创建一个 mouseclick 事件
            const mouseEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window,
                button: 0 // 左键点击
            })
            svg_send.dispatchEvent(mouseEvent)
            sendResponse({action: 'send_input_message', data: data, status: 1})
        } else {
            sendResponse({action: 'send_input_message', data: data, status: 0})
        }
    } else if (url.startsWith('https://eos.douyin.com/')) {
        const textarea = document.querySelector("textarea[class*='input-']")
        if (textarea) {
            // 输入框塞数据
            textarea.value = word
            // 触发输入事件
            const inputEvent = new Event('input', {bubbles: true})
            textarea.dispatchEvent(inputEvent)
            // 触发发送
            const parentEle = document.querySelector('div[class*="input-wrap-"]')
            const svg_send = parentEle.querySelector('div[class*="button-"]')
            // 创建一个 mouseclick 事件
            const mouseEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window,
                button: 0 // 左键点击
            })
            svg_send.dispatchEvent(mouseEvent)
            sendResponse({action: 'send_input_message', data: data, status: 1})
        }
    }
}


// 获取抖音账号信息
function getDyAccountNo() {
    const accountNoEle = document.querySelector("div[class*='dropdown-panel-']")
    if (!accountNoEle) {
        createTopTips('未找到抖音账号信息')
        return
    }
    const accountNo = accountNoEle.querySelector("div[class*='panel-profile-account-']").textContent
    const accountName = accountNoEle.querySelector("div[class*='panel-profile-name-']").textContent
    console.log('accountNo', accountNo.split('：')[1])
    console.log('accountName', accountName)
    dyAccountNo = accountNo.split('：')[1]

    localStorage.setItem('dyAccountNo', dyAccountNo)
    localStorage.setItem('dyRoomName', accountName)


}


// 创建一个屏幕顶部的fixed提示框，黑色背景，白色16号字体。参数为需要展示的文字，文字居中展示
function createTopTips(text, timeOut = 5000) {
    if (!fixedTipBox) {
        fixedTipBox = document.createElement('div')
        fixedTipBox.style.cssText = `
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          background-color: rgba(0, 0, 0, 0.5);
          color: #fff;
          font-size: 24px;
          line-height: 48px;
          padding: 10px;
          text-align: center;
          z-index: 9999;
          cursor: pointer; /* 鼠标悬浮时显示为可点击状态 */
      `
        fixedTipBox.textContent = text
        document.body.appendChild(fixedTipBox)
    }

    fixedTipBox.textContent = text

    // 点击提示框移除它
    fixedTipBox.addEventListener('click', () => {
        fixedTipBox.remove()
    })

    // 指定时间后自动删除提示框
    const autoRemoveTimer = setTimeout(() => {
        if (fixedTipBox.parentNode) {
            fixedTipBox.remove()
        }
    }, timeOut)

    // 返回定时器 ID，便于外部操作（如取消自动移除）
    return {fixedTipBox, autoRemoveTimer}
}
