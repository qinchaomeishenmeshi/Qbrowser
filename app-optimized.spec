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
    ('static', 'static'),
    ('templates', 'templates'),
    ('data', 'data'),
    ('logs', 'logs'),
]

# 添加 PyQt6 相关模块
hiddenimports = [
    'PyQt6.QtCore', 
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets', 
    'DrissionPage',
    # WebEngine相关（如果需要）
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebEngineCore',
]

# 排除不必要的模块以减少打包大小
excludes = [
    # 开发工具
    'mypy',
    'black', 
    'pytest',
    'pytest_asyncio',
    
    # 不需要的标准库模块
    'tkinter',
    'turtle',
    'test',
    'unittest',
    'doctest',
    'pdb',
    'profile',
    'pstats',
    
    # 不需要的第三方库
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'IPython',
    'jupyter',
    
    # WebEngine调试组件
    'PyQt6.QtWebEngineCore.debug',
    'PyQt6.QtWebEngineWidgets.debug',
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
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

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
    uac_admin=True, # 添加 管理员权限
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        # WebEngine相关文件不能使用UPX压缩
        'QtWebEngineProcess.exe',
        'QtWebEngineProcess',
        'icudtl.dat',
        'qtwebengine_devtools_resources.pak',
        'qtwebengine_resources.pak',
        'qtwebengine_resources_100p.pak',
        'qtwebengine_resources_200p.pak',
        # Qt相关的大文件
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'Qt6WebEngineCore.dll',
        'Qt6WebEngineWidgets.dll',
    ],
    name='全网直播浏览器',
)