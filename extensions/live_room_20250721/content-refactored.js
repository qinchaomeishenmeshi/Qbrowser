/**
 * @file content-refactored.js
 * @description 重构后的抖音直播间内容脚本，使用配置管理器替换硬编码配置
 */

// =================================================================================
// #region Configuration & State
// =================================================================================

// 全局配置管理器实例
let config = null;

// 应用状态
const APP_STATE = {
  dyAccountNo: null,
  cacheData: "",
  isSyncing: false,
  livePlanData: null,
};

// 同步按钮文本配置（将从配置文件加载）
let SYNC_BUTTON_TEXT = {};

// #endregion

// =================================================================================
// #region Initialization
// =================================================================================

/**
 * 初始化应用
 */
async function init() {
  console.log("页面加载完成 DOMContentLoaded");

  try {
    // 加载配置
    config = await configManager.loadConfig();
    SYNC_BUTTON_TEXT = config.ui.sync_button.text;
    
    console.log("✅ 配置加载完成");
    
    // 初始化各个模块
    setupAccountObserver();
    injectFetchInterceptor();
    setupEventListeners();
    setupPeriodicTasks();

    // 根据域名执行特定逻辑
    if (configManager.isTargetHostname(window.location.hostname, 'eos')) {
      syncPunishList();
    }

    // 检查是否为百应直播控制页面
    const buyinUrl = configManager.get('urls.buyin_live_control_create');
    if (window.location.href.startsWith(buyinUrl)) {
      setupMixedCutSyncButton();
    }
  } catch (error) {
    console.error("❌ 初始化失败:", error);
  }
}

// 等待DOM加载完成后初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// #endregion

// =================================================================================
// #region Event Listeners & Observers
// =================================================================================

/**
 * 设置事件监听器
 */
function setupEventListeners() {
  chrome.runtime.onMessage.addListener(handleChromeMessages);
  window.addEventListener("fetchResponse", handleFetchResponses);
}

/**
 * 处理Chrome消息
 */
function handleChromeMessages(request, sender, sendResponse) {
  console.log("接收到消息:", { request, sender });

  if (
    request.action === "DO_DAILY_TASK" &&
    configManager.isTargetHostname(window.location.hostname, 'eos')
  ) {
    console.log(
      `执行每日任务: ${new Date().getHours() * 100 + new Date().getMinutes()}`
    );
    get_replay_punish_list().then((res) => {
      console.log("punish_list", res);
    });
  } else {
    console.log("其他消息", request);
  }
}

/**
 * 处理Fetch响应
 */
function handleFetchResponses(event) {
  const { url, status, body } = event.detail;
  console.log("接口监听:", { url, status });

  const urls = configManager.getUrls();
  
  if (url.includes(urls.live_plans_api) && status === 200) {
    console.log("拦截到直播计划数据:", body);
    APP_STATE.livePlanData = body;
    createTopTips(configManager.getTip('live_plan_data_success'), { type: "success" });
  } else if (url.includes(urls.plan_detail_api) && status === 200) {
    handlePlanDetailResponse(body);
  } else if (url.includes(urls.agreement_api) && status === 200) {
    handleAgreementResponse(url);
  }
}

/**
 * 设置账号观察器
 */
