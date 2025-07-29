image.png# 打包文件大小增加分析报告

## 问题概述
- **之前打包大小**: 约59MB
- **当前打包大小**: 约195MB
- **增加幅度**: 约136MB (增长230%)

## 主要原因分析

### 1. 新增PyQt6 WebEngine依赖 (主要原因)

**影响**: 约100-120MB增加

在提交 `eba85db` 中添加了 `pyqt6-webengine` 依赖:
```toml
"pyqt6-webengine",
```

**WebEngine组件大小分析**:
- `pyqt6_webengine_qt6-6.9.1-py3-none-win_amd64.whl`: 110MB
- `pyqt6_webengine_qt6-6.9.1-py3-none-macosx_10_14_x86_64.whl`: 120MB
- `pyqt6_webengine_qt6-6.9.1-py3-none-macosx_11_0_arm64.whl`: 108MB

**WebEngine包含的组件**:
- Chromium内核 (约80-90MB)
- WebEngine运行时库
- 多媒体编解码器
- GPU加速支持
- 安全沙箱组件

### 2. 构建配置变更

**影响**: 约10-20MB增加

在 `.github/workflows/build-exe.yml` 中，构建命令变更为:
```bash
uv sync --extra scheduler --extra dev
```

**新增的依赖组**:
- **scheduler组**: apscheduler, jinja2, aiofiles, python-multipart, python-dateutil, orjson
- **dev组**: mypy, black, pytest, pytest-asyncio, pyinstaller

### 3. 依赖管理重构

**影响**: 约5-10MB增加

在提交 `5b9f36f` 中，将分散的依赖文件合并到 `pyproject.toml`:

**之前的依赖结构**:
- `requirements.txt`: 12个核心依赖
- `requirements_scheduler.txt`: 调度器相关依赖
- `backup-requirements.txt`: 完整依赖列表

**现在的依赖结构**:
- 所有依赖统一在 `pyproject.toml` 中管理
- 构建时安装了额外的开发和调度器依赖

### 4. PyInstaller配置未优化

**影响**: 约5MB增加

当前 `app.spec` 配置:
```python
hiddenimports = [
    'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'DrissionPage'
]
```

**缺少的优化**:
- 未排除WebEngine的调试符号
- 未排除不必要的语言包
- 未排除开发工具依赖

## 详细对比分析

### 依赖变化对比

**之前 (requirements.txt)**:
```
PyQt6==6.9.0
qasync==0.27.1
DrissionPage~=4.1.0.18
httpx~=0.28.1
ujson~=5.10.0
loguru~=0.7.3
requests~=2.32.3
aiohttp>=3.12.8
uvicorn~=0.34.2
fastapi~=0.115.12
pydantic~=2.11.4
```

**现在 (pyproject.toml dependencies)**:
```
# 新增了44个依赖包，包括:
pyqt6-webengine  # 主要增加项
psutil~=7.0.0
openpyxl==3.1.5
lxml==5.4.0
# ... 其他依赖
```

**额外依赖组 (--extra scheduler --extra dev)**:
```
# scheduler组 (约5-8MB)
apscheduler>=3.10.4
jinja2>=3.1.2
aiofiles>=23.2.1
python-multipart>=0.0.6
python-dateutil>=2.8.2
orjson>=3.9.10

# dev组 (约8-12MB)
mypy>=1.7.1
black>=23.11.0
pytest>=7.4.3
pytest-asyncio>=0.21.1
pyinstaller>=6.0.0
```

## 双版本构建方案

### 🚀 完整版 (Full Version)
**目标文件大小**: 150-170MB

**包含组件**:
- 完整的PyQt6 WebEngine支持
- 所有生产依赖
- 内置定时任务管理界面
- 完整的用户体验

**优化措施**:
- 移除开发依赖 (-15MB)
- 优化PyInstaller配置 (-10MB)
- UPX压缩关键组件 (-10MB)

### ⚡ 轻量版 (Lite Version)
**目标文件大小**: 60-80MB

**排除组件**:
- PyQt6 WebEngine (-100MB)
- WebEngine相关Qt组件 (-20MB)
- 开发工具依赖 (-15MB)

**功能调整**:
- 定时任务管理使用外部浏览器
- 自动检测WebEngine可用性
- 优雅降级处理

### 🔧 技术实现

#### 1. 条件化WebEngine加载
```python
# 支持轻量版构建
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    LITE_MODE = False
except ImportError:
    QWebEngineView = None
    LITE_MODE = True
```

#### 2. 智能UI适配
- 完整版：内嵌WebEngine视图
- 轻量版：外部浏览器打开
- 用户体验保持一致

#### 3. 构建配置分离
- `app.spec`: 完整版配置
- `app-lite.spec`: 轻量版配置
- GitHub Actions并行构建

### 4. 立即优化措施

**修改构建命令**:
```bash
# 当前
uv sync --extra scheduler --extra dev

# 优化后
uv sync --extra scheduler
```

**更新 app.spec**:
```python
# 排除WebEngine调试组件
excludes=[
    'PyQt6.QtWebEngineCore.debug',
    'PyQt6.QtWebEngineWidgets.debug',
    'PyQt6.QtWebEngine.locales.unused',
],

# 优化UPX压缩
upx_exclude=[
    'QtWebEngineProcess.exe',  # WebEngine进程不能压缩
    'icudtl.dat',              # ICU数据文件
],
```

**移除非必要依赖**:
```toml
# 可选移除的依赖
"openpyxl==3.1.5",      # Excel处理，如不需要可移除
"lxml==5.4.0",          # XML处理，DrissionPage已包含
"psutil~=7.0.0",        # 系统信息，如不需要可移除
```

## 预期优化效果

| 版本 | 文件大小 | 减少幅度 | 适用场景 |
|------|----------|----------|----------|
| 当前版本 | 195MB | - | 基准版本 |
| 完整版 | 150-170MB | 25-45MB | 最佳体验 |
| 轻量版 | 60-80MB | 115-135MB | 资源敏感 |

## 使用建议

- **完整版**: 推荐给需要最佳用户体验的用户
- **轻量版**: 推荐给对文件大小敏感或系统资源有限的用户
- **功能差异**: 仅定时任务管理界面的显示方式不同

## 总结

**主要增长因素排序**:
1. **PyQt6 WebEngine** (100-120MB) - 占增长的80%
2. **额外依赖组** (15-25MB) - 占增长的15%
3. **依赖管理重构** (5-10MB) - 占增长的5%

**建议的优化策略**:
1. **短期**: 移除dev依赖组，优化构建配置 (-20-30MB)
2. **中期**: 优化WebEngine打包配置 (-10-20MB)
3. **长期**: 实现条件化WebEngine加载，提供多版本选择

**双版本构建优势**:
- 满足不同用户需求
- 保持功能完整性
- 显著减少文件大小（轻量版）
- 提供最佳用户体验（完整版）