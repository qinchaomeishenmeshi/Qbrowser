# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_submodules
from pathlib import Path

# 脚本路径
script_path = 'app2.py'

# 插件路径（源路径 -> 打包后路径）
datas = [
    ('user_ids.txt', '.'),
    ('extensions/live_room', 'extensions/live_room')
]

# 如果未来还有其他资源，如配置文件：
# datas.append(('config.yaml', '.'))

# 打包选项
a = Analysis(
    [script_path],
    pathex=[str(Path.cwd())],  # 使用当前工作目录
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='qw_browser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # False 表示不显示黑框控制台
    icon='logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app2',
)