function setupAccountObserver() {
  if (!configManager.isTargetHostname(window.location.hostname, 'eos')) return;
  
  const timeouts = configManager.getTimeouts();
  const selectors = configManager.getSelectors();
  
  let timeoutId = null;
  const observer = new MutationObserver((_mutations, obs) => {
    const accountPanel = document.querySelector(selectors.account_panel);
    if (accountPanel) {
      console.log("检测到账号面板元素已加载");
      obs.disconnect();
      getDyAccountNo();
      clearTimeout(timeoutId);
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  timeoutId = setTimeout(() => {
    observer.disconnect();
    createTopTips(configManager.getTip('account_loading_timeout'), { type: "error" });
    console.error("账号面板元素加载超时");
  }, timeouts.account_observer);
}

/**
 * 设置周期性任务
 */
function setupPeriodicTasks() {
  const timeouts = configManager.getTimeouts();
  const selectors = configManager.getSelectors();
  
  // 每小时同步一次违规记录
  setInterval(syncPunishList, timeouts.periodic_punish_sync);
  
  // 每3秒检查一次违规弹窗
  setInterval(() => {
    const modal_wrapper = document.querySelector(selectors.modal_wrapper);
    if (modal_wrapper) {
      getModalText();
    }
  }, timeouts.modal_check_interval);
}

// #endregion

// =================================================================================
// #region UI Functions
// =================================================================================

/**
 * 设置混剪同步按钮
 */
function setupMixedCutSyncButton() {
  console.log("setupMixedCutSyncButton:");

  const timeouts = configManager.getTimeouts();
  const selectors = configManager.getSelectors();
  const uiConfig = configManager.getUI();

  const observer = new MutationObserver((mutations, obs) => {
    const savePlanButton = Array.from(document.querySelectorAll("button")).find(
      (btn) => btn.textContent.trim() === selectors.save_plan_button_text
    );

    if (savePlanButton) {
      console.log("检测到'保存计划'按钮，准备插入新按钮。");
      obs.disconnect();

      const syncButton = document.createElement("button");
      syncButton.textContent = SYNC_BUTTON_TEXT.default;

      // 应用样式配置
      syncButton.className = savePlanButton.className;
      Object.assign(syncButton.style, uiConfig.sync_button.buyin_styles);

      syncButton.addEventListener("click", async () => {
        await handleBuyinSyncButtonClick(syncButton);
      });

      savePlanButton.parentElement.insertBefore(syncButton, savePlanButton);
      console.log("'同步混剪系统'按钮已成功添加。");
    }
  });

  console.log("开始观察DOM变化以寻找'保存计划'按钮...");
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  setTimeout(() => {
    observer.disconnect();
    console.log("超时：未找到'保存计划'按钮，停止观察。");
  }, timeouts.save_plan_button_observer);
}

/**
 * 处理百应同步按钮点击
 */
async function handleBuyinSyncButtonClick(syncButton) {
  if (!APP_STATE.livePlanData) {
    console.warn("暂无缓存的直播计划数据");
    createTopTips(configManager.getTip('no_live_plan_data'), { type: "error" });
    return;
  }

  try {
    const { code, data } = JSON.parse(APP_STATE.livePlanData);
    if (code !== 0 || !data.live_plan_map) {
      createTopTips(configManager.getTip('live_plan_format_error'), { type: "error" });
      return;
    }

    const params = new URLSearchParams(window.location.search);
    const planId = params.get("planId");
    const planData = data.live_plan_map[planId];

    if (!planData || !planData.products?.products) {
      createTopTips(configManager.getTip('no_plan_or_products'), { type: "error" });
      return;
    }

    const productList = planData.products.products;
    console.log("开始处理商品列表:", productList);
    createTopTips(configManager.getTip('sync_start', { count: productList.length }), {
      type: "info",
    });

    await processProductList(productList);

    const planName = planData.title || "";
    await buYinSendProductsListToBackground(productList, planName);

    createTopTips(configManager.getTip('sync_complete'), { type: "success" });
  } catch (error) {
    console.error("处理直播计划数据时出错:", error);
    createTopTips(configManager.getTip('sync_error'), { type: "error" });
  }
}

/**
 * 处理商品列表
 */
async function processProductList(productList) {
  const urls = configManager.getUrls();
  const httpConfig = configManager.getHttp();
  const business = configManager.getBusiness();

  const productPromises = productList.map(async (product) => {
    const promotionId = product.product_id;
    if (!promotionId) return;

    console.log(`正在处理商品 ID: ${promotionId}`);

    const headers = {
      Accept: httpConfig.headers.accept,
      "Content-Type": httpConfig.headers.content_type,
      Referer: `https://haohuo.jinritemai.com/ecommerce/trade/detail/index.html?id=${promotionId}&origin_type=pc_buyin_selection_decision`,
      "User-Agent": httpConfig.user_agent,
    };
    const body = `promotion_id=${promotionId}&enter_from=&meta_param=&is_h5=1`;

    try {
      const responseData = await fetchProductDetail(urls.product_detail_api, {
        method: "POST",
        headers,
        body,
        credentials: httpConfig.credentials,
      });

      if (responseData.status_code === 0) {
        console.log(`商品 ${promotionId} 同步成功:`, responseData.detail_info);
        const formattedData = formatProductDetails(responseData);
        if (formattedData) {
          product.detailInfo = JSON.stringify(formattedData.detail);
          product.configStr = formattedData.config.join(",");
          product.infoStr = formattedData.info.join(",");
          product.fromType = business.product_from_types.buyin;
        }
      } else {
        throw new Error(responseData.error || `获取商品 ${promotionId} 详情失败`);
      }
    } catch (error) {
      console.error(`商品 ${promotionId} 同步失败:`, error);
      createTopTips(`商品 ${promotionId} 同步失败`, { type: "error" });
    }
  });

  await Promise.allSettled(productPromises);
}

/**
 * 获取商品详情
 */
function fetchProductDetail(url, options) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      {
        action: "FETCH_PRODUCT_DETAIL",
        data: { url, options },
      },
      (response) => {
        if (chrome.runtime.lastError) {
          return reject(chrome.runtime.lastError);
        }
        if (response && response.success) {
          resolve(response.data);
        } else {
          reject(new Error(response?.error || "Background script returned an error."));
        }
      }
    );
  });
}

