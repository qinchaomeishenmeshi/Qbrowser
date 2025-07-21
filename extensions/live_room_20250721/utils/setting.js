// 在内容脚本的开头设置一个标志变量
if (!window.__scriptInjected) {
    window.__scriptInjected = true // 设置标志，表示脚本已经注入
    console.log('内容脚本已注入到页面')
}

// 延迟时间设置
var DELAY = {
    // DOM 操作延迟时间
    DOM_DELAY: 500,
    // 页面加载延迟时间
    PAGE_DELAY: 3000
}

const taskTypeEnums = {
    // 任务类型
    AUTO: '1',
    POI: '2',
    ALL: '3'
}

// 接口API
const API = {
    // basicURL
    BaseUrl: 'https://hj.qwang.com.cn/dev-api',

    // 获取任务task的api
    getTaskApi: '/videoclip/admin/autopublishtask/getNoPublicData',
    // 同步账号的api
    syncAccountApi: '/videoclip/admin/juzhensubaccount/accountManage',
    // 单独同步userID的api
    syncUserIdApi: '/videoclip/admin/autopublishtask/updateUserIdByAccountNo',
    // 发布成功的api
    updateAutoPublishTaskApi: '/videoclip/admin/autopublishtask/updateAutoPublishTask',
    // 记录失败日志的api
    failedApi: '/videoclip/admin/autopublishtask/failAutoPublishTask',
    // 抖音获取话题id的api
    getTopicIdApi: '/videoclip/admin/autopublishtask/getTopicName?topicName=',
    // 邮件推送的api
    sendEmailApi: '/videoclip/admin/send/email',
    // 创建直播计划同步回混剪系统
    createPlan: '/aiplay/admin/LivePlan/createPlan',
    // 直播计划同步回混剪系统
    saveProductListApi: '/aiplay/ai/interaction/saveProductList',
    // 百应直播计划同步回混剪系统
    saveEcProductListApi: '/aiplay/ai/interaction/saveEcProductList',
    // 定时获取主动评论的数据
    pullAdminComment: '/vediows/admin/livestreamingcomments/pullAdminComment',
    // 保存违规信息
    liveviolationrecordsdealSaveApi: '/aiplay/admin/liveviolationrecordsdeal/save',
    // 保存直播复盘记录
    livebroadcastreviewSaveApi: '/aiplay/admin/livebroadcastreview/batchSave',
    // 保存百应直播复盘记录
    livereplaydatasynmessageApi: '/aiplay/admin/livereplaydata/synmessage',
    // 保存百应直播大屏信息
    livereplaydatadetailsynmessageApi: '/aiplay/admin/livereplaydatadetail/synmessage'

}

// 页面地址
const PAGE = {
    // 机构号首页
    creatorHomePage: 'https://creator.douyin.com/creator-micro/home',
    // 子账号首页
    childCreatorHomePage: 'https://creator.douyin.com/',
    // 子账号内容管理页码
    childContentPage: 'https://creator.douyin.com/content/manage',
    // 子账号内容管理页面 - 发布完成
    childContentPagePublished: 'https://creator.douyin.com/content/manage?enter_from=publish',
    // 子账号发布管理页面
    childHomePage: 'https://creator.douyin.com/content/',
    // 子账号上传页面
    childUploadPage: 'https://creator.douyin.com/content/upload',
    // 子账号发布页面
    childPublishPage: 'https://creator.douyin.com/content/publish?enter_from=publish_page',
    // 测试页面
    systemPage: 'https://creator.douyin.com/content/publish?enter_from=publish_page',
    // systemPage: 'https://bj.devwwd.site'
    livePage: '/livesite/live/current'
}

// 话题名称列表
var topicNames = []
// 记录当前页数
var currentPage = 1
// 记录最大页数
var maxPage = 1
// 当前账号列表
var currentAccountList = []
// 创建一个空数组来保存收集到的数据
var accountList = []
