# 依赖管理迁移指南

## 📋 迁移概述

本项目已完成从传统的 `requirements.txt` 到现代化 `uv` + `pyproject.toml` 的依赖管理迁移。

## 🔄 迁移内容

### 1. 核心依赖统一
所有核心依赖已迁移到 `pyproject.toml` 的 `dependencies` 部分：
- PyQt6、qasync（GUI框架）
- DrissionPage（浏览器自动化）
- httpx、requests、aiohttp（HTTP客户端）
- fastapi、uvicorn（Web框架）
- loguru（日志）
- ujson、pydantic（数据处理）
- psutil（系统监控）
- apscheduler（定时任务）

### 2. 可选依赖分组

#### scheduler 组（调度器相关）
```toml
scheduler = [
    "apscheduler>=3.10.4",
    "jinja2>=3.1.2",
    "aiofiles>=23.2.1",
    "python-multipart>=0.0.6",
    "python-dateutil>=2.8.2",
    "orjson>=3.9.10",
    "httpx>=0.25.2",
]
```

#### data-analysis 组（数据分析）
```toml
data-analysis = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
]
```

#### image-processing 组（图像处理）
```toml
image-processing = [
    "pillow>=10.0.0",
]
```

#### dev 组（开发工具）
```toml
dev = [
    "mypy>=1.7.1",
    "black>=23.11.0",
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
]
```

## 🚀 使用指南

### 基础安装
```bash
# 安装核心依赖
uv sync
```

### 安装可选依赖组
```bash
# 安装调度器依赖
uv sync --extra scheduler

# 安装数据分析依赖
uv sync --extra data-analysis

# 安装图像处理依赖
uv sync --extra image-processing

# 安装开发工具
uv sync --extra dev

# 安装所有依赖
uv sync --extra full
```

### 添加新依赖
```bash
# 添加核心依赖
uv add package-name

# 添加到特定组
uv add --optional scheduler package-name
uv add --optional dev package-name
```

## 📁 文件状态

### 保留的文件
- `pyproject.toml` - 主要依赖配置文件
- `uv.lock` - 锁定文件，确保依赖版本一致性

### 历史文件（可选保留）
- `requirements.txt` - 传统依赖文件，已迁移到 pyproject.toml
- `requirements_scheduler.txt` - 调度器依赖，已迁移到 scheduler 组
- `backup-requirements.txt` - 备份文件

## ✅ 验证

运行依赖测试脚本验证迁移结果：
```bash
python test_dependencies.py
```

预期结果：
- ✅ 核心依赖: 12/12 通过
- ✅ 调度器依赖: 6/6 通过
- ⚠️ 可选依赖: 根据安装情况而定

## 🎯 优势

1. **统一管理**: 所有依赖在一个文件中管理
2. **模块化**: 按功能分组，按需安装
3. **版本锁定**: uv.lock 确保环境一致性
4. **性能优化**: uv 比 pip 更快的依赖解析和安装
5. **现代化**: 符合 Python 包管理最佳实践

## 🔧 故障排除

### 依赖冲突
```bash
# 清理并重新安装
uv clean
uv sync
```

### 版本问题
```bash
# 更新所有依赖到最新兼容版本
uv update
```

### 环境重置
```bash
# 完全重置虚拟环境
rm -rf .venv
uv sync
```