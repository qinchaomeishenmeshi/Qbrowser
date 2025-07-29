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

# 轻量版隐藏导入（排除WebEngine）
hiddenimports = [
    'PyQt6.QtCore', 
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets', 
    'DrissionPage',
    # 轻量版不包含WebEngine相关模块
]

# 排除模块以减少打包大小
excludes = [
    # WebEngine相关模块（轻量版核心排除项）
    'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebEngine',
    'PyQt6.QtWebEngineQuick',
    'PyQt6.QtWebChannel',
    'PyQt6.QtPdf',
    'PyQt6.QtPdfWidgets',
    
    # 开发工具
    'mypy',
    'black', 
    'pytest',
    'pytest_asyncio',
    'coverage',
    'flake8',
    'pylint',
    
    # 不需要的标准库模块
    'tkinter',
    'turtle',
    'test',
    'unittest',
    'doctest',
    'pdb',
    'profile',
    'pstats',
    'cProfile',
    'trace',
    'timeit',
    'calendar',
    'cmd',
    'code',
    'codeop',
    'compileall',
    'dis',
    'distutils',
    'ensurepip',
    'lib2to3',
    'pydoc',
    'py_compile',
    'tabnanny',
    'turtledemo',
    'venv',
    
    # 不需要的第三方库
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
    'qtconsole',
    'spyder',
    'idle',
    
    # 多媒体和图像处理（如果不需要）
    'PIL.ImageTk',
    'PIL.ImageQt',
    'cv2',
    'skimage',
    
    # 网络和协议（保留基础的）
    'ftplib',
    'imaplib',
    'nntplib',
    'poplib',
    'smtplib',
    'telnetlib',
    
    # 数据库（如果不使用）
    'sqlite3',
    'dbm',
    
    # XML处理（保留基础的）
    'xml.dom',
    'xml.sax',
    'xml.parsers.expat',
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

# 轻量版EXE配置
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='全网直播浏览器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # 轻量版启用strip以减少大小
    upx=True,    # 启用UPX压缩
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
    strip=True,   # 轻量版启用strip
    upx=True,     # 启用UPX压缩
    upx_exclude=[
        # 基础Qt库文件，压缩可能导致问题
        'Qt6Core.dll',
        'Qt6Gui.dll', 
        'Qt6Widgets.dll',
        # Python相关
        'python*.dll',
        'vcruntime*.dll',
        'msvcp*.dll',
        # 其他系统库
        'api-ms-*.dll',
        'ucrtbase.dll',
    ],
    name='全网直播浏览器-轻量版',  # 轻量版目录名
)