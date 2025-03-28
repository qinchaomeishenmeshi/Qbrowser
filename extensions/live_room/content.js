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
    if (url.includes('/data/life/live/shelves/anchor/') && status === 200) {
        try {
            const data = JSON.parse(body)
            console.log('直播商品列表数据:', data)
            cacheData = JSON.stringify(data)
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
})


function createSyncContainer() {
    // 移除已有的同步容器（关键修复）
    const existingContainer = document.querySelector('.sync_wj');
    if (existingContainer) {
        existingContainer.remove();
    }

    // 查找父容器
    const tabGuide = document.querySelector(
        'div.okee-current-live-loading.okee-current-live-loading-block div#tab-guide span'
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
    syncButton.style.background = 'border-box linear-gradient(to bottom right, #ff4fa3, #fe2c55)'
    syncButton.style.border = '1px solid transparent'
    syncButton.style.borderRadius = '4px'
    syncButton.style.color = '#fff'
    syncButton.style.fontSize = '12px'
    syncButton.style.height = '28px'
    syncButton.style.lineHeight = '18px'
    syncButton.style.minWidth = '80px'
    syncButton.style.padding = '4px 16px'
    syncButton.style.textAlign = 'center'
    syncButton.style.cursor = 'pointer'
    syncButton.textContent = syncBtnText
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
            const getRandomDelay = () => Math.floor(Math.random() * 10000) + 10000

            productsList = data.card_list
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


// 获取主动评论数据
let debounceTimeout = null;

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

// 回复评论
function replyEosMessage(targetNode, word, _data, _sendResponse) {
    console.log('replyEosMessage', targetNode, word)
    if (targetNode) {
        // 模拟鼠标移入显示评论按钮
        targetNode.addEventListener('mouseenter', function () {
            targetNode.classList.add('hover')
            console.log('鼠标移入该区域内了')
            // 创建一个 mouseclick 事件
            const mouseEvent = new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window,
                button: 0 // 左键点击
            })
            const hover_btn = targetNode.querySelector('div[class*="hover-button-"]')
            if (!hover_btn) {
                return
            }
            const reply_btn = hover_btn.childNodes[1]
            console.log('回复按钮', reply_btn)
            reply_btn.dispatchEvent(mouseEvent)

            const reply_list_ele = targetNode.querySelector('div[class*="reply-list-"]')
            if (!reply_list_ele) {
                return
            }
            const reply_nick_btn = reply_list_ele.childNodes[0]
            console.log('回复昵称按钮', reply_list_ele, reply_nick_btn)
            reply_nick_btn.dispatchEvent(mouseEvent)
        })

        const targetNodeRect = targetNode.getBoundingClientRect()
        simulateMouseMoveWithElement(
            targetNodeRect.x + targetNodeRect.width / 2,
            targetNodeRect.y + targetNodeRect.height / 2,
            targetNode
        )
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

    // 链接socket
    // connectSocket()
}

// 连接socket
function connectSocket() {
    if (socketWs) {
        createTopTips('socket--已链接，无需重复链接')
        return
    }

    // 初始化重连起始时间
    if (!reconnectStartTime) {
        reconnectStartTime = Date.now()
    }

    // 检查是否超出 5 分钟
    const elapsedTime = Date.now() - reconnectStartTime
    if (elapsedTime > 300000) {
        // 300,000 毫秒 = 5 分钟
        createTopTips('socket--重连时间超过5分钟，停止重连', true)
        reconnectStartTime = null // 重置时间计数
        return
    }

    const SOCKET_URL =
        'wss://hj.qwang.com.cn/websocket/livestreamingcomment/COMMENT_PLUGIN/' + dyAccountNo
    const ws = new WebSocket(SOCKET_URL)
    let heartbeatInterval

    ws.onopen = function () {
        createTopTips('socket--链接已打开')
        socketWs = ws
        reconnectStartTime = null // 重置重连时间计数，因为连接成功了

        // 心跳检测
        heartbeatInterval = setInterval(() => {
            createTopTips('直播监控中...', 9000)
            if (socketWs.readyState === WebSocket.OPEN) {
                socketWs.send(
                    JSON.stringify({
                        type: 'ping',
                        roomName: localStorage.getItem('dyRoomName'),
                        roomNo: localStorage.getItem('dyAccountNo'),
                        terminal: "pc"
                    })
                )
            }
        }, 10000) // 每10秒发送心跳
    }

    ws.onmessage = function (event) {
        console.log('socket接收消息', event)
        try {
            let reply_obj = JSON.parse(event.data)
            comment = reply_obj
            console.log('socket onmessage', reply_obj)
            console.log('回复内容为：', reply_obj['commentReply'])

            if (reply_obj.type === 'reply' && reply_obj['commentReply']) {
                // 匹配消息标签
                // let replyNode = null
                // const chatWrap = document.querySelector("div[class*='comment-wrap-']");
                // if (!chatWrap) return; // 如果未找到目标节点，继续监听
                // const chatListEle = chatWrap.querySelector("div[class*='list-']");
                // if (!chatListEle) return; // 如果未找到目标节点，继续监听
                // const chatroomItems = chatListEle.querySelectorAll('div[class*="item-"]');
                // // 获取最近20个评论
                // const sliceChatRoomItems = Array.from(chatroomItems).slice(-20)
                // for (let i = 0; i < sliceChatRoomItems.length; i++) {
                //     let targetNode = sliceChatRoomItems[i];
                //     let auther = targetNode.querySelector("div[class*='item-name-']")?.textContent.trim();
                //     let content = targetNode.querySelector("div[class*='item-content-']")?.textContent.trim();
                //     if (auther === reply_obj["accountName"] && content === reply_obj["commentContent"]) {
                //         // 找到匹配的评论，执行操作
                //         replyNode = targetNode;
                //         break;
                //     }
                // }
                // if (!replyNode) {
                //     console.log('未匹配到了评论信息')
                // 未匹配到消息标签，直接回复
                sendMessage(
                    window.location.href,
                    reply_obj['commentReply'],
                    {id: reply_obj.id},
                    (res) => {
                        if (res.status !== 1) {
                            console.log('socket--回复评论消息发送失败', res)
                        } else {
                            console.log('socket--回复评论消息发送成功', res)
                            let reply_result = {
                                type: 'replyOk',
                                id: res.data.id.toString()
                            }
                            console.log('socket--回复评论成功，发送回执', JSON.stringify(reply_result))
                            socketWs.send(JSON.stringify(reply_result))
                        }
                    }
                )
                // } else {
                //     console.log('匹配到了评论信息', replyNode)
                //     // 匹配到标签就按照@进行回复
                //     replyEosMessage(replyNode, reply_obj["commentReply"], {id: reply_obj.id}, (res) => {
                //         if (res.status !== 1) {
                //             console.log("socket--回复评论消息发送失败", res);
                //         } else {
                //             console.log("socket--回复评论消息发送成功", res);
                //             let reply_result = {
                //                 type: "replyOk",
                //                 id: res.data.id.toString(),
                //             };
                //             console.log("socket--回复评论成功，发送回执", JSON.stringify(reply_result));
                //             socketWs.send(JSON.stringify(reply_result));
                //         }
                //     });
                // }
            } else {
                console.log('socket--未匹配到回复规则，不回复')
            }
        } catch (error) {
            if (event.data === 'success') {
                console.log('socket--接收心跳消息回执')
                return
            }
            console.log('socket--JSON 解析错误:', error, event.data)
        }
    }

    ws.onerror = function (error) {
        console.error('socket--WebSocket 错误:', error)
    }

    ws.onclose = function () {
        console.log('socket--连接已关闭，尝试重新连接...')
        clearInterval(heartbeatInterval) // 停止心跳检测
        socketWs = null

        // 设置 5 秒后重新连接
        setTimeout(connectSocket, 5000)
    }
}

// 监听评论

function observeComments(chatroomItems) {
    const config = {childList: true, subtree: false, attributes: false}
    const observer = new MutationObserver((mutationsList) => {
        mutationsList.forEach((mutation) => {
            // 监听子节点的新增
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        // 确保是元素节点
                        // 防止重复处理，给处理过的节点添加标记
                        console.log('新增评论节点1:', node.dataset.processed)
                        if (node.dataset.processed === 'true') {
                            return
                        }
                        handleComment(node, chatroomItems.childNodes[chatroomItems.childNodes.length - 1]) // 处理新增节点
                    }
                })
            }
        })
    })
    observer.observe(chatroomItems, config)
}

