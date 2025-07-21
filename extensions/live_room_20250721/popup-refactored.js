// 重构版本的 popup.js - 使用配置管理器
// 导入配置管理器（在manifest中已引入）
// const configManager = new ConfigManager();

// DOM Elements
const wordList = document.getElementById("word-list");
const addWordButton = document.getElementById("add-word-button");
const randomSendButton = document.getElementById("random-send-button");
const inputModal = document.getElementById("input-modal");
const newWordsInput = document.getElementById("new-words-input");
const saveWordsButton = document.getElementById("save-words-button");
const cancelWordsButton = document.getElementById("cancel-words-button");
const clearWordsButton = document.getElementById("clear-words-button");

const tabKeywords = document.getElementById("tab-keywords");
const tabComments = document.getElementById("tab-comments");
const keywordsTab = document.getElementById("keywords-tab");
const commentsTab = document.getElementById("comments-tab");

const rulesInput = document.getElementById('keywords-rules-input');
const timeRulesInput = document.getElementById('time-rules-input');
const saveRulesButton = document.getElementById('save-rules-button');

const ignoreNickInput = document.getElementById('ignore-user-input');
const audioCheckbox = document.getElementById("audio-detection-toggle");

// 配置管理器实例
let configManager = null;

// 初始化配置管理器
async function initializeConfig() {
    try {
        if (typeof ConfigManager !== 'undefined') {
            configManager = new ConfigManager();
            await configManager.loadConfig();
            console.log('Popup配置管理器初始化成功');
        } else {
            console.warn('ConfigManager未定义，使用默认配置');
        }
    } catch (error) {
        console.error('配置管理器初始化失败:', error);
    }
}

// 获取配置值的辅助函数
function getConfigValue(key, defaultValue) {
    if (configManager) {
        return configManager.get(key, defaultValue);
    }
    return defaultValue;
}

// 保存规则事件处理
saveRulesButton.addEventListener('click', async () => {
    const rulesText = rulesInput.value.trim();
    const timeRulesText = timeRulesInput.value.trim();

    // 解析关键词规则  你好#大家好
    const keywordRules = rulesText
        .split('\n')
        .map(line => {
            const [keyword, reply] = line.split('#').map(s => s.trim());
            return {keyword, reply};
        })
        .filter(rule => rule.keyword && rule.reply);

    console.log('解析后的规则:', keywordRules);

    // 解析忽略用户规则
    const ignoreNick = ignoreNickInput.value.trim();

    // 解析时间规则 5#大家好
    const timeRules = timeRulesText.split('\n').map(s => {
        const [time, reply] = s.split('#').map(s => s.trim());
        return {time, reply};
    });

    console.log('直播间开启音频检测：', audioCheckbox.checked);

    // 使用配置管理器获取存储键名
    const storageKey = getConfigValue('storage.keys.liveroom_comments_rule', 'liveroom_comments_rule');
    
    // 存储到本地
    await chrome.storage.local.set({
        [storageKey]: {
            keywords: keywordRules, 
            time: timeRules, 
            ignoreNick: ignoreNick, 
            audioChecked: audioCheckbox.checked
        }
    });

    console.log('保存的关键词规则:', keywordRules);
    console.log('保存的忽略昵称规则:', ignoreNick);
    console.log('保存的时间规则:', timeRules);
    console.log('保存的音频检测规则：', audioCheckbox.checked);
    
    // 使用配置管理器获取提示文本
    const successMessage = getConfigValue('messages.save_success', '保存成功！');
    alert(successMessage);
});

// Load words from storage and display
async function loadWords() {
    console.log('load words');
    const storageKey = getConfigValue('storage.keys.frequent_words', 'frequentWords');
    const result = await chrome.storage.local.get(storageKey);
    const words = result[storageKey] || [];
    wordList.innerHTML = "";

    words.forEach((wordObj, index) => {
        const wordItem = document.createElement("div");
        wordItem.className = "word-item";
        wordItem.style.backgroundColor = wordObj.used ? "#ddd" : "#fff";

        const wordText = document.createElement("span");
        wordText.textContent = wordObj.word;

        const sendButton = document.createElement("button");
        const sendButtonText = getConfigValue('ui.buttons.send', '发送');
        sendButton.textContent = sendButtonText;
        sendButton.addEventListener("click", () => {
            sendInputMessage(wordObj, index);
        });

        wordItem.appendChild(wordText);
        wordItem.appendChild(sendButton);
        wordList.appendChild(wordItem);
    });
}

