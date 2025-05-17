import asyncio
import json
import os
from typing import List, Dict

from loguru import logger

from browser.browser_manager import BrowserManager
from browser.browser_store import browser_store
from conf import CACHE_FILE, PORTS_FILE


class BrowserService:
    def __init__(self):
        self.browser_store = browser_store  # 全局单例
        self.available_ports = list(range(9000, 10000))
        self.used_ports = set()
        # 注意：异步环境下不能直接await，所以需在外部调用load_ports
        # 推荐在FastAPI启动或App初始化时await browser_service.load_ports()

    def _allocate_port(self) -> int:
        for port in self.available_ports:
            if port not in self.used_ports:
                self.used_ports.add(port)
                return port
        raise RuntimeError("No available ports.")

    async def start_browsers(self, user_ids: List[str]) -> List[Dict]:
        results = []
        for idx, user_id in enumerate(user_ids, 1):
            manager = await self.browser_store.get(user_id)
            if manager and manager.is_running:
                results.append(
                    {
                        "user_id": user_id,
                        "status": "already_running",
                        "port": manager.port,
                    }
                )
                continue
            port = self._allocate_port()
            manager = BrowserManager(user_id, port)
            ok = await asyncio.to_thread(manager.initialize)
            await self.browser_store.add(manager)
            results.append(
                {
                    "user_id": user_id,
                    "status": "started" if ok else "failed",
                    "port": port,
                }
            )
        await self.save_ports()
        return results

    async def stop_all_browsers(self):
        await self.browser_store.clear()
        self.used_ports.clear()
        await self.save_ports()

    async def save_ports(self):
        managers = await self.browser_store.get_all()
        mapping = {m.user_id: {"port": m.port} for m in managers}
        with open(PORTS_FILE, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved ports mapping for {len(mapping)} instances.")

    async def load_ports(self):
        if os.path.exists(PORTS_FILE):
            try:
                mapping = json.load(open(PORTS_FILE, encoding="utf-8"))
                self.used_ports = {v["port"] for v in mapping.values()}
                logger.info(f"Loaded ports mapping: {mapping}")
            except Exception:
                logger.warning("Failed to load ports mapping.")

    def save_cache(self, user_ids: List[str]):
        json.dump(
            user_ids,
            open(CACHE_FILE, "w", encoding="utf-8"),
            ensure_ascii=False,
            indent=2,
        )

    def load_cache(self) -> List[str]:
        if os.path.exists(CACHE_FILE):
            try:
                return json.load(open(CACHE_FILE, encoding="utf-8"))
            except Exception:
                return []
        return []

    def clear_cache(self):
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        self.clear_ports()

    def clear_ports(self):
        if os.path.exists(PORTS_FILE):
            os.remove(PORTS_FILE)
        self.used_ports.clear()

    async def get_or_create_browser(self, user_id: str) -> BrowserManager:
        """
        获取已存在的浏览器实例，否则新建并返回。
        """
        manager = await self.browser_store.get(user_id)
        if manager and manager.is_running:
            return manager
        port = self._allocate_port()
        manager = BrowserManager(user_id, port)
        ok = await asyncio.to_thread(manager.initialize)
        if ok:
            await self.browser_store.add(manager)
            await self.save_ports()
            return manager
        else:
            raise RuntimeError(f"Failed to start browser for {user_id}")


browser_service = BrowserService()
