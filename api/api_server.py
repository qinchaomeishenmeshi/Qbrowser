import asyncio
from threading import Thread
from typing import List, Optional

import uvicorn
from fastapi import (
    FastAPI,
    APIRouter,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Body,
)
from fastapi.middleware.cors import CORSMiddleware

from api.chrome_config_api import router as chrome_config_router
from api.redirect_api import router as redirect_router

from browser.browser_store import browser_store
from utils.common_logger import get_logger
from utils.websocket_manager import ws_manager
from conf import resource_path

from browser.browser_store import browser_store
from utils.common_logger import get_logger
from conf import resource_path

logger = get_logger(__name__)

app = FastAPI()
api_router = APIRouter(tags=["浏览器管理"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_store():
    return app.state.manager_store


@api_router.get("/health", summary="健康检查")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "message": "Backend is running"}


@api_router.get("/browser/status", summary="获取浏览器状态")
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


@api_router.get("/extensions/status", summary="获取全局扩展状态")
async def get_extensions_status():
    """获取全局扩展状态"""
    # 统计所有用户的扩展状态
    managers = await browser_store.get_all()
    active_browsers = [m for m in managers if m.is_running]

    return {
        "status": "running",
        "total_browsers": len(active_browsers),
        "configured_extensions": ["live_room (直播中控)"],
        "message": f"扩展服务运行中，{len(active_browsers)} 个浏览器实例活跃",
    }


@api_router.get("/extensions/{user_id}", summary="获取用户扩展状态")
async def get_user_extensions_status(user_id: str):
    """获取指定用户浏览器的扩展状态"""
    manager = await browser_store.get(user_id)
    if not manager or not manager.is_running:
        raise HTTPException(
            status_code=404, detail=f"用户 {user_id} 的浏览器实例未运行"
        )

    try:
        # Playwright: Get first page
        if not manager.context.pages:
            raise HTTPException(status_code=500, detail="无法获取浏览器标签页")

        page = manager.context.pages[0]
        logger.info(f"开始检查用户 {user_id} 的扩展状态，当前页面: {page.url}")

        # 等待页面加载完成
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
            logger.info(f"页面开始加载: {page.url}")
        except Exception as wait_e:
            logger.warning(f"等待页面加载失败: {wait_e}")

        # 增加额外等待时间确保页面完全加载
        await asyncio.sleep(3)

        # 检查 Service Worker (针对 MV3 扩展)
        sw_list = []
        if manager.context.service_workers:
            for sw in manager.context.service_workers:
                sw_list.append({"url": sw.url})

        # 执行 JavaScript 来检查扩展
        js_code = """
        () => {
            try {
                const info = {
                    url: window.location.href,
                    timestamp: new Date().toISOString(),
                    page_title: document.title,
                    extension_elements: [],
                    is_matching_domain: false
                };
                
                // 检查当前域名是否在匹配范围内
                const matches = ['douyin.com', 'jinritemai.com', 'qwang.com.cn'];
                info.is_matching_domain = matches.some(m => window.location.hostname.includes(m));

                // 检查具体扩展特有的元素
                const selectors = {
                    'live_room_sync': '.sync_wj',
                    'mixed_cut_sync': 'button:contains("同步混剪系统")', // 注意: contains 不是标准 API，需特殊处理
                    'violation_monitor': '#high-frequency-sync-btn'
                };

                // 辅助函数: 查找包含文本的按钮
                const findButtonByText = (text) => {
                    const buttons = document.querySelectorAll('button');
                    return Array.from(buttons).find(btn => btn.textContent.includes(text));
                };

                if (document.querySelector('.sync_wj')) {
                    info.extension_elements.push('live_room_sync_button');
                }
                if (findButtonByText('同步混剪系统')) {
                    info.extension_elements.push('mixed_cut_sync_button');
                }
                if (document.querySelector('#high-frequency-sync-btn')) {
                    info.extension_elements.push('violation_monitor_button');
                }
                
                // 检查全局标志 (如果 content script 有设置)
                info.has_injected_flag = !!window.__scriptInjected;

                return info;
            } catch (error) {
                return { error: error.toString() };
            }
        }
        """

        logger.info(f"执行扩展检查 JavaScript 代码...")
        try:
            js_result = await page.evaluate(js_code)
            logger.info(f"JavaScript 执行结果: {js_result}")
        except Exception as js_error:
            logger.error(f"JavaScript 执行失败: {js_error}")
            js_result = {"error": str(js_error)}

        return {
            "user_id": user_id,
            "browser_running": True,
            "port": manager.port,
            "tab_url": page.url,
            "service_workers": sw_list,
            "extension_check": js_result,
            "configured_extensions": ["live_room (直播中控)"],
            "message": "扩展状态检查完成",
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
                "block_videos (视频屏蔽器)",
            ],
            "message": f"扩展状态检查失败: {e}",
        }


