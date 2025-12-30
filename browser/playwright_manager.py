import asyncio
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from playwright_stealth import stealth_async

from conf import BASE_DIR, resource_path
from conf.browser_config import chrome_path_manager
from utils.common_logger import get_logger
from utils.screen_utils import get_viewport_dict

logger = get_logger(__name__)


class PlaywrightManager:
    """
    Playwright 浏览器管理器
    负责单个浏览器实例的生命周期管理 (Migration Phase 1)
    """

    def __init__(self, user_id: str, port: int = 9222, headless: bool = False) -> None:
        self.user_id = user_id
        self.port = port
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 数据目录 - 使用绝对路径
        self.data_dir_base = Path(BASE_DIR) / "browser_data" / "douyin"
        self.user_data_dir = self.data_dir_base / user_id
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        # 扩展路径
        self.extensions = []
        self._init_extensions()

    def _init_extensions(self):
        """初始化扩展路径"""
        ext_path = Path(resource_path("extensions/live_room"))
        if ext_path.exists():
            self.extensions.append(str(ext_path.resolve()))
            logger.info(f"Loaded extension: {ext_path}")

    async def initialize(self) -> bool:
        """初始化 Playwright 浏览器上下文"""
        try:
            self.playwright = await async_playwright().start()

            # 1. 基础启动参数
            args = [
                "--disable-blink-features=AutomationControlled",
                "--no-default-browser-check",
            ]

            # 2. 加载扩展的特殊处理
            if self.extensions:
                ext_paths = ",".join(self.extensions)
                args.extend(
                    [
                        f"--disable-extensions-except={ext_paths}",
                        f"--load-extension={ext_paths}",
                    ]
                )
                logger.info(f"Extension paths added to args: {ext_paths}")

            # 3. 启动持久化上下文
            # 暂时不强制指定 executable_path，使用 Playwright 自带 Chromium 进行测试
            # chrome_path = await chrome_path_manager.get_chrome_path()

            abs_user_data_dir = str(self.user_data_dir.resolve())
            logger.info(
                f"Launching Playwright context. User data dir: {abs_user_data_dir}"
            )

            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=abs_user_data_dir,
                # executable_path=chrome_path,
                headless=self.headless,
                args=args,
                viewport=get_viewport_dict(),
                accept_downloads=True,
            )

            # 获取第一个页面或新建
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = await self.context.new_page()

            # 应用反检测 (Stealth)
            await stealth_async(self.page)

            # 注入用户标识 (Tag)
            await self.inject_user_tag(self.page)

            logger.info(f"Playwright browser initialized for user: {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"Playwright initialization failed: {e}", exc_info=True)
            await self.cleanup()
            return False

    async def inject_user_tag(self, page: Page):
        """注入用户 ID 悬浮窗"""
        js_code = f"""
        () => {{
            const d = document.createElement('div');
            d.innerText = 'Browser ID: {self.user_id} (Playwright)';
            Object.assign(d.style, {{
                position: 'fixed',
                top: '10px',
                left: '10px',
                background: 'rgba(0,100,0,0.8)',
                color: 'white',
                padding: '5px 10px',
                zIndex: 999999,
                borderRadius: '8px',
                fontSize: '14px'
            }});
            document.body.appendChild(d);
        }}
        """
        try:
            await page.evaluate(js_code)
        except Exception as e:
            logger.warning(f"Tag injection failed: {e}")

    @property
    def is_running(self) -> bool:
        """检查浏览器是否正在运行"""
        return self.context is not None

    async def cleanup(self):
        """资源清理"""
        if self.context:
            try:
                await self.context.close()
            except Exception as e:
                logger.error(f"Error closing context for {self.user_id}: {e}")
            finally:
                self.context = None

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.error(f"Error stopping playwright for {self.user_id}: {e}")
            finally:
                self.playwright = None

        logger.info(f"Playwright resources cleaned up for {self.user_id}")
