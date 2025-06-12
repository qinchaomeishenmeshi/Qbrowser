#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务管理 API

提供 RESTful API 接口来管理定时任务：
1. 创建、删除、启用、禁用任务
2. 查询任务配置和执行结果
3. 任务状态监控
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from worker.scheduler_client import (
    scheduler_client, 
    create_cron_task, 
    create_interval_task,
    TaskConfig,
    TriggerType
)
from utils.common_logger import get_logger
from utils.common_response import PublicResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/scheduler", tags=["定时任务管理"])


# Pydantic 模型定义
class CronTaskRequest(BaseModel):
    """创建 Cron 定时任务请求"""
    task_id: str = Field(..., description="任务唯一标识")
    name: str = Field(..., description="任务名称")
    description: str = Field("", description="任务描述")
    cron_expression: str = Field(..., description="Cron 表达式，如 '0 */30 * * * *'")
    target_function: str = Field(..., description="目标函数名")
    function_params: Dict[str, Any] = Field(..., description="函数参数")
    enabled: bool = Field(True, description="是否启用")


class IntervalTaskRequest(BaseModel):
    """创建间隔定时任务请求"""
    task_id: str = Field(..., description="任务唯一标识")
    name: str = Field(..., description="任务名称")
    description: str = Field("", description="任务描述")
    interval_seconds: int = Field(..., description="间隔秒数")
    target_function: str = Field(..., description="目标函数名")
    function_params: Dict[str, Any] = Field(..., description="函数参数")
    enabled: bool = Field(True, description="是否启用")


class TaskToggleRequest(BaseModel):
    """任务启用/禁用请求"""
    task_id: str = Field(..., description="任务ID")


@router.post("/tasks/cron", summary="创建 Cron 定时任务")
async def create_cron_task_api(request: CronTaskRequest):
    """创建基于 Cron 表达式的定时任务
    
    Cron 表达式格式：
    - 6位格式：秒 分 时 日 月 周
    - 5位格式：分 时 日 月 周（秒默认为0）
    
    示例：
    - "0 */30 * * * *" - 每30分钟执行
    - "0 0 8 * * *" - 每天8点执行
    - "0 0 0 1 * *" - 每月1号执行
    """
    try:
        success = await create_cron_task(
            task_id=request.task_id,
            name=request.name,
            description=request.description,
            cron_expression=request.cron_expression,
            target_function=request.target_function,
            function_params=request.function_params,
            enabled=request.enabled
        )
        
        if success:
            return PublicResponse.success(
                data={"task_id": request.task_id},
                message="Cron 定时任务创建成功"
            )
        else:
            return PublicResponse.error(message="Cron 定时任务创建失败")
            
    except Exception as e:
        logger.error(f"创建 Cron 定时任务失败: {e}")
        return PublicResponse.error(message=f"创建失败: {str(e)}")


@router.post("/tasks/interval", summary="创建间隔定时任务")
async def create_interval_task_api(request: IntervalTaskRequest):
    """创建基于固定间隔的定时任务
    
    间隔时间以秒为单位：
    - 60 - 每分钟执行
    - 1800 - 每30分钟执行
    - 3600 - 每小时执行
    - 86400 - 每天执行
    """
    try:
        success = await create_interval_task(
            task_id=request.task_id,
            name=request.name,
            description=request.description,
            interval_seconds=request.interval_seconds,
            target_function=request.target_function,
            function_params=request.function_params,
            enabled=request.enabled
        )
        
        if success:
            return PublicResponse.success(
                data={"task_id": request.task_id},
                message="间隔定时任务创建成功"
            )
        else:
            return PublicResponse.error(message="间隔定时任务创建失败")
            
    except Exception as e:
        logger.error(f"创建间隔定时任务失败: {e}")
        return PublicResponse.error(message=f"创建失败: {str(e)}")


