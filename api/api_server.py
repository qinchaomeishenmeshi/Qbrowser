import asyncio
from threading import Thread
from typing import List

import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from api.api_business import business_router
from api.scheduler_api import router as scheduler_router
from api.chrome_config_api import router as chrome_config_router
from browser.browser_manager import BrowserManager
from browser.browser_store import browser_store
from utils.common_logger import get_logger
from conf import resource_path

logger = get_logger(__name__)

app = FastAPI()
api_router = APIRouter()

# 配置模板和静态文件
templates = Jinja2Templates(directory=resource_path("templates"))

# 挂载静态文件（如果存在）
try:
    app.mount("/static", StaticFiles(directory=resource_path("static")), name="static")
except Exception:
    pass  # 静态文件目录不存在时忽略

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_store():
    return app.state.manager_store


@api_router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "message": "Backend is running"}


@api_router.get("/status")
async def get_status():
    count = await browser_store.count()
    return {"running": True, "user_count": count}


@api_router.get("/browser/status")
async def get_browser_status():
    """获取浏览器状态"""
    count = await browser_store.count()
    managers = await browser_store.get_all()
    active_count = len([m for m in managers if m.is_running])
    return {
        "status": "running",
        "total_instances": count,
        "active_instances": active_count,
        "message": "Browser service is running",
    }


@api_router.get("/extensions/status")
async def get_extensions_status():
    """获取扩展状态"""
    return {
        "status": "running",
        "loaded_extensions": [],
        "message": "Extensions service is running",
    }


