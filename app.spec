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
    ('conf.py', '.'),
    ('user_ids_cache.json', '.'),
    ('user_ports_cache.json', '.'),
    ('static', 'static'),
]

# 添加 PyQt6 相关模块
hiddenimports = [
    'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'DrissionPage'
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
    excludes=[],
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