@router.get("/tasks", summary="获取所有任务配置")
async def get_tasks():
    """获取所有任务配置列表"""
    try:
        tasks = scheduler_client.get_task_configs()
        return PublicResponse.success(
            data=tasks,
            message=f"获取到 {len(tasks)} 个任务配置"
        )
    except Exception as e:
        logger.error(f"获取任务配置失败: {e}")
        return PublicResponse.error(message=f"获取失败: {str(e)}")


@router.get("/tasks/{task_id}/results", summary="获取任务执行结果")
async def get_task_results(
    task_id: str,
    limit: int = Query(100, description="返回结果数量限制")
):
    """获取指定任务的执行结果"""
    try:
        results = scheduler_client.get_task_results(task_id=task_id, limit=limit)
        return PublicResponse.success(
            data=results,
            message=f"获取到 {len(results)} 条执行结果"
        )
    except Exception as e:
        logger.error(f"获取任务执行结果失败: {e}")
        return PublicResponse.error(message=f"获取失败: {str(e)}")


@router.get("/results", summary="获取所有任务执行结果")
async def get_all_results(
    limit: int = Query(100, description="返回结果数量限制")
):
    """获取所有任务的执行结果"""
    try:
        results = scheduler_client.get_task_results(limit=limit)
        return PublicResponse.success(
            data=results,
            message=f"获取到 {len(results)} 条执行结果"
        )
    except Exception as e:
        logger.error(f"获取任务执行结果失败: {e}")
        return PublicResponse.error(message=f"获取失败: {str(e)}")


@router.post("/tasks/enable", summary="启用任务")
async def enable_task(request: TaskToggleRequest):
    """启用指定任务"""
    try:
        success = await scheduler_client.enable_task(request.task_id)
        if success:
            return PublicResponse.success(
                data={"task_id": request.task_id},
                message="任务启用成功"
            )
        else:
            return PublicResponse.error(message="任务启用失败")
    except Exception as e:
        logger.error(f"启用任务失败: {e}")
        return PublicResponse.error(message=f"启用失败: {str(e)}")


@router.post("/tasks/disable", summary="禁用任务")
async def disable_task(request: TaskToggleRequest):
    """禁用指定任务"""
    try:
        success = await scheduler_client.disable_task(request.task_id)
        if success:
            return PublicResponse.success(
                data={"task_id": request.task_id},
                message="任务禁用成功"
            )
        else:
            return PublicResponse.error(message="任务禁用失败")
    except Exception as e:
        logger.error(f"禁用任务失败: {e}")
        return PublicResponse.error(message=f"禁用失败: {str(e)}")


@router.put("/tasks/{task_id}", summary="更新任务")
async def update_task(task_id: str, request: Union[CronTaskRequest, IntervalTaskRequest]):
    """更新指定任务"""
    try:
        # 先删除原任务
        await scheduler_client.remove_task(task_id)
        
        # 根据请求类型创建新任务
        if hasattr(request, 'cron_expression'):
            # Cron任务
            success = await create_cron_task(
                task_id=task_id,
                name=request.name,
                description=request.description,
                cron_expression=request.cron_expression,
                target_function=request.target_function,
                function_params=request.function_params,
                enabled=request.enabled
            )
        else:
            # 间隔任务
            success = await create_interval_task(
                task_id=task_id,
                name=request.name,
                description=request.description,
                interval_seconds=request.interval_seconds,
                target_function=request.target_function,
                function_params=request.function_params,
                enabled=request.enabled
            )
        
        if success:
            return PublicResponse.success(
                data={"task_id": task_id},
                message="任务更新成功"
            )
        else:
            return PublicResponse.error(message="任务更新失败")
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        return PublicResponse.error(message=f"更新失败: {str(e)}")


@router.delete("/tasks/{task_id}", summary="删除任务")
async def delete_task(task_id: str):
    """删除指定任务"""
    try:
        success = await scheduler_client.remove_task(task_id)
        if success:
            return PublicResponse.success(
                data={"task_id": task_id},
                message="任务删除成功"
            )
        else:
            return PublicResponse.error(message="任务删除失败")
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return PublicResponse.error(message=f"删除失败: {str(e)}")


