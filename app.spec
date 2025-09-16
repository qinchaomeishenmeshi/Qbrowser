# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 脚本路径
script_path = 'app.py'  # 主脚本文件 app.py

# 条件包含文件的函数
def add_data_if_exists(file_path, dest_path='.'):
    """如果文件存在则添加到数据列表中"""
    if Path(file_path).exists():
        return [(file_path, dest_path)]
    else:
        print(f"Warning: {file_path} not found, skipping...")
        return []

def add_dir_if_exists(dir_path, dest_path=None):
    """如果目录存在则添加到数据列表中"""
    if dest_path is None:
        dest_path = dir_path
    if Path(dir_path).exists() and any(Path(dir_path).iterdir()):
        return [(dir_path, dest_path)]
    else:
        print(f"Warning: {dir_path} not found or empty, skipping...")
        return []

# 插件路径（源路径 -> 打包后路径）
datas = []

# 必需的扩展目录
datas.extend(add_dir_if_exists('extensions/live_room', 'extensions/live_room'))

# frp客户端文件
datas.extend(add_data_if_exists('frp_client/frpc.exe', 'frp_client'))
datas.extend(add_data_if_exists('frp_client/frpc.toml', 'frp_client'))

# 配置和模板目录
datas.extend(add_dir_if_exists('conf', 'conf'))
datas.extend(add_dir_if_exists('templates', 'templates'))

# 工具模块和文档
datas.extend(add_dir_if_exists('utils', 'utils'))
datas.extend(add_dir_if_exists('docs', 'docs'))

# 可选的文件和目录
datas.extend(add_dir_if_exists('static', 'static'))
datas.extend(add_dir_if_exists('data', 'data'))
datas.extend(add_dir_if_exists('logs', 'logs'))

# 配置文件
datas.extend(add_data_if_exists('start_windows_skip_singleton.bat', '.'))
datas.extend(add_data_if_exists('logo.ico', '.'))
datas.extend(add_data_if_exists('app.manifest', '.'))

print(f"Included {len(datas)} data files/directories for packaging")

# 添加 PyQt6 相关模块
hiddenimports = [
    'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 
    'PyQt6.QtNetwork',  # 新增：QLocalServer/QLocalSocket 需要
    'DrissionPage',
    'qasync',  # 异步事件循环
    'asyncio',  # 异步支持
    'loguru',  # 日志系统
    'filelock',  # 保持兼容性
    # 工具模块
    'utils.singleton_manager',  # 新增：单例管理器
    'utils.common_logger', 
    'utils.qt_compatibility',
    'utils.api_client',
    'utils.async_file_manager',
    'utils.common_response',
    'utils.cookies',
    'utils.cookies_manager',
    'utils.get_ab',
    'utils.head_requester',
    'utils.port_manager',
    'utils.smart_cache_strategy',
    'utils.tab_pool_manager',
    'utils.util',
    # API模块
    'api.api_business',
    'api.api_server', 
    'api.chrome_config_api',
    'api.scheduler_api',
    # 浏览器模块
    'browser.browser_manager',
    'browser.browser_operator', 
    'browser.browser_store',
    # 服务模块
    'service.browser_service',
    # 工作线程模块
    'worker.core_data',
    'worker.coupon_client',
    'worker.eos_client', 
    'worker.living_client',
    'worker.scheduler_client',
    # UI模块
    'ui.modern_app',
    'ui.config',
    'ui.components',
    'ui.pages',
    'ui.styles',
]

# 打包选项
a = Analysis(
    [script_path],
    pathex=[str(Path.cwd())],  # 使用当前工作目录
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不必要的模块以减小打包大小
        'tkinter',
        'matplotlib', 
        'scipy',
        'numpy',
        'pandas',
        'jupyter',
        'IPython',
        'notebook',
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)  # 或者使用 AES 加密：cipher=AES

# 设置为不显示控制台窗口
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='全网直播浏览器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 设置为 False 来避免显示终端窗口
    icon='logo.ico',  # 确保替换为你的图标文件路径
    winmanifest='app.manifest',  # 添加 manifest 文件来请求管理员权限
    uac_admin=True, # 添加 管理员权限 ！！！
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],  # 如果有需要排除的库，请在这里列出
    name='全网直播浏览器',
)
