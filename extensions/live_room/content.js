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
  abData: null, // 用于存储AB数据
};

// #endregion

// =================================================================================
// #region Initialization
// =================================================================================

document.addEventListener("DOMContentLoaded", init);

function init() {
  console.log("页面加载完成 DOMContentLoaded");

  setupAccountObserver();
  injectFetchInterceptor();
  setupEventListeners();
  setupPeriodicTasks();

  if (window.location.hostname === "eos.douyin.com") {
    syncPunishList();
  }

  if (
    window.location.href.startsWith(
      "https://buyin.jinritemai.com/dashboard/buyin_live_control/prepare/create"
    )
  ) {
    setupMixedCutSyncButton();
  }
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
  } else if (url.includes("/api/anchor/creative/get_ab") && status === 200) {
    console.log("拦截到AB数据:", body);

    APP_STATE.abData = body;
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
  // 每3秒检查一次违规弹窗
  setInterval(() => {
    const modal_wrapper = document.querySelector(
      ".okee-main-modal-wrapper .okee-main-modal-body .okee-main-content-container .okee-main-content-header.okee-main-modal-content-header"
    );
    if (modal_wrapper) {
      getModalText();
    }
  }, 3000);
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

// #endregion
