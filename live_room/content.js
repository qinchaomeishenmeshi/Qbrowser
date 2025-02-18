// 获取抖音账号信息
let dyAccountNo = null

// 连接socket
let socketWs = null
let reconnectStartTime = null // 记录重连的起始时间

// 保存规则配置后启动定时器
let timerId = null
// 监听直播间声音的定时器
let audioTimerId = null
// 页面刷新的定时器
let reloadPageTimerId = null
// 播放直播画面按钮
let playLiveScreenBtn = null

const liveScreenURL = 'https://eos.douyin.com/dp/liveScreen'

let comment = {}

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
    }
})

// 监听规则变化
chrome.storage.onChanged.addListener((changes, namespace) => {
    console.log('changes', namespace, changes)
    if (namespace === 'local' && changes.liveroom_comments_rule?.newValue) {
        if (
            changes.liveroom_comments_rule.newValue.time &&
            changes.liveroom_comments_rule.newValue.time.length > 0
        ) {
            // 定时回复内容
            const newReply = changes.liveroom_comments_rule.newValue.time[0].reply
            // 定时器间隔时间
            const newInterval = parseInt(changes.liveroom_comments_rule.newValue.time[0].time)
            if (!isNaN(newInterval) && newInterval > 0) {
                console.log(`检测到时间设置变化，新间隔时间: ${newInterval} ms`)
                startTimer(newInterval, newReply) // 重置定时器
            } else {
                console.warn('时间设置无效，未重置定时器')
                stopTimer()
            }
        } else {
            stopTimer()
        }
    }
})

// 监听直播间变化
document.addEventListener('DOMContentLoaded', () => {
    console.log("页面加载完成 DOMContentLoaded")
    // 定义选择器常量，提高可维护性
    const SELECTORS = {
        chatWrap: "div[class*='comment-wrap-']",
        chatList: "div[class*='list-']",
        chatItems: 'div[class*="item-"]'
    }

    // 开启页面刷新的定时器
    startReloadPageTimer()

    // 创建 MutationObserver 回调函数
    const observerCallback = async () => {
        try {
            // 查找聊天容器
            const chatWrap = document.querySelector(SELECTORS.chatWrap)
            if (!chatWrap) return

            // 自动进入直播间
            if (!playLiveScreenBtn) {
                playLiveScreenBtn = document.querySelector('button[class="okee-current-live-btn okee-current-live-btn-size-md okee-current-live-btn-type-primary okee-current-live-btn-shape-angle okee-current-live-can-input-grouped"]');
                if (playLiveScreenBtn) {
                    playLiveScreenBtn.click()
                    console.log("监测到播放直播画面按钮")
                } else {
                    console.log("未监测到播放直播画面按钮")
                }
            }

            // 获取直播间配置信息中的是否开启音频检测
            const result = await chrome.storage.local.get('liveroom_comments_rule');
            const audioChecked = result.liveroom_comments_rule?.audioChecked || false
            if (audioChecked) {
                console.log('已配置开启直播间声音检测')
                startAudioTimer()
            } else {
                console.log('未配置开启直播间声音检测')
                checkAudioStopTimer()
            }

            // 查找评论列表
            const chatListEle = chatWrap.querySelector(SELECTORS.chatList)
            if (!chatListEle) return

            // 查找评论项
            const chatroomItems = chatListEle.querySelectorAll(SELECTORS.chatItems)
            if (!chatroomItems?.length) return

            // 目标节点加载完成，停止全局监听
            console.log('目标节点已加载:', chatroomItems)
            observer.disconnect()

            // 开始监听评论区变化
            observeComments(chatListEle)
        } catch (error) {
            console.error('直播间监听出错:', error)
        }
    }

    // 配置 MutationObserver
    const observerConfig = {
        childList: true,
        subtree: true
    }

    // 创建并启动 observer
    const observer = new MutationObserver(observerCallback)
    observer.observe(document.body, observerConfig)
    creatTopTips('插件已开启评论区监听')
    console.log('准备连接socket')
    setTimeout(() => {
        getDyAccountNo()
    },5000)
})

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
        creatTopTips('未找到抖音账号信息')
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
    connectSocket()
}

