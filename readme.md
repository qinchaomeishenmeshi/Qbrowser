# QW-Browser 清简浏览器

## 项目简介

**QW-Browser** 是一个基于 **Playwright** 引擎和 **Tauri** 框架构建的桌面级浏览器管理系统。它提供了多用户浏览器实例的统一管理、自动化操作和状态监控功能，专为需要多账号隔离、反检测和高效批量操作的业务场景设计。

## 技术栈

| 层级           | 技术                                     |
| -------------- | ---------------------------------------- |
| **前端**       | Vue 3 + TypeScript + Element Plus + Vite |
| **桌面框架**   | Tauri (Rust)                             |
| **后端**       | Python 3.9+ + FastAPI + Uvicorn          |
| **浏览器引擎** | Playwright (Chromium)                    |
| **数据存储**   | SQLite + JSON 文件缓存                   |
| **实时通信**   | WebSocket                                |

## 核心特性

- 🖥️ **桌面应用**: 基于 Tauri 打包的原生桌面应用，支持 macOS / Windows / Linux。
- 🚀 **Playwright 驱动**: 采用异步 Playwright 引擎，性能优越，支持无头/有头模式。
- 🛡️ **反检测 (Stealth)**: 内置 `playwright-stealth`，自动隐藏 WebDriver 特征，规避反爬检测。
- 👥 **多用户隔离**: 每个用户独立的浏览器上下文（Context），数据完全隔离。
- 🔄 **异步架构**: 全链路 `async/await` 设计，支持高并发浏览器实例管理。
- 🌐 **网络监听**: 基于 CDP 和 Playwright 路由机制，精准捕获 API 的 Cookies/Headers 数据。
- 🧩 **扩展系统**: 支持动态注入 Chrome 扩展（如直播工具等）。
- 📡 **实时状态推送**: WebSocket 实时推送浏览器状态变更。

## 功能模块

### 1. 浏览器实例管理

| 功能       | 描述                                             |
| ---------- | ------------------------------------------------ |
| 启动浏览器 | 为指定用户创建独立的浏览器实例，支持指定初始 URL |
| 停止浏览器 | 停止用户的浏览器进程，保留实例配置缓存           |
| 删除实例   | 彻底删除浏览器实例及其所有用户数据               |
| 批量操作   | 支持批量启动、停止多个浏览器实例                 |
| 状态查询   | 查询活跃实例数量、端口占用、运行状态等           |

### 2. 页面重定向

| 功能         | 描述                                 |
| ------------ | ------------------------------------ |
| 单页面重定向 | 将指定用户的当前页面重定向到目标 URL |
| 批量重定向   | 同时重定向多个用户的页面             |
| 规则管理     | 创建、查询、删除重定向规则           |
| 规则应用     | 将预设规则应用到指定用户             |

### 3. Cookies/Headers 采集

| 功能       | 描述                                                 |
| ---------- | ---------------------------------------------------- |
| 自动采集   | 监听特定 API 路径，自动提取请求的 Cookies 和 Headers |
| 多站点支持 | 内置百应 (Baiying)、EOS 等平台的采集配置             |
| 数据缓存   | 采集数据自动持久化存储，支持智能刷新                 |

### 4. Chrome 配置

| 功能       | 描述                               |
| ---------- | ---------------------------------- |
| 路径检测   | 自动检测系统中可用的 Chrome 浏览器 |
| 自定义路径 | 手动设置 Chrome 可执行文件路径     |
| 配置管理   | 获取/清除当前 Chrome 配置          |

### 5. 扩展管理

| 功能     | 描述                                     |
| -------- | ---------------------------------------- |
| 扩展加载 | 启动时自动加载 `extensions` 目录下的扩展 |
| 状态检查 | 检查扩展的加载状态和注入情况             |

### 6. 系统监控

| 功能           | 描述                 |
| -------------- | -------------------- |
| 健康检查       | 后端服务健康状态检查 |
| 日志查看       | 系统运行日志查看     |
| WebSocket 状态 | 实时连接状态查询     |

## 项目结构