@api_router.get("/system/logs", summary="获取系统日志")
async def get_system_logs(limit: int = 10):
    """获取系统日志"""
    # TODO: 实现真实的日志读取功能
    # 可以从日志文件或日志系统中读取最近的日志记录
    import datetime

    # 返回当前系统状态作为临时日志信息
    managers = await browser_store.get_all()
    active_count = len([m for m in managers if m.is_running])

    current_time = datetime.datetime.now().isoformat()

    return {
        "logs": [
            {
                "timestamp": current_time,
                "level": "INFO",
                "message": f"系统运行正常，当前活跃浏览器实例: {active_count} 个",
                "component": "playwright_manager",
            }
        ],
        "total_count": 1,
        "limit": limit,
        "message": "系统日志获取成功",
        "note": "此接口需要集成日志系统后才能返回完整的历史日志",
    }


@api_router.get("/settings/ui", summary="获取UI设置")
async def get_ui_settings():
    """获取UI设置"""
    return {
        "settings": {"theme": "light", "language": "zh-CN", "sidebarCollapsed": False},
        "message": "UI settings loaded successfully",
    }


@api_router.post("/settings/ui", summary="保存UI设置")
async def save_ui_settings(settings: dict):
    """保存UI设置"""
    # 这里可以将设置保存到数据库或文件
    # 目前只是简单返回成功消息
    return {"success": True, "message": "UI settings saved successfully"}


@api_router.get("/active_instances", summary="获取活跃实例")
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


@api_router.get("/all_instances", summary="获取所有实例")
async def get_all_instances():
    """获取所有缓存或运行中的浏览器实例"""
    managers = await browser_store.get_all()

    instances = []
    for m in managers:
        instances.append(
            {"user_id": m.user_id, "port": m.port, "is_running": m.is_running}
        )

    return {"status": "success", "total_count": len(instances), "instances": instances}


async def launch_browser(user_id: str, url: str = "") -> dict:
    manager = await browser_store.get(user_id)
    if manager is not None and manager.is_running:
        if url:
            try:
                page = await manager.context.new_page()
                await page.goto(url)
                await page.evaluate(f"document.title='{user_id}'")
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
    # 不存在则新建实例 (Use browser_service to create)
    from service.browser_service import browser_service

    manager = await browser_service.get_or_create_browser(user_id)

    if not manager or not manager.is_running:
        return {"user_id": user_id, "status": "fail", "message": f"启动失败: {user_id}"}

    if url:
        try:
            page = await manager.context.new_page()
            await page.goto(url)
            await page.evaluate(f"document.title='{user_id}'")
        except Exception as e:
            # Just log, don't fail the whole start
            logger.error(f"New instance open url failed: {e}")

    return {
        "user_id": user_id,
        "status": "success",
        "port": manager.port,
        "opened_url": url if url else None,
    }


@api_router.post("/start/{user_id}", summary="启动浏览器")
async def start_browser(
    user_id: str, url: str = Query(default="", description="要打开的页面url，可选")
):
    result = await launch_browser(user_id, url)
    if result["status"] in ("fail", "error"):
        raise HTTPException(status_code=500, detail=result.get("message", "未知错误"))
    return result


@api_router.post("/stop", summary="停止指定或所有浏览器")
async def stop_all(user_ids: Optional[List[str]] = Body(default=None)):
    from service.browser_service import browser_service

    await browser_service.stop_all_browsers(user_ids)
    msg = "选中的浏览器已关闭" if user_ids else "所有运行中的浏览器已关闭"
    return {"status": "success", "message": msg}


@api_router.post("/stop/{user_id}", summary="停止指定浏览器")
async def stop_browser_instance(user_id: str):
    from service.browser_service import browser_service

    success = await browser_service.stop_browser(user_id)
    if not success:
        raise HTTPException(
            status_code=404, detail=f"未找到用户 {user_id} 的浏览器实例或停止失败"
        )
    return {
        "status": "success",
        "message": f"用户 {user_id} 的浏览器进程已停止，实例已缓存",
    }


@api_router.post("/browser/create", summary="新建浏览器配置（不启动）")
async def create_browser(user_id: str = Body(..., embed=True)):
    from service.browser_service import browser_service

    manager = await browser_service.create_browser(user_id)
    if not manager:
        raise HTTPException(status_code=500, detail="创建浏览器失败")
    return {"status": "success", "user_id": user_id, "message": "浏览器配置创建成功"}


