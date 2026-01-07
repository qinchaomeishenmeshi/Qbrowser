import asyncio
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from playwright_stealth import stealth_async

from conf import DATA_DIR, resource_path
from conf.browser_config import chrome_path_manager
from utils.common_logger import get_logger
from utils.screen_utils import get_viewport_dict

logger = get_logger(__name__)


class PlaywrightManager:
    """
    Playwright 浏览器管理器
    负责单个浏览器实例的生命周期管理 (Migration Phase 1)
    """

    def __init__(
        self,
        user_id: str,
        port: int = 9222,
        headless: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.user_id = user_id
        self.port = port
        self.headless = headless
        self.config = config or {}  # 指纹配置
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 数据目录 - 使用绝对路径
        self.data_dir_base = Path(DATA_DIR) / "browser_data" / "douyin"
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
                "--force-webrtc-ip-handling-policy=default_public_interface_only",  # WebRTC 防泄漏
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

            # 3. 准备指纹参数
            viewport = self.config.get("viewport") or get_viewport_dict()
            user_agent = self.config.get("user_agent")  # 如果为None，Playwright使用默认
            timezone_id = self.config.get("timezone_id")
            locale = self.config.get("locale")
            geolocation = self.config.get("geolocation")
            permissions = ["geolocation"] if geolocation else []
            proxy = self.config.get("proxy")
            executable_path = self.config.get("executable_path")

            if not executable_path:
                # 如果没有指定路径，尝试获取系统 Chrome 路径
                executable_path = await chrome_path_manager.get_chrome_path()
                if executable_path:
                    logger.info(f"Using system default chrome: {executable_path}")

            if executable_path:
                path_obj = Path(executable_path)
                if not path_obj.exists():
                    logger.warning(
                        f"Custom kernel path not found: {executable_path}. Falling back to bundled browser."
                    )
                    # 如果系统/自定义路径都找不到，最后才会回退到 Playwright 内置 (虽然在打包版里可能不存在)
                    executable_path = None
                else:
                    logger.info(f"Using custom chromium kernel: {executable_path}")

            # 4. 启动持久化上下文
            abs_user_data_dir = str(self.user_data_dir.resolve())
            logger.info(
                f"Launching Playwright context. User: {self.user_id}, Config: {self.config}"
            )

            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=abs_user_data_dir,
                executable_path=executable_path,  # Custom Kernel
                headless=self.headless,
                args=args,
                viewport=viewport,
                user_agent=user_agent,
                timezone_id=timezone_id,
                locale=locale,
                geolocation=geolocation,
                permissions=permissions,
                proxy=proxy,
                accept_downloads=True,
            )

            # 5. 注入隐身脚本 (Stealth JS)
            stealth_js_path = Path(resource_path("browser/stealth.js"))
            if stealth_js_path.exists():
                js_content = stealth_js_path.read_text(encoding="utf-8")

                # 替换配置
                # 如果 config 中没有相关字段，使用默认值
                canvas_seed = self.config.get("canvas_seed", 123.456)
                audio_seed = self.config.get("audio_seed", 654.321)
                webgl_vendor = self.config.get("webgl_vendor", "Google Inc. (NVIDIA)")
                webgl_renderer = self.config.get(
                    "webgl_renderer",
                    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
                )

                # Use regex to safely replace values in the JS CONFIG object (replacing entire line)
                import re

                js_content = re.sub(
                    r"canvas_seed:.+", f"canvas_seed: {canvas_seed},", js_content
                )
                js_content = re.sub(
                    r"audio_seed:.+", f"audio_seed: {audio_seed}", js_content
                )  # Last item, no comma
                # Fix quotes for string replacements
                js_content = re.sub(
                    r"webgl_vendor:.+", f"webgl_vendor: '{webgl_vendor}',", js_content
                )
                js_content = re.sub(
                    r"webgl_renderer:.+",
                    f"webgl_renderer: '{webgl_renderer}',",
                    js_content,
                )

                await self.context.add_init_script(script=js_content)
                logger.info("Stealth script injected.")

            else:
                logger.warning(f"Stealth script not found at {stealth_js_path}")

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