@router.get("/status", summary="获取调度器状态")
async def get_scheduler_status():
    """获取调度器运行状态"""
    try:
        is_running = scheduler_client.scheduler.running
        task_count = len(scheduler_client.task_configs)
        enabled_count = sum(1 for config in scheduler_client.task_configs.values() if config.enabled)
        
        # 获取最近的执行统计
        recent_results = scheduler_client.get_task_results(limit=50)
        success_count = sum(1 for result in recent_results if result.get('status') == 'success')
        failed_count = sum(1 for result in recent_results if result.get('status') == 'failed')
        
        status_data = {
            "is_running": is_running,
            "total_tasks": task_count,
            "enabled_tasks": enabled_count,
            "disabled_tasks": task_count - enabled_count,
            "recent_executions": {
                "total": len(recent_results),
                "success": success_count,
                "failed": failed_count
            }
        }
        
        return PublicResponse.success(
            data=status_data,
            message="调度器状态获取成功"
        )
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        return PublicResponse.error(message=f"获取失败: {str(e)}")


@router.post("/start", summary="启动调度器")
async def start_scheduler():
    """启动定时任务调度器"""
    try:
        if scheduler_client.scheduler.running:
            return PublicResponse.success(message="调度器已在运行中")
        
        await scheduler_client.start()
        return PublicResponse.success(message="调度器启动成功")
    except Exception as e:
        logger.error(f"启动调度器失败: {e}")
        return PublicResponse.error(message=f"启动失败: {str(e)}")


@router.post("/stop", summary="停止调度器")
async def stop_scheduler():
    """停止定时任务调度器"""
    try:
        if not scheduler_client.scheduler.running:
            return PublicResponse.success(message="调度器已停止")
        
        await scheduler_client.stop()
        return PublicResponse.success(message="调度器停止成功")
    except Exception as e:
        logger.error(f"停止调度器失败: {e}")
        return PublicResponse.error(message=f"停止失败: {str(e)}")


# 预定义任务模板
@router.get("/templates", summary="获取任务模板")
async def get_task_templates():
    """获取预定义的任务模板"""
    templates = [
        {
            "name": "直播间数据监控",
            "description": "定时获取直播间核心数据",
            "target_function": "get_core_data",
            "function_params": {
                "user_id": "请填写用户ID",
                "room_id": "请填写直播间ID"
            },
            "cron_examples": {
                "每30分钟": "0 */30 * * * *",
                "每小时": "0 0 * * * *",
                "每天8点": "0 0 8 * * *",
                "工作日9点": "0 0 9 * * 1-5"
            },
            "interval_examples": {
                "每30分钟": 1800,
                "每小时": 3600,
                "每2小时": 7200,
                "每天": 86400
            }
        },
        {
            "name": "历史直播列表监控",
            "description": "定时获取用户历史直播列表",
            "target_function": "get_history_live_list",
            "function_params": {
                "user_id": "请填写用户ID"
            },
            "cron_examples": {
                "每小时": "0 0 * * * *",
                "每天8点": "0 0 8 * * *",
                "每周一8点": "0 0 8 * * 1"
            },
            "interval_examples": {
                "每小时": 3600,
                "每2小时": 7200,
                "每天": 86400
            }
        },
        {
            "name": "批量数据获取",
            "description": "批量获取多个直播间的核心数据",
            "target_function": "get_core_data_main",
            "function_params": {
                "data": [
                    {
                        "user_id": "请填写用户ID",
                        "room_id": "请填写直播间ID",
                        "user_name": "请填写用户名",
                        "buyin_account_id": "请填写账户ID"
                    }
                ]
            },
            "cron_examples": {
                "每小时": "0 0 * * * *",
                "每天8点": "0 0 8 * * *"
            },
            "interval_examples": {
                "每小时": 3600,
                "每天": 86400
            }
        }
    ]
    
    return PublicResponse.success(
        data=templates,
        message="任务模板获取成功"
    )