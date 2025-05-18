import asyncio
import json
import os
from typing import List, Dict

from browser.browser_manager import BrowserManager
from browser.browser_store import browser_store
from conf import CACHE_FILE, PORTS_FILE
from utils.common_logger import get_logger
from utils.port_manager import PortManager

logger = get_logger(__name__)


class BrowserService:
    def __init__(self):
        self.browser_store = browser_store  # 全局单例
        self.port_manager = PortManager()  # 使用新的端口管理器

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

            try:
                port = await self.port_manager.allocate_port()
                manager = BrowserManager(user_id, port)
                ok = await asyncio.to_thread(manager.initialize)
                if ok:
                    await self.browser_store.add(manager)
                    results.append(
                        {
                            "user_id": user_id,
                            "status": "started",
                            "port": port,
                        }
                    )
                else:
                    await self.port_manager.release_port(port)
                    results.append(
                        {
                            "user_id": user_id,
                            "status": "failed",
                            "port": None,
                        }
                    )
            except Exception as e:
                logger.error(f"启动浏览器失败 {user_id}: {e}")
                results.append(
                    {
                        "user_id": user_id,
                        "status": "error",
                        "port": None,
                        "error": str(e),
                    }
                )

        await self.save_ports()
        return results

    async def stop_all_browsers(self):
        await self.browser_store.clear()
        await self.port_manager.clear_ports()
        await self.save_ports()

    async def save_ports(self):
        """
        保存端口映射到文件
        """
        managers = await self.browser_store.get_all()
        mapping = {m.user_id: {"port": m.port} for m in managers}
        try:
            with open(PORTS_FILE, "w", encoding="utf-8") as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
            logger.info(f"保存端口映射成功，共 {len(mapping)} 个实例")
        except Exception as e:
            logger.error(f"保存端口映射失败: {e}")

    async def load_ports(self):
        """
        从文件加载端口映射
        """
        if os.path.exists(PORTS_FILE):
            try:
                with open(PORTS_FILE, encoding="utf-8") as f:
                    mapping = json.load(f)
                ports = {v["port"] for v in mapping.values()}
                await self.port_manager.load_ports(ports)
                logger.info(f"加载端口映射成功: {mapping}")
            except Exception as e:
                logger.error(f"加载端口映射失败: {e}")

    def save_cache(self, user_ids: List[str]):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(user_ids, f, ensure_ascii=False, indent=2)
            logger.info(f"保存用户缓存成功，共 {len(user_ids)} 个用户")
        except Exception as e:
            logger.error(f"保存用户缓存失败: {e}")

    def load_cache(self) -> List[str]:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载用户缓存失败: {e}")
                return []
        return []

    def clear_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                os.remove(CACHE_FILE)
                logger.info("清除用户缓存成功")
            except Exception as e:
                logger.error(f"清除用户缓存失败: {e}")
        self.clear_ports()

    def clear_ports(self):
        if os.path.exists(PORTS_FILE):
            try:
                os.remove(PORTS_FILE)
                logger.info("清除端口映射文件成功")
            except Exception as e:
                logger.error(f"清除端口映射文件失败: {e}")
        asyncio.create_task(self.port_manager.clear_ports())

    async def get_or_create_browser(self, user_id: str) -> BrowserManager:
        """
        获取已存在的浏览器实例，否则新建并返回
        """
        manager = await self.browser_store.get(user_id)
        if manager and manager.is_running:
            return manager

        try:
            port = await self.port_manager.allocate_port()
            manager = BrowserManager(user_id, port)
            ok = await asyncio.to_thread(manager.initialize)
            if ok:
                await self.browser_store.add(manager)
                await self.save_ports()
                return manager
            else:
                await self.port_manager.release_port(port)
                raise RuntimeError(f"初始化浏览器失败: {user_id}")
        except Exception as e:
            logger.error(f"创建浏览器实例失败 {user_id}: {e}")
            raise


browser_service = BrowserService()
