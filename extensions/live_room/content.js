/**
 * @file content.js
 * @description 抖音直播间内容脚本，用于数据同步、UI交互和违规记录处理。
 */

// =================================================================================
// #region Constants & State
// =================================================================================

const SYNC_BUTTON_TEXT = {
  default: "同步混剪系统",
  loading: "同步中...",
  success: "同步成功",
  error: "同步失败",
  reload: "重新同步",
};

const APP_STATE = {
  dyAccountNo: null,
  cacheData: "",
  isSyncing: false,
  livePlanData: null, // 用于存储直播计划数据
  violationCheckInterval: null, // 违规弹窗检查定时器
  highFrequencyButtonAdded: false, // 跟踪违规监控按钮是否已添加
  highFrequencySyncInterval: null, // 违规监控定时器
  isHighFrequencySyncActive: false, // 违规监控是否激活
};

// #endregion

// =================================================================================
// #region Initialization
// =================================================================================

document.addEventListener("DOMContentLoaded", init);

// 页面卸载时清理资源
window.addEventListener("beforeunload", cleanup);

function init() {
  console.log("页面加载完成 DOMContentLoaded");

  // 脚本初始化
  injectFetchInterceptor();
  // 事件监听初始化
  setupEventListeners();

  if (window.location.hostname === "eos.douyin.com") {
    // 账号状态监听初始化
    setupAccountObserver();
    // 直播状态检查任务
    checkLiveStatus();
    // 违规记录同步任务
    setupPeriodicTasks();

    // 检查页面加载时的直播状态，如果已在直播中则启动违规弹窗检查
    const savedLiveStatus = localStorage.getItem("liveStatus");
    if (savedLiveStatus) {
      const liveStatus = JSON.parse(savedLiveStatus);
      if (liveStatus.isLiving) {
        console.log("页面加载时检测到直播中状态，启动违规弹窗检查");
        startViolationCheck();
      }
    }
  }

  if (
    window.location.href.startsWith(
      "https://buyin.jinritemai.com/dashboard/buyin_live_control/prepare/create"
    )
  ) {
    setupMixedCutSyncButton();
  }

  // // 检测是否进入商品推广页面，如果是则模拟请求
  // if (
  //   window.location.href.startsWith(
  //     "https://buyin.jinritemai.com/dashboard/merch-picking-library/merch-promoting"
  //   )
  // ) {
  //   simulatePackDetailRequest();
  // }
}

/**
 * 添加违规监控按钮到current-live-room元素中
 * 使用MutationObserver等待元素出现
 */