// 加载关键词配置信息
async function loadKeywords() {
    const storageKey = getConfigValue('storage.keys.liveroom_comments_rule', 'liveroom_comments_rule');
    const result = await chrome.storage.local.get(storageKey);
    
    if (!result || !result[storageKey]) {
        console.warn("未设置回复规则");
        return;
    }
    
    const rules = result[storageKey]?.keywords || [];
    console.log("读取保存的关键词配置", rules);
    
    // 关键词配置信息回显
    rules.forEach(rule => {
        let content = `${rule.keyword}#${rule.reply}`;
        rulesInput.value += content + '\n';
    });
    
    // 忽略用户回显
    ignoreNickInput.value = result[storageKey]?.ignoreNick || '';
    
    // 定时规则回显
    const timeRules = result[storageKey]?.time || [];
    timeRules.forEach(rule => {
        if (rule.time.length === 0) {
            return;
        }
        let content = `${rule.time}#${rule.reply}`;
        timeRulesInput.value += content + '\n';
    });
    
    audioCheckbox.checked = result[storageKey]?.audioChecked || false;
}

// 标签页切换功能
tabKeywords.addEventListener("click", () => {
    switchTab(tabKeywords, keywordsTab);
});

tabComments.addEventListener("click", () => {
    switchTab(tabComments, commentsTab);
});

function switchTab(tabButton, tabContent) {
    // 清除所有 Tab 按钮和内容的激活状态
    document.querySelectorAll(".tab-button").forEach(button => button.classList.remove("active"));
    document.querySelectorAll(".tab").forEach(tab => tab.classList.remove("active"));

    // 激活当前按钮和内容
    tabButton.classList.add("active");
    tabContent.classList.add("active");
}

// 清空常用词
clearWordsButton.addEventListener("click", async () => {
    console.log('清空常用词');
    const confirmText = getConfigValue('messages.confirm_clear', '确定要清空吗？');
    let confirmResult = confirm(confirmText);
    
    if (confirmResult === true) {
        const storageKey = getConfigValue('storage.keys.frequent_words', 'frequentWords');
        await chrome.storage.local.remove([storageKey], function () {
            if (chrome.runtime.lastError) {
                console.error("删除数据时出错:", chrome.runtime.lastError);
            } else {
                console.log("指定的数据已被删除");
                loadWords();
            }
        });
    }
});

// 取消添加词汇
cancelWordsButton.addEventListener("click", async () => {
    newWordsInput.value = "";
    inputModal.classList.add("hidden");
});

// Save new words from input modal
saveWordsButton.addEventListener("click", async () => {
    const newWords = newWordsInput.value.split("\n").map(word => word.trim()).filter(Boolean);
    const storageKey = getConfigValue('storage.keys.frequent_words', 'frequentWords');
    const result = await chrome.storage.local.get(storageKey);
    const words = result[storageKey] || [];

    newWords.forEach(word => words.push({word: word, used: false}));
    await chrome.storage.local.set({[storageKey]: words});

    newWordsInput.value = "";
    inputModal.classList.add("hidden");
    loadWords();
});

// Mark word as used
async function markAsUsed(index) {
    const storageKey = getConfigValue('storage.keys.frequent_words', 'frequentWords');
    const result = await chrome.storage.local.get(storageKey);
    const words = result[storageKey] || [];

    if (words[index]) {
        words[index].used = true;
        await chrome.storage.local.set({[storageKey]: words});
        loadWords();
    }
}

// 向输入框输入数据完成发送
async function sendInputMessage(text, index) {
    chrome.tabs.query({active: true, currentWindow: true}, function (tabs) {
        chrome.tabs.sendMessage(tabs[0].id, {
            action: 'send_input_message', 
            data: {
                word: text.word,
                url: tabs[0].url
            }
        }, function (response) {
            console.log('result = ', response);
            if (response && response.status === 1) {
                markAsUsed(index);
            }
        });
    });
}

// Handle random send
randomSendButton.addEventListener("click", async () => {
    const storageKey = getConfigValue('storage.keys.frequent_words', 'frequentWords');
    const result = await chrome.storage.local.get(storageKey);
    const words = result[storageKey] || [];
    const unusedWords = words.filter(wordObj => !wordObj.used);

    if (unusedWords.length > 0) {
        const randomWord = unusedWords[Math.floor(Math.random() * unusedWords.length)];
        // 发送内容
        const index = words.findIndex(wordObj => wordObj.word === randomWord.word);
        await sendInputMessage(randomWord, index);
    } else {
        const noWordsMessage = getConfigValue('messages.no_available_words', '没有可用的关键词');
        alert(noWordsMessage);
    }
});

// Show input modal for adding new words
addWordButton.addEventListener("click", () => {
    inputModal.classList.remove("hidden");
});

// Close modal if clicked outside
inputModal.addEventListener("click", (event) => {
    if (event.target === inputModal) {
        inputModal.classList.add("hidden");
    }
});

// 初始化应用
async function initializeApp() {
    await initializeConfig();
    // 加载提示词和关键词
    loadWords();
    loadKeywords();
}

// 启动应用
initializeApp();