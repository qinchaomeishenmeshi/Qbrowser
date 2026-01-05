# 清简浏览器 API 服务器文档

## 概述

清简浏览器 API 服务器是一个基于 FastAPI 的浏览器管理服务，提供浏览器实例的启动、停止、连接和管理功能。本文档详细描述了所有可用的 API 接口。

## 技术栈

- **框架**: FastAPI
- **异步支持**: asyncio
- **浏览器引擎**: Playwright (Chromium)
- **模板引擎**: Jinja2
- **CORS**: 支持跨域请求

## 服务器配置

- **默认地址**: http://127.0.0.1:8000
- **API 前缀**: /api
- **文档地址**: http://127.0.0.1:8000/docs
- **静态文件**: /static

---

## API 接口详情

### 1. 健康检查接口

#### GET /api/health

- **功能**: 系统健康检查
- **参数**: 无
- **返回值**:
  ```json
  {
    "status": "ok",
    "message": "Backend is running"
  }
  ```
- **说明**: 用于检查服务是否正常运行

---

### 2. 浏览器管理接口

#### GET /api/browser/status

- **功能**: 获取浏览器服务详细状态
- **参数**: 无
- **返回值**:
  ```json
  {
    "status": "running",
    "total_instances": 5,
    "active_instances": 3,
    "message": "Browser service is running"
  }
  ```
- **说明**: 返回浏览器服务状态、总实例数和活跃实例数

#### GET /api/active_instances

- **功能**: 获取所有活跃的浏览器实例
- **参数**: 无
- **返回值**:
  ```json
  {
    "status": "success",
    "active_count": 3,
    "active_instances": ["user1", "user2", "user3"]
  }
  ```
- **说明**: 返回当前运行中的浏览器实例用户 ID 列表

#### POST /api/start/{user_id}

- **功能**: 启动指定用户的浏览器实例
- **参数**:
  - `user_id` (路径参数): 用户 ID
  - `url` (查询参数，可选): 要打开的页面 URL
- **返回值**:
  ```json
  {
    "user_id": "user1",
    "status": "success",
    "port": 9001,
    "opened_url": "https://example.com"
  }
  ```
- **状态码**:
  - `success`: 新实例启动成功
  - `already_running`: 实例已存在
  - `fail`: 启动失败
  - `error`: 启动过程中出错

#### POST /api/start_all

- **功能**: 批量启动多个浏览器实例
- **参数**:
  - `user_ids` (查询参数): 用户 ID 列表
  - `url` (查询参数，可选): 要打开的页面 URL
- **返回值**:
  ```json
  {
    "results": [
      {
        "user_id": "user1",
        "status": "success",
        "port": 9001
      }
    ]
  }
  ```

#### POST /api/stop

- **功能**: 停止所有浏览器实例
- **参数**: 无
- **返回值**:
  ```json
  {
    "status": "success",
    "message": "所有浏览器已关闭"
  }
  ```

---

### 3. 浏览器连接管理接口

#### POST /api/connect/{user_id}

- **功能**: 连接到已打开的浏览器实例
- **参数**:
  - `user_id` (路径参数): 用户 ID
  - `port` (查询参数): 浏览器运行的端口号
- **返回值**:
  ```json
  {
    "user_id": "user1",
    "status": "connected",
    "port": 9001,
    "message": "成功连接到端口 9001 上的浏览器实例"
  }
  ```
- **状态码**:
  - `connected`: 连接成功
  - `already_connected`: 已存在连接
  - `connection_failed`: 连接失败
  - `connection_error`: 连接过程中出错

#### POST /api/connect_batch

- **功能**: 批量连接多个已打开的浏览器实例
- **参数** (请求体):
  ```json
  {
    "connections": [
      { "user_id": "user1", "port": 9001 },
      { "user_id": "user2", "port": 9002 }
    ]
  }
  ```
- **返回值**:
  ```json
  {
    "results": [
      {
        "user_id": "user1",
        "status": "connected",
        "port": 9001,
        "message": "成功连接"
      }
    ]
  }
  ```

#### GET /api/detect_browser/{port}

- **功能**: 检测指定端口是否有浏览器实例运行
- **参数**:
  - `port` (路径参数): 要检测的端口号
- **返回值**:
  ```json
  {
    "port": 9001,
    "status": "browser_detected",
    "tabs_count": 3,
    "message": "端口 9001 上检测到浏览器实例，共 3 个标签页"
  }
  ```
- **状态码**:
  - `browser_detected`: 检测到浏览器
  - `not_browser`: 端口被占用但不是浏览器
  - `port_free`: 端口未被占用
  - `connection_failed`: 连接失败
  - `detection_error`: 检测过程中出错

