# conf.py
import os
import sys
import platform


# 获取打包后的资源路径
def resource_path(relative_path):
    """用于PyInstaller打包后的静态资源读取 (只读)"""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS  # 打包后的临时解压目录
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_app_data_dir():
    """获取应用数据存储目录 (可写)"""
    app_name = "com.qwbrowser.desktop"
    system = platform.system()

    if system == "Windows":
        base_path = os.environ.get("APPDATA") or os.path.expanduser(
            "~\\AppData\\Roaming"
        )
    elif system == "Darwin":  # macOS
        base_path = os.path.expanduser("~/Library/Application Support")
    else:  # Linux / Unix
        base_path = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")

    data_dir = os.path.join(base_path, app_name)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def writable_path(relative_path):
    """获取可写文件路径"""
    return os.path.join(get_app_data_dir(), relative_path)


# 项目根目录 (仅用于读取静态资源)
BASE_DIR = resource_path("")

# 数据存储目录 (用于数据库、日志、配置等可写文件)
DATA_DIR = writable_path("data")
LOG_DIR = writable_path("logs")

# 缓存和端口文件
CACHE_FILE = writable_path("user_ids_cache.json")
PORTS_FILE = writable_path("user_ports_cache.json")
