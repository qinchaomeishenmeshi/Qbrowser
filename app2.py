import asyncio
import json
import logging
import os
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, BrowserContext, Page, Playwright

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_absolute_extension_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent
    extension_path = base_dir / relative_path
    absolute_path = extension_path.resolve(strict=True)
    if platform.system() == 'Windows':
        win_path = str(absolute_path)
        if any(c in win_path for c in (' ', '&', '^')):
            win_path = f'"{win_path}"'
        try:
            from ctypes import windll, create_unicode_buffer
            buffer = create_unicode_buffer(256)
            if windll.kernel32.GetShortPathNameW(win_path, buffer, 256):
                win_path = buffer.value
        except Exception:
            pass
        return win_path
    return str(absolute_path)


@dataclass
class BrowserConfig:
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    base_url: str = "https://eos.douyin.com"
    extension_path = get_absolute_extension_path("extensions/live_room")
    data_dir_base: Path = Path("browser_data") / "douyin"


class BrowserManager:
    def __init__(self, user_id: str, config: Optional[BrowserConfig] = None):
        self.user_id = user_id
        self.config = config or BrowserConfig()
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.user_data_dir = self.config.data_dir_base / user_id
        self._playwright: Optional[Playwright] = None
        self._startup_time = None
        self.last_urls_file = self.user_data_dir / "last_urls.json"

    async def inject_user_tag(self, page: Page):
        await page.evaluate(f"""
            (() => {{
                const div = document.createElement('div');
                div.innerText = '浏览器ID: {self.user_id}';
                div.style.position = 'fixed';
                div.style.top = '10px';
                div.style.left = '10px';
                div.style.background = 'rgba(0,0,0,0.6)';
                div.style.color = 'white';
                div.style.padding = '5px 10px';
                div.style.zIndex = '999999';
                div.style.borderRadius = '8px';
                div.style.fontSize = '14px';
                div.style.pointerEvents = 'none';
                document.body.appendChild(div);
            }})()
        """)

    async def initialize(self) -> bool:
        try:
            lock_file = self.user_data_dir / "SingletonLock"
            retry_count = 0
            while lock_file.exists():
                if retry_count >= 5:
                    logger.error(f"用户目录 {self.user_data_dir} 被占用，放弃启动")
                    return False
                logger.warning(f"检测到目录 {self.user_data_dir} 被占用，等待释放...")
                await asyncio.sleep(2)
                retry_count += 1

            self._playwright = await async_playwright().start()
            logger.info(f"扩展路径: {self.config.extension_path}")

            self.context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=False,
                channel="chrome",
                no_viewport=True,
                args=[
                    f"--disable-extensions-except={self.config.extension_path}",
                    f"--load-extension={self.config.extension_path}",
                ],
            )

            # 关闭除一个about:blank页面以外的所有页面
            blank_page = None
            for page in self.context.pages:
                if page.url == "about:blank" and blank_page is None:
                    blank_page = page
                else:
                    await page.close()
            if not blank_page:
                blank_page = await self.context.new_page()
            self.page = blank_page
            await self.page.evaluate(f"document.title = '{self.user_id}'")

            if self.last_urls_file.exists():
                try:
                    with open(self.last_urls_file, 'r', encoding='utf-8') as f:
                        urls = json.load(f)
                    if isinstance(urls, list) and urls:
                        for url in urls:
                            page = await self.context.new_page()
                            await page.goto(url)
                            await self.inject_user_tag(page)
                        logger.info(f"恢复上次打开的 {len(urls)} 个页面")
                except Exception as e:
                    logger.warning(f"恢复 URL 失败：{str(e)}")
            self._startup_time = time.time()
            logger.info(f"浏览器已启动，用户: {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {str(e)}", exc_info=True)
            await self.cleanup()
            return False

    async def cleanup(self):
        try:
            if self.context:
                urls = [page.url for page in self.context.pages if
                        page.url and not page.url.startswith('chrome://') and page.url != 'about:blank']
                if urls:
                    self.user_data_dir.mkdir(parents=True, exist_ok=True)
                    with open(self.last_urls_file, 'w', encoding='utf-8') as f:
                        json.dump(urls, f, ensure_ascii=False, indent=2)
                    logger.info(f"已保存 {len(urls)} 个打开页面 URL")

            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}", exc_info=True)
        finally:
            await asyncio.sleep(2)
            self.page = None
            self.context = None
            self._playwright = None

    @property
    def is_running(self) -> bool:
        try:
            return bool(self.context)
        except Exception:
            return False

    @property
    def uptime(self) -> Optional[float]:
        if self._startup_time and self.is_running:
            return time.time() - self._startup_time
        return None


async def main(user_ids: list):
    logger.info("启动程序")
    browser_managers = [BrowserManager(user_id) for user_id in user_ids]
    try:
        for browser_manager in browser_managers:
            try:
                result = await browser_manager.initialize()
                if not result:
                    logger.error(f"用户 {browser_manager.user_id} 的浏览器初始化失败")
            except Exception as e:
                logger.error(f"用户 {browser_manager.user_id} 的浏览器初始化失败: {str(e)}")
            else:
                logger.info(f"用户 {browser_manager.user_id} 的浏览器初始化成功")

        logger.info("所有浏览器已启动，按 Ctrl+C 可以安全退出程序")
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        logger.info("检测到退出信号，正在安全关闭所有浏览器...")
    except Exception as e:
        logger.error(f"程序异常: {str(e)}")
    finally:
        await asyncio.gather(
            *(browser_manager.cleanup() for browser_manager in browser_managers)
        )


def get_user_ids_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(exe_dir, 'user_ids.txt')


if __name__ == "__main__":
    user_ids_path = get_user_ids_path()
    with open(user_ids_path, 'r', encoding='utf-8') as f:
        user_ids = [line.strip() for line in f if line.strip()]
    print(user_ids)
    asyncio.run(main(user_ids))
