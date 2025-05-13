chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'getStats') {
        chrome.storage.local.get(['blockDomains'], async (result) => {
            const domainList = result.blockDomains || [];
            const isBlocked = domainList.includes(message.domain);

            // 从 content script 获取当前页 video 数量
            let videoCount = 0;
            if (sender.tab?.id) {
                try {
                    const results = await chrome.scripting.executeScript({
                        target: {tabId: sender.tab.id},
                        func: () => document.querySelectorAll('video').length
                    });
                    videoCount = results[0]?.result ?? 0;
                } catch (e) {
                }
            }

            sendResponse({blocked: isBlocked, count: videoCount, domainList});
        });
        return true;
    }

    if (message.type === 'toggleDomain') {
        chrome.storage.local.get(['blockDomains'], (res) => {
            const list = res.blockDomains || [];
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
