# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 脚本路径
script_path = 'app.py'  # 主脚本文件 app.py

# 插件路径（源路径 -> 打包后路径）
datas = [
    ('extensions/live_room', 'extensions/live_room'),
    ('extensions/block_videos', 'extensions/block_videos'),
    ('frp_client/frpc.exe', 'frp_client'),
    ('frp_client/frpc.toml', 'frp_client'),
    ('conf', 'conf'),
    ('user_ids_cache.json', '.'),
    ('user_ports_cache.json', '.'),
    ('user_ids.txt', '.'),  # 添加用户ID配置文件
    ('static', 'static'),
    ('templates', 'templates'),
    ('data', 'data'),
    ('logs', 'logs'),
    # 新增：工具模块和文档
    ('utils', 'utils'),  # 包含所有工具模块
    ('docs', 'docs'),    # 文档目录
    ('tests', 'tests'),  # 测试目录
    # 新增：批处理文件
    ('start_windows_skip_singleton.bat', '.'),
    # 新增：测试脚本
    ('test_singleton_manager.py', '.'),
]

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
