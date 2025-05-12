# conf.py
import os
import sys

# PyInstaller 会把资源解压到 _MEIPASS
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 放在同目录下，exe 运行时也能找到
CACHE_FILE = os.path.join(BASE_DIR, "user_ids_cache.json")
PORTS_FILE = os.path.join(BASE_DIR, "user_ports_cache.json")
