import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict

from browser.browser_manager import BrowserManager
from browser.browser_store import browser_store
from conf import CACHE_FILE, PORTS_FILE, DATA_DIR
from utils.common_logger import get_logger
from utils.cookies_manager import CookiesManager
from utils.port_manager import PortManager

logger = get_logger(__name__)


class BrowserService:
    def __init__(self):
        self.browser_store = browser_store  # 全局单例
        self.port_manager = PortManager()  # 使用新的端口管理器
        self.cookies_manager = CookiesManager(Path(os.path.join(DATA_DIR, "cookies")))

    async def start_browsers(self, user_ids: List[str]) -> List[Dict]:
        results = []
        for idx, user_id in enumerate(user_ids, 1):
            try:
                # 使用get_or_create_browser统一处理浏览器实例获取和创建
                manager = await self.get_or_create_browser(user_id)
                
                if manager and manager.is_running:
                    # 检查是否是已存在的实例
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
        从文件加载端口映射并尝试恢复浏览器实例
        """
        if os.path.exists(PORTS_FILE):
            try:
                with open(PORTS_FILE, encoding="utf-8") as f:
                    mapping = json.load(f)

                ports = {
                    v["port"]
                    for v in mapping.values()
                    if isinstance(v, dict) and "port" in v
                }
                await self.port_manager.load_ports(ports)
                
                # 尝试恢复浏览器实例
                recovered_count = 0
                invalid_entries = []
                
                for user_id, config in mapping.items():
                    if isinstance(config, dict) and "port" in config:
                        port = config["port"]
                        try:
                            # 检查端口是否真的在使用中
                            if await self._is_browser_running_on_port(port):
                                # 创建浏览器管理器实例但不初始化（连接到现有进程）
                                manager = BrowserManager(user_id, port)
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
                
                # 清理无效的缓存条目
                if invalid_entries:
                    for user_id in invalid_entries:
                        mapping.pop(user_id, None)
                    
                    # 更新缓存文件
                    with open(PORTS_FILE, "w", encoding="utf-8") as f:
                        json.dump(mapping, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"清理无效缓存条目: {invalid_entries}")
                
                logger.info(f"加载端口映射成功: {mapping}, 恢复实例: {recovered_count}个")
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
        print(f"获取或创建浏览器实例 {manager}")
        if manager and manager.is_running:
            return manager
        
        # 如果存在但未运行的实例，先清理掉
        if manager and not manager.is_running:
            await self.browser_store.remove(user_id)
            logger.warning(f"清理未运行的浏览器实例: {user_id}")

        try:
            port = await self.port_manager.allocate_port()
            manager = BrowserManager(user_id, port)
            ok = await asyncio.to_thread(manager.initialize)
            if ok and manager.is_running:
                await self.browser_store.add(manager)
                await self.save_ports()
                logger.info(f"成功创建浏览器实例: {user_id} (端口: {port})")
                return manager
            else:
                await self.port_manager.release_port(port)
                raise RuntimeError(f"初始化浏览器失败: {user_id}")
        except Exception as e:
            logger.error(f"创建浏览器实例失败 {user_id}: {e}")
            raise RuntimeError(f"无法为用户 {user_id} 创建或获取浏览器实例: {e}")

    async def _is_browser_running_on_port(self, port: int) -> bool:
        """
        检查指定端口是否有浏览器进程在运行
        """
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    async def _try_connect_existing_browser(self, manager: BrowserManager) -> bool:
        """
        尝试连接到现有的浏览器进程
        """
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions
            
            # 创建连接选项
            co = ChromiumOptions()
            co.set_local_port(manager.port)
            
            # 尝试连接到现有浏览器
            browser = ChromiumPage(addr_or_opts=co)
            
            # 验证连接是否成功
            if browser and hasattr(browser, 'tabs_count'):
                manager.browser = browser
                return True
            else:
                return False
        except Exception as e:
            logger.debug(f"连接现有浏览器失败 (端口 {manager.port}): {e}")
            return False

browser_service = BrowserService()
