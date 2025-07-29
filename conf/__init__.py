# conf.py
import os
import sys


# 获取打包后的资源路径
def resource_path(relative_path):
    """用于PyInstaller打包后的资源路径转换"""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS  # 打包后的临时解压目录
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def writable_path(relative_path):
    """获取可写文件路径，打包后使用exe所在目录"""
    if getattr(sys, "frozen", False):
        # 打包后使用exe所在目录作为可写目录
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境使用项目根目录
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# 项目根目录
BASE_DIR = resource_path("")
DATA_DIR = resource_path("data")

# 缓存和端口文件都在根目录
CACHE_FILE = resource_path("user_ids_cache.json")
PORTS_FILE = resource_path("user_ports_cache.json")