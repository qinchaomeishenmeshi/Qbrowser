// 最大错误次数
var MAX_ERROR_COUNT = 999;

// ajx请求
function $ajax(url, options = {}) {
  return new Promise((resolve, reject) => {
    fetch(url, options)
      .then((response) => response.json())
      .then((data) => {
        resolve(data);
      })
      .catch((error) => {
        reject(error);
      });
  });
}

// 通用的调用接口方法
function $Request(api = "", { options = {}, params = {} } = {}) {
  return new Promise((resolve, reject) => {
    const requestURL = API.BaseUrl + api;
    const requestOptions = {
      method: options.method || "POST",
      headers: {
        "Content-Type": options.contentType || "application/json",
      },
      body: JSON.stringify(params),
      timeout: 60 * 1000,
    };

    if (options.contentType === "multipart/form-data") {
      var formdata = new FormData();
      // 遍历参数
      for (const key in params) {
        formdata.append(key, params[key]);
      }
      requestOptions.body = formdata;
      delete requestOptions.headers;
    }
    console.log(requestURL + ":接口请求的参数", JSON.stringify(params));

    // 如果错误次数超过最大错误次数，直接返回
    if (MAX_ERROR_COUNT <= 0) {
      return Promise.reject(new Error("接口请求错误次数超过最大限制"));
    }
    fetch(requestURL, requestOptions)
      .then((response) => response.json())
      .then((data) => {
        console.log(api + ":接口请求返回的data", data);
        if (data.code === 200) {
          resolve(data.data);
        } else {
          MAX_ERROR_COUNT--;
          resolve(new Error(`${api}---接口返回错误: ${JSON.stringify(data)}`));
        }
      })
      .catch((error) => {
        MAX_ERROR_COUNT--;
        $handleError(`${api}---接口返回错误: ${JSON.stringify(error)}`);
        reject(error);
      });
  });
}

// 错误处理函数，将错误信息存储在 localStorage 中
async function $handleError(error) {
  console.error("发生错误:", error);

  // 获取存储的错误日志
  let errorLogs = parseJSON(localStorage.getItem("errorLogs"), []);

  // 创建新的错误日志
  const errorLog = {
    message: error?.message || String(error),
    stack: error?.stack || "No stack trace available",
    time: new Date().toLocaleString(),
  };

  // 保留最新的 20 条错误日志
  errorLogs = [errorLog, ...errorLogs.slice(0, 19)];

  // 更新本地存储中的错误日志
  localStorage.setItem("errorLogs", JSON.stringify(errorLogs));
}

// 解析JSON
function parseJSON(jsonString = "", defaultValue = null) {
  // 不可为空，null,undefined
  if (!jsonString || jsonString === "null" || jsonString === "undefined") {
    return defaultValue;
  }
  try {
    return JSON.parse(jsonString);
  } catch (error) {
    return defaultValue;
  }
}

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// 获取ab数据 - 通过Chrome插件background脚本请求
const getSignBuyin = async () => {
  try {
    const response = await new Promise((resolve, reject) => {
      var raw = JSON.stringify({
        scene_info: {
          request_page: 2,
        },
        biz_id: "3766154142163272068",
        biz_id_type: 2,
        enter_from: "pc.unknow.unknow",
        data_module: "pc-non-core",
        extra: {
          use_kol_product: "1",
        },
        source_type: "force",
        "User-Agent":
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
      });
      chrome.runtime.sendMessage(
        {
          action: "FETCH_AB_DATA",
          data: {
            url: API.originUrl + API.getSignBuyinApi,
            options: {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: raw,
            },
          },
        },
        (response) => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else {
            resolve(response);
          }
        }
      );
    });

    if (response.data) {
      console.log("获取ab数据成功:", response.data);
      return response.data.data;
    } else {
      console.error("获取ab数据失败:", response.data.msg);
      throw new Error(response.data.msg);
    }
  } catch (error) {
    console.error("获取ab数据请求失败:", error);
    throw error;
  }
};

// 获取commodityDetail信息
async function getCommodityDetail(productId, productsList) {
  // 添加随机延时（0-2秒）
  await delay(Math.random() * 2000);
  const baseUrl = `https://eos.douyin.com/life/alliance/v2/goods/product/commodity/detail/get?from_type=5&product_id=${productId}`;
  return fetch(baseUrl)
    .then((response) => response.json())
    .then((data) => {
      console.log("获取commodityDetail信息成功:", data);

      return data;
    })
    .catch((error) => {
      console.error("获取commodityDetail信息失败:", error);
      window.alert("获取commodityDetail信息失败" + JSON.stringify(error));
    });
}

// 获取商品详情数据
async function getProductDetail(productId, productsList) {
  window.scrollBy({
    top: Math.random() * 100,
    behavior: "smooth",
  });
  const baseUrl = `https://eos.douyin.com/life/alliance/v2/goods/product/detail/get?from_type=5&image_size=%7B%22width%22:750%7D&product_id=${productId}`;
  return fetch(baseUrl)
    .then((response) => response.json())
    .then((data) => {
      console.log("获取商品详情成功:", data);

      return data;
    })
    .catch((error) => {
      console.error("获取商品详情失败:", error);
      window.alert("获取商品详情失败" + JSON.stringify(error));
    });
}

// 百应获取直播中控台商品列表信息，通过promotion_ids获取
async function getPromotionsV2(promotion_ids) {
  const baseUrl = `https://buyin.jinritemai.com/api/anchor/livepc/promotions_v2`;
  const signBuyin = await getSignBuyin();
  // 构建查询参数
  const params = {
    // ewid: "127d19629b5f6ea3169dc747fa9aa9dd",
    list_type: "1",
    source_type: "force",
    promotion_ids: promotion_ids,
    extra: "hit_marketing_ab",
    promotion_info_fields: "all",
    room_info_fields: "all",
    ms_token: signBuyin.ms_token,
    a_bogus: signBuyin.a_bogus,
  };

  // 将参数转换为URL查询字符串
  const queryString = new URLSearchParams(params).toString();
  const fullUrl = `${baseUrl}?${queryString}`;

  try {
    const response = await fetch(fullUrl, {
      method: "GET",
      headers: {
        Accept: "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
      },
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("获取promotions_v2信息成功:", data);
    return data;
  } catch (error) {
    console.error("获取promotions_v2信息失败:", error);
    throw error; // 重新抛出错误，让调用者处理
  }
}
