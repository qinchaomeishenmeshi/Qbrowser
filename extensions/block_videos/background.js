const DEFAULT_DOMAINS = ['douyinec.com']; // 在此添加默认屏蔽网站

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'getStats') {
        chrome.storage.local.get(['blockDomains'], async (result) => {
            let domainList = result.blockDomains;

            // 如果是首次加载，设置默认屏蔽列表
            if (!Array.isArray(domainList)) {
                domainList = [...DEFAULT_DOMAINS];
                chrome.storage.local.set({blockDomains: domainList});
            }

            const isBlocked = domainList.includes(message.domain);

            // 从 content script 获取当前页 video 数量
            let videoCount = 0;
            if (sender.tab?.id) {
                try {
                    const results = await chrome.scripting.executeScript({
                        target: {tabId: sender.tab.id},
                        func: () => document.querySelectorAll('video, img').length
                    });
                    videoCount = results[0]?.result ?? 0;
                } catch (e) {
                    console.error('获取视频数量失败:', e);
                }
            }

            sendResponse({blocked: isBlocked, count: videoCount, domainList});
        });
        return true;
    }

    if (message.type === 'toggleDomain') {
        chrome.storage.local.get(['blockDomains'], (res) => {
            let list = res.blockDomains || [];
            const domain = message.domain;
            const index = list.indexOf(domain);

            if (index > -1) {
                list.splice(index, 1);
            } else {
                list.push(domain);
            }

            chrome.storage.local.set({blockDomains: list});
        });
    }
});
