function extractDomain(url) {
    try {
        const a = document.createElement('a');
        a.href = url;
        const hostname = a.hostname.replace(/^www\./, '');

        if (hostname === 'localhost' || /^\d+\.\d+\.\d+\.\d+$/.test(hostname)) {
            return hostname;
        }

        const parts = hostname.split('.');
        const tlds = ['com', 'net', 'org', 'gov', 'edu', 'cn', 'co', 'uk', 'jp', 'de', 'fr'];
        const last = parts[parts.length - 1];
        const secondLast = parts[parts.length - 2];

        if (tlds.includes(last) && tlds.includes(secondLast) && parts.length >= 3) {
            return parts.slice(-3).join('.');
        }

        return parts.slice(-2).join('.');
    } catch (e) {
        return '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggle');
    const statusDiv = document.getElementById('status');
    const domainInput = document.getElementById('domain');
    const blockedListEl = document.getElementById('blocked-list');

    let currentTab, currentDomain;

    // 加载当前域名和状态
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
        currentTab = tabs[0];
        currentDomain = extractDomain(currentTab.url);
        domainInput.value = currentDomain;

        chrome.storage.local.get(['blockDomains'], (res) => {
            const domainList = res.blockDomains || [];
            const isBlocked = domainList.includes(currentDomain);

            chrome.tabs.sendMessage(currentTab.id, {type: 'getVideoCount'}, (response) => {
                const count = response?.count ?? 0;
                statusDiv.textContent = isBlocked
                    ? `[OK] 已屏蔽此站，共屏蔽 ${count} 个视频`
                    : `⭕ 未屏蔽此站`;

                renderBlockedList(domainList);
            });
        });
    });

    // 切换当前域名屏蔽状态
    toggleBtn.addEventListener('click', () => {
        chrome.storage.local.get(['blockDomains'], (res) => {
            const domainList = res.blockDomains || [];
            const index = domainList.indexOf(currentDomain);
            const shouldBlock = index === -1;

            if (shouldBlock) {
                domainList.push(currentDomain);
            } else {
                domainList.splice(index, 1);
            }

            chrome.storage.local.set({blockDomains: domainList}, () => {
                chrome.tabs.sendMessage(currentTab.id, {type: 'getVideoCount'}, (response) => {
                    const count = response?.count ?? 0;
                    statusDiv.textContent = shouldBlock
                        ? `[OK] 已屏蔽此站，共屏蔽 ${count} 个视频`
                        : `⭕ 未屏蔽此站`;

                    renderBlockedList(domainList);

                    chrome.scripting.executeScript({
                        target: {tabId: currentTab.id},
                        files: ['content.js']
                    });
                });
            });
        });
    });

    // 渲染屏蔽列表
    function renderBlockedList(domainList) {
        blockedListEl.innerHTML = '';

        if (domainList.length === 0) {
            blockedListEl.textContent = '暂无屏蔽网站';
            return;
        }

        domainList.forEach(domain => {
            const li = document.createElement('li');
            li.textContent = domain + ' ';
            const btn = document.createElement('button');
            btn.textContent = '[X]取消';
            btn.style.marginLeft = '10px';
            btn.addEventListener('click', () => {
                removeDomain(domain);
            });
            li.appendChild(btn);
            blockedListEl.appendChild(li);
        });
    }

    // 从 block 列表中移除并刷新 UI
    function removeDomain(domainToRemove) {
        chrome.storage.local.get(['blockDomains'], (res) => {
            const domainList = res.blockDomains || [];
            const updated = domainList.filter(d => d !== domainToRemove);
            chrome.storage.local.set({blockDomains: updated}, () => {
                renderBlockedList(updated);

                // 如果是当前域名，刷新状态和页面视频显示
                if (domainToRemove === currentDomain) {
                    statusDiv.textContent = '⭕ 未屏蔽此站';

                    chrome.scripting.executeScript({
                        target: {tabId: currentTab.id},
                        files: ['content.js']
                    });
                }
            });
        });
    }
});
