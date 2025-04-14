import asyncio
import logging
import os
import platform
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
    """跨平台安全的绝对路径获取，兼容 PyInstaller"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的临时目录路径
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
    """浏览器配置数据类"""
    viewport_width: Optional[int] = None  # 不限制宽度
    viewport_height: Optional[int] = None  # 不限制高度
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

    async def initialize(self) -> bool:
        """初始化浏览器上下文和页面"""
        try:
            # 新增：检查目录是否可用
            lock_file = self.user_data_dir / "SingletonLock"
            retry_count = 0
            while lock_file.exists():
                if retry_count >= 5:  # 最多重试5次
                    logger.error(f"用户目录 {self.user_data_dir} 被占用，放弃启动")
                    return False
                logger.warning(f"检测到目录 {self.user_data_dir} 被占用，等待释放...")
                await asyncio.sleep(2)
                retry_count += 1

            self._playwright = await async_playwright().start()
            print(f"扩展路径: {self.config.extension_path}")

            self.context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=False,
                channel="chrome",
                no_viewport=True,
                args=[
                    f"--disable-extensions-except={self.config.extension_path}",
                    f"--load-extension={self.config.extension_path}",
                ], )
            # 增加一个空页作为浏览器标识
            empty_page = self.context.pages[0] if self.context.pages[0] else await self.context.new_page()
            # 设置浏览器标题为 user_id
            await empty_page.evaluate(f"document.title = '浏览器ID: {self.user_id}'")
            # 新打开一个页面
            self.page = await self.context.new_page()
            await self.page.goto(self.config.base_url)
            self._startup_time = asyncio.get_running_loop().time()

            logger.info(f"浏览器已启动，用户: {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {str(e)}", exc_info=True)
            await self.cleanup()
            return False

    async def cleanup(self):
        try:
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
            # 强制等待浏览器进程退出（避免残留）
            await asyncio.sleep(2)
            self.page = None
            self.context = None
            self._playwright = None

    @property
    def is_running(self) -> bool:
        """优化后的浏览器状态检测（线程安全/版本兼容/异常防护）"""
        try:
            return bool(self.context)
        except Exception:
            return False

    @property
    def uptime(self) -> Optional[float]:
        """获取运行时间（秒），修改为同步方式"""
        if self._startup_time and self.is_running:
            return time.time() - self._startup_time
        return None


async def main(user_ids: list):
    """主函数"""
    logger.info("启动程序")
    browser_managers = [BrowserManager(user_id) for user_id in user_ids]

    try:
        # 依次初始化每个浏览器实例
        for browser_manager in browser_managers:
            try:
                result = await browser_manager.initialize()
                if not result:
                    logger.error(f"用户 {browser_manager.user_id} 的浏览器初始化失败")
            except Exception as e:
                logger.error(f"用户 {browser_manager.user_id} 的浏览器初始化失败: {str(e)}")
            else:
                logger.info(f"用户 {browser_manager.user_id} 的浏览器初始化成功")

        # 创建一个永久运行的任务
        logger.info("所有浏览器已启动，按 Ctrl+C 可以安全退出程序")
        # 等待直到程序被中断
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        logger.info("检测到退出信号，正在安全关闭所有浏览器...")
    except Exception as e:
        logger.error(f"程序异常: {str(e)}")

    finally:
        # 并发清理所有浏览器资源
        await asyncio.gather(
            *(browser_manager.cleanup() for browser_manager in browser_managers)
        )


import sys


# def get_resource_path(filename):
#     if hasattr(sys, '_MEIPASS'):
#         # 打包后的临时目录
#         return os.path.join(sys._MEIPASS, filename)
#     return os.path.join(os.path.abspath("."), filename)
#
#
# if __name__ == "__main__":
#     user_ids_path = get_resource_path('user_ids.txt')
#     with open(user_ids_path, 'r', encoding='utf-8') as f:
#         user_ids = [line.strip() for line in f]
#     print(user_ids)
#     asyncio.run(main(user_ids))


def get_user_ids_path():
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        exe_dir = os.path.dirname(sys.executable)
    else:
        # 正常 Python 运行
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(exe_dir, 'user_ids.txt')


if __name__ == "__main__":
    user_ids_path = get_user_ids_path()
    with open(user_ids_path, 'r', encoding='utf-8') as f:
        user_ids = [line.strip() for line in f]
    print(user_ids)
    asyncio.run(main(user_ids))

#     pyinstaller app2.py \
#   --onefile \
#   --add-data "extensions/live_room:extensions/live_room"

# pyinstaller app2.py --onefile --add-data "extensions/live_room"
