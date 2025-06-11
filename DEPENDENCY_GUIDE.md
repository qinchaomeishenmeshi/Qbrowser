# 依赖安装指南

## 📦 项目依赖概述

本项目使用 `uv` 作为包管理器，依赖分为以下几个类别：

- **核心依赖**: 项目运行的基础依赖
- **调度器依赖**: 定时任务功能所需依赖
- **数据分析依赖**: 数据处理功能所需依赖（可选）
- **图像处理依赖**: 图像处理功能所需依赖（可选）
- **开发工具依赖**: 开发和测试所需依赖（可选）

## 🚀 快速开始

### 1. 基础安装（仅核心依赖）
```bash
# 安装核心依赖
uv sync
```

### 2. 完整功能安装（包含调度器）
```bash
# 安装核心依赖 + 调度器依赖
uv sync --extra scheduler
```

### 3. 开发环境安装
```bash
# 安装核心依赖 + 调度器依赖 + 开发工具
uv sync --extra scheduler --extra dev
```

### 4. 完整安装（所有依赖）
```bash
# 安装所有依赖组
uv sync --extra full
```

## 📋 依赖组详细说明

### 核心依赖 (必需)
```toml
dependencies = [
    "aiohttp>=3.12.8",      # 异步HTTP客户端
    "PyQt6==6.9.0",         # GUI框架
    "qasync==0.27.1",       # Qt异步支持
    "DrissionPage~=4.1.0.18", # 浏览器自动化
    "httpx~=0.28.1",        # HTTP客户端
    "ujson~=5.10.0",        # 高性能JSON处理
    "loguru~=0.7.3",        # 日志记录
    "requests~=2.32.3",     # HTTP请求库
    "uvicorn~=0.34.2",      # ASGI服务器
    "fastapi~=0.115.12",    # Web框架
    "pydantic~=2.11.4",     # 数据验证
    "psutil~=6.1.0",        # 系统监控
]
```

### 调度器依赖 (scheduler)
```bash
# 单独安装调度器依赖
uv add --optional scheduler apscheduler jinja2 aiofiles python-multipart python-dateutil orjson
```

包含：
- `apscheduler>=3.10.4` - 任务调度器
- `jinja2>=3.1.2` - 模板引擎
- `aiofiles>=23.2.1` - 异步文件操作
- `python-multipart>=0.0.6` - 文件上传处理
- `python-dateutil>=2.8.2` - 时间处理
- `orjson>=3.9.10` - 高性能JSON

### 数据分析依赖 (data-analysis)
```bash
# 安装数据分析依赖
uv sync --extra data-analysis
```

包含：
- `pandas>=2.0.0` - 数据分析库
- `numpy>=1.24.0` - 数值计算库

### 图像处理依赖 (image-processing)
```bash
# 安装图像处理依赖
uv sync --extra image-processing
```

包含：
- `pillow>=10.0.0` - 图像处理库

### 开发工具依赖 (dev)
```bash
# 安装开发工具依赖
uv sync --extra dev
```

包含：
- `mypy>=1.7.1` - 类型检查
- `black>=23.11.0` - 代码格式化
- `pytest>=7.4.3` - 测试框架
- `pytest-asyncio>=0.21.1` - 异步测试支持

## 🔍 依赖状态检查

### 运行依赖测试
```bash
# 检查当前依赖状态
python test_dependencies.py
```

### 检查APScheduler功能
```bash
# 测试调度器功能
python test_apscheduler.py
```

## 🛠️ 常用命令

### 查看已安装的包
```bash
uv pip list
```

### 查看过时的包
```bash
uv pip list --outdated
```

### 更新所有依赖
```bash
uv sync --upgrade
```

### 添加新依赖
```bash
# 添加到核心依赖
uv add package_name

# 添加到可选依赖组
uv add --optional group_name package_name
```

### 移除依赖
```bash
uv remove package_name
```

## 🚨 故障排除

### 1. 依赖冲突
```bash
# 重新解析依赖
uv lock --upgrade
uv sync
```

### 2. 缓存问题
```bash
# 清理缓存
uv cache clean
```

### 3. 虚拟环境问题
```bash
# 重建虚拟环境
rm -rf .venv
uv sync
```

## 📊 当前依赖状态

根据最新测试结果：

- ✅ **核心依赖**: 12/12 通过
- ✅ **调度器依赖**: 6/6 通过
- ⚠️ **可选依赖**: 0/3 通过 (pandas, numpy, pillow 未安装)

如需使用数据分析或图像处理功能，请按需安装对应的依赖组。

## 🔗 相关文件

- `pyproject.toml` - 主要依赖配置
- `uv.lock` - 锁定的依赖版本
- `test_dependencies.py` - 依赖测试脚本
- `test_apscheduler.py` - 调度器功能测试
- `dependency_analysis_report.md` - 详细的依赖分析报告