// 连接socket
function connectSocket() {
    if (socketWs) {
        creatTopTips('socket--已链接，无需重复链接')
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
        creatTopTips('socket--重连时间超过5分钟，停止重连', true)
        reconnectStartTime = null // 重置时间计数
        return
    }

    const SOCKET_URL =
        'wss://hj.qwang.com.cn/websocket/livestreamingcomment/COMMENT_PLUGIN/' + dyAccountNo
    const ws = new WebSocket(SOCKET_URL)
    let heartbeatInterval

    ws.onopen = function () {
        creatTopTips('socket--链接已打开')
        socketWs = ws
        reconnectStartTime = null // 重置重连时间计数，因为连接成功了

        // 心跳检测
        heartbeatInterval = setInterval(() => {
            creatTopTips('直播监控中...', 9000)
            if (socketWs.readyState === WebSocket.OPEN) {
                socketWs.send(
                    JSON.stringify({
                        type: 'ping',
                        roomName: localStorage.getItem('dyRoomName'),
                        roomNo: localStorage.getItem('dyAccountNo'),
                        terminal:"pc"
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
                return; // 避免重复处理
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

// 启动定时器
function startTimer(interval, content) {
    if (timerId) {
        stopTimer() // 清理旧定时器
    }
    timerId = setInterval(() => {
        console.log('执行定时任务...')
        // 在这里处理具体的任务逻辑
        sendMessage(window.location.href, content, {}, () => {
            console.log('定时任务发送消息成功:', content)
        })
    }, interval)
    console.log(`定时器已启动，间隔时间: ${interval} ms`)
}

// 停止定时器
function stopTimer() {
    if (timerId) {
        clearInterval(timerId)
        timerId = null
        console.log('定时器已停止')
    }
}

// 启动音频定时器
function startAudioTimer() {
    if (audioTimerId) {
        checkAudioStopTimer() // 清理旧定时器
    }
    audioTimerId = setInterval(() => {
        checkAudio()
    }, 3000)
}

// 检查直播间音频
// 检查直播间音频
function checkAudio() {
    // 首先检查直播状态
    const submenuContent = document.querySelector('.okee-main-submenu-content span');
    if (!submenuContent || submenuContent.textContent !== '正在直播') {
        console.log('当前不是直播状态，跳过音频检查');
        return;
    }

    const videoElement = document.querySelector('video');
    if (!videoElement) {
        if (audioTimerId) {
            checkAudioStopTimer(); // 清理旧定时器
        }
        creatTopTips('未找到音频或视频元素，请先进入直播间。');
        return;
    }
    creatTopTips('开启监听直播声音状态', 3000);

    // 将视频音量设置为 0.1
    videoElement.volume = 0.1;

    // 防止重复绑定 MediaElementSourceNode
    if (!videoElement._audioSourceNode) {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const mediaElementSource = audioContext.createMediaElementSource(videoElement);
        const analyser = audioContext.createAnalyser();

        // 绑定到 videoElement，避免重复创建
        videoElement._audioSourceNode = {mediaElementSource, analyser, audioContext};

        // 连接音频处理链
        mediaElementSource.connect(analyser);
        analyser.connect(audioContext.destination);
    }

    const {analyser} = videoElement._audioSourceNode; // 从缓存中获取 AnalyserNode
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const debounceInterval = 500; // 每 500ms 检测一次
    let lastCheckTime = 0;
    let warningInterval = null; // 定时器，用于循环语音播报
    let isNoSoundWarningActive = false;

    // 语音播报函数
    function speakMessage(message) {
        const audioResult = {
            type: 'alarm',
            roomNo: localStorage.getItem('dyAccountNo'),
            roomName: localStorage.getItem('dyRoomName'),
        };
        console.log('socket--无声音提醒', JSON.stringify(audioResult));
        socketWs.send(JSON.stringify(audioResult));

        const utterance = new SpeechSynthesisUtterance(message);
        utterance.lang = 'zh-CN';
        window.speechSynthesis.speak(utterance);
    }

    function startNoSoundWarning() {
        if (isNoSoundWarningActive) return;
        console.log('启动无声音提醒循环');
        isNoSoundWarningActive = true;
        const dyRoomName = localStorage.getItem('dyRoomName');

        warningInterval = setInterval(() => {
            speakMessage(`直播间${dyRoomName}当前没有声音，请检查音频设置！`);
        }, 3000);
    }

    function stopNoSoundWarning() {
        if (!isNoSoundWarningActive) return;
        creatTopTips('停止无声音提醒');
        isNoSoundWarningActive = false;

        clearInterval(warningInterval);
        warningInterval = null;
        window.speechSynthesis.cancel();
    }

    let noSoundWarningSent = false;

    function checkAudioActivity() {
        const currentTime = performance.now();
        const xgPlayer = document.querySelector('.xgplayer.xgplayer-pause');
        if (currentTime - lastCheckTime < debounceInterval) {
            requestAnimationFrame(checkAudioActivity);
            return;
        }

        // 视频播放组件不存在时停止提醒
        if (!document.querySelector('video')) {
            stopNoSoundWarning();
            return;
        }

        lastCheckTime = currentTime;
        analyser.getByteFrequencyData(dataArray);

        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        if (average > 0 || xgPlayer) {
            console.log('当前有声音');
            noSoundWarningSent = false;
            stopNoSoundWarning();
        } else {
            console.log('当前无声音');
            startNoSoundWarning();
        }

        requestAnimationFrame(checkAudioActivity);
    }

    checkAudioActivity();
}


// 检查直播间音频的定时器
function checkAudioStopTimer() {
    if (audioTimerId) {
        clearInterval(audioTimerId)
        audioTimerId = null
        console.log('检测直播间音频的定时器已停止')
    }
}

// 开始一个5分钟刷新页面的定时器
function startReloadPageTimer() {
    stopReloadPageTimer()
    reloadPageTimerId = setInterval(() => {
        console.log('执行页面自动刷新的定时任务...')
        location.reload()
        // 进入直播间
    }, 1000 * 60 * 5)
}

// 停止页面刷新的定时器
function stopReloadPageTimer() {
    if (reloadPageTimerId) {
        clearInterval(reloadPageTimerId)
        reloadPageTimerId = null
        console.log('页面刷新的定时器已停止')
    }
}

// 创建一个屏幕顶部的fixed提示框，黑色背景，白色16号字体。参数为需要展示的文字，文字居中展示
function creatTopTips(text, timeOut = 5000) {
    const fixedTipBox = document.createElement('div');
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
    `;
    fixedTipBox.textContent = text;

    // 点击提示框移除它
    fixedTipBox.addEventListener('click', () => {
        fixedTipBox.remove();
    });

    document.body.appendChild(fixedTipBox);

    // 指定时间后自动删除提示框
    const autoRemoveTimer = setTimeout(() => {
        if (fixedTipBox.parentNode) {
            fixedTipBox.remove();
        }
    }, timeOut);

    // 返回定时器 ID，便于外部操作（如取消自动移除）
    return {fixedTipBox, autoRemoveTimer};
}
