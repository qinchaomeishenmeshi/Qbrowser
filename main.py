import asyncio
import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page

BASE_DIR = Path(__file__).parent.resolve()

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
        self.user_data_dir = BASE_DIR / "browser_data" / "douyin" / user_id
        self.extension_path = (
            "/Users/cherishxn/工作项目/2024/短视频生产系统/wujie-plugins 2"
        )
        # self.viewport = ChromeUtils.get_screen_resolution()

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
                ],
            )

            self.page = await self.browser.new_page()
            await self.page.goto("https://eos.douyin.com")
            # 更新user_data
            logger.info(f"浏览器已启动，用户: {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"初始化浏览器失败: {str(e)}")
            return False

    async def cleanup(self):
        """清理资源"""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            logger.info("浏览器资源已清理")

        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}")


# async def main():
#     """主函数"""
#     logger.info("启动程序")
#     browser_manager = BrowserManager("123")
#
#     try:
#         if await browser_manager.initialize():
#             try:
#                 # 创建一个永久运行的任务
#                 logger.info("浏览器已启动，按 Ctrl+C 可以安全退出程序")
#                 # 等待直到程序被中断
#                 await asyncio.Event().wait()
#             except KeyboardInterrupt:
#                 logger.info("检测到退出信号，正在安全关闭浏览器...")
#             except Exception as e:
#                 logger.error(f"程序异常: {str(e)}")
#         else:
#             logger.error("浏览器初始化失败")
#             return
#
#     except Exception as e:
#         logger.error(f"程序运行出错: {str(e)}")
#
#     finally:
#         await browser_manager.cleanup()

async def main(user_ids: list):
    """主函数"""
    logger.info("启动程序")
    browser_managers = [BrowserManager(user_id) for user_id in user_ids]

    try:
        # 并发初始化所有浏览器实例
        initialization_results = await asyncio.gather(
            *(browser_manager.initialize() for browser_manager in browser_managers),
            return_exceptions=True
        )

        # 检查初始化结果
        for browser_manager, result in zip(browser_managers, initialization_results):
            if isinstance(result, Exception):
                logger.error(f"用户 {browser_manager.user_id} 的浏览器初始化失败: {str(result)}")
            elif not result:
                logger.error(f"用户 {browser_manager.user_id} 的浏览器初始化失败")

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


if __name__ == "__main__":
    # 传入多个用户 ID
    user_ids = ["123", "456", "789"]
    asyncio.run(main(user_ids))

# if __name__ == "__main__":
# asyncio.run(main())