/**
 * 创建同步容器
 */
function createSyncContainer() {
  const existingContainer = document.querySelector(".sync_wj");
  if (existingContainer) {
    existingContainer.remove();
  }

  const selectors = configManager.getSelectors();
  const parentElement = document.querySelector(selectors.sync_container_parent)?.parentElement;

  if (!parentElement) {
    console.error(configManager.getTip('no_target_container'));
    return;
  }

  const syncContainer = document.createElement("div");
  syncContainer.className = "sync_wj";

  const syncButton = document.createElement("button");
  const uiConfig = configManager.getUI();
  Object.assign(syncButton.style, uiConfig.sync_button.styles);
  syncButton.textContent = SYNC_BUTTON_TEXT.default;

  syncButton.addEventListener("click", () => handleSyncButtonClick(syncButton));

  syncContainer.appendChild(syncButton);
  parentElement.appendChild(syncContainer);
}

/**
 * 处理同步按钮点击
 */
async function handleSyncButtonClick(syncButton) {
  if (APP_STATE.isSyncing) return;

  setSyncButtonState(syncButton, true);

  try {
    const result = await processProducts(
      JSON.parse(APP_STATE.cacheData),
      sendProductsListToBackground
    );
    console.log("发送商品数据到后台成功", result);
    syncButton.textContent = SYNC_BUTTON_TEXT.success;
    createTopTips(configManager.getTip('all_products_complete'), {
      type: "success",
    });
    setTimeout(() => {
      syncButton.textContent = SYNC_BUTTON_TEXT.default;
    }, configManager.get('timeouts.success_message_duration'));
  } catch (error) {
    console.error("发送商品数据到后台失败", error);
    createTopTips(error.toString(), { type: "error" });
    syncButton.textContent = SYNC_BUTTON_TEXT.error;
    setTimeout(() => {
      syncButton.textContent = SYNC_BUTTON_TEXT.reload;
    }, configManager.get('timeouts.success_message_duration'));
  } finally {
    setSyncButtonState(syncButton, false);
  }
}

/**
 * 设置同步按钮状态
 */
function setSyncButtonState(button, isLoading) {
  APP_STATE.isSyncing = isLoading;
  button.style.opacity = isLoading ? "0.7" : "1";
  button.style.cursor = isLoading ? "not-allowed" : "pointer";
  if (isLoading) {
    button.textContent = SYNC_BUTTON_TEXT.loading;
  }
}

/**
 * 创建顶部提示框
 * @param {string} text - 需要展示的文字
 * @param {object} options - 配置项
 */
function createTopTips(text, options = {}) {
  const { timeout = 3000, type = "info" } = options;
  const uiConfig = configManager.getUI();
  const tipConfig = uiConfig.top_tips;

  const style = { ...tipConfig };
  delete style.colors; // 移除colors属性，因为它不是CSS样式
  
  style.backgroundColor = tipConfig.colors[type] || tipConfig.colors.info;

  const tipElement = document.createElement("div");
  Object.assign(tipElement.style, style);
  tipElement.textContent = text;
  document.body.appendChild(tipElement);

  setTimeout(() => {
    tipElement.style.top = "40px";
    tipElement.style.opacity = "1";
  }, 50);

  const removeTip = () => {
    clearTimeout(autoRemoveTimer);
    tipElement.style.top = "20px";
    tipElement.style.opacity = "0";
    setTimeout(() => tipElement.remove(), 300);
  };

  const autoRemoveTimer = setTimeout(removeTip, timeout);
  tipElement.addEventListener("click", removeTip);

  return { element: tipElement, close: removeTip };
}

// #endregion

// =================================================================================
// #region API & Data Functions
// =================================================================================

/**
 * 注入Fetch拦截器
 */
