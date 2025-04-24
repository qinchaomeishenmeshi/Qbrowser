;(function () {
    const originalFetch = window.fetch
    const TARGET_PATH = '/data/life/live/plan/detail/'
    // const BAN_INFO_PATH = "/data/life/live/user/ban_info/"
    // const TARGET_PATH = '/data/life/live/shelves/anchor/'

    window.fetch = function (url, options) {
        if (url.includes(TARGET_PATH)) {
            return originalFetch(url, options).then((response) => {
                response
                    .clone()
                    .text()
                    .then((body) => {
                        const event = new CustomEvent('fetchResponse', {
                            detail: {
                                url: url,
                                status: response.status,
                                body: body
                            }
                        })
                        window.dispatchEvent(event)
                    })
                return response
            })
        }
        // if (url.includes(BAN_INFO_PATH)) {
        //     return originalFetch(url, options).then((response) => {
        //         response
        //             .clone()
        //             .text()
        //             .then((body) => {
        //                 const event = new CustomEvent('fetchResponse', {
        //                     detail: {
        //                         url: url,
        //                         status: response.status,
        //                         body: body
        //                     }
        //                 })
        //                 window.dispatchEvent(event)
        //             })
        //     })
        // }
        return originalFetch(url, options)
    }
})()