// 处理评论
async function handleComment(commentItem, commentItemNode) {
    // 从本地存储中读取关键词规则
    const result = await chrome.storage.local.get('liveroom_comments_rule')
    if (!result) {
        console.warn('未设置回复规则')
        return
    }
    const rules = result.liveroom_comments_rule?.keywords || []
    const ignoreNicks = result.liveroom_comments_rule?.ignoreNick.split('\n') || []
    let auther = commentItemNode.querySelector("div[class*='item-name-']")?.textContent.trim()
    let content = commentItemNode.querySelector("div[class*='item-content-']")?.textContent.trim()
    let login_nick_name = document
        .querySelector("div[class*='panel-profile-name-']")
        .textContent.trim()
    console.log('当前登录账号:', login_nick_name)
    if (content) {
        console.log('评论内容:', content, comment)
        if (content === comment['commentReply']) {
            console.log('回复信息跳过')
            return
        }
        // if (auther === login_nick_name + '：') {
        //   console.log('当前登录账号发出的评论不做采集')
        //   return
        // }

        // 将采集的评论数据发送至混剪系统
        if (socketWs && dyAccountNo) {
            if (commentItem.dataset.processed === 'true') {
                return // 避免重复处理
            }
            // 标记该节点已处理状态
            commentItem.dataset.processed = 'true'
            console.log('新增评论节点2:', commentItem)
            let socket_message = JSON.stringify({
                type: 'comment',
                commentContent: content,
                accountName: auther,
                roomNo: localStorage.getItem('dyAccountNo'),
                roomName: localStorage.getItem('dyRoomName')
            })
            console.log('评论信息已发送', socket_message)
            socketWs.send(socket_message)
        }

        let isIgnore = false
        // 匹配用户昵称
        for (const nickname of ignoreNicks) {
            if (nickname.length > 0 && auther && auther.includes(nickname)) {
                console.log(`匹配到忽略昵称: ${nickname}`)
                isIgnore = true
                return // 匹配后退出
            }
        }
        if (isIgnore) {
            return
        }

        rules.forEach((rule) => {
            if (content && content.includes(rule.keyword)) {
                console.log(`匹配到关键词: ${rule.keyword}, 准备发送回复: ${rule.reply}`)
                replyEosMessage(commentItemNode, rule.reply, {}, () => {
                    console.log('自动回复发送成功:', rule.reply)
                })
                // sendMessage(window.location.href, rule.reply, {}, () => {
                //     console.log('自动回复发送成功:', rule.reply);
                // });
            } else {
                console.log('未匹配到回复内容')
            }
        })
    }
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

// function listenLivePlanPage() {
//     console.log('监听直播计划页面----livesite/live/plan/edit?')
//     const saveBtn = document.querySelector(
//         'okee-current-live-loading.okee-current-live-loading-block button.okee-current-live-btn.okee-current-live-btn-type-primary'
//     )
//     if (saveBtn) {
//         saveBtn.addEventListener('click', () => {
//             console.log('保存按钮被点击，开始监听接口请求')
//             // 注入重写 fetch 的代码
//             const script = `
//                 (function() {
//                     const originalFetch = window.fetch;
//                     const whiteList = ['life/live/user/info/v1', 'life/live/shelves/anchor', 'life/live/status'];
//                     window.fetch = function(url, options) {
//                         if (whiteList.some(keyword => url.includes(keyword))) {
//                             return originalFetch(url, options).then(response => {
//                                 response.clone().text().then(body => {
//                                     // 触发自定义事件来传递数据
//                                     const event = new CustomEvent('fetchResponse', {
//                                         detail: {
//                                             url: url,
//                                             body: body
//                                         }
//                                     });
//                                     window.dispatchEvent(event);
//                                 });
//                                 return response;
//                             });
//                         } else {
//                             return originalFetch(url, options);
//                         }
//                     };
//                 })();
//             `
//             const scriptElement = document.createElement('script')
//             scriptElement.textContent = script
//             document.head.appendChild(scriptElement)
//         })
//     } else {
//         console.log('未找到保存按钮')
//     }
//
//     // 监听自定义事件来获取拦截的数据
//     window.addEventListener('fetchResponse', (event) => {
//         const {url, body} = event.detail
//         console.log('拦截到接口请求:', url)
//
//         if (url.includes('life/live/shelves/anchor')) {
//             console.log('拦截到直播货架主播数据:', body)
//             const data = JSON.parse(body)
//             const params = {
//                 dyAccountNo,
//                 products: []
//             }
//             // 可以将拦截的数据合并到 params 中，根据实际需求调整
//             params.shelvesAnchorData = data
//             console.log('发送数据到混剪系统:', params)
//             // 调用接口传递给后台
//             // const result = await $Request(API.createPlan, {
//             //   params
//             // });
//             // console.log('createPlan的res:', result);
//         }
//     })
// }
//
// async function getLivePlanData() {
//     try {
//         // https://eos.douyin.com/data/life/live/shelves/anchor/
//         // ?agg_card_id=0
//         // &room_id=0
//         // &req_source=pc_current&
//         // with_promotion_price_type=true
//         // &verifyFp=
//         // verify_m7o73xbx_1eRklkey_pPsb_48nq_9fGr_asmzoi8y99V2
//         // &fp=verify_m7o73xbx_1eRklkey_pPsb_48nq_9fGr_asmzoi8y99V2
//         // &msToken=Rgp7ZlZPgigzJFE9BxTtrOtNythGpbVfWtnvdkwH1znC8s5V515NKiBGtwMJZdVrc9lNUqVq5SWUiwv4rn-xCayBqOUo2wT_Ixo-vzxSo9_1iIs_cS1M7T9nu3yRyAfA1Io-V_ThjHNvlLAkYe2JVBWryPIc_JEagrllmYFkvA5h-6C1qQvesn0%3D&a_bogus=YjUfDwWLQ25VOd-n8OOQt4H4e69%2FNP8yRrT%2FSy3o9Fq2GHzGKWBqEdCxJoqGsbJFu8m5Eeq7rxzMOjxbOBi0Z2rkLmkfSLtfO4V9V0XLhqNXGt4mEN8NCLvzKw0e0Qvw-5C7N1D5AsMn2fVAnHViWBBaC5zHQRDdSNMSD%2FLy9EAXfSSkk9-0OHkZOyiqRD%3D%3D
//         const searchParams = new URLSearchParams(window.location.search).get('id')
//         const url = `https://eos.douyin.com/data/life/live/plan/detail/?plan_id=${searchParams}`
//         console.log('searchParams:', searchParams)
//         const response = await fetch(url, {
//             credentials: 'include' // 携带cookie
//         })
//
//         const responseData = await response.json()
//         console.log('获取直播计划数据成功:', responseData)
//         return responseData
//     } catch (e) {
//         console.error('获取直播计划数据失败:', e)
//     }
//     return null
// }
//
// // 新增独立事件绑定函数
// function bindButtonEvent(button) {
//     console.log('绑定保存按钮点击事件')
//     button.addEventListener('click', () => {
//         console.log('保存按钮被点击，开始监听接口请求')
//         injectFetchInterceptor()
//     })
// }