function injectFetchInterceptor() {
  console.log("注入拦截器");
  const scriptURL = chrome.runtime.getURL("fetch-interceptor.js");
  if (!document.querySelector("script[data-fetch-interceptor]")) {
    const scriptElement = document.createElement("script");
    scriptElement.setAttribute("data-fetch-interceptor", "true");
    scriptElement.src = scriptURL;
    document.head.appendChild(scriptElement);
  }
}

/**
 * 处理计划详情响应
 */
function handlePlanDetailResponse(body) {
  try {
    const data = JSON.parse(body);
    console.log("直播商品列表数据:", data.data);
    APP_STATE.cacheData = JSON.stringify(data.data);
    if (APP_STATE.cacheData) {
      console.log("缓存数据:", APP_STATE.cacheData);
      const delay = configManager.get('timeouts.sync_container_delay');
      setTimeout(createSyncContainer, delay);
    }
  } catch (e) {
    console.error("数据解析失败:", e);
  }
}

/**
 * 处理协议响应
 */
function handleAgreementResponse(url) {
  try {
    const userId = new URL(url, window.location.origin).searchParams.get("user_id");
    if (userId) {
      const storageKeys = configManager.getStorageKeys();
      localStorage.setItem(storageKeys.agreement_user_id, userId);
      console.log("✅ 已保存 user_id 到 localStorage:", userId);
    } else {
      console.warn("⚠️ URL 中没有找到 user_id 参数");
    }
  } catch (e) {
    console.error("解析 user_id 或存储时出错:", e);
  }
}

/**
 * 发送商品列表到后台
 */
async function sendProductsListToBackground(productsList) {
  const business = configManager.getBusiness();
  const storageKeys = configManager.getStorageKeys();
  
  const params = {
    attr: business.attr_default,
    dyAccountNo: APP_STATE.dyAccountNo,
    planContent: APP_STATE.cacheData,
    products: productsList.map((product, index) => ({
      ...product,
      product_info: product.product_info?.product_id
        ? product.product_info
        : undefined,
      fromType: business.product_from_types.live_room,
      sort: index + 1,
    })),
  };

  console.log("发送商品数据到后台", params);
  return await $Request(API.saveProductListApi, { params });
}

/**
 * 百应发送商品列表到后台
 */
async function buYinSendProductsListToBackground(productsList, planName) {
  const selectors = configManager.getSelectors();
  const business = configManager.getBusiness();
  
  const dyAccountName =
    document.querySelector(selectors.dy_account_name)?.textContent || 
    business.default_account_name;
  console.log("抖音账号名称:", dyAccountName);

  // 转换属性名格式
  productsList.forEach((product) => {
    Object.keys(product).forEach((key) => {
      if (key.includes("_")) {
        const newKey = key.replace(/_([a-z])/g, (match, p1) => p1.toUpperCase());
        product[newKey] = product[key];
        delete product[key];
      }
    });
  });

  const params = {
    attr: business.attr_default,
    name: planName,
    dyAccountNo: dyAccountName,
    dyAccountName: dyAccountName,
    products: productsList,
  };

  console.log("发送百应商品数据到后台", params);
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      {
        action: "FETCH_EC_PRODUCT_LIST",
        data: {
          url: API.BaseUrl + API.saveEcProductListApi,
          options: {
            method: "POST",
            headers: {
              "Content-Type": configManager.get('http.headers.content_type_json'),
            },
            body: JSON.stringify(params),
            credentials: configManager.get('http.credentials'),
          },
        },
      },
      (response) => {
        if (chrome.runtime.lastError) {
          console.error("Error sending message:", chrome.runtime.lastError);
          reject(chrome.runtime.lastError);
        } else if (response.success) {
          resolve(response.data);
        } else {
          console.error("Error in background script:", response.error);
          reject(response.error);
        }
      }
    );
  });
}

/**
 * 同步违规列表
 */
async function syncPunishList() {
  console.log("开始同步违规记录");
  try {
    await get_replay_punish_list();
  } catch (error) {
    console.error("Error syncing punish list:", error);
  }
}

/**
 * 获取弹窗文本
 */
