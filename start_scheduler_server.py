#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务服务启动脚本

启动一个包含定时任务管理功能的 FastAPI 服务器，提供：
1. RESTful API 接口管理定时任务
2. Web 管理界面
3. 自动启动定时任务调度器

使用方法：
    python start_scheduler_server.py
    
然后访问：
    - API 文档: http://localhost:8000/docs
    - 管理界面: http://localhost:8000/scheduler/dashboard
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

# 导入定时任务相关模块
from api.scheduler_api import router as scheduler_router
from worker.scheduler_client import scheduler_client
from utils.common_logger import get_logger

logger = get_logger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="直播间数据采集定时任务系统",
    description="提供定时任务管理和直播间数据采集功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 设置模板目录
templates = Jinja2Templates(directory="templates")

# 注册路由
app.include_router(scheduler_router)

# 静态文件服务（如果需要）
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路径重定向到管理界面"""
    return templates.TemplateResponse(
        "scheduler_dashboard.html", 
        {"request": request}
    )


@app.get("/scheduler/dashboard", response_class=HTMLResponse)
async def scheduler_dashboard(request: Request):
    """定时任务管理界面"""
    return templates.TemplateResponse(
        "scheduler_dashboard.html", 
        {"request": request}
    )


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化操作"""
    logger.info("🚀 定时任务服务启动中...")
    
    try:
        # 启动定时任务调度器
        await scheduler_client.start()
        logger.info("✅ 定时任务调度器启动成功")
        
        # 加载已保存的任务配置
        task_count = len(scheduler_client.task_configs)
        enabled_count = sum(1 for config in scheduler_client.task_configs.values() if config.enabled)
        
        logger.info(f"📋 已加载 {task_count} 个任务配置，其中 {enabled_count} 个已启用")
        
    except Exception as e:
        logger.error(f"❌ 启动定时任务调度器失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    logger.info("🛑 定时任务服务关闭中...")
    
    try:
        # 停止定时任务调度器
        await scheduler_client.stop()
        logger.info("✅ 定时任务调度器已停止")
        
    except Exception as e:
        logger.error(f"❌ 停止定时任务调度器失败: {e}")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    scheduler_running = scheduler_client.scheduler.running if scheduler_client.scheduler else False
    task_count = len(scheduler_client.task_configs)
    
    return {
        "status": "healthy",
        "scheduler_running": scheduler_running,
        "task_count": task_count,
        "timestamp": asyncio.get_event_loop().time()
    }


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🕐 直播间数据采集定时任务系统")
    print("="*60)
    print("📡 API 文档: http://localhost:8000/docs")
    print("🎛️  管理界面: http://localhost:8000/scheduler/dashboard")
    print("🔍 健康检查: http://localhost:8000/health")
    print("="*60 + "\n")
    
    # 确保必要的目录存在
    os.makedirs("data/tasks", exist_ok=True)
    os.makedirs("data/results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 启动服务器
    uvicorn.run(
        "start_scheduler_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 生产环境建议设为 False
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()