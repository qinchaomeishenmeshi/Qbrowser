# QW-Browser API 服务器文档

## 概述

`api_server.py` 是 QW-Browser 项目的核心 API 服务器，基于 FastAPI 框架构建，提供了完整的浏览器管理、扩展控制、任务调度等功能的 RESTful API 接口。

## 技术栈

- **框架**: FastAPI
- **异步支持**: asyncio, uvicorn
- **浏览器控制**: Playwright
- **模板引擎**: Jinja2Templates
- **跨域支持**: CORS 中间件

## 服务器配置

### 基本配置

- **默认端口**: 8000
- **访问地址**: <http://127.0.0.1:8000>
- **API 文档**: <http://127.0.0.1:8000/docs>
- **Chrome 配置页面**: <http://127.0.0.1:8000/chrome_config>

### 中间件

- **CORS**: 允许所有来源的跨域请求
- **静态文件**: 支持静态资源服务
- **模板**: Jinja2 模板引擎支持

## API 接口详细说明

### 1. 健康检查与状态

#### GET /api/health

**功能**: 健康检查端点  
**参数**: 无  
**返回值**:

```json
{
  "status": "ok",
  "message": "Backend is running"
}
```

#### GET /api/status

**功能**: 获取服务器运行状态  
**参数**: 无  
**返回值**:

```json
{
  "running": true,
  "user_count": 5
}
```

### 2. 浏览器管理

#### GET /api/browser/status

**功能**: 获取浏览器服务状态  
**参数**: 无  
**返回值**:

```json
{
  "status": "running",
  "total_instances": 10,
  "active_instances": 8,
  "message": "Browser service is running"
}
```

#### GET /api/active_instances

**功能**: 获取所有激活的浏览器实例  
**参数**: 无  
**返回值**:

```json
{
  "status": "success",
  "active_count": 3,
  "active_instances": ["user1", "user2", "user3"]
}
```

#### POST /api/start/{user_id}

**功能**: 启动指定用户的浏览器实例  
**路径参数**:

- `user_id` (string): 用户 ID

**查询参数**:

- `url` (string, 可选): 要打开的页面 URL

**返回值**:

```json
{
  "user_id": "user1",
  "status": "success",
  "port": 9001,
  "opened_url": "https://example.com"
}
```

**状态说明**:

- `success`: 新实例启动成功
- `already_running`: 实例已存在
- `fail`: 启动失败
- `error`: 发生错误

#### POST /api/start_all

**功能**: 批量启动多个用户的浏览器实例  
**查询参数**:

- `user_ids` (List[string]): 要批量启动的用户 ID 列表
- `url` (string, 可选): 要打开的页面 URL

**返回值**:

```json
{
  "results": [
    {
      "user_id": "user1",
      "status": "success",
      "port": 9001,
      "opened_url": "https://example.com"
    }
  ]
}
```

#### POST /api/stop

**功能**: 停止所有浏览器实例  
**参数**: 无  
**返回值**:

```json
{
  "status": "success",
  "message": "所有浏览器已关闭"
}
```

### 3. 浏览器连接管理 (新增功能)

#### POST /api/connect/{user_id}

**功能**: 连接到已打开的浏览器实例  
**路径参数**:

- `user_id` (string): 用户 ID

**查询参数**:

- `port` (int): 要连接的浏览器端口号

**返回值**:

```json
{
  "user_id": "user1",
  "status": "connected",
  "port": 9001,
  "message": "成功连接到端口 9001 上的浏览器实例"
}
```

**状态说明**:

- `connected`: 连接成功
- `already_connected`: 已存在连接
- `connection_failed`: 连接失败
- `connection_error`: 连接错误

#### POST /api/connect_batch

**功能**: 批量连接多个已打开的浏览器实例  
**请求体**:

```json
{
  "connections": [
    { "user_id": "user1", "port": 9001 },
    { "user_id": "user2", "port": 9002 }
  ]
}
```

**返回值**:

```json
{
  "results": [
    {
      "user_id": "user1",
      "status": "connected",
      "port": 9001,
      "message": "成功连接到端口 9001 上的浏览器实例"
    }
  ]
}
```

#### GET /api/detect_browser/{port}

**功能**: 检测指定端口是否有浏览器实例运行  
**路径参数**:

- `port` (int): 要检测的端口号

**返回值**:

```json
{
  "port": 9001,
  "status": "browser_detected",
  "tabs_count": 3,
  "message": "端口 9001 上检测到浏览器实例，共 3 个标签页"
}
```

**状态说明**:

- `browser_detected`: 检测到浏览器
- `not_browser`: 端口被占用但不是浏览器
- `port_free`: 端口空闲
- `connection_failed`: 连接失败

### 4. 扩展管理

#### GET /api/extensions/status

