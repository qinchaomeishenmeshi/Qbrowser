import asyncio
from typing import Optional, List

from browser.browser_manager import BrowserManager


class BrowserManagerStore:
    def __init__(self):
        self._managers: List[BrowserManager] = []
        self._lock = asyncio.Lock()

    async def add(self, manager: BrowserManager):
        async with self._lock:
            existing_manager = await self.get(manager.user_id)
            if existing_manager:
                if existing_manager.is_running:
                    return existing_manager  # 如果已存在且运行中，直接返回
                else:
                    # 如果存在但没有运行，先清理
                    await self.remove(manager.user_id)
            self._managers.append(manager)
            return manager

    async def remove(self, user_id: str) -> bool:
        async with self._lock:
            for i, m in enumerate(self._managers):
                if m.user_id == user_id:
                    if m.is_running:
                        await asyncio.to_thread(m.cleanup)
                    self._managers.pop(i)
                    return True
            return False

    async def get(self, user_id: str) -> Optional[BrowserManager]:
        async with self._lock:
            for m in self._managers:
                if m.user_id == user_id:
                    return m
            return None

    async def clear(self):
        async with self._lock:
            for m in self._managers:
                if m.is_running:
                    await asyncio.to_thread(m.cleanup)
            self._managers.clear()

    async def count(self):
        async with self._lock:
            return len(self._managers)

    async def get_all(self) -> List[BrowserManager]:
        async with self._lock:
            return list(self._managers)


# 单例
browser_store = BrowserManagerStore()