---

### 4. 扩展管理接口

#### GET /api/extensions/status

- **功能**: 获取全局扩展状态
- **参数**: 无
- **返回值**:
  ```json
  {
    "status": "running",
    "total_browsers": 3,
    "configured_extensions": ["live_room (直播中控)", "block_videos (视频屏蔽器)"],
    "message": "扩展服务运行中，3 个浏览器实例活跃"
  }
  ```

#### GET /api/extensions/{user_id}

- **功能**: 获取指定用户浏览器的扩展状态
- **参数**:
  - `user_id` (路径参数): 用户 ID
- **返回值**:
  ```json
  {
    "user_id": "user1",
    "browser_running": true,
    "port": 9001,
    "tab_url": "https://example.com",
    "extension_check": {
      "url": "https://example.com",
      "extensions": [],
      "chrome_available": true
    },
    "configured_extensions": ["live_room (直播中控)", "block_videos (视频屏蔽器)"],
    "message": "扩展状态检查完成"
  }
  ```

---

### 5. 任务调度接口

#### GET /api/scheduler/recent

- **功能**: 获取最近的任务记录
- **参数**: 无
- **返回值**:
  ```json
  {
    "tasks": [],
    "total_count": 0,
    "message": "暂无最近任务记录",
    "note": "此接口需要集成任务调度系统后才能返回真实数据"
  }
  ```
- **说明**: 当前返回空数据，需要后续集成任务调度系统

---

### 6. 系统管理接口

#### GET /api/system/logs

- **功能**: 获取系统日志
- **参数**:
  - `limit` (查询参数，可选): 日志条数限制，默认 10
- **返回值**:
  ```json
  {
    "logs": [
      {
        "timestamp": "2024-01-20T10:30:00.123456",
        "level": "INFO",
        "message": "系统运行正常，当前活跃浏览器实例: 3 个",
        "component": "playwright_manager"
      }
    ],
    "total_count": 1,
    "limit": 10,
    "message": "系统日志获取成功",
    "note": "此接口需要集成日志系统后才能返回完整的历史日志"
  }
  ```

---

### 7. UI 设置接口

#### GET /api/settings/ui

- **功能**: 获取 UI 设置
- **参数**: 无
- **返回值**:
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

- **功能**: 保存 UI 设置
- **参数** (请求体):
  ```json
  {
    "theme": "dark",
    "language": "zh-CN",
    "sidebarCollapsed": true
  }
  ```
- **返回值**:
  ```json
  {
    "success": true,
    "message": "UI settings saved successfully"
  }
  ```

---

## 页面路由

### GET /

- **功能**: 根路径，重定向到定时任务管理界面
- **返回**: HTML 页面

### GET /scheduler/dashboard

- **功能**: 定时任务管理界面
- **返回**: HTML 页面

### GET /chrome/config

- **功能**: Chrome 配置管理界面
- **返回**: HTML 页面

---

## 错误处理

### HTTP 状态码

- `200`: 请求成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

---

## 使用示例

### 启动浏览器实例

```bash
curl -X POST "http://127.0.0.1:8000/api/start/user1?url=https://example.com"
```

### 连接现有浏览器

```bash
curl -X POST "http://127.0.0.1:8000/api/connect/user1?port=9001"
```

### 批量连接浏览器

```bash
curl -X POST "http://127.0.0.1:8000/api/connect_batch" \
  -H "Content-Type: application/json" \
  -d '{
    "connections": [
      {"user_id": "user1", "port": 9001},
      {"user_id": "user2", "port": 9002}
    ]
  }'
```

### 检测端口浏览器

```bash
curl "http://127.0.0.1:8000/api/detect_browser/9001"
```

---

## 注意事项

1. **端口管理**: 浏览器实例使用 9000+ 端口，请确保端口未被占用
2. **并发限制**: 建议控制同时运行的浏览器实例数量
3. **资源清理**: 及时停止不需要的浏览器实例以释放资源
4. **扩展检查**: 扩展状态检查需要页面完全加载后才能获取准确结果
5. **开发中功能**: 部分接口（如日志、任务调度）需要后续完善

---

## 更新日志

### v1.1 (最新)

- 移除重复的 `/api/status` 接口
- 优化 `/api/extensions/status` 接口，添加活跃浏览器统计
- 改进 `/api/scheduler/recent` 接口，添加开发说明
- 增强 `/api/system/logs` 接口，提供实时系统状态
- 统一错误信息为中文，提升用户体验

### v1.0

- 初始版本，包含基础浏览器管理功能
- 支持浏览器启动、停止、连接操作
- 提供扩展状态检查功能
