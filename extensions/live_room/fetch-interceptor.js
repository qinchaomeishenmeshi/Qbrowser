(function () {
  console.log("=== fetch & XHR interceptor loaded ===");

  const TARGET_PATH = "/data/life/live/plan/detail/";
  const AGREEMENT_GET_PATH = "/data/life/live/case/agreement/get";
  const LIVE_CORE_DARA = "/compass_api/author/live/live_screen/core_data";
  const LIVE_PLANS_PATH = "/api/anchor/livepc/get_live_plans";
  const PACK_DETAIL_PATH = "/pc/selection/decision/pack_detail";

  function shouldIntercept(url) {
    return (
      url.includes(TARGET_PATH) ||
      url.includes(AGREEMENT_GET_PATH) ||
      url.includes(LIVE_CORE_DARA) ||
      url.includes(LIVE_PLANS_PATH) ||
      url.includes(PACK_DETAIL_PATH)
    );
  }

  function dispatch(url, status, body, requestBody = null) {
    window.dispatchEvent(
      new CustomEvent("fetchResponse", {
        detail: { url, status, body, requestBody },
      })
    );
  }

  // —— 拦截 fetch ——
  const _fetch = window.fetch;
  window.fetch = function (input, init) {
    const url = typeof input === "string" ? input : input.url;
    if (shouldIntercept(url)) {
      const requestBody = init && init.body ? init.body : null;
      return _fetch.call(this, input, init).then((response) => {
        response
          .clone()
          .text()
          .then((body) => {
            // 对于pack_detail接口，传递请求体信息
            if (url.includes(PACK_DETAIL_PATH)) {
              dispatch(url, response.status, body, requestBody);
            } else {
              dispatch(url, response.status, body);
            }
          });
        return response;
      });
    }
    return _fetch.call(this, input, init);
  };

  // —— 拦截 XHR ——
  const _open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url, ...args) {
    this._url = url;
    return _open.call(this, method, url, ...args);
  };
  const _send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function (body) {
    if (shouldIntercept(this._url)) {
      this.addEventListener("load", () => {
        let respBody = this.response || this.responseText;
        dispatch(
          this._url,
          this.status,
          typeof respBody === "string" ? respBody : JSON.stringify(respBody)
        );
      });
    }
    return _send.call(this, body);
  };
})();