**功能**: 获取扩展服务状态  
**参数**: 无  
**返回值**:

```json
{
  "status": "running",
  "loaded_extensions": [],
  "message": "Extensions service is running"
}
```

#### GET /api/extensions/{user_id}

**功能**: 获取指定用户浏览器的扩展状态  
**路径参数**:

- `user_id` (string): 用户 ID

**返回值**:

```json
{
  "user_id": "user1",
  "browser_running": true,
  "port": 9001,
  "tab_url": "https://example.com",
  "extension_check": {
    "url": "https://example.com",
    "chrome_available": true,
    "runtime_available": true,
    "extensions": [
      {
        "component": "playwright_manager",
        "status": "active",
        "type": "chrome_extension_api"
      }
    ]
  },
  "configured_extensions": ["live_room (直播中控)", "block_videos (视频屏蔽器)"],
  "message": "扩展状态检查完成"
}
```

### 5. 任务调度

#### GET /api/scheduler/recent

**功能**: 获取最近的任务  
**参数**: 无  
**返回值**:

```json
{
  "tasks": [],
  "message": "No recent tasks"
}
```

### 6. 系统管理

#### GET /api/system/logs

**功能**: 获取系统日志  
**查询参数**:

- `limit` (int, 默认 10): 日志条数限制

**返回值**:

```json
{
  "logs": [],
  "message": "No logs available"
}
```

#### GET /api/settings/ui

**功能**: 获取 UI 设置  
**参数**: 无  
**返回值**:

```json
{
  "settings": {
    "theme": "light",
    "language": "zh-CN",
    "sidebarCollapsed": false
  },
  "message": "UI settings loaded successfully"
}
```

#### POST /api/settings/ui

**功能**: 保存 UI 设置  
**请求体**: 设置对象  
**返回值**:

```json
{
  "success": true,
  "message": "UI settings saved successfully"
}
```

## 核心功能模块

### 浏览器管理器 (PlaywrightManager)

- 负责单个浏览器实例的生命周期管理
- 支持端口分配和浏览器初始化
- 提供浏览器状态检查功能

### 浏览器存储 (browser_store)

- 全局浏览器实例存储管理
- 支持添加、获取、删除浏览器实例
- 提供实例计数和批量操作

### 异步任务处理

- 使用 `asyncio.to_thread` 处理阻塞操作
- 支持并发浏览器启动和管理
- 异步日志记录和错误处理

## 错误处理

### HTTP 异常

- **404**: 资源不存在（如用户浏览器实例未运行）
- **500**: 服务器内部错误（如浏览器启动失败）
- **400**: 请求参数错误（如批量连接参数缺失）

### 日志记录

- 使用统一的日志记录器 `get_logger(__name__)`
- 记录关键操作和错误信息
- 支持调试模式详细日志输出

## 安全特性

### CORS 配置

- 允许所有来源的跨域请求
- 支持所有 HTTP 方法和头部
- 启用凭据传递

### 端口管理

- 动态端口分配（从 9000 开始递增）
- 端口占用检测和验证
- 防止端口冲突

## 扩展性设计

### 模块化架构

- API 路由分离（business_router, scheduler_router, chrome_config_router）
- 独立的浏览器管理模块
- 可插拔的扩展系统

### 配置管理

- 支持静态文件和模板配置
- 环境变量和配置文件支持
- 资源路径动态解析

## 使用示例

### 启动单个浏览器

```bash
curl -X POST "http://127.0.0.1:8000/api/start/user1?url=https://example.com"
```

### 批量启动浏览器

```bash
curl -X POST "http://127.0.0.1:8000/api/start_all?user_ids=user1&user_ids=user2&url=https://example.com"
```

### 连接现有浏览器

```bash
curl -X POST "http://127.0.0.1:8000/api/connect/user1?port=9001"
```

### 批量连接浏览器

```bash
curl -X POST "http://127.0.0.1:8000/api/connect_batch" \
  -H "Content-Type: application/json" \
  -d '{"connections": [{"user_id": "user1", "port": 9001}]}'
```

### 检测浏览器实例

```bash
curl "http://127.0.0.1:8000/api/detect_browser/9001"
```

## 性能优化

### 异步处理

- 所有 I/O 操作使用异步模式
- 并发浏览器管理
- 非阻塞的网络请求处理

### 资源管理

- 自动浏览器实例清理
- 内存使用优化
- 连接池管理

## 监控和调试

### 健康检查

- 提供多层次的状态检查接口
- 实时监控浏览器实例状态
- 扩展运行状态检测

### 调试支持

- 详细的错误日志记录
- JavaScript 执行结果跟踪
- 网络连接状态监控

---

**注意**: 本文档基于当前版本的 `api_server.py` 文件生成，如有更新请及时同步文档内容。