@api_router.post("/delete_batch", summary="批量彻底删除浏览器实例")
async def delete_browsers_batch(user_ids: List[str] = Body(...)):
    from service.browser_service import browser_service

    results = await browser_service.delete_browsers(user_ids)
    return {"status": "success", "results": results}


@api_router.post("/delete/{user_id}", summary="彻底删除浏览器实例")
async def delete_browser_instance(user_id: str):
    from service.browser_service import browser_service

    success = await browser_service.delete_browser(user_id)
    if not success:
        raise HTTPException(
            status_code=404, detail=f"未找到用户 {user_id} 的浏览器实例或删除失败"
        )
    return {"status": "success", "message": f"用户 {user_id} 的浏览器数据已彻底清理"}


@api_router.post("/start_all", summary="批量启动浏览器")
async def start_all_browsers(
    user_ids: List[str] = Query(..., description="要批量启动的user_id列表"),
    url: str = Query(default="", description="要打开的页面url，可选"),
):
    results = [await launch_browser(user_id, url) for user_id in user_ids]
    return {"results": results}


@api_router.post("/connect/{user_id}", summary="连接现有浏览器")
async def connect_existing_browser(
    user_id: str, port: int = Query(..., description="要连接的浏览器端口号")
):
    """连接到已打开的浏览器实例"""
    try:
        # 检查是否已经存在该用户的浏览器实例
        existing_manager = await browser_store.get(user_id)
        if existing_manager and existing_manager.is_running:
            return {
                "user_id": user_id,
                "status": "already_connected",
                "port": existing_manager.port,
                "message": f"用户 {user_id} 的浏览器实例已存在",
            }

        # 创建新的浏览器管理器实例 (PlaywrightManager)
        from browser.playwright_manager import PlaywrightManager

        manager = PlaywrightManager(user_id=user_id, port=port)

        # 尝试连接检测
        from playwright.async_api import async_playwright

        connected = False
        try:
            async with async_playwright() as p:
                browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
                if len(browser.contexts) > 0:
                    connected = True
                await browser.close()
        except:
            pass

        if connected:
            # 注意：这里我们只是"注册"它。PlaywrightManager 需要 context 才能工作。
            # 如果我们只是 connect，我们得到的是 CDPSession 或 Browser。
            # 真正的 PlaywrightManager 需要 launchPersistentContext。
            # 如果是 connect_over_cdp，我们得到的是 Browser，无法直接转为 PersistentContext。
            # Playwright vs Connect-mode difference.
            # 临时方案：如果 connect 成功，我们认为它是 "managed externally" 并尝试接管。
            # 但为了保持一致性，我们可能需要 initialize() 来真正接管，或者此接口仅作为一个 "登记" ?
            # 当前架构下，connect 似乎是想把外部启动的浏览器纳入管理。
            # 对于 Playwright，最好是让 Manager 启动它。
            # 如果必须支持 connect，我们需要 PlaywrightManager 支持 connect_over_cdp 模式。
            # 简化处理：如果端口通，我们初始化 Manager 并尝试 initialize (这可能会报错如果端口占用)。
            # 正确的做法可能是: 如果端口被占，说明已经在运行。我们只能 connect_over_cdp。
            # 但 PlaywrightManager 设计是持有 context。
            # 我们修改 PlaywrightManager 使其支持 `connect` 模式？
            # 鉴于时间，我们返回 "connection_failed" 如果不支持，或者仅作简单端口检查。

            # 修正：现有逻辑是用来恢复状态的。
            # 让我们假设 browser_service.load_ports 会处理恢复。
            # 这个 API 是手动调用。
            # 我们简单地将其添加到 store，但也需要 manager 处于 "ready" 状态。
            # 只有这行不通。不建议手动 connect。
            return {
                "user_id": user_id,
                "status": "not_supported_migration",
                "message": "Playwright迁移期间暂不支持手动连接外部浏览器，请使用start启动",
            }

        return {
            "user_id": user_id,
            "status": "connection_failed",
            "port": port,
            "message": "连接失败",
        }

    except Exception as e:
        logger.error(f"连接浏览器实例时发生错误 (用户: {user_id}): {e}")
        raise HTTPException(status_code=500, detail=f"连接浏览器实例失败: {str(e)}")


