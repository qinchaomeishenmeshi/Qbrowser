# browser_config.py
# Chrome浏览器路径配置管理

import os
import json
from pathlib import Path
from typing import Optional
from conf import writable_path, resource_path
from utils.common_logger import get_logger

from utils.database_manager import db_manager

logger = get_logger(__name__)

# 默认Chrome路径配置（按操作系统）
DEFAULT_CHROME_PATHS = {
    "darwin": [  # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ],
    "win32": [  # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    ],
    "linux": [  # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
        "/usr/bin/microsoft-edge",
        "/usr/bin/brave-browser",
    ],
}


class ChromePathManager:
    """Chrome浏览器路径管理器"""

    def __init__(self):
        self._custom_path = None
        self._loaded = False

    async def _ensure_loaded(self) -> None:
        """从数据库加载Chrome路径配置"""
        if self._loaded:
            return
        try:
            self._custom_path = await db_manager.get_value("chrome_path")
            if self._custom_path:
                logger.info(f"已从数据库加载Chrome路径配置: {self._custom_path}")
            self._loaded = True
        except Exception as e:
            logger.warning(f"加载Chrome路径配置失败: {e}")
            self._custom_path = None

    async def set_chrome_path(self, path: str) -> bool:
        """设置自定义Chrome路径

        Args:
            path: Chrome可执行文件的完整路径

        Returns:
            bool: 设置是否成功
        """
        if not path:
            self._custom_path = None
            try:
                await db_manager.delete_value("chrome_path")
                logger.info("已通过数据库清除自定义Chrome路径，将使用系统默认路径")
                return True
            except Exception as e:
                logger.error(f"清除Chrome路径配置失败: {e}")
                return False

        path_obj = Path(path)
        if not path_obj.exists():
            logger.error(f"Chrome路径不存在: {path}")
            return False

        if not path_obj.is_file():
            logger.error(f"Chrome路径不是文件: {path}")
            return False

        self._custom_path = str(path_obj.resolve())
        try:
            await db_manager.set_value("chrome_path", self._custom_path)
            logger.info(f"Chrome路径设置已保存到数据库: {self._custom_path}")
            return True
        except Exception as e:
            logger.error(f"保存Chrome路径配置失败: {e}")
            return False

    async def get_chrome_path(self) -> Optional[str]:
        """获取Chrome浏览器路径

        Returns:
            str: Chrome可执行文件路径，如果未找到返回None
        """
        await self._ensure_loaded()

        # 1. 优先使用自定义路径
        if self._custom_path and Path(self._custom_path).exists():
            logger.info(f"使用自定义Chrome路径: {self._custom_path}")
            return self._custom_path

        # 2. 尝试系统默认路径
        platform = (
            os.name
            if os.name != "posix"
            else "darwin" if "darwin" in os.sys.platform else "linux"
        )
        if platform == "nt":
            platform = "win32"

        default_paths = DEFAULT_CHROME_PATHS.get(platform, [])

        for path_template in default_paths:
            # 处理Windows路径中的{username}占位符
            if "{username}" in path_template:
                username = os.getenv("USERNAME") or os.getenv("USER", "")
                path = path_template.format(username=username)
            else:
                path = path_template

            if Path(path).exists():
                logger.info(f"找到系统Chrome路径: {path}")
                return path

        logger.warning("未找到可用的Chrome浏览器路径")
        return None

    async def get_current_config(self) -> dict:
        """获取当前配置信息

        Returns:
            dict: 包含当前配置的字典
        """
        await self._ensure_loaded()
        return {
            "custom_path": self._custom_path,
            "effective_path": await self.get_chrome_path(),
            "storage_mode": "database",
            "platform": os.sys.platform,
        }

    def auto_detect_chrome(self) -> list:
        """自动检测系统中可用的Chrome浏览器

        Returns:
            list: 可用的Chrome路径列表
        """
        available_paths = []

        platform = (
            os.name
            if os.name != "posix"
            else "darwin" if "darwin" in os.sys.platform else "linux"
        )
        if platform == "nt":
            platform = "win32"

        default_paths = DEFAULT_CHROME_PATHS.get(platform, [])

        for path_template in default_paths:
            # 处理Windows路径中的{username}占位符
            if "{username}" in path_template:
                username = os.getenv("USERNAME") or os.getenv("USER", "")
                path = path_template.format(username=username)
            else:
                path = path_template

            if Path(path).exists():
                available_paths.append(path)

        logger.info(f"检测到 {len(available_paths)} 个可用的Chrome浏览器")
        return available_paths


# 全局实例
chrome_path_manager = ChromePathManager()
