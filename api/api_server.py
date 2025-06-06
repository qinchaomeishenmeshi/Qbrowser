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
from browser.browser_manager import BrowserManager
from browser.browser_store import browser_store
from utils.common_logger import get_logger

logger = get_logger(__name__)

app = FastAPI()
api_router = APIRouter()

# 配置模板和静态文件
templates = Jinja2Templates(directory="templates")

# 挂载静态文件（如果存在）
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
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


@api_router.get("/status")
async def get_status():
    count = await browser_store.count()
    return {"running": True, "user_count": count}


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


app.include_router(api_router)  # 浏览器管理接口
app.include_router(business_router)  # 业务接口
app.include_router(scheduler_router)  # 定时任务管理接口


# 定时任务管理界面路由
@app.get("/", response_class=HTMLResponse)
async def dashboard_redirect(request: Request):
    """根路径重定向到定时任务管理界面"""
    return templates.TemplateResponse("scheduler_dashboard.html", {"request": request})


@app.get("/scheduler/dashboard", response_class=HTMLResponse)
async def scheduler_dashboard(request: Request):
    """定时任务管理界面"""
    return templates.TemplateResponse("scheduler_dashboard.html", {"request": request})


def run_server(host: str = "127.0.0.1", port: int = 8000):
    def _run():
        uvicorn.run(app, host=host, port=port, log_level="info")

    Thread(target=_run, daemon=True).start()


if __name__ == "__main__":
    run_server()
