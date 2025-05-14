# conf.py
import os
import sys

# 获取打包后的资源路径
def resource_path(relative_path):
    """用于PyInstaller打包后的资源路径转换"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS  # 打包后的临时解压目录
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

BASE_DIR = resource_path("")
CACHE_FILE = os.path.join(BASE_DIR, "user_ids_cache.json")
PORTS_FILE = os.path.join(BASE_DIR, "user_ports_cache.json")