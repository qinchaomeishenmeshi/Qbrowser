#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务调度器 - 用于定时获取直播间相关数据

功能特性：
1. 支持 cron 表达式和固定间隔的定时任务
2. 异步任务执行，支持并发处理
3. 任务状态监控和日志记录
4. 数据持久化存储
5. 任务配置的动态管理
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from utils.common_logger import get_logger
from worker.living_client import LivingClient
from conf import resource_path

logger = get_logger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    SUCCESS = "success"      # 执行成功
    FAILED = "failed"        # 执行失败
    DISABLED = "disabled"    # 已禁用


class TriggerType(Enum):
    """触发器类型枚举"""
    CRON = "cron"           # cron 表达式
    INTERVAL = "interval"   # 固定间隔


@dataclass
class TaskConfig:
    """任务配置数据类"""
    task_id: str                    # 任务唯一标识
    name: str                       # 任务名称
    description: str                # 任务描述
    trigger_type: TriggerType       # 触发器类型
    trigger_config: Dict[str, Any]  # 触发器配置
    target_function: str            # 目标函数名
    function_params: Dict[str, Any] # 函数参数
    enabled: bool = True            # 是否启用
    max_instances: int = 1          # 最大并发实例数
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


@dataclass
class TaskResult:
    """任务执行结果数据类"""
    task_id: str
    execution_id: str
    status: TaskStatus
    start_time: str
    end_time: Optional[str] = None
    duration: Optional[float] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class SchedulerClient:
    """定时任务调度器客户端"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = "data/scheduler"
        self.data_dir = Path(resource_path(data_dir))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.data_dir / "task_configs.json"
        self.results_file = self.data_dir / "task_results.json"
        
        self.scheduler = AsyncIOScheduler()
        self.living_client = LivingClient()
        self.task_configs: Dict[str, TaskConfig] = {}
        self.task_results: List[TaskResult] = []
        
        # 注册事件监听器
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        
        # 加载配置
        self._load_configs()
        self._load_results()
    
    async def start(self):
        """启动调度器"""
        try:
            self.scheduler.start()
            logger.info("定时任务调度器已启动")
            
            # 重新添加所有启用的任务
            for task_config in self.task_configs.values():
                if task_config.enabled:
                    await self._add_job(task_config)
                    
        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            raise
    
    async def stop(self):
        """停止调度器"""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("定时任务调度器已停止")
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
    
    async def add_task(self, task_config: TaskConfig) -> bool:
        """添加新任务"""
        try:
            # 验证任务配置
            if not self._validate_task_config(task_config):
                return False
            
            # 保存配置
            self.task_configs[task_config.task_id] = task_config
            self._save_configs()
            
            # 如果调度器已启动且任务启用，则添加到调度器
            if self.scheduler.running and task_config.enabled:
                await self._add_job(task_config)
            
            logger.info(f"任务 {task_config.name} ({task_config.task_id}) 添加成功")
            return True
            
        except Exception as e:
            logger.error(f"添加任务失败: {e}")
            return False
    
    async def remove_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            if task_id not in self.task_configs:
                logger.warning(f"任务 {task_id} 不存在")
                return False
            
            # 从调度器中移除
            if self.scheduler.running:
                try:
                    self.scheduler.remove_job(task_id)
                except Exception:
                    pass  # 任务可能不在调度器中
            
            # 从配置中删除
            del self.task_configs[task_id]
            self._save_configs()
            
            logger.info(f"任务 {task_id} 删除成功")
            return True
            
        except Exception as e:
            logger.error(f"删除任务失败: {e}")
            return False
    
    async def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        return await self._toggle_task(task_id, True)
    
    async def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        return await self._toggle_task(task_id, False)
    
    async def _toggle_task(self, task_id: str, enabled: bool) -> bool:
        """切换任务启用状态"""
        try:
            if task_id not in self.task_configs:
                logger.warning(f"任务 {task_id} 不存在")
                return False
            
            task_config = self.task_configs[task_id]
            task_config.enabled = enabled
            task_config.updated_at = datetime.now().isoformat()
            
            if self.scheduler.running:
                if enabled:
                    await self._add_job(task_config)
                else:
                    try:
                        self.scheduler.remove_job(task_id)
                    except Exception:
                        pass
            
            self._save_configs()
            
            status = "启用" if enabled else "禁用"
            logger.info(f"任务 {task_id} {status}成功")
            return True
            
        except Exception as e:
            logger.error(f"切换任务状态失败: {e}")
            return False
    
    def get_task_configs(self) -> List[Dict[str, Any]]:
        """获取所有任务配置"""
        return [asdict(config) for config in self.task_configs.values()]
    
    def get_task_results(self, task_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务执行结果"""
        results = self.task_results
        
        if task_id:
            results = [r for r in results if r.task_id == task_id]
        
        # 按时间倒序排列，取最新的 limit 条
        results = sorted(results, key=lambda x: x.start_time, reverse=True)[:limit]
        
        return [asdict(result) for result in results]
    
    async def _add_job(self, task_config: TaskConfig):
        """添加任务到调度器"""
        try:
            # 移除已存在的任务
            try:
                self.scheduler.remove_job(task_config.task_id)
            except Exception:
                pass
            
            # 创建触发器
            trigger = self._create_trigger(task_config)
            if not trigger:
                logger.error(f"创建触发器失败: {task_config.task_id}")
                return
            
            # 添加任务
            self.scheduler.add_job(
                func=self._execute_task,
                trigger=trigger,
                id=task_config.task_id,
                name=task_config.name,
                max_instances=task_config.max_instances,
                args=[task_config]
            )
            
            logger.info(f"任务 {task_config.name} 已添加到调度器")
            
        except Exception as e:
            logger.error(f"添加任务到调度器失败: {e}")
    
    def _create_trigger(self, task_config: TaskConfig):
        """创建触发器"""
        try:
            if task_config.trigger_type == TriggerType.CRON:
                return CronTrigger(**task_config.trigger_config)
            elif task_config.trigger_type == TriggerType.INTERVAL:
                return IntervalTrigger(**task_config.trigger_config)
            else:
                logger.error(f"不支持的触发器类型: {task_config.trigger_type}")
                return None
        except Exception as e:
            logger.error(f"创建触发器失败: {e}")
            return None
    
    async def _execute_task(self, task_config: TaskConfig):
        """执行任务"""
        execution_id = f"{task_config.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        task_result = TaskResult(
            task_id=task_config.task_id,
            execution_id=execution_id,
            status=TaskStatus.RUNNING,
            start_time=start_time.isoformat()
        )
        
        try:
            logger.info(f"开始执行任务: {task_config.name} ({execution_id})")
            
            # 根据目标函数执行相应的方法
            result_data = await self._call_target_function(
                task_config.target_function,
                task_config.function_params
            )
            
            # 更新结果
            end_time = datetime.now()
            task_result.status = TaskStatus.SUCCESS
            task_result.end_time = end_time.isoformat()
            task_result.duration = (end_time - start_time).total_seconds()
            task_result.result_data = result_data
            
            logger.info(f"任务执行成功: {task_config.name} ({execution_id})")
            
        except Exception as e:
            end_time = datetime.now()
            task_result.status = TaskStatus.FAILED
            task_result.end_time = end_time.isoformat()
            task_result.duration = (end_time - start_time).total_seconds()
            task_result.error_message = str(e)
            
            logger.error(f"任务执行失败: {task_config.name} ({execution_id}) - {e}")
        
        finally:
            # 保存执行结果
            self.task_results.append(task_result)
            self._save_results()
    
    async def _call_target_function(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用目标函数 - 通过 HTTP API 接口"""
        
        # 创建本地 API 客户端
        api_client = LocalApiClient()
        
        if function_name == "get_core_data_main":
            # 调用直播间核心数据接口
            data = params.get("data", {})
            return await api_client.post("/live/live_screen/core_data", data)
        
        elif function_name == "get_history_live_main":
            # 调用历史直播数据接口
            return await api_client.post("/live/data", params)
        
        else:
            raise ValueError(f"不支持的目标函数: {function_name}")
    
    def _validate_task_config(self, task_config: TaskConfig) -> bool:
        """验证任务配置"""
        if not task_config.task_id or not task_config.name:
            logger.error("任务ID和名称不能为空")
            return False
        
        if task_config.task_id in self.task_configs:
            logger.error(f"任务ID {task_config.task_id} 已存在")
            return False
        
        if not task_config.trigger_config:
            logger.error("触发器配置不能为空")
            return False
        
        if task_config.target_function not in [ "get_core_data_main", "get_history_live_main"]:
            logger.error(f"不支持的目标函数: {task_config.target_function}")
            return False
        
        return True
    
    def _job_executed(self, event):
        """任务执行完成事件处理"""
        logger.debug(f"任务执行完成: {event.job_id}")
    
    def _job_error(self, event):
        """任务执行错误事件处理"""
        logger.error(f"任务执行错误: {event.job_id} - {event.exception}")
    
    def _load_configs(self):
        """加载任务配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for config_dict in data:
                        config_dict['trigger_type'] = TriggerType(config_dict['trigger_type'])
                        task_config = TaskConfig(**config_dict)
                        self.task_configs[task_config.task_id] = task_config
                logger.info(f"加载了 {len(self.task_configs)} 个任务配置")
        except Exception as e:
            logger.error(f"加载任务配置失败: {e}")
    
    def _save_configs(self):
        """保存任务配置"""
        try:
            data = []
            for config in self.task_configs.values():
                config_dict = asdict(config)
                config_dict['trigger_type'] = config.trigger_type.value
                data.append(config_dict)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务配置失败: {e}")
    
    def _load_results(self):
        """加载任务结果"""
        try:
            if self.results_file.exists():
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for result_dict in data:
                        result_dict['status'] = TaskStatus(result_dict['status'])
                        task_result = TaskResult(**result_dict)
                        self.task_results.append(task_result)
                logger.info(f"加载了 {len(self.task_results)} 个任务结果")
        except Exception as e:
            logger.error(f"加载任务结果失败: {e}")
    
    def _save_results(self):
        """保存任务结果（只保留最近1000条）"""
        try:
            # 只保留最近的1000条结果
            recent_results = sorted(self.task_results, key=lambda x: x.start_time, reverse=True)[:1000]
            self.task_results = recent_results
            
            data = []
            for result in self.task_results:
                result_dict = asdict(result)
                result_dict['status'] = result.status.value
                data.append(result_dict)
            
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务结果失败: {e}")


# 全局调度器实例
scheduler_client = SchedulerClient()


class LocalApiClient:
    """本地 API 客户端，用于调用本地业务接口"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:6001", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.default_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Scheduler-Client/1.0'
        }
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发起 POST 请求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.info(f"调用本地API: {url}")
                logger.debug(f"请求数据: {data}")
                
                async with session.post(
                    url=url,
                    json=data,
                    headers=self.default_headers
                ) as response:
                    response_text = await response.text()
                    logger.info(f"API响应状态: {response.status}")
                    logger.debug(f"API响应内容: {response_text}")
                    
                    # 解析响应
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError:
                        logger.error(f"API响应解析失败: {response_text}")
                        return {
                            "status": "failed",
                            "message": f"响应解析失败: {response_text[:200]}...",
                            "data": None
                        }
                    
                    # 检查HTTP状态码
                    if response.status >= 400:
                        logger.error(f"API调用失败 {response.status}: {response_text}")
                        return {
                            "status": "failed",
                            "message": f"HTTP错误: {response.status}",
                            "data": result
                        }
                    
                    # 转换响应格式以兼容原有逻辑
                    if result.get("code") == 200 and result.get("status") == "success":
                        return {
                            "status": "success",
                            "message": "执行成功",
                            "data": result.get("data")
                        }
                    else:
                        return {
                            "status": "failed",
                            "message": result.get("message", "未知错误"),
                            "data": result.get("data")
                        }
                        

        except Exception as e:
            logger.error(f"API调用未知错误: {e}", exc_info=True)
            return {
                "status": "failed",
                "message": f"未知错误: {str(e)}",
                "data": None
            }
    


# 便捷函数
async def create_cron_task(
    task_id: str,
    name: str,
    description: str,
    cron_expression: str,
    target_function: str,
    function_params: Dict[str, Any],
    enabled: bool = True
) -> bool:
    """创建 cron 定时任务
    
    Args:
        task_id: 任务唯一标识
        name: 任务名称
        description: 任务描述
        cron_expression: cron 表达式，如 "0 */30 * * * *" (每30分钟)
        target_function: 目标函数名 (get_core_data, get_history_live_list, get_core_data_main)
        function_params: 函数参数
        enabled: 是否启用
    
    Returns:
        bool: 创建是否成功
    """
    # 解析 cron 表达式
    parts = cron_expression.split()
    if len(parts) == 6:
        second, minute, hour, day, month, day_of_week = parts
    elif len(parts) == 5:
        minute, hour, day, month, day_of_week = parts
        second = "0"
    else:
        raise ValueError("cron 表达式格式错误")
    
    trigger_config = {
        "second": second,
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": day_of_week
    }
    
    task_config = TaskConfig(
        task_id=task_id,
        name=name,
        description=description,
        trigger_type=TriggerType.CRON,
        trigger_config=trigger_config,
        target_function=target_function,
        function_params=function_params,
        enabled=enabled
    )
    
    return await scheduler_client.add_task(task_config)


async def create_interval_task(
    task_id: str,
    name: str,
    description: str,
    interval_seconds: int,
    target_function: str,
    function_params: Dict[str, Any],
    enabled: bool = True
) -> bool:
    """创建固定间隔定时任务
    
    Args:
        task_id: 任务唯一标识
        name: 任务名称
        description: 任务描述
        interval_seconds: 间隔秒数
        target_function: 目标函数名
        function_params: 函数参数
        enabled: 是否启用
    
    Returns:
        bool: 创建是否成功
    """
    trigger_config = {
        "seconds": interval_seconds
    }
    
    task_config = TaskConfig(
        task_id=task_id,
        name=name,
        description=description,
        trigger_type=TriggerType.INTERVAL,
        trigger_config=trigger_config,
        target_function=target_function,
        function_params=function_params,
        enabled=enabled
    )
    
    return await scheduler_client.add_task(task_config)


if __name__ == "__main__":
    async def main():
        """测试示例"""
        try:
            # 启动调度器
            await scheduler_client.start()
            
            # 创建测试任务 - 每30分钟获取直播间数据
            await create_cron_task(
                task_id="live_data_monitor",
                name="直播间数据监控",
                description="每30分钟获取指定直播间的核心数据",
                cron_expression="0 */30 * * * *",  # 每30分钟执行
                target_function="get_core_data",
                function_params={
                    "user_id": "001",
                    "room_id": "7512002735768865571"
                }
            )
            
            # 创建测试任务 - 每小时获取历史直播列表
            await create_interval_task(
                task_id="history_live_monitor",
                name="历史直播监控",
                description="每小时获取用户的历史直播列表",
                interval_seconds=3600,  # 1小时
                target_function="get_history_live_list",
                function_params={
                    "user_id": "001"
                }
            )
            
            logger.info("定时任务已创建，调度器运行中...")
            
            # 保持运行
            while True:
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        finally:
            await scheduler_client.stop()
    
    asyncio.run(main())