@api_router.get("/extensions/{user_id}")
async def get_user_extensions_status(user_id: str):
    """获取指定用户浏览器的扩展状态"""
    manager = await browser_store.get(user_id)
    if not manager or not manager.is_running:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 的浏览器实例未运行")
    
    try:
        # 通过 JavaScript 检查浏览器中的扩展
        tab = manager.browser.get_tab()
        if not tab:
            raise HTTPException(status_code=500, detail="无法获取浏览器标签页")
        
        logger.info(f"开始检查用户 {user_id} 的扩展状态，当前页面: {tab.url}")
        
        # 等待页面加载完成
        try:
            tab.wait.load_start()
            logger.info(f"页面开始加载: {tab.url}")
        except Exception as wait_e:
            logger.warning(f"等待页面加载失败: {wait_e}")
        
        # 增加额外等待时间确保页面完全加载
        await asyncio.sleep(3)
        
        # 执行 JavaScript 来检查扩展
        js_code = """
        (() => {
            try {
                console.log('=== 开始检查扩展状态 ===');
                const extensions = [];
                const info = {
                    url: window.location.href,
                    readyState: document.readyState,
                    timestamp: new Date().toISOString(),
                    page_title: document.title
                };
                
                // 检查 Chrome 扩展 API
                info.chrome_available = typeof chrome !== 'undefined';
                info.runtime_available = typeof chrome !== 'undefined' && !!chrome.runtime;
                console.log('Chrome API available:', info.chrome_available);
                console.log('Runtime available:', info.runtime_available);
                
                if (info.chrome_available && info.runtime_available) {
                    try {
                        // 尝试获取扩展 ID
                        if (chrome.runtime.id) {
                            info.extension_id = chrome.runtime.id;
                            console.log('Extension ID:', chrome.runtime.id);
                        }
                        extensions.push({
                            name: 'Chrome扩展API可用',
                            status: 'active',
                            type: 'chrome_extension_api',
                            extension_id: chrome.runtime.id || 'unknown'
                        });
                    } catch (e) {
                        console.error('Chrome API error:', e);
                        extensions.push({
                            name: 'Chrome扩展API错误',
                            status: 'error',
                            error: e.toString(),
                            type: 'chrome_extension_api'
                        });
                    }
                }
                
                // 检查页面中是否有扩展注入的元素
                const extensionSelectors = [
                    '[data-extension]',
                    '[id*="extension"]', 
                    '[class*="extension"]',
                    '[data-live-room]',
                    '[data-block-videos]',
                    '.live-room-extension',
                    '.video-blocker',
                    '#live-room-control',
                    '#video-block-extension'
                ];
                
                let totalElements = 0;
                extensionSelectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            totalElements += elements.length;
                            console.log(`Found ${elements.length} elements for selector: ${selector}`);
                            extensions.push({
                                name: `扩展元素: ${selector}`,
                                status: 'detected',
                                count: elements.length,
                                type: 'dom_injection'
                            });
                        }
                    } catch (selectorError) {
                        console.error(`Selector error for ${selector}:`, selectorError);
                    }
                });
                
                // 检查是否有扩展相关的全局变量
                const globalVars = ['extensionLoaded', 'liveRoomExtension', 'blockVideosExtension'];
                globalVars.forEach(varName => {
                    try {
                        if (window[varName]) {
                            console.log(`Found global variable: ${varName}`);
                            extensions.push({
                                name: `全局变量: ${varName}`,
                                status: 'detected',
                                value: typeof window[varName],
                                type: 'global_variable'
                            });
                        }
                    } catch (globalError) {
                        console.error(`Global variable check error for ${varName}:`, globalError);
                    }
                });
                
                // 检查扩展脚本
                const scripts = Array.from(document.scripts).filter(s => 
                    s.src && (s.src.includes('extension') || s.src.includes('chrome-extension'))
                );
                info.extension_scripts = scripts.length;
                console.log('Extension scripts found:', scripts.length);
                
                // 检查 body 类名
                const bodyClasses = document.body.className;
                info.body_classes = bodyClasses;
                info.has_extension_classes = bodyClasses.includes('extension') || bodyClasses.includes('plugin');
                
                info.extensions = extensions;
                info.total_extension_elements = totalElements;
                info.user_agent = navigator.userAgent;
                
                console.log('=== 扩展检查完成 ===', info);
                return info;
            } catch (error) {
                console.error('扩展检查出错:', error);
                const errorResult = {
                    error: error.toString(),
                    stack: error.stack,
                    url: window.location.href,
                    timestamp: new Date().toISOString()
                };
                console.log('错误结果:', errorResult);
                return errorResult;
            }
        })()
        """
        
        logger.info(f"执行扩展检查 JavaScript 代码...")
        try:
            result = tab.run_js(js_code)
            logger.info(f"JavaScript 执行成功，结果类型: {type(result)}")
            logger.info(f"JavaScript 执行结果: {result}")
        except Exception as js_error:
            logger.error(f"JavaScript 执行失败: {js_error}", exc_info=True)
            result = {"js_execution_error": str(js_error), "error_type": type(js_error).__name__}
        
        return {
            "user_id": user_id,
            "browser_running": True,
            "port": manager.port,
            "tab_url": tab.url,
            "extension_check": result,
            "configured_extensions": [
                "live_room (直播中控)",
                "block_videos (视频屏蔽器)"
            ],
            "message": "扩展状态检查完成"
        }
        
    except Exception as e:
        logger.error(f"检查用户 {user_id} 扩展状态失败: {e}", exc_info=True)
        return {
            "user_id": user_id,
            "browser_running": True,
            "port": manager.port,
            "extension_check": None,
            "error": str(e),
            "configured_extensions": [
                "live_room (直播中控)",
                "block_videos (视频屏蔽器)"
            ],
            "message": f"扩展状态检查失败: {e}"
        }


@api_router.get("/scheduler/recent")
async def get_recent_tasks():
    """获取最近的任务"""
    return {"tasks": [], "message": "No recent tasks"}


@api_router.get("/system/logs")
async def get_system_logs(limit: int = 10):
    """获取系统日志"""
    return {"logs": [], "message": "No logs available"}


@api_router.get("/settings/ui")
async def get_ui_settings():
    """获取UI设置"""
    return {
        "settings": {"theme": "light", "language": "zh-CN", "sidebarCollapsed": False},
        "message": "UI settings loaded successfully",
    }


