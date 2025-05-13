// —— 自动重定向逻辑 ——
// 如果当前页面是 https://www.douyinec.com 或其子路径，立即跳转：
if (location.hostname === 'www.douyinec.com') {
    // 防止反复跳转
    const target = 'https://buyin.jinritemai.com/mpa/account/login?log_out=1&type=24';
    if (location.href !== target) {
        window.location.replace(target);
    }
    // 跳转之后后续脚本不再执行
    throw new Error('redirecting to jinritemai login');
}

function countAllVideos(root = document) {
    let count = root.querySelectorAll('video, img').length;

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
        if (enabled) {
            root.querySelectorAll('video, img').forEach(v => v.remove());
        }

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
