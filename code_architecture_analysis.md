# QW-Browser 项目代码架构分析

## 项目概述

QW-Browser 是一个基于 PyQt6 的浏览器管理系统，集成了多个服务模块，包括浏览器自动化、定时任务调度、API 服务等功能。项目采用模块化设计，支持多种启动方式。

## 核心启动文件分析

### 1. app.py - 主应用程序入口

**功能定位**: 完整的 GUI 应用程序，提供图形界面和所有核心功能

**核心特性**:
- **单例模式**: 使用文件锁机制防止重复启动
- **轻量版支持**: 自动检测 QtWebEngineWidgets 可用性，支持轻量版构建
- **权限检查**: Windows 平台管理员权限检测和提示
- **异步架构**: 基于 qasync 的事件循环，支持异步操作
- **优雅退出**: 信号处理和资源清理机制

**主要组件**:
```python
# 核心类和功能
class App(QMainWindow):  # 传统 GUI 界面
    - 浏览器管理功能
    - 用户ID配置加载
    - 进度显示和日志输出
    - 缓存管理
    - 设置界面

# 关键函数
check_single_instance()     # 单例检查
release_single_instance()   # 资源释放
is_admin()                  # 权限检查
main()                      # 应用程序入口
```

**启动流程**:
1. 单例检查 → 权限验证 → Qt兼容性初始化
2. 创建QApplication和异步事件循环
3. 设置信号处理和异常捕获
4. 加载现代化UI界面 (ModernApp)
5. 启动事件循环

### 2. run_app.py - 备用启动入口

**功能定位**: 简化的启动脚本，统一调用 app.py 的 main 函数

**设计目的**:
- 提供备用启动方式
- 确保启动逻辑一致性
- 避免重复实现

**使用场景**:
- 推荐: `python app.py`
- 备用: `python run_app.py`

### 3. start_api_server.py - API服务器启动脚本

**功能定位**: 独立的 FastAPI 服务器，提供 Chrome 配置管理的 Web 界面和 API

**核心功能**:
- Chrome 配置管理 Web 界面
- RESTful API 服务
- 开发/生产模式切换
- 命令行参数支持

**服务端点**:
- 主服务: `http://127.0.0.1:8000`
- Chrome配置页面: `/chrome/config`
- API文档: `/docs`

**启动参数**:
```bash
python start_api_server.py --host 127.0.0.1 --port 8000 --no-debug
```

### 4. start_scheduler_server.py - 定时任务服务启动脚本

**功能定位**: 独立的定时任务调度服务，基于 FastAPI 和 lifespan 生命周期管理

**核心特性**:
- **生命周期管理**: 使用 FastAPI lifespan 机制
- **任务调度**: 集成 scheduler_client 进行任务管理
- **Web界面**: 提供任务管理仪表板
- **健康检查**: 提供服务状态监控

**服务架构**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段
    await scheduler_client.start()
    yield  # 运行阶段
    # 关闭阶段
    await scheduler_client.stop()
```

**服务端点**:
- 管理界面: `http://localhost:8000/scheduler/dashboard`
- API文档: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/health`

### 5. ui/ 模块 - 现代化用户界面

**功能定位**: 基于 PyQt6 的现代化 UI 框架

**模块结构**:
```
ui/
├── __init__.py
├── config.py          # UI配置（主题、字体、布局）
├── factory.py         # UI工厂模式
├── modern_app.py      # 现代化主界面
├── components/        # UI组件
└── pages/            # 页面模块
    └── dashboard.py   # 仪表板页面
```

**设计特点**:
- **主题系统**: 支持明暗主题切换
- **响应式设计**: 现代化卡片布局
- **组件化**: 可复用的UI组件
- **渐变效果**: 支持渐变背景和阴影效果

## 架构关系图

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   run_app.py    │───▶│     app.py       │───▶│   ui/modern_app.py  │
│   (备用入口)     │    │   (主应用程序)    │    │   (现代化界面)       │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  核心服务模块     │
                    │ ─────────────── │
                    │ • browser_service│
                    │ • scheduler_client│
                    │ • browser_operator│
                    └──────────────────┘

┌─────────────────────┐              ┌──────────────────────────┐
│ start_api_server.py │              │ start_scheduler_server.py│
│ (API服务器)          │              │ (定时任务服务)            │
│ ─────────────────── │              │ ──────────────────────── │
│ • Chrome配置管理     │              │ • 任务调度管理            │
│ • RESTful API       │              │ • Web仪表板              │
│ • 端口: 8000        │              │ • 健康检查               │
└─────────────────────┘              └──────────────────────────┘
```

## 启动方式对比

| 启动方式 | 用途 | 界面 | 服务 | 适用场景 |
|---------|------|------|------|----------|
| `python app.py` | 完整应用 | GUI界面 | 所有服务 | 日常使用 |
| `python run_app.py` | 备用启动 | GUI界面 | 所有服务 | 备用方式 |
| `python start_api_server.py` | API服务 | Web界面 | API服务 | 服务器部署 |
| `python start_scheduler_server.py` | 定时任务 | Web界面 | 调度服务 | 任务管理 |

## 技术栈总结

**前端技术**:
- PyQt6: GUI框架
- qasync: 异步事件循环
- 现代化UI设计: 主题系统、响应式布局

**后端技术**:
- FastAPI: Web框架
- uvicorn: ASGI服务器
- asyncio: 异步编程

**核心功能**:
- 浏览器自动化管理
- 定时任务调度
- 配置管理
- 日志系统
- 缓存机制

**部署特性**:
- 单例模式防重复启动
- 跨平台支持 (Windows/macOS/Linux)
- 权限检查和提示
- 优雅退出机制
- 轻量版构建支持

## 开发建议

1. **模块化开发**: 各个启动脚本职责明确，便于独立部署和测试
2. **配置管理**: UI配置集中管理，便于主题和样式统一
3. **异步架构**: 充分利用异步编程提升性能
4. **错误处理**: 完善的异常捕获和日志记录
5. **用户体验**: 现代化界面设计，支持多种启动方式