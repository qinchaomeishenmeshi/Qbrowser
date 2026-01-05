# 清简浏览器 API Service (Playwright Edition)

## 项目简介

**清简浏览器 API** 是短视频生产系统的核心浏览器服务组件，经过全新重构，现在基于高性能的 **Playwright** 引擎构建。它提供了一套无头(Headless)浏览器管理的 RESTful API，专为高并发、反检测和容器化部署而设计。

本项目不再依赖 GUI 环境，完全由 API 驱动，支持多用户隔离、自动化任务调度和复杂的浏览器交互场景（如百应、直播中控、EOS 等）。

## 核心特性

- 🚀 **Playwright 驱动**: 采用异步 Playwright 引擎，性能远超传统的 Selenium/DrissionPage。
- 🛡️ **反检测 (Stealth)**: 内置 `playwright-stealth`，自动隐藏 `navigator.webdriver` 等特征，有效规避反爬检测。
- 🔄 **异步架构**: 全链路 `async/await` 设计，支持高并发浏览器实例管理。
- 🌐 **高级网络监听**: 基于 CDP 和 Playwright 路由机制，精准捕获特定 API 的 Request/Response 数据（如 Cookies、Headers）。
- 📦 **容器化就绪**: 完美支持 Docker 部署，开箱即用。
- 🧩 **扩展系统**: 支持动态注入 Chrome 扩展（如 `live_room` 直播工具）。

## 功能概览

| 模块 | 功能描述 |
|Args|Description|
|---|---|
| **实例管理** | 启动、停止、清理特定用户的浏览器上下文（Context），支持多用户隔离。 |
| **页面控制** | 页面导航、重定向 (Redirect)、自动刷新、截图。 |
| **数据采集** | 自动提取指定站点的 Cookies 和 Headers，支持 API 路径过滤。 |
| **业务集成** | 内置百应 (Baiying)、直播中控 (Screen)、EOS 等特定平台的登录检查和跳转逻辑。 |
| **状态监控** | 实时查看浏览器活跃数量、扩展加载状态和健康检查。 |

## 🚀 快速开始

### 1. 环境与依赖

- **Python**: 3.9+
- **Chrome**: 建议安装最新版 Google Chrome
- **系统**: MacOS / Linux / Windows

安装 Python 依赖：

```bash
pip install -e "."
```

_注：项目会自动安装 `playwright` 及其浏览器驱动。_

### 2. 启动服务

**方式一：直接运行 (开发调试)**

```bash
python main.py
# 服务地址: http://127.0.0.1:8000
```

**方式二：Docker 运行 (生产部署)**

```bash
docker-compose up -d
```

### 3. API 文档

启动后访问 Swagger UI 查看完整接口定义：
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 典型使用场景

### 1. 启动浏览器并打开页面

```bash
# 启动用户 test_user_001 的浏览器并打开百度
curl -X POST "http://127.0.0.1:8000/api/start/test_user_001?url=https://www.baidu.com"
```

### 2. 采集 Cookies 和 Headers (API 调用)

Python 代码示例 (使用 `httpx` 调用本服务):

```python
import httpx

# 调用收集接口
response = httpx.get("http://127.0.0.1:8000/api/redirect/collect/test_user_001?site_key=baiying")
data = response.json()

print(f"Cookies: {data['cookies']}")
```

### 3. 页面重定向

```bash
curl -X POST "http://127.0.0.1:8000/api/redirect/user/test_user_001?target_url=https://example.com"
```

## 目录结构说明

- `api/`: FastAPI 路由和业务逻辑
  - `api_server.py`: 主服务入口
  - `redirect_api.py`: 重定向与采集业务
- `browser/`: 浏览器核心层
  - `playwright_manager.py`: 单个 Playwright 实例生命周期管理
  - `playwright_operator.py`: 高级操作封装 (Redirect, Fetch Cookies)
  - `browser_store.py`: 全局实例存储池
- `conf/`: 配置文件 (Chrome 路径, API 端口等)
- `utils/`: 工具库 (网络监听, Cookies 加密等)
- `tests/`: 测试脚本 (`verify_playwright.py`)

## 迁移说明 (vs 旧版)

本版本已完全移除 `BrowserManager` (DrissionPage) 和 `socket` 通信模块。所有浏览器交互均通过 Playwright 的 WebSocket (CDP) 进行。请确保 worker 脚本已更新为调用新的 API 端点。

---

_短视频生产系统研发部_
