;(function () {
    console.log('=== fetch & XHR interceptor loaded ===');

    const TARGET_PATH = '/data/life/live/plan/detail/';
    const AGREEMENT_GET_PATH = '/data/life/live/case/agreement/get';
    const LIVE_CORE_DARA = '/compass_api/author/live/live_screen/core_data'

    function shouldIntercept(url) {
        return url.includes(TARGET_PATH) || url.includes(AGREEMENT_GET_PATH) || url.includes(LIVE_CORE_DARA)
    }

    function dispatch(url, status, body) {
        window.dispatchEvent(new CustomEvent('fetchResponse', {
            detail: {url, status, body}
        }));
    }

    // —— 拦截 fetch ——
    const _fetch = window.fetch;
    window.fetch = function (input, init) {
        const url = typeof input === 'string' ? input : input.url;
        if (shouldIntercept(url)) {
            return _fetch.call(this, input, init).then(response => {
                response.clone().text().then(body => dispatch(url, response.status, body));
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
            this.addEventListener('load', () => {
                let respBody = this.response || this.responseText;
                dispatch(this._url, this.status, typeof respBody === 'string' ? respBody : JSON.stringify(respBody));
            });
        }
        return _send.call(this, body);
    };

})();