async function getModalText() {
  const selectors = configManager.getSelectors();
  const business = configManager.getBusiness();
  const storageKeys = configManager.getStorageKeys();
  
  const targetSpan = Array.from(document.querySelectorAll(selectors.violation_reason_span)).find(
    (span) => span.textContent.includes("处罚原因")
  );

  if (!targetSpan) return;

  const modal_span_text = targetSpan.textContent;
  console.log("弹窗内容:", modal_span_text);

  // 使用配置中的正则表达式
  const patternStr = business.violation_pattern;
  const pattern = new RegExp(patternStr.slice(1, -2), patternStr.slice(-1)); // 移除首尾的/和标志
  const match = modal_span_text.match(pattern);

  if (!match) return;

  const result = {
    violationReason: match[1].trim(),
    violationTime: match[2].trim(),
    punishmentType: match[3].trim(),
  };

  const dyAccountNo = localStorage.getItem(storageKeys.dy_account_no);
  const roomName = localStorage.getItem(storageKeys.dy_room_name);

  const params = { ...result, name: roomName, dyAccountNo };

  if (!params.violationTime) {
    createTopTips(configManager.getTip('modal_content_failed'), { type: "error" });
    return;
  }

  console.log("保存违规记录参数:", params);
  await $Request(API.liveviolationrecordsdealSaveApi, { params });
  createTopTips(configManager.getTip('violation_record_saved', { account: dyAccountNo }), { 
    type: "success" 
  });
}

/**
 * 获取违规记录列表
 */
async function get_replay_punish_list() {
  console.log("执行 get_replay_punish_list");
  if (!configManager.isTargetHostname(window.location.hostname, 'eos')) {
    console.log("非 eos.douyin.com 域名，不执行");
    return;
  }

  createTopTips(configManager.getTip('sync_punish_start'));

  const storageKeys = configManager.getStorageKeys();
  const business = configManager.getBusiness();
  const urls = configManager.getUrls();
  
  const dyAccountNo = localStorage.getItem(storageKeys.dy_account_no);
  const dyRoomName = localStorage.getItem(storageKeys.dy_room_name);

  const today = new Date();
  const periodDays = business.punish_sync_period_days;
  const fmt = (d) => d.toISOString().slice(0, 10);

  const end_date = fmt(today);
  const begin = new Date(today);
  begin.setDate(begin.getDate() - (periodDays - 1));
  const begin_date = fmt(begin);

  try {
    const res = await fetch(urls.punish_list_api, {
      method: "POST",
      headers: { "Content-Type": configManager.get('http.headers.content_type_json') },
      body: JSON.stringify({
        user_id: business.default_user_id,
        begin_date,
        end_date,
        compare_begin_date: begin_date,
        compare_end_date: end_date,
      }),
    });

    const { data: list = [] } = await res.json();

    if (!list || list.length === 0) {
      createTopTips(configManager.getTip('sync_punish_no_records'), { type: "success" });
      console.log("ℹ️ 当前无违规记录");
      return;
    }

    for (const item of list) {
      try {
        const params = {
          violationReason: item.violation_reason,
          violationTime: item.time,
          punishmentType: item.punish_result,
          dyAccountNo,
          name: dyRoomName,
        };
        console.log("保存参数：", params);
        await $Request(API.liveviolationrecordsdealSaveApi, { params });
      } catch (e) {
        console.error("⚠️ 单条保存失败：", e, item);
      }
    }

    createTopTips(configManager.getTip('sync_punish_complete'), { type: "success" });
    console.log("✅ 全部记录已处理完毕");
  } catch (err) {
    console.error("❌ 同步过程出错：", err);
    createTopTips(configManager.getTip('sync_punish_failed', { error: err.message || "未知错误" }), { 
      type: "error" 
    });
  }
}

// #endregion

// =================================================================================
// #region Utility Functions
// =================================================================================

/**
 * 获取抖音账号信息
 */
function getDyAccountNo() {
  const selectors = configManager.getSelectors();
  const storageKeys = configManager.getStorageKeys();
  
  const accountPanel = document.querySelector(selectors.account_panel);
  if (!accountPanel) {
    createTopTips(configManager.getTip('no_douyin_account'), { type: "error" });
    return;
  }

  const accountNoText = accountPanel.querySelector(selectors.account_no)?.textContent;
  const accountName = accountPanel.querySelector(selectors.account_name)?.textContent;

  if (accountNoText) {
    APP_STATE.dyAccountNo = accountNoText.split("：")[1];
    console.log("获取到抖音号:", APP_STATE.dyAccountNo);
    localStorage.setItem(storageKeys.dy_account_no, APP_STATE.dyAccountNo);
  }

  if (accountName) {
    console.log("获取到抖音名:", accountName);
    localStorage.setItem(storageKeys.dy_room_name, accountName);
  }
}

// #endregion