function addHighFrequencySyncButton() {
  try {
    // 检查是否已经添加过按钮
    if (APP_STATE.highFrequencyButtonAdded) {
      console.log("违规监控按钮已添加过，跳过重复添加");
      return;
    }

    // 首先尝试直接查找元素
    const currentLiveRoomElement = document.getElementById("current-live-room");
    if (currentLiveRoomElement) {
      addButtonToElement(currentLiveRoomElement);
      return;
    }

    console.log("current-live-room元素未找到，开始监听DOM变化");

    // 使用MutationObserver监听DOM变化
    const observer = new MutationObserver((mutations, obs) => {
      const element = document.getElementById("current-live-room");
      if (element) {
        console.log("检测到current-live-room元素已加载");
        obs.disconnect();
        addButtonToElement(element);
        clearTimeout(timeoutId);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    // 设置超时机制，避免无限等待
    const timeoutId = setTimeout(() => {
      observer.disconnect();
      console.warn("等待current-live-room元素超时");
    }, 30000); // 30秒超时
  } catch (error) {
    console.error("添加违规监控按钮失败:", error);
  }
}

/**
 * 将按钮添加到指定元素中
 * @param {Element} currentLiveRoomElement - 目标元素
 */
function addButtonToElement(currentLiveRoomElement) {
  // 检查是否已存在违规监控按钮，避免重复添加
  const existingButton = currentLiveRoomElement.querySelector(
    "#high-frequency-sync-btn"
  );
  if (existingButton) {
    console.log("违规监控按钮已存在，跳过添加");
    APP_STATE.highFrequencyButtonAdded = true;
    return;
  }

  // 创建违规监控按钮
  const syncButton = document.createElement("button");
  syncButton.id = "high-frequency-sync-btn";
  syncButton.textContent = "开始违规监控";
  syncButton.style.cssText = `
    background-color: #2ed573;
    color: #ffffff;
    border: 1px solid #2ed573;
    font-weight: 600;
    outline: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    margin-left: 10px;
    transition: all 0.3s ease;
  `;

  // 添加事件监听器
  syncButton.addEventListener("mouseenter", function () {
    this.style.opacity = "0.8";
  });

  syncButton.addEventListener("mouseleave", function () {
    this.style.opacity = "1";
  });

  syncButton.addEventListener("click", function () {
    console.log("点击了违规监控按钮");
    toggleHighFrequencySync(syncButton);
  });

  // 将按钮添加到元素中
  currentLiveRoomElement.appendChild(syncButton);

  // 更新状态，标记按钮已添加
  APP_STATE.highFrequencyButtonAdded = true;
  console.log("违规监控按钮已添加到current-live-room元素中");
}

// #endregion

// =================================================================================
// #region Event Listeners & Observers
// =================================================================================

function setupEventListeners() {
  chrome.runtime.onMessage.addListener(handleChromeMessages);
  window.addEventListener("fetchResponse", handleFetchResponses);
}

function handleChromeMessages(request, sender, sendResponse) {
  console.log("接收到消息:", { request, sender });

  if (
    request.action === "DO_DAILY_TASK" &&
    window.location.hostname === "eos.douyin.com"
  ) {
    console.log(
      `执行每日任务: ${new Date().getHours() * 100 + new Date().getMinutes()}`
    );
    get_replay_punish_list().then((res) => {
      console.log("punish_list", res);
    });
  } else if (request.action === "SHOW_TASK_RESULT") {
    console.log("收到后台任务结果:", request.data);
    createTopTips("后台任务已完成，数据已获取", { type: "success" });
    // 这里可以处理返回的数据
    handlePackDetailResult(request.data, request.packId);
    sendResponse({ success: true });
  } else {
    console.log("其他消息", request);
  }
}

function handleFetchResponses(event) {
  const { url, status, body } = event.detail;
  console.log("接口监听:", { url, status });

  if (url.includes("/api/anchor/livepc/get_live_plans") && status === 200) {
    console.log("拦截到直播计划数据:", body);
    APP_STATE.livePlanData = body;
    createTopTips("直播计划数据已获取成功", { type: "success" });
  } else if (url.includes("/data/life/live/plan/detail/") && status === 200) {
    handlePlanDetailResponse(body);
  } else if (
    url.includes("/data/life/live/case/agreement/get") &&
    status === 200
  ) {
    handleAgreementResponse(body);
  } else if (
    url.includes("/pc/selection/decision/pack_detail") &&
    status === 200
  ) {
    handlePackDetailResult(JSON.parse(body));
  } else {
    handleAgreementResponse(url);
  }
}

function setupAccountObserver() {
  if (window.location.hostname !== "eos.douyin.com") return;
  let timeoutId = null;
  const observer = new MutationObserver((_mutations, obs) => {
    const accountPanel = document.querySelector(
      "div[class*='dropdown-panel-']"
    );
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
    createTopTips("账号信息加载超时，请手动刷新页面", { type: "error" });
    console.error("账号面板元素加载超时");
  }, 10000);
}

function setupPeriodicTasks() {
  // 每小时同步一次违规记录
  setInterval(syncPunishList, 3600000);

  // 每3分钟检查一次直播状态（仅在eos.douyin.com域名下）
  if (window.location.hostname === "eos.douyin.com") {
    setInterval(() => {
      console.log("定时检查直播状态...");
      checkLiveStatus();
    }, 180000); // 3分钟 = 180000毫秒
  }
}

/**
 * 启动违规弹窗检查定时器
 */
function startViolationCheck() {
  if (APP_STATE.violationCheckInterval) {
    console.log("违规弹窗检查已在运行中");
    return;
  }

  console.log("启动违规弹窗检查定时器");
  APP_STATE.violationCheckInterval = setInterval(() => {
    const modal_wrapper = document.querySelector(
      ".okee-main-modal-wrapper .okee-main-modal-body .okee-main-content-container .okee-main-content-header.okee-main-modal-content-header"
    );
    if (modal_wrapper) {
      getModalText();
    }
  }, 3000);
}

/**
 * 停止违规弹窗检查定时器
 */
function stopViolationCheck() {
  if (APP_STATE.violationCheckInterval) {
    console.log("停止违规弹窗检查定时器");
    clearInterval(APP_STATE.violationCheckInterval);
    APP_STATE.violationCheckInterval = null;
  }
}

// #endregion

// =================================================================================
// #region UI Functions
// =================================================================================

function setupMixedCutSyncButton() {
  console.log("setupMixedCutSyncButton:");

  const observer = new MutationObserver((mutations, obs) => {
    const savePlanButton = Array.from(document.querySelectorAll("button")).find(
      (btn) => btn.textContent.trim() === "保存计划"
    );

    if (savePlanButton) {
      console.log("检测到'保存计划'按钮，准备插入新按钮。");
      obs.disconnect(); // 找到后停止观察

      const syncButton = document.createElement("button");
      syncButton.textContent = SYNC_BUTTON_TEXT.default;

      // 沿用现有按钮的 class 来尽量匹配样式，并添加自定义样式
      syncButton.className = savePlanButton.className;
      Object.assign(syncButton.style, {
        marginRight: "12px", // 与右侧按钮保持间距

        border: "none",
        backgroundImage: "linear-gradient(270deg, #ff3b37, #be1142 80%)",
        color: "#fff",
      });

      syncButton.addEventListener("click", async () => {
        if (!APP_STATE.livePlanData) {
          console.warn("暂无缓存的直播计划数据");
          createTopTips("请先刷新页面以获取直播计划数据", { type: "error" });
          return;
        }

        try {
          const { code, data } = JSON.parse(APP_STATE.livePlanData);
          if (code !== 0 || !data.live_plan_map) {
            createTopTips("直播计划数据格式不正确", { type: "error" });
            return;
          }

          const params = new URLSearchParams(window.location.search);
          const planId = params.get("planId");
          const planData = data.live_plan_map[planId];

          if (!planData || !planData.products?.products) {
            createTopTips("未找到当前计划或商品列表为空", { type: "error" });
            return;
          }

          const productList = planData.products.products;

          console.log("开始处理商品列表:", productList);
          createTopTips(`开始同步 ${productList.length} 个商品...`, {
            type: "info",
          });
          const promotion_ids = productList.map(
            (product) => product.promotion_id
          );
          const { data: promotionsV2Data } = await getPromotionsV2(
            promotion_ids
          );
          console.log("promotionsV2Data", promotionsV2Data);
          const promotions = promotionsV2Data.promotions || [];
          if (!promotions.length) {
            createTopTips("请先将商品添加至中控台", { type: "error" });
            return;
          }

          const productPromises = promotions.map(async (product) => {
            console.log("product", product);

            const product_id = product.product_id;

            console.log(`正在处理商品 ID: ${product_id}`);
            if (!product_id) return;

            const url = `https://haohuo.jinritemai.com/aweme/v2/shop/promotion/pack/detail/?is_h5=1&origin_type=pc_buyin_selection_decision`;
            const UserAgent =
              "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
            const headers = {
              Accept: "application/json, text/plain, */*",
              "Content-Type": "application/x-www-form-urlencoded",
              Referer: `https://haohuo.jinritemai.com/ecommerce/trade/detail/index.html?id=${product_id}&origin_type=pc_buyin_selection_decision`,
              "User-Agent": UserAgent,
            };
            const body = `promotion_id=${product_id}&enter_from=&meta_param=&is_h5=1`;

            try {
              const responseData = await new Promise((resolve, reject) => {
                chrome.runtime.sendMessage(
                  {
                    action: "FETCH_PRODUCT_DETAIL",
                    data: {
                      url,
                      options: {
                        method: "POST",
                        headers,
                        body,
                        credentials: "include",
                      },
                    },
                  },
                  (response) => {
                    if (chrome.runtime.lastError) {
                      return reject(chrome.runtime.lastError);
                    }
                    if (response && response.success) {
                      resolve(response.data);
                    } else {
                      reject(
                        new Error(
                          response?.error ||
                            "Background script returned an error."
                        )
                      );
                    }
                  }
                );
              });
              console.log(
                "Product detail fetched via background:",
                responseData
              );

              if (responseData.status_code === 0) {
                console.log(
                  `商品 ${product_id} 同步成功:`,
                  responseData.detail_info
                );
                const formattedData = formatProductDetails(responseData);
                if (formattedData) {
                  product.detailInfo = formattedData.detail;
                  product.fromType = "7";
                } else {
                  console.warn(
                    `商品 ${product_id} 的详情数据格式不正确，无法格式化。`
                  );
                }
              } else {
                throw new Error(
                  responseData.error || `获取商品 ${product_id} 详情失败`
                );
              }
            } catch (error) {
              console.error(`商品 ${product_id} 同步失败:`, error);
              createTopTips(`商品 ${product_id} 同步失败`, { type: "error" });
            }
          });

          await Promise.allSettled(productPromises);

          //

          // 等所有商品处理结束后 获取最终productList
          console.log("所有商品处理完成，最终的 promotions:", promotions);
          const planName = planData.title || "";

          await buYinSendProductsListToBackground(promotions, planName);

          createTopTips("所有商品已处理完毕", { type: "success" });
        } catch (error) {
          console.error("处理直播计划数据时出错:", error);
          createTopTips("处理数据时出错，请检查控制台日志", { type: "error" });
        }
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

  // 设置一个超时，以防按钮永远不出现
  setTimeout(() => {
    observer.disconnect();
    console.log("超时：未找到'保存计划'按钮，停止观察。");
  }, 30000); // 30秒超时
}

function createSyncContainer() {
  const existingContainer = document.querySelector(".sync_wj");
  if (existingContainer) {
    existingContainer.remove();
  }

  const parentElement = document.querySelector(
    "div.okee-app-live-loading.okee-app-live-loading-block>div>div:nth-last-child(1) button:nth-child(1)"
  )?.parentElement;

  if (!parentElement) {
    console.error("未找到目标容器，无法创建同步按钮");
    return;
  }

  const syncContainer = document.createElement("div");
  syncContainer.className = "sync_wj";

  const syncButton = document.createElement("button");
  Object.assign(syncButton.style, {
    background:
      "linear-gradient(to right bottom, #7db1ff, #004EFE) border-box border-box",
    border: "1px solid transparent",
    borderRadius: "6px",
    color: "#fff",
    fontSize: "14px",
    height: "36px",
    lineHeight: "22px",
    minWidth: "80px",
    padding: "6px 16px",
    textAlign: "center",
    marginLeft: "10px",
    cursor: "pointer",
    transition: "opacity 0.3s",
  });
  syncButton.textContent = SYNC_BUTTON_TEXT.default;

  syncButton.addEventListener("click", () => handleSyncButtonClick(syncButton));

  syncContainer.appendChild(syncButton);
  parentElement.appendChild(syncContainer);
}

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
    createTopTips("所有商品处理完成，请在混剪系统中查看", {
      type: "success",
    });
    setTimeout(() => {
      syncButton.textContent = SYNC_BUTTON_TEXT.default;
    }, 3000);
  } catch (error) {
    console.error("发送商品数据到后台失败", error);
    createTopTips(error.toString(), { type: "error" });
    syncButton.textContent = SYNC_BUTTON_TEXT.error;
    setTimeout(() => {
      syncButton.textContent = SYNC_BUTTON_TEXT.reload;
    }, 3000);
  } finally {
    setSyncButtonState(syncButton, false);
  }
}

function setSyncButtonState(button, isLoading) {
  APP_STATE.isSyncing = isLoading;
  button.style.opacity = isLoading ? "0.7" : "1";
  button.style.cursor = isLoading ? "not-allowed" : "pointer";
  if (isLoading) {
    button.textContent = SYNC_BUTTON_TEXT.loading;
  }
}

/**
 * 创建一个美观且多功能的顶部提示框
 * @param {string} text - 需要展示的文字
 * @param {object} options - 配置项
 * @param {number} [options.timeout=3000] - 自动关闭的延迟时间（毫秒）
 * @param {string} [options.type='info'] - 提示类型 ('info', 'success', 'error')
 */
function createTopTips(text, options = {}) {
  const { timeout = 3000, type = "info" } = options;

  const style = {
    position: "fixed",
    top: "20px",
    left: "50%",
    transform: "translateX(-50%)",
    color: "#fff",
    padding: "12px 20px",
    borderRadius: "8px",
    fontSize: "16px",
    zIndex: "9999",
    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
    transition: "top 0.3s ease-in-out, opacity 0.3s ease-in-out",
    opacity: "0",
    cursor: "pointer",
  };

  const typeColors = {
    info: "#1677ff",
    success: "#52c41a",
    error: "#f5222d",
    warning: "#faad14",
  };
  style.backgroundColor = typeColors[type] || typeColors.info;

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
// #region Pack Detail Simulation Functions
// =================================================================================

/**
 * 模拟发送pack_detail请求(风险控制暂时无法使用)
 */
async function _simulatePackDetailRequest() {
  console.log("开始模拟pack_detail请求");

  // 从URL中提取id参数
  const urlParams = new URLSearchParams(window.location.search);
  const bizId = urlParams.get("id");

  if (!bizId) {
    console.warn("未找到商品ID，无法模拟请求");
    return;
  }

  console.log("提取到商品ID:", bizId);
  const signBuyin = await getSignBuyin();
  const params = new URLSearchParams({
    ewid: "127d19629b5f6ea3169dc747fa9aa9dd",
    msToken: signBuyin.ms_token,
    a_bogus: signBuyin.a_bogus,
    // msToken:
    // "8m4PjFeCJeQY4-kBssEnnKUTYBzyAnDj_zTCWF3QjVxp7HJtURhqHbNVMGWY0qtP58mHHlmKe7WuiYuINz-tUohcljJyOsAa26LJuztu4uoTRx-0whdax5oJ5NStCTQQiUExWEqEonKhJLmwX37zNospjDaSHVOq7-drzCNGNuAKRmIoxbmynQnX",
    // a_bogus:
    // "my4VkF6yYxW5PplGmOkJt1QlGUVlrTuyfrTxWeFTyoP3OhMb7xBIh9xfcqKf4BOUDuB3i9V7in8dYdfOT2D6MHnkKmkkuqtR2z55V86o0qi6GlGmgNR8C8RzowMK0mJwaA9XN1f5AsMN2fnAIrVTWp-GH5zq55EdbNMjD2LyCEWgDC8kin3kOHD2N6Jqmj%3D%3D",
    verifyFp: "verify_mdwgzymu_QBL6lC1i_ZW9L_4kSD_8M7b_FQHDPO4j2b4Z",
    fp: "verify_mdwgzymu_QBL6lC1i_ZW9L_4kSD_8M7b_FQHDPO4j2b4Z",
  });
  // 构造请求URL和数据
  const url = `https://buyin.jinritemai.com/pc/selection/decision/pack_detail?${params}`;

  const requestBody = {
    scene_info: {
      request_page: 2,
    },
    biz_id: bizId,
    biz_id_type: 2,
    enter_from: "pc.unknow.unknow",
    data_module: "core",
    extra: { use_kol_product: "1" },
  };

  const headers = {
    "x-secsdk-csrf-token":
      "00010000000147fb5783dea5ad475ab365e85f4200e59c404472fe3a2b364fb34111518b05471858c7cde603a360",
  };

  // 发送fetch请求，让拦截器捕获响应
  createTopTips("正在获取商品详情...", { type: "info" });

  fetch(url, {
    method: "POST",
    headers: headers,
    body: JSON.stringify(requestBody),
  })
    .then((response) => {
      console.log("pack_detail请求已发送，状态:", response.status);
      // 不在这里处理响应，让拦截器处理
      if (!response.ok) {
        createTopTips("获取商品详情失败", { type: "error" });
      }
    })
    .catch((error) => {
      console.error("pack_detail请求失败:", error);
      createTopTips("获取商品详情失败", { type: "error" });
    });
}

/**
 * 处理pack_detail请求的结果
 */
function handlePackDetailResult(data) {
  try {
    // 这里可以根据需要处理返回的数据
    if (data && data.code === 0) {
      console.log("pack_detail请求成功，数据:", data.data);
      createTopTips(`商品详情获取成功`, {
        type: "success",
      });

      // 可以在这里添加更多的数据处理逻辑
      // 例如：显示商品信息、更新UI等
    } else {
      console.warn("pack_detail请求失败:", data);
      createTopTips("商品详情获取失败", { type: "error" });
    }
  } catch (error) {
    console.error("处理pack_detail结果时出错:", error);
    createTopTips("处理数据时出错", { type: "error" });
  }
}

// #endregion

// =================================================================================
// #region API & Data Functions
// =================================================================================

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

function handlePlanDetailResponse(body) {
  try {
    const data = JSON.parse(body);
    console.log("直播商品列表数据:", data.data);
    APP_STATE.cacheData = JSON.stringify(data.data);
    if (APP_STATE.cacheData) {
      console.log("缓存数据:", APP_STATE.cacheData);
      setTimeout(createSyncContainer, 3000);
    }
  } catch (e) {
    console.error("数据解析失败:", e);
  }
}

function handleAgreementResponse(url) {
  try {
    const userId = new URL(url, window.location.origin).searchParams.get(
      "user_id"
    );
    if (userId) {
      localStorage.setItem("agreement_user_id", userId);
      console.log("[OK] 已保存 user_id 到 localStorage:", userId);
    } else {
      console.warn("[WARNING] URL 中没有找到 user_id 参数");
    }
  } catch (e) {
    console.error("解析 user_id 或存储时出错:", e);
  }
}

async function sendProductsListToBackground(productsList) {
  const params = {
    attr: "1",
    dyAccountNo: APP_STATE.dyAccountNo,
    planContent: APP_STATE.cacheData,
    products: productsList.map((product, index) => ({
      ...product,
      product_info: product.product_info?.product_id
        ? product.product_info
        : undefined,
      fromType: "5",
      sort: index + 1,
    })),
  };

  console.log("发送商品数据到后台", params);
  return await $Request(API.saveProductListApi, { params });
}

async function buYinSendProductsListToBackground(productsList, planName) {
  // 获取class为：btn-item-role-exchange-name__title的文本
  const dyAccountName =
    document.querySelector(".btn-item-role-exchange-name__title")
      ?.textContent || "chrome-plugins";
  console.log("抖音账号名称:", dyAccountName);
  // 递归将对象的所有key从下划线格式转换为小驼峰格式
  const convertKeysToCamelCase = (obj) => {
    if (Array.isArray(obj)) {
      return obj.map((v) => convertKeysToCamelCase(v));
    } else if (obj !== null && typeof obj === "object") {
      return Object.keys(obj).reduce((acc, key) => {
        const newKey = key.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
        acc[newKey] = convertKeysToCamelCase(obj[key]);
        return acc;
      }, {});
    }
    return obj;
  };

  // 转换productsList中的所有key
  let convertedProductsList = convertKeysToCamelCase(productsList);

  console.log("转换后的商品列表:", convertedProductsList);

  const params = {
    attr: "1",
    dyPlanName: planName,
    dyAccountNo: dyAccountName,
    dyAccountName: dyAccountName,
    products: convertedProductsList,
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
              "Content-Type": "application/json",
            },
            body: JSON.stringify(params),
            credentials: "include",
          },
        },
      },
      (response) => {
        console.log("response", response);

        if (chrome.runtime.lastError) {
          const message = `同步百应商品失败: ${chrome.runtime.lastError.message}`;
          console.error(message);
          createTopTips(message, { type: "error" });
          reject(chrome.runtime.lastError);
        } else if (response.data?.code == 200) {
          const message = "同步百应商品成功";
          createTopTips(message, { type: "success" });
          resolve(response.data);
        } else {
          const message = `同步百应商品失败: ${
            response.error?.message || "未知错误"
          }`;
          console.error(
            "Error in background script:",
            response.data?.msg || "未知错误"
          );
          createTopTips(message, { type: "error" });
          reject(response.error);
        }
      }
    );
  });
}

async function syncPunishList() {
  console.log("开始同步违规记录");
  try {
    await get_replay_punish_list();
    // await get_replay_live_room_list(); // This function is not defined in the script
  } catch (error) {
    console.error("Error syncing punish list:", error);
  }
}

async function getModalText() {
  const targetSpan = Array.from(document.querySelectorAll("span")).find(
    (span) => span.textContent.includes("处罚原因")
  );

  if (!targetSpan) return;

  const modal_span_text = targetSpan.textContent;
  console.log("弹窗内容:", modal_span_text);

  const pattern =
    /处罚原因：(.+?)\s*违规时间：([\d-]+\s[\d:]+)\s*处罚方式：(.+?)(?:\s|$)/s;
  const match = modal_span_text.match(pattern);

  if (!match) return;

  const result = {
    violationReason: match[1].trim(),
    violationTime: match[2].trim(),
    punishmentType: match[3].trim(),
  };

  const dyAccountNo = localStorage.getItem("dyAccountNo");
  const roomName = localStorage.getItem("dyRoomName");

  const params = { ...result, name: roomName, dyAccountNo };

  if (!params.violationTime) {
    createTopTips("弹窗内容获取失败", { type: "error" });
    return;
  }

  console.log("保存违规记录参数:", params);
  await $Request(API.liveviolationrecordsdealSaveApi, { params });
  createTopTips(`账号：${dyAccountNo}, 违规记录保存成功`, { type: "success" });
}

async function get_replay_punish_list() {
  console.log("执行 get_replay_punish_list");
  if (window.location.hostname !== "eos.douyin.com") {
    console.log("非 eos.douyin.com 域名，不执行");
    return;
  }

  createTopTips("同步违规记录——开始");

  const dyAccountNo = localStorage.getItem("dyAccountNo");
  const dyRoomName = localStorage.getItem("dyRoomName");

  const today = new Date();
  const periodDays = 30;
  const fmt = (d) => d.toISOString().slice(0, 10);

  const end_date = fmt(today);
  const begin = new Date(today);
  begin.setDate(begin.getDate() - (periodDays - 1));
  const begin_date = fmt(begin);

  try {
    const res = await fetch(
      "https://eos.douyin.com/life/api/live_screen/v4/replay/punish_list",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "1258293549605997", // TODO: This seems to be a hardcoded value
          begin_date,
          end_date,
          compare_begin_date: begin_date, // Simplified logic as per original
          compare_end_date: end_date,
        }),
      }
    );

    const { data: list = [] } = await res.json();

    if (!list || list.length === 0) {
      createTopTips("同步完成：无新的违规记录", { type: "success" });
      console.log("[INFO] 当前无违规记录");
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
        console.error("[WARNING] 单条保存失败：", e, item);
      }
    }

    createTopTips("同步违规记录——完成", { type: "success" });
    console.log("[OK] 全部记录已处理完毕");
  } catch (err) {
    console.error("[ERROR] 同步过程出错：", err);
    createTopTips(`同步失败：${err.message || "未知错误"}`, { type: "error" });
  }
}