```
qw-browser/
├── api/                          # FastAPI 路由层
│   ├── api_server.py             # 主 API 服务入口
│   ├── redirect_api.py           # 页面重定向接口
│   └── chrome_config_api.py      # Chrome 配置接口
├── browser/                      # 浏览器核心层
│   ├── playwright_manager.py     # Playwright 实例生命周期管理
│   ├── playwright_operator.py    # 高级操作封装 (重定向、采集等)
│   └── browser_store.py          # 全局实例存储池
├── conf/                         # 配置模块
│   └── browser_config.py         # Chrome 路径配置管理
├── config/                       # 应用配置
│   └── settings.py               # 全局设置
├── extensions/                   # Chrome 扩展目录
├── frontend/                     # Tauri + Vue 前端
│   ├── src/                      # Vue 源码
│   │   ├── views/                # 页面组件
│   │   │   ├── Dashboard.vue     # 仪表盘首页
│   │   │   ├── BrowserList.vue   # 浏览器实例列表
│   │   │   ├── Extensions.vue    # 扩展管理
│   │   │   ├── Logs.vue          # 日志查看
│   │   │   └── Settings.vue      # 系统设置
│   │   ├── api/                  # API 调用封装
│   │   ├── stores/               # Pinia 状态管理
│   │   └── router/               # 路由配置
│   └── src-tauri/                # Tauri 后端 (Rust)
├── models/                       # Pydantic 数据模型
├── service/                      # 业务服务层
│   └── browser_service.py        # 浏览器服务逻辑
├── utils/                        # 工具库
│   ├── database_manager.py       # SQLite 数据库管理
│   ├── cookies_manager.py        # Cookies 管理
│   ├── websocket_manager.py      # WebSocket 管理
│   ├── page_redirect_manager.py  # 重定向规则管理
│   └── playwright_network_listener.py  # 网络请求监听
├── tests/                        # 测试用例
├── main.py                       # 后端启动入口
└── pyproject.toml                # Python 项目配置
```

## 快速开始

### 环境要求

- **Python**: 3.9+
- **Node.js**: 18+
- **Rust**: (用于 Tauri 构建)
- **Chrome**: 建议安装最新版 Google Chrome

### 1. 安装后端依赖

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e "."
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 开发模式运行

**方式一：分别运行**

```bash
# 终端 1: 启动后端 API 服务
python main.py
# 后端服务地址: http://127.0.0.1:6001

# 终端 2: 启动前端开发服务器
cd frontend
npm run tauri dev
```

**方式二：仅后端 (API 模式)**

```bash
python main.py
# API 文档: http://127.0.0.1:6001/docs
```

### 4. 生产构建

```bash
cd frontend
npm run tauri build
```

## API 接口概览

### 浏览器管理

| 方法 | 路径                    | 描述           |
| ---- | ----------------------- | -------------- |
| GET  | `/api/health`           | 健康检查       |
| GET  | `/api/browser/status`   | 获取浏览器状态 |
| GET  | `/api/all_instances`    | 获取所有实例   |
| GET  | `/api/active_instances` | 获取活跃实例   |
| POST | `/api/start/{user_id}`  | 启动浏览器     |
| POST | `/api/stop/{user_id}`   | 停止浏览器     |
| POST | `/api/delete/{user_id}` | 删除浏览器实例 |
| POST | `/api/start_all`        | 批量启动浏览器 |
| POST | `/api/stop`             | 停止所有浏览器 |

### 页面重定向

| 方法   | 路径                         | 描述           |
| ------ | ---------------------------- | -------------- |
| POST   | `/api/redirect/single`       | 单页面重定向   |
| POST   | `/api/redirect/batch`        | 批量重定向     |
| GET    | `/api/redirect/rules`        | 获取重定向规则 |
| POST   | `/api/redirect/rules`        | 添加重定向规则 |
| DELETE | `/api/redirect/rules/{name}` | 删除重定向规则 |
| POST   | `/api/redirect/apply-rule`   | 应用重定向规则 |

### Chrome 配置

| 方法   | 路径                            | 描述             |
| ------ | ------------------------------- | ---------------- |
| GET    | `/api/chrome-config/current`    | 获取当前配置     |
| GET    | `/api/chrome-config/detect`     | 检测可用浏览器   |
| POST   | `/api/chrome-config/set-path`   | 设置 Chrome 路径 |
| DELETE | `/api/chrome-config/clear-path` | 清除自定义路径   |

### WebSocket

| 路径            | 描述               |
| --------------- | ------------------ |
| `/ws/browser`   | 浏览器状态实时推送 |
| `/ws/scheduler` | 调度状态实时推送   |

## 使用示例

### 启动浏览器并打开页面

```bash
curl -X POST "http://127.0.0.1:6001/api/start/user_001?url=https://www.baidu.com"
```

### 页面重定向

```bash
curl -X POST "http://127.0.0.1:6001/api/redirect/single" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "target_url": "https://example.com"}'
```

### 批量启动浏览器

```bash
curl -X POST "http://127.0.0.1:6001/api/start_all?user_ids=user_001&user_ids=user_002"
```

## Docker 部署

```bash
docker-compose up -d
```

## 配置说明

### 环境变量

| 变量          | 默认值      | 描述                  |
| ------------- | ----------- | --------------------- |
| `API_HOST`    | `127.0.0.1` | API 监听地址          |
| `API_PORT`    | `6001`      | API 监听端口          |
| `CHROME_PATH` | 自动检测    | Chrome 可执行文件路径 |
| `DEBUG`       | `false`     | 调试模式              |
