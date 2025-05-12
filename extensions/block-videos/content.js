function countAllVideos(root = document) {
    let count = root.querySelectorAll('video').length;

    const iframes = root.querySelectorAll('iframe');
    for (const iframe of iframes) {
        try {
            const doc = iframe.contentDocument || iframe.contentWindow.document;
            if (doc) {
                count += countAllVideos(doc); // 递归统计
            }
        } catch (e) {
            // 跨域 iframe 无法访问，忽略
        }
    }

    return count;
}

function applyBlock(enabled) {
    const blockVideos = (root = document) => {
        root.querySelectorAll('video').forEach(v => v.style.display = enabled ? 'none' : '');

        const iframes = root.querySelectorAll('iframe');
        for (const iframe of iframes) {
            try {
                const doc = iframe.contentDocument || iframe.contentWindow.document;
                if (doc) blockVideos(doc);
            } catch (e) {
                // ignore cross-origin
            }
        }
    };

    blockVideos();
}

const domain = location.hostname.replace(/^www\./, '');

chrome.storage.local.get(['blockDomains'], (res) => {
    const blockDomains = res.blockDomains || [];
    const shouldBlock = blockDomains.includes(domain);

    applyBlock(shouldBlock);

    const observer = new MutationObserver(() => {
        applyBlock(shouldBlock);
    });
    observer.observe(document.body, {childList: true, subtree: true});
});

// 响应来自 popup 的视频数量请求（含 iframe）
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === 'getVideoCount') {
        const count = countAllVideos();
        sendResponse({count});
    }
});