@api_router.post("/settings/ui")
async def save_ui_settings(settings: dict):
    """保存UI设置"""
    # 这里可以将设置保存到数据库或文件
    # 目前只是简单返回成功消息
    return {"success": True, "message": "UI settings saved successfully"}


@api_router.get("/active_instances")
async def get_active_instances():
    """获取所有激活的浏览器实例"""
    # 从 browser_store 获取所有浏览器管理器实例
    managers = await browser_store.get_all()

    # 筛选出正在运行的浏览器实例的 user_id
    active_devices = [manager.user_id for manager in managers if manager.is_running]

    logger.info(f"获取到 {len(active_devices)} 个活跃浏览器实例: {active_devices}")
    return {
        "status": "success",
        "active_count": len(active_devices),
        "active_instances": active_devices,
    }


async def launch_browser(user_id: str, url: str = "") -> dict:
    manager = await browser_store.get(user_id)
    if manager is not None and manager.is_running:
        if url:
            try:
                tab = manager.browser.new_tab(url=url)
                tab.run_js(f"document.title='{user_id}'")
                return {
                    "user_id": user_id,
                    "status": "already_running",
                    "port": manager.port,
                    "opened_url": url,
                }
            except Exception as e:
                return {
                    "user_id": user_id,
                    "status": "error",
                    "message": f"已存在实例但新建tab失败: {e}",
                }
        else:
            return {
                "user_id": user_id,
                "status": "already_running",
                "port": manager.port,
                "opened_url": None,
            }
    # 不存在则新建实例
    count = await browser_store.count()
    port = 9000 + count
    manager = BrowserManager(user_id=user_id, port=port)
    success = await asyncio.to_thread(manager.initialize)
    if not success:
        return {"user_id": user_id, "status": "fail", "message": f"启动失败: {user_id}"}
    await browser_store.add(manager)
    if url:
        try:
            tab = manager.browser.new_tab(url=url)
            tab.run_js(f"document.title='{user_id}'")
        except Exception as e:
            return {
                "user_id": user_id,
                "status": "error",
                "message": f"新实例新建tab失败: {e}",
            }
    return {
        "user_id": user_id,
        "status": "success",
        "port": port,
        "opened_url": url if url else None,
    }


@api_router.post("/start/{user_id}")
async def start_browser(
    user_id: str, url: str = Query(default="", description="要打开的页面url，可选")
):
    result = await launch_browser(user_id, url)
    if result["status"] in ("fail", "error"):
        raise HTTPException(status_code=500, detail=result.get("message", "未知错误"))
    return result


@api_router.post("/stop")
async def stop_all():
    await browser_store.clear()
    return {"status": "success", "message": "所有浏览器已关闭"}


@api_router.post("/start_all")
async def start_all_browsers(
    user_ids: List[str] = Query(..., description="要批量启动的user_id列表"),
    url: str = Query(default="", description="要打开的页面url，可选"),
):
    results = [await launch_browser(user_id, url) for user_id in user_ids]
    return {"results": results}


app.include_router(api_router, prefix="/api")  # 浏览器管理接口
app.include_router(business_router)  # 业务接口
app.include_router(scheduler_router)  # 定时任务管理接口
app.include_router(chrome_config_router, prefix="/api")  # Chrome配置接口


# 定时任务管理界面路由
@app.get("/", response_class=HTMLResponse)
async def dashboard_redirect(request: Request):
    """根路径重定向到定时任务管理界面"""
    return templates.TemplateResponse("scheduler_dashboard.html", {"request": request})


@app.get("/scheduler/dashboard", response_class=HTMLResponse)
async def scheduler_dashboard(request: Request):
    """定时任务管理界面"""
    return templates.TemplateResponse("scheduler_dashboard.html", {"request": request})


@app.get("/chrome/config", response_class=HTMLResponse)
async def chrome_config_page(request: Request):
    """Chrome配置管理界面"""
    return templates.TemplateResponse("chrome_config.html", {"request": request})


def run_server(host: str = "127.0.0.1", port: int = 8000):
    def _run():
        uvicorn.run(app, host=host, port=port, log_level="info")

    Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    run_server()
