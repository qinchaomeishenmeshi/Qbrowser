#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务服务启动脚本（使用 lifespan 生命周期）
"""

import os
import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入定时任务相关模块
from api.scheduler_api import router as scheduler_router
from worker.scheduler_client import scheduler_client
from utils.common_logger import get_logger
from conf import resource_path

logger = get_logger(__name__)

# 设置模板目录
templates = Jinja2Templates(directory=resource_path("templates"))

# 定义 lifespan 生命周期处理函数
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 定时任务服务启动中...")

    try:
        await scheduler_client.start()
        logger.info("✅ 定时任务调度器启动成功")
        task_count = len(scheduler_client.task_configs)
        enabled_count = sum(1 for config in scheduler_client.task_configs.values() if config.enabled)
        logger.info(f"📋 已加载 {task_count} 个任务配置，其中 {enabled_count} 个已启用")
    except Exception as e:
        logger.error(f"❌ 启动定时任务调度器失败: {e}")

    yield  # 应用生命周期执行中...

    logger.info("🛑 定时任务服务关闭中...")
    try:
        await scheduler_client.stop()
        logger.info("✅ 定时任务调度器已停止")
    except Exception as e:
        logger.error(f"❌ 停止定时任务调度器失败: {e}")


# 创建 FastAPI 应用并绑定 lifespan
app = FastAPI(
    title="直播间数据采集定时任务系统",
    description="提供定时任务管理和直播间数据采集功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 注册路由和静态资源
app.include_router(scheduler_router)
static_path = resource_path("static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("scheduler_dashboard.html", {"request": request})


@app.get("/scheduler/dashboard", response_class=HTMLResponse)
async def scheduler_dashboard(request: Request):
    return templates.TemplateResponse("scheduler_dashboard.html", {"request": request})


@app.get("/health")
async def health_check():
    scheduler_running = scheduler_client.scheduler.running if scheduler_client.scheduler else False
    task_count = len(scheduler_client.task_configs)
    return {
        "status": "healthy",
        "scheduler_running": scheduler_running,
        "task_count": task_count,
        "timestamp": asyncio.get_event_loop().time()
    }


def main():
    print("\n" + "=" * 60)
    print("🕐 直播间数据采集定时任务系统")
    print("=" * 60)
    print("📡 API 文档: http://localhost:8000/docs")
    print("🎛️  管理界面: http://localhost:8000/scheduler/dashboard")
    print("🔍 健康检查: http://localhost:8000/health")
    print("=" * 60 + "\n")

    # 确保数据目录存在
    os.makedirs(resource_path("data/tasks"), exist_ok=True)
    os.makedirs(resource_path("data/results"), exist_ok=True)
    os.makedirs(resource_path("logs"), exist_ok=True)

    # 启动 FastAPI 服务
    uvicorn.run(
        "start_scheduler_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
