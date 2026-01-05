#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 消息协议定义

统一定义 WebSocket 通信的事件类型和消息格式，
确保前后端消息结构一致。
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class EventType(str, Enum):
    """事件类型枚举"""

    # 连接事件
    CONNECTED = "connected"
    PONG = "pong"

    # 浏览器生命周期事件
    BROWSER_ADDED = "browser_added"  # 新建浏览器
    BROWSER_STARTING = "browser_starting"
    BROWSER_STARTED = "browser_started"
    BROWSER_STOPPING = "browser_stopping"
    BROWSER_STOPPED = "browser_stopped"
    BROWSER_DELETED = "browser_deleted"
    BROWSER_ERROR = "browser_error"

    # 批量操作事件
    BATCH_STARTED = "batch_started"
    BATCH_PROGRESS = "batch_progress"
    BATCH_COMPLETED = "batch_completed"

    # 系统事件
    SYSTEM_STATUS_CHANGED = "system_status_changed"


class BrowserStatus(str, Enum):
    """浏览器状态枚举"""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DELETED = "deleted"


class WSMessage(BaseModel):
    """标准 WebSocket 消息格式"""

    event: str  # 使用 str 以便序列化
    channel: str = "browser"
    timestamp: Optional[str] = None
    data: Dict[str, Any] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于 JSON 序列化"""
        return {
            "event": self.event,
            "channel": self.channel,
            "timestamp": self.timestamp,
            "data": self.data,
        }


class BrowserEventData(BaseModel):
    """浏览器事件数据"""

    user_id: str
    status: str
    port: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class BatchEventData(BaseModel):
    """批量操作事件数据"""

    operation: str  # start / stop
    total: int
    completed: int = 0
    success: int = 0
    failed: int = 0
    current_user_id: Optional[str] = None
    results: Optional[list] = None


def create_browser_event(
    event_type: EventType,
    user_id: str,
    status: BrowserStatus,
    port: int = None,
    message: str = None,
    error: str = None,
) -> Dict[str, Any]:
    """
    创建浏览器事件消息

    Args:
        event_type: 事件类型
        user_id: 用户ID
        status: 浏览器状态
        port: 端口号
        message: 附加消息
        error: 错误信息

    Returns:
        可直接用于广播的字典
    """
    data = BrowserEventData(
        user_id=user_id,
        status=status.value if isinstance(status, BrowserStatus) else status,
        port=port,
        message=message,
        error=error,
    )

    msg = WSMessage(
        event=event_type.value if isinstance(event_type, EventType) else event_type,
        channel="browser",
        data=data.model_dump(exclude_none=True),
    )

    return msg.to_dict()


def create_batch_event(
    event_type: EventType,
    operation: str,
    total: int,
    completed: int = 0,
    success: int = 0,
    failed: int = 0,
    current_user_id: str = None,
    results: list = None,
) -> Dict[str, Any]:
    """
    创建批量操作事件消息

    Args:
        event_type: 事件类型 (BATCH_STARTED/BATCH_PROGRESS/BATCH_COMPLETED)
        operation: 操作类型 (start/stop)
        total: 总数
        completed: 已完成数
        success: 成功数
        failed: 失败数
        current_user_id: 当前正在处理的用户ID
        results: 最终结果列表

    Returns:
        可直接用于广播的字典
    """
    data = BatchEventData(
        operation=operation,
        total=total,
        completed=completed,
        success=success,
        failed=failed,
        current_user_id=current_user_id,
        results=results,
    )

    msg = WSMessage(
        event=event_type.value if isinstance(event_type, EventType) else event_type,
        channel="browser",
        data=data.model_dump(exclude_none=True),
    )

    return msg.to_dict()
