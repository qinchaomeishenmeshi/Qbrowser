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
from utils.websocket_manager import ws_manager
from utils.ws_protocol import (
    EventType,
    BrowserStatus,
    create_browser_event,
    create_batch_event,
)

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
        total = len(user_ids)
        success_count = 0
        failed_count = 0

        # 广播批量操作开始
        await ws_manager.broadcast(
            create_batch_event(EventType.BATCH_STARTED, operation="start", total=total),
            channel="browser",
        )

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
                        success_count += 1
                    else:
                        results.append(
                            {
                                "user_id": user_id,
                                "status": "started",
                                "port": manager.port,
                            }
                        )
                        success_count += 1
                else:
                    results.append(
                        {
                            "user_id": user_id,
                            "status": "failed",
                            "port": None,
                        }
                    )
                    failed_count += 1

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
                failed_count += 1

            # 广播进度（每处理一个就广播一次）
            await ws_manager.broadcast(
                create_batch_event(
                    EventType.BATCH_PROGRESS,
                    operation="start",
                    total=total,
                    completed=idx,
                    success=success_count,
                    failed=failed_count,
                    current_user_id=user_id,
                ),
                channel="browser",
            )

        await self.save_ports()

        # 广播批量操作完成
        await ws_manager.broadcast(
            create_batch_event(
                EventType.BATCH_COMPLETED,
                operation="start",
                total=total,
                completed=total,
                success=success_count,
                failed=failed_count,
                results=results,
            ),
            channel="browser",
        )

        return results

    async def stop_browser(self, user_id: str, broadcast: bool = True) -> bool:
        """停止单个浏览器实例"""
        try:
            manager = await self.browser_store.get(user_id)
            if not manager or not manager.is_running:
                return True

            # 只有开启广播时才发送「正在停止」
            if broadcast:
                await ws_manager.broadcast(
                    create_browser_event(
                        EventType.BROWSER_STOPPING,
                        user_id=user_id,
                        status=BrowserStatus.STOPPING,
                    ),
                    channel="browser",
                )

            success = await self.browser_store.stop(user_id)

            if success and broadcast:
                # 广播「已停止」事件
                await ws_manager.broadcast(
                    create_browser_event(
                        EventType.BROWSER_STOPPED,
                        user_id=user_id,
                        status=BrowserStatus.STOPPED,
                        message="浏览器已成功停止",
                    ),
                    channel="browser",
                )

            return success
        except Exception as e:
            logger.error(f"停止浏览器实例失败 {user_id}: {e}", exc_info=True)
            return False

    async def stop_all_browsers(self, user_ids: Optional[List[str]] = None) -> None:
        """停止所有或指定的浏览器实例"""
        try:
            managers = await self.browser_store.get_all()
            if user_ids is not None:
                # 仅停止指定的且正在运行的
                running_managers = [
                    m for m in managers if m.is_running and m.user_id in user_ids
                ]
            else:
                # 停止全部正在运行的
                running_managers = [m for m in managers if m.is_running]

            total = len(running_managers)

            if total == 0:
                return

            # 广播批量操作开始
            await ws_manager.broadcast(
                create_batch_event(
                    EventType.BATCH_STARTED, operation="stop", total=total
                ),
                channel="browser",
            )

            success_count = 0
            failed_count = 0

            for idx, manager in enumerate(running_managers, 1):
                try:
                    ok = await self.stop_browser(manager.user_id, broadcast=False)
                    if ok:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"批量停止失败 {manager.user_id}: {e}")
                    failed_count += 1

                # 广播进度
                await ws_manager.broadcast(
                    create_batch_event(
                        EventType.BATCH_PROGRESS,
                        operation="stop",
                        total=total,
                        completed=idx,
                        success=success_count,
                        failed=failed_count,
                        current_user_id=manager.user_id,
                    ),
                    channel="browser",
                )

            await self.port_manager.clear_ports()
            await self.save_ports()

            # 广播批量操作完成
            await ws_manager.broadcast(
                create_batch_event(
                    EventType.BATCH_COMPLETED,
                    operation="stop",
                    total=total,
                    success=success_count,
                    failed=failed_count,
                ),
                channel="browser",
            )

            logger.info(
                f"所有浏览器实例已停止: 成功 {success_count}, 失败 {failed_count}"
            )
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
        """获取已存在的浏览器实例（运行中或已停止），否则新建并返回"""
        manager = await self.browser_store.get(user_id)

        # 如果已存在且正在运行，直接返回
        if manager and manager.is_running:
            return manager

        # 广播「正在启动」事件
        await ws_manager.broadcast(
            create_browser_event(
                EventType.BROWSER_STARTING,
                user_id=user_id,
                status=BrowserStatus.STARTING,
            ),
            channel="browser",
        )

        # 如果存在但已停止，我们需要重新初始化
        try:
            if manager:
                # 如果 manager 已经存在，可能需要尝试使用原有端口或重新分配
                port = manager.port
                # 检查原有端口是否仍可用，不可用则重新分配
                if not await self._is_port_available(port):
                    port = await self.port_manager.allocate_port()
                    manager.port = port
            else:
                port = await self.port_manager.allocate_port()
                manager = PlaywrightManager(user_id, port)
                await self.browser_store.add(manager)

            ok = await manager.initialize()
            if ok and manager.is_running:
                await self.save_ports()
                logger.info(f"成功启动浏览器实例: {user_id} (端口: {port})")

                # 广播「启动成功」事件
                await ws_manager.broadcast(
                    create_browser_event(
                        EventType.BROWSER_STARTED,
                        user_id=user_id,
                        status=BrowserStatus.RUNNING,
                        port=port,
                        message="浏览器启动成功",
                    ),
                    channel="browser",
                )

                return manager
            else:
                raise RuntimeError(f"初始化浏览器失败: {user_id}")
        except Exception as e:
            logger.error(f"创建或启动浏览器实例失败 {user_id}: {e}", exc_info=True)

            # 广播「启动失败」事件
            await ws_manager.broadcast(
                create_browser_event(
                    EventType.BROWSER_ERROR,
                    user_id=user_id,
                    status=BrowserStatus.ERROR,
                    error=str(e),
                ),
                channel="browser",
            )

            return None

    async def create_browser(self, user_id: str) -> Optional[PlaywrightManager]:
        """仅新建浏览器配置而不启动"""
        try:
            manager = await self.browser_store.get(user_id)
            if manager:
                return manager

            port = await self.port_manager.allocate_port()
            manager = PlaywrightManager(user_id, port)
            await self.browser_store.add(manager)
            await self.save_ports()

            # 广播「已新建」事件，让前端列表实时更新
            await ws_manager.broadcast(
                create_browser_event(
                    EventType.BROWSER_ADDED,
                    user_id=user_id,
                    status=BrowserStatus.STOPPED,
                    message="新浏览器已创建",
                ),
                channel="browser",
            )
            return manager
        except Exception as e:
            logger.error(f"创建浏览器配置失败 {user_id}: {e}", exc_info=True)
            return None

    async def delete_browser(self, user_id: str) -> bool:
        """删除浏览器实例及其本地缓存数据"""
        try:
            manager = await self.browser_store.get(user_id)
            if manager:
                # 1. 如果正在运行，先停止
                if manager.is_running:
                    await self.stop_browser(user_id, broadcast=False)

                # 2. 从存储移除
                await self.browser_store.remove(user_id)
                # 3. 释放端口
                await self.port_manager.release_port(manager.port)
                # 4. 从数据库移除端口记录
                await db_manager.delete_port(user_id)

                # 5. 删除本地数据目录
                import shutil

                if manager.user_data_dir.exists():
                    shutil.rmtree(manager.user_data_dir)
                    logger.info(f"已删除用户数据目录: {manager.user_data_dir}")

                # 广播「已删除」事件
                await ws_manager.broadcast(
                    create_browser_event(
                        EventType.BROWSER_DELETED,
                        user_id=user_id,
                        status=BrowserStatus.DELETED,
                        message="浏览器已彻底删除",
                    ),
                    channel="browser",
                )

                return True
            return False
        except Exception as e:
            logger.error(f"删除浏览器实例失败 {user_id}: {e}", exc_info=True)
            return False

    async def delete_browsers(self, user_ids: List[str]) -> Dict[str, bool]:
        """批量删除浏览器"""
        results = {}
        for user_id in user_ids:
            results[user_id] = await self.delete_browser(user_id)
        return results

    async def _is_port_available(self, port: int) -> bool:
        """检查端口是否可用（未被占用）"""
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            result = sock.connect_ex(("127.0.0.1", port))
            return result != 0  # 0 means occupied
        finally:
            sock.close()

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
