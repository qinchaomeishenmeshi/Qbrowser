import asyncio
from typing import Optional, List
from browser.playwright_manager import PlaywrightManager


class BrowserManagerStore:
    """浏览器管理器存储类

    负责管理多个浏览器实例的存储、检索和生命周期管理。
    提供线程安全的异步操作接口。
    """

    def __init__(self) -> None:
        """初始化浏览器管理器存储"""
        self._managers: List[PlaywrightManager] = []
        self._lock = asyncio.Lock()

    async def add(self, manager: PlaywrightManager) -> None:
        """添加浏览器管理器实例

        Args:
            manager: 要添加的浏览器管理器实例

        Note:
            如果已存在相同user_id的实例，将忽略此次添加操作
        """
        async with self._lock:
            # 避免重复 user_id
            if not any(m.user_id == manager.user_id for m in self._managers):
                self._managers.append(manager)
            else:
                # 如果已存在同 user_id，可选择覆盖或忽略，这里忽略
                pass

    async def remove(self, user_id: str) -> bool:
        """移除指定用户的浏览器管理器实例

        Args:
            user_id: 要移除的用户ID

        Returns:
            如果成功移除返回True，如果用户不存在返回False

        Note:
            如果浏览器正在运行，会先执行清理操作
        """
        async with self._lock:
            for i, m in enumerate(self._managers):
                if m.user_id == user_id:
                    if m.is_running:
                        await m.cleanup()
                    self._managers.pop(i)
                    return True
            return False

    async def get(self, user_id: str) -> Optional[PlaywrightManager]:
        """获取指定用户的浏览器管理器实例

        Args:
            user_id: 用户ID

        Returns:
            浏览器管理器实例，如果不存在则返回None
        """
        async with self._lock:
            for m in self._managers:
                if m.user_id == user_id:
                    return m
            return None

    async def clear(self) -> None:
        """清除所有浏览器管理器实例

        对所有正在运行的浏览器执行清理操作，然后清空存储。
        """
        async with self._lock:
            for m in self._managers:
                if m.is_running:
                    await m.cleanup()
            self._managers.clear()

    async def count(self) -> int:
        """获取当前存储的浏览器管理器实例数量

        Returns:
            浏览器管理器实例的数量
        """
        async with self._lock:
            return len(self._managers)

    async def get_all(self) -> List[PlaywrightManager]:
        """获取所有浏览器管理器实例

        Returns:
            浏览器管理器实例列表的副本
        """
        async with self._lock:
            return list(self._managers)


# 单例
browser_store = BrowserManagerStore()
