#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 连接管理器

提供 WebSocket 连接池管理和消息广播功能，用于：
1. 任务调度状态实时推送
2. 浏览器实例状态变更通知
3. 系统事件广播
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from utils.common_logger import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 活跃连接池，按频道分组
        self.active_connections: Dict[str, List[WebSocket]] = {
            "scheduler": [],  # 调度器状态频道
            "browser": [],  # 浏览器状态频道
            "system": [],  # 系统事件频道
        }
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str = "scheduler"):
        """
        接受新的 WebSocket 连接

        Args:
            websocket: WebSocket 连接对象
            channel: 订阅频道 (scheduler/browser/system)
        """
        await websocket.accept()
        async with self._lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = []
            self.active_connections[channel].append(websocket)

        logger.info(
            f"WebSocket 连接已建立 [频道: {channel}]，当前连接数: {len(self.active_connections[channel])}"
        )

        # 发送连接成功消息
        await self.send_personal(
            websocket,
            {
                "event": "connected",
                "channel": channel,
                "timestamp": datetime.now().isoformat(),
                "message": f"已订阅 {channel} 频道",
            },
        )

    async def disconnect(self, websocket: WebSocket, channel: str = "scheduler"):
        """
        断开 WebSocket 连接

        Args:
            websocket: WebSocket 连接对象
            channel: 订阅频道
        """
        async with self._lock:
            if (
                channel in self.active_connections
                and websocket in self.active_connections[channel]
            ):
                self.active_connections[channel].remove(websocket)
                logger.info(
                    f"WebSocket 连接已断开 [频道: {channel}]，剩余连接数: {len(self.active_connections[channel])}"
                )

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        发送消息到单个连接

        Args:
            websocket: 目标 WebSocket 连接
            message: 消息内容
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"发送 WebSocket 消息失败: {e}")

    async def broadcast(self, message: Dict[str, Any], channel: str = "scheduler"):
        """
        广播消息到指定频道的所有连接

        Args:
            message: 消息内容
            channel: 目标频道
        """
        if channel not in self.active_connections:
            return

        # 添加时间戳
        message["timestamp"] = datetime.now().isoformat()

        disconnected = []
        async with self._lock:
            connections = self.active_connections[channel].copy()

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"广播消息失败，标记连接为断开: {e}")
                disconnected.append(websocket)

        # 清理断开的连接
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    if ws in self.active_connections[channel]:
                        self.active_connections[channel].remove(ws)

    async def broadcast_all(self, message: Dict[str, Any]):
        """
        广播消息到所有频道的所有连接

        Args:
            message: 消息内容
        """
        for channel in self.active_connections:
            await self.broadcast(message, channel)

    def get_connection_count(self, channel: str = None) -> int:
        """
        获取连接数量

        Args:
            channel: 指定频道，None 表示所有频道

        Returns:
            连接数量
        """
        if channel:
            return len(self.active_connections.get(channel, []))
        return sum(len(conns) for conns in self.active_connections.values())

    def get_status(self) -> Dict[str, Any]:
        """获取 WebSocket 管理器状态"""
        return {
            "channels": {
                channel: len(conns)
                for channel, conns in self.active_connections.items()
            },
            "total_connections": self.get_connection_count(),
        }


# 全局单例
ws_manager = WebSocketManager()


# 便捷函数
async def broadcast_task_event(
    event_type: str,
    task_id: str,
    status: str = None,
    duration: float = None,
    error: str = None,
    data: Dict[str, Any] = None,
):
    """
    广播任务事件

    Args:
        event_type: 事件类型 (task_started/task_completed/task_failed/task_created/task_deleted)
        task_id: 任务 ID
        status: 任务状态
        duration: 执行时长（秒）
        error: 错误信息
        data: 附加数据
    """
    message = {
        "event": event_type,
        "task_id": task_id,
    }

    if status:
        message["status"] = status
    if duration is not None:
        message["duration"] = round(duration, 2)
    if error:
        message["error"] = error
    if data:
        message["data"] = data

    await ws_manager.broadcast(message, "scheduler")


async def broadcast_browser_event(
    event_type: str, user_id: str, status: str = None, data: Dict[str, Any] = None
):
    """
    广播浏览器事件

    Args:
        event_type: 事件类型 (browser_started/browser_stopped/browser_error)
        user_id: 用户 ID
        status: 浏览器状态
        data: 附加数据
    """
    message = {
        "event": event_type,
        "user_id": user_id,
    }

    if status:
        message["status"] = status
    if data:
        message["data"] = data

    await ws_manager.broadcast(message, "browser")
