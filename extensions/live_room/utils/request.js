// 最大错误次数
var MAX_ERROR_COUNT = 999

// ajx请求
function $ajax(url, options = {}) {
    return new Promise((resolve, reject) => {
        fetch(url, options)
            .then((response) => response.json())
            .then((data) => {
                resolve(data)
            })
            .catch((error) => {
                reject(error)
            })
    })
}

// 通用的调用接口方法
function $Request(api = '', {options = {}, params = {}} = {}) {
    return new Promise((resolve, reject) => {
        const requestURL = API.BaseUrl + api
        const requestOptions = {
            method: options.method || 'POST',
            headers: {
                'Content-Type': options.contentType || 'application/json'
            },
            body: JSON.stringify(params),
            timeout: 60 * 1000
        }

        if (options.contentType === 'multipart/form-data') {
            var formdata = new FormData()
            // 遍历参数
            for (const key in params) {
                formdata.append(key, params[key])
            }
            requestOptions.body = formdata
            delete requestOptions.headers
        }
        console.log(requestURL + ':接口请求的参数', JSON.stringify(params))

        // 如果错误次数超过最大错误次数，直接返回
        if (MAX_ERROR_COUNT <= 0) {
            return Promise.reject(new Error('接口请求错误次数超过最大限制'))
        }
        fetch(requestURL, requestOptions)
            .then((response) => response.json())
            .then((data) => {
                console.log(api + ':接口请求返回的data', data)
                if (data.code === 200) {
                    resolve(data.data)
                } else {
                    MAX_ERROR_COUNT--
                    resolve(new Error(`${api}---接口返回错误: ${JSON.stringify(data)}`))
                }
            })
            .catch((error) => {
                MAX_ERROR_COUNT--
                $handleError(`${api}---接口返回错误: ${JSON.stringify(error)}`)
                reject(error)
            })
    })
}

// 错误处理函数，将错误信息存储在 localStorage 中
async function $handleError(error) {
    console.error('发生错误:', error)

    // 获取存储的错误日志
    let errorLogs = parseJSON(localStorage.getItem('errorLogs'), [])

    // 创建新的错误日志
    const errorLog = {
        message: error?.message || String(error),
        stack: error?.stack || 'No stack trace available',
        time: new Date().toLocaleString()
    }

    // 保留最新的 20 条错误日志
    errorLogs = [errorLog, ...errorLogs.slice(0, 19)]

    // 更新本地存储中的错误日志
    localStorage.setItem('errorLogs', JSON.stringify(errorLogs))
}

// 解析JSON
function parseJSON(jsonString = '', defaultValue = null) {
    // 不可为空，null,undefined
    if (!jsonString || jsonString === 'null' || jsonString === 'undefined') {
        return defaultValue
    }
    try {
        return JSON.parse(jsonString)
    } catch (error) {
        return defaultValue
    }
}
