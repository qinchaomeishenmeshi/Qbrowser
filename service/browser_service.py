import asyncio
import os
from pathlib import Path
from typing import List, Dict, Optional, Any

from browser.playwright_manager import PlaywrightManager
from browser.browser_store import browser_store
from conf import DATA_DIR
from utils.common_logger import get_logger
from utils.cookies_manager import CookiesManager
from utils.port_manager import PortManager
from utils.database_manager import db_manager

logger = get_logger(__name__)


class BrowserService:
    """浏览器服务类

    负责管理多个浏览器实例的启动、停止、状态监控等功能。
    使用 SQLite 数据库持久化状态。
    """

    def __init__(self) -> None:
        """初始化浏览器服务"""
        self.browser_store = browser_store  # 全局单例
        self.port_manager = PortManager()  # 使用新的端口管理器
        self.cookies_manager = CookiesManager(Path(os.path.join(DATA_DIR, "cookies")))

    async def start_browsers(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """批量启动浏览器实例"""
        results = []
        for idx, user_id in enumerate(user_ids, 1):
            try:
                manager = await self.get_or_create_browser(user_id)

                if manager and manager.is_running:
                    existing_manager = await self.browser_store.get(user_id)
                    if existing_manager and existing_manager.is_running:
                        results.append(
                            {
                                "user_id": user_id,
                                "status": "already_running",
                                "port": manager.port,
                            }
                        )
                    else:
                        results.append(
                            {
                                "user_id": user_id,
                                "status": "started",
                                "port": manager.port,
                            }
                        )
                else:
                    results.append(
                        {
                            "user_id": user_id,
                            "status": "failed",
                            "port": None,
                        }
                    )

            except Exception as e:
                logger.error(f"启动浏览器失败 {user_id}: {e}", exc_info=True)
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

    async def stop_all_browsers(self) -> None:
        """停止所有浏览器实例"""
        try:
            await self.browser_store.clear()
            await self.port_manager.clear_ports()
            await self.save_ports()
            logger.info("所有浏览器实例已停止")
        except Exception as e:
            logger.error(f"停止浏览器实例时发生错误: {e}", exc_info=True)
            raise

    async def save_ports(self) -> None:
        """保存端口映射到数据库"""
        try:
            managers = await self.browser_store.get_all()
            # 清空旧数据并更新
            await db_manager.clear_all_ports()
            for m in managers:
                await db_manager.save_port(m.user_id, m.port)
            logger.info(f"保存端口映射到数据库成功，共 {len(managers)} 个实例")
        except Exception as e:
            logger.error(f"保存端口映射失败: {e}")

    async def load_ports(self) -> None:
        """从数据库加载端口映射并尝试恢复浏览器实例"""
        try:
            mapping = await db_manager.get_all_ports()
            if not mapping:
                return

            ports = list(mapping.values())
            await self.port_manager.load_ports(ports)

            recovered_count = 0
            invalid_entries = []

            for user_id, port in mapping.items():
                try:
                    if await self._is_browser_running_on_port(port):
                        manager = PlaywrightManager(user_id, port)
                        if await self._try_connect_existing_browser(manager):
                            await self.browser_store.add(manager)
                            recovered_count += 1
                            logger.info(f"恢复浏览器实例成功: {user_id} (端口: {port})")
                        else:
                            invalid_entries.append(user_id)
                            await self.port_manager.release_port(port)
                    else:
                        invalid_entries.append(user_id)
                        await self.port_manager.release_port(port)
                except Exception as e:
                    logger.warning(f"恢复浏览器实例失败 {user_id}: {e}")
                    invalid_entries.append(user_id)
                    await self.port_manager.release_port(port)

            # 清理无效记录
            for u_id in invalid_entries:
                await db_manager.delete_port(u_id)

            logger.info(f"数据库加载端口成功，恢复实例: {recovered_count}个")
        except Exception as e:
            logger.error(f"加载端口映射失败: {e}", exc_info=True)

    async def save_cache(self, user_ids: List[str]) -> None:
        """保存用户ID缓存到数据库"""
        try:
            await db_manager.set_value("user_ids_cache", user_ids)
            logger.info(f"保存用户缓存到数据库成功，共 {len(user_ids)} 个用户")
        except Exception as e:
            logger.error(f"保存用户缓存失败: {e}", exc_info=True)

    async def load_cache(self) -> List[str]:
        """从数据库加载用户ID缓存"""
        try:
            return await db_manager.get_value("user_ids_cache", [])
        except Exception as e:
            logger.error(f"加载用户缓存失败: {e}", exc_info=True)
            return []

    async def clear_cache(self) -> None:
        """清除用户缓存和端口映射"""
        try:
            await db_manager.delete_value("user_ids_cache")
            await self.clear_ports()
            logger.info("清除用户缓存成功")
        except Exception as e:
            logger.error(f"清除用户缓存失败: {e}", exc_info=True)

    async def clear_ports(self) -> None:
        """清空端口映射记录"""
        try:
            await db_manager.clear_all_ports()
            await self.port_manager.clear_ports()
            logger.info("库中端口映射已清空")
        except Exception as e:
            logger.error(f"清除端口映射失败: {e}", exc_info=True)

    async def get_or_create_browser(self, user_id: str) -> Optional[PlaywrightManager]:
        """获取已存在的浏览器实例，否则新建并返回"""
        manager = await self.browser_store.get(user_id)
        if manager and manager.is_running:
            return manager

        if manager and not manager.is_running:
            await self.browser_store.remove(user_id)
            logger.warning(f"清理未运行的浏览器实例: {user_id}")

        try:
            port = await self.port_manager.allocate_port()
            manager = PlaywrightManager(user_id, port)
            ok = await manager.initialize()
            if ok and manager.is_running:
                await self.browser_store.add(manager)
                await self.save_ports()
                logger.info(f"成功创建浏览器实例: {user_id} (端口: {port})")
                return manager
            else:
                await self.port_manager.release_port(port)
                raise RuntimeError(f"初始化浏览器失败: {user_id}")
        except Exception as e:
            logger.error(f"创建浏览器实例失败 {user_id}: {e}", exc_info=True)
            return None

    async def _is_browser_running_on_port(self, port: int) -> bool:
        """检查指定端口是否有浏览器进程在运行"""
        try:
            import socket

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error(f"检查端口 {port} 连接失败: {e}", exc_info=True)
            return False

    async def _try_connect_existing_browser(self, manager: PlaywrightManager) -> bool:
        """尝试连接到现有的浏览器进程"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                try:
                    browser = await p.chromium.connect_over_cdp(
                        f"http://localhost:{manager.port}"
                    )
                    await browser.close()
                    return True
                except:
                    return False
        except Exception as e:
            logger.warning(f"Check existing browser failed: {e}")
            return False


browser_service = BrowserService()


browser_service = BrowserService()
