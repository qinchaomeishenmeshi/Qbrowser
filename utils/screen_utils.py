# utils/screen_utils.py
# 屏幕分辨率相关工具函数

from typing import Tuple
from utils.common_logger import get_logger

logger = get_logger(__name__)

# 默认分辨率（fallback）
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080


def get_screen_size() -> Tuple[int, int]:
    """
    获取主显示器的屏幕分辨率

    Returns:
        Tuple[int, int]: (宽度, 高度)
    """
    try:
        from screeninfo import get_monitors

        monitors = get_monitors()
        if monitors:
            # 获取主显示器（通常是第一个）
            primary = monitors[0]
            width = primary.width
            height = primary.height
            logger.debug(f"检测到屏幕分辨率: {width}x{height}")
            return (width, height)
    except ImportError:
        logger.warning("screeninfo 库未安装，使用默认分辨率")
    except Exception as e:
        logger.warning(f"获取屏幕分辨率失败: {e}，使用默认分辨率")

    return (DEFAULT_WIDTH, DEFAULT_HEIGHT)


def get_browser_window_size() -> Tuple[int, int]:
    """
    获取浏览器窗口的推荐大小
    会留出一定边距给系统任务栏和窗口边框

    Returns:
        Tuple[int, int]: (宽度, 高度)
    """
    width, height = get_screen_size()

    # 留出边距：
    # - 宽度减少10像素（窗口边框和阴影）
    # - 高度减少80像素（macOS菜单栏 + Dock，或 Windows任务栏）
    browser_width = max(width - 10, 800)
    browser_height = max(height - 80, 600)

    logger.info(f"浏览器窗口大小: {browser_width}x{browser_height}")
    return (browser_width, browser_height)


def get_window_size_argument() -> str:
    """
    获取 Chrome 启动参数格式的窗口大小字符串

    Returns:
        str: 格式为 "宽度,高度" 的字符串，如 "1910,1000"
    """
    width, height = get_browser_window_size()
    return f"{width},{height}"


def get_viewport_dict() -> dict:
    """
    获取 Playwright viewport 配置字典

    Returns:
        dict: 格式为 {"width": 宽度, "height": 高度}
    """
    width, height = get_browser_window_size()
    return {"width": width, "height": height}