// #endregion

// =================================================================================
// #region Utility Functions
// =================================================================================

function getDyAccountNo() {
  const accountPanel = document.querySelector("div[class*='dropdown-panel-']");
  if (!accountPanel) {
    createTopTips("未找到抖音账号信息", { type: "error" });
    return;
  }

  const accountNoText = accountPanel.querySelector(
    "div[class*='panel-profile-account-']"
  )?.textContent;
  const accountName = accountPanel.querySelector(
    "div[class*='panel-profile-name-']"
  )?.textContent;

  if (accountNoText) {
    APP_STATE.dyAccountNo = accountNoText.split("：")[1];
    console.log("获取到抖音号:", APP_STATE.dyAccountNo);
    localStorage.setItem("dyAccountNo", APP_STATE.dyAccountNo);
  }

  if (accountName) {
    console.log("获取到抖音名:", accountName);
    localStorage.setItem("dyRoomName", accountName);
  }
}

/**
 * 检查直播状态
 * 调用抖音菜单接口，判断CurrentLive菜单项的name字段是"直播间"还是"正在直播"
 * 并将状态存储到localStorage中
 */
async function checkLiveStatus() {
  console.log("开始检查直播状态");

  try {
    const response = await fetch(
      "https://eos.douyin.com/data/life/live/menu/detail/v1/",
      {
        headers: {
          accept:
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
          "accept-language": "zh-CN,zh;q=0.9",
          "cache-control": "max-age=0",
          priority: "u=0, i",
          "sec-ch-ua":
            '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
          "sec-ch-ua-mobile": "?0",
          "sec-ch-ua-platform": '"macOS"',
          "sec-fetch-dest": "document",
          "sec-fetch-mode": "navigate",
          "sec-fetch-site": "none",
          "sec-fetch-user": "?1",
          "upgrade-insecure-requests": "1",
        },
        body: null,
        method: "GET",
        mode: "cors",
        credentials: "include",
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("菜单接口返回数据:", data);

    // 查找CurrentLive菜单项
    let currentLiveName = null;
    if (data.menu && data.menu.sub_menu) {
      for (const mainMenu of data.menu.sub_menu) {
        if (mainMenu.sub_menu) {
          for (const subMenu of mainMenu.sub_menu) {
            if (subMenu.menu_key === "CurrentLive") {
              currentLiveName = subMenu.name;
              break;
            }
          }
        }
        if (currentLiveName) break;
      }
    }

    if (currentLiveName) {
      console.log(`找到CurrentLive菜单项，name字段为: ${currentLiveName}`);

      // 判断直播状态
      const isLiving = currentLiveName === "正在直播";
      const liveStatus = {
        currentLiveName: currentLiveName,
        isLiving: isLiving,
        lastCheckTime: new Date().toISOString(),
      };

      // 获取之前的直播状态
      const previousLiveStatus = localStorage.getItem("liveStatus");
      const previousIsLiving = previousLiveStatus
        ? JSON.parse(previousLiveStatus).isLiving
        : false;

      // 存储到localStorage
      localStorage.setItem("liveStatus", JSON.stringify(liveStatus));
      console.log("直播状态已保存到localStorage:", liveStatus);

      // 根据直播状态变化控制违规弹窗检查
      if (isLiving && !previousIsLiving) {
        // 开始直播，启动违规弹窗检查
        startViolationCheck();
        console.log("检测到开始直播，已启动违规弹窗检查");
      } else if (!isLiving && previousIsLiving) {
        // 结束直播，停止违规弹窗检查
        stopViolationCheck();
        console.log("检测到结束直播，已停止违规弹窗检查");
      } else if (isLiving) {
        // 仍在直播中，确保违规弹窗检查正在运行
        if (!APP_STATE.violationCheckInterval) {
          startViolationCheck();
          console.log("直播中但违规检查未运行，已重新启动");
        }
      }

      // 延迟1秒执行，确保DOM元素有足够时间加载
      setTimeout(() => {
        addHighFrequencySyncButton();
      }, 1000);

      // 显示提示信息
      createTopTips(`${liveStatus.isLiving ? "直播中" : "未开播"}`, {
        type: isLiving ? "success" : "warning",
      });
    } else {
      console.warn("未找到CurrentLive菜单项");
      createTopTips("未找到直播状态信息", { type: "warning" });
    }
  } catch (error) {
    console.error("检查直播状态失败:", error);
    createTopTips(`检查直播状态失败: ${error.message}`, { type: "error" });
  }
}

/**
 * 切换违规监控状态
 * @param {HTMLElement} button - 违规监控按钮元素
 */
function toggleHighFrequencySync(button) {
  if (APP_STATE.isHighFrequencySyncActive) {
    // 停止违规监控
    stopHighFrequencySync(button);
  } else {
    // 开始违规监控
    startHighFrequencySync(button);
  }
}

/**
 * 开始违规监控
 * @param {HTMLElement} button - 违规监控按钮元素
 */
function startHighFrequencySync(button) {
  console.log("开始违规监控");

  // 立即执行一次同步
  syncPunishList();

  // 设置每分钟执行一次的定时器
  APP_STATE.highFrequencySyncInterval = setInterval(() => {
    console.log("执行违规监控任务");
    syncPunishList();
  }, 60000); // 60000毫秒 = 1分钟

  // 更新状态
  APP_STATE.isHighFrequencySyncActive = true;

  // 更新按钮文本和样式
  button.textContent = "停止违规监控";
  button.style.backgroundColor = "#fff2f5";
  button.style.color = "#fe2c55";
  button.style.fontWeight = "600";
  button.style.border = "none";
  button.style.outline = "none";

  createTopTips("违规监控已开始，每分钟执行一次", { type: "success" });
}

/**
 * 停止违规监控
 * @param {HTMLElement} button - 违规监控按钮元素
 */
function stopHighFrequencySync(button) {
  console.log("停止违规监控");

  // 清除定时器
  if (APP_STATE.highFrequencySyncInterval) {
    clearInterval(APP_STATE.highFrequencySyncInterval);
    APP_STATE.highFrequencySyncInterval = null;
  }

  // 更新状态
  APP_STATE.isHighFrequencySyncActive = false;

  // 恢复按钮文本和样式
  button.textContent = "开始违规监控";
  button.style.backgroundColor = "#2ed573";
  button.style.color = "#ffffff";
  button.style.fontWeight = "600";
  button.style.border = "1px solid #2ed573";
  button.style.outline = "none";

  createTopTips("违规监控已停止", { type: "info" });
}

/**
 * 页面卸载时清理所有定时器资源
 */
function cleanup() {
  console.log("页面卸载，清理定时器资源");

  // 清理违规检查定时器
  if (APP_STATE.violationCheckInterval) {
    clearInterval(APP_STATE.violationCheckInterval);
    APP_STATE.violationCheckInterval = null;
  }

  // 清理违规监控定时器
  if (APP_STATE.highFrequencySyncInterval) {
    clearInterval(APP_STATE.highFrequencySyncInterval);
    APP_STATE.highFrequencySyncInterval = null;
  }

  // 重置状态
  APP_STATE.isHighFrequencySyncActive = false;
  APP_STATE.highFrequencyButtonAdded = false;
}

// #endregion
