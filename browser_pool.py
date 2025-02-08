import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class BrowserManager:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.user_data_dir = Path("browser_data") / "douyin" / user_id  # 独立的用户数据目录
        self.extension_path = "/Users/cherishxn/工作项目/2024/短视频生产系统/live-room-plugins/live_room"  # 替换为你的插件路径

    async def initialize(self) -> bool:
        """初始化浏览器和页面"""
        try:
            # 确保目录存在
            self.user_data_dir.mkdir(parents=True, exist_ok=True)

            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=False,
                channel="chrome",
                args=[
                    f"--disable-extensions-except={self.extension_path}",
                    f"--load-extension={self.extension_path}",
                    "--disable-blink-features=AutomationControlled",  # 隐藏自动化提示
                ],
                viewport={"width": 1280, "height": 720},  # 设置视口大小
                screen={"width": 1280, "height": 720},  # 设置屏幕分辨率
                permissions=["geolocation"],  # 允许定位
            )

            self.page = await self.browser.new_page()
            await self.page.goto("https://eos.douyin.com")

            logger.info(f"浏览器已启动，用户: {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"初始化浏览器失败: {str(e)}")
            return False

    async def cleanup(self):
        """清理资源"""
        try:
            # 检查 page 是否未关闭
            if self.page and not self.page.is_closed():
                await self.page.close()
                self.page = None

            # 检查 browser 是否未关闭
            if self.browser:
                try:
                    # 尝试关闭 browser，如果已关闭则会抛出异常
                    await self.browser.close()
                except Exception as e:
                    logger.warning(f"关闭 browser 时出错（可能已关闭）: {str(e)}")
                finally:
                    self.browser = None

            logger.info(f"用户 {self.user_id} 的浏览器资源已清理")

        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}")


class BrowserPool:
    def __init__(self, user_ids: List[str]):
        self.user_ids = user_ids
        self.browser_managers: Dict[str, BrowserManager] = {
            user_id: BrowserManager(user_id) for user_id in user_ids
        }

    async def initialize_all(self) -> bool:
        """初始化所有浏览器"""
        tasks = [manager.initialize() for manager in self.browser_managers.values()]
        results = await asyncio.gather(*tasks)
        return all(results)

    async def cleanup_all(self):
        """关闭所有浏览器"""
        tasks = [manager.cleanup() for manager in self.browser_managers.values()]
        await asyncio.gather(*tasks)

    def get_browser(self, user_id: str) -> Optional[BrowserManager]:
        """根据 user_id 获取对应的 BrowserManager 实例"""
        return self.browser_managers.get(user_id)


async def main():
    """主函数"""
    logger.info("启动程序")

    # 配置用户数量
    user_count = 10
    users = [f"qw{i + 1}" for i in range(user_count)]
    browser_pool = BrowserPool(users)

    try:
        if await browser_pool.initialize_all():
            logger.info("所有浏览器已启动，按 Ctrl+C 可以安全退出程序")
            await asyncio.Event().wait()
        else:
            logger.error("部分浏览器初始化失败")
            return

    except asyncio.CancelledError:
        logger.info("检测到任务取消，正在安全关闭浏览器...")
    except KeyboardInterrupt:
        logger.info("检测到用户中断，正在安全关闭浏览器...")
    except Exception as e:
        logger.error(f"程序异常: {str(e)}")
    finally:
        logger.info("正在安全关闭浏览器...")
        await browser_pool.cleanup_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