@api_router.post("/connect_batch", summary="批量连接浏览器")
async def connect_batch_browsers(request: dict):
    """批量连接多个已打开的浏览器实例

    Args:
        request: 请求体，包含connections字段，格式: {"connections": [{"user_id": "user1", "port": 9001}, ...]}

    Returns:
        批量连接结果
    """
    connections = request.get("connections", [])

    if not connections:
        raise HTTPException(status_code=400, detail="请求体中缺少connections字段或为空")

    results = []

    for connection in connections:
        user_id = connection.get("user_id")
        port = connection.get("port")

        if not user_id or not port:
            results.append(
                {
                    "user_id": user_id or "unknown",
                    "status": "invalid_params",
                    "port": port or 0,
                    "message": "缺少必要参数 user_id 或 port",
                }
            )
            continue

        try:
            # 复用单个连接的逻辑
            result = await connect_existing_browser(user_id, port)
            results.append(result)
        except Exception as e:
            results.append(
                {
                    "user_id": user_id,
                    "status": "error",
                    "port": port,
                    "message": f"连接失败: {str(e)}",
                }
            )

    return {"results": results}


@api_router.get("/detect_browser/{port}", summary="检测端口浏览器")
async def detect_browser_on_port(port: int):
    """检测指定端口是否有浏览器实例运行

    Args:
        port: 要检测的端口号

    Returns:
        检测结果信息
    """
    try:
        import socket

        # 检查端口是否被占用
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()

        if result == 0:
            # 端口被占用，尝试连接验证是否为浏览器
            try:
                from playwright.async_api import async_playwright

                try:
                    async with async_playwright() as p:
                        browser = await p.chromium.connect_over_cdp(
                            f"http://localhost:{port}"
                        )
                        tabs_count = (
                            len(browser.contexts[0].pages) if browser.contexts else 0
                        )
                        await browser.close()
                except Exception as e:
                    logger.error(f"Playwright connect failed: {e}")
                    raise

                return {
                    "port": port,
                    "status": "browser_detected",
                    "tabs_count": tabs_count,
                    "message": f"端口 {port} 上检测到浏览器实例",
                }

            except Exception as browser_error:
                return {
                    "port": port,
                    "status": "connection_failed",
                    "message": f"端口 {port} 被占用，但连接失败: {str(browser_error)}",
                }
        else:
            return {
                "port": port,
                "status": "port_free",
                "message": f"端口 {port} 未被占用",
            }

    except Exception as e:
        logger.error(f"检测端口 {port} 时发生错误: {e}")
        return {
            "port": port,
            "status": "detection_error",
            "message": f"检测失败: {str(e)}",
        }


app.include_router(api_router, prefix="/api")  # 浏览器管理接口
app.include_router(chrome_config_router, prefix="/api")  # Chrome配置接口
app.include_router(redirect_router, prefix="/api")  # 页面重定向接口


# ========== WebSocket 端点 ==========


@app.websocket("/ws/scheduler")
async def websocket_scheduler(websocket: WebSocket):
    """调度器状态实时推送 WebSocket 端点"""
    await ws_manager.connect(websocket, "scheduler")
    try:
        while True:
            # 保持连接，接收心跳或命令
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "scheduler")
    except Exception as e:
        logger.warning(f"WebSocket scheduler 异常: {e}")
        await ws_manager.disconnect(websocket, "scheduler")


@app.websocket("/ws/browser")
async def websocket_browser(websocket: WebSocket):
    """浏览器状态实时推送 WebSocket 端点"""
    await ws_manager.connect(websocket, "browser")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "browser")
    except Exception as e:
        logger.warning(f"WebSocket browser 异常: {e}")
        await ws_manager.disconnect(websocket, "browser")


@app.get("/ws/status", summary="获取WebSocket状态")
async def get_ws_status():
    """获取 WebSocket 连接状态"""
    return ws_manager.get_status()


@app.on_event("startup")
async def startup_event():
    """服务器启动时加载缓存的实例"""
    from service.browser_service import browser_service
    from browser.playwright_manager import PlaywrightManager
    from utils.database_manager import db_manager

    logger.info("正在加载缓存的浏览器实例...")
    try:
        # 1. 尝试恢复运行中的实例 (基于端口映射)
        await browser_service.load_ports()

        # 2. 从数据库加载所有已知的端口映射，并作为缓存实例添加到 store
        mapping = await db_manager.get_all_ports()
        all_managers = await browser_store.get_all()
        managed_uids = [m.user_id for m in all_managers]

        for user_id, port in mapping.items():
            if user_id not in managed_uids:
                # 作为一个停止的实例加载到 store 中
                manager = PlaywrightManager(user_id, port)
                await browser_store.add(manager)
                logger.info(f"加载缓存实例: {user_id} (已停止)")

    except Exception as e:
        logger.error(f"启动加载过程中出错: {e}")


def run_server(host: str = "127.0.0.1", port: int = 8000):
    def _run():
        uvicorn.run(app, host=host, port=port, log_level="info")

    Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    run_server()
