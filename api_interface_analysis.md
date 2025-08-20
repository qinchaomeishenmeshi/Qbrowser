# API 接口分析报告

## 当前接口列表

### 1. 健康检查和状态接口
- `GET /api/health` - 健康检查端点
- `GET /api/status` - 获取服务状态（返回用户数量）
- `GET /api/browser/status` - 获取浏览器状态（详细信息）

### 2. 浏览器管理接口
- `POST /api/start/{user_id}` - 启动单个浏览器实例
- `POST /api/start_all` - 批量启动浏览器实例
- `POST /api/stop` - 停止所有浏览器实例
- `GET /api/active_instances` - 获取所有激活的浏览器实例

### 3. 浏览器连接接口（新增）
- `POST /api/connect/{user_id}` - 连接到已打开的浏览器实例
- `POST /api/connect_batch` - 批量连接多个已打开的浏览器实例
- `GET /api/detect_browser/{port}` - 检测指定端口是否有浏览器实例运行

### 4. 扩展管理接口
- `GET /api/extensions/status` - 获取扩展状态（通用）
- `GET /api/extensions/{user_id}` - 获取指定用户浏览器的扩展状态

### 5. 任务调度接口
- `GET /api/scheduler/recent` - 获取最近的任务

### 6. 系统管理接口
- `GET /api/system/logs` - 获取系统日志

### 7. UI设置接口
- `GET /api/settings/ui` - 获取UI设置
- `POST /api/settings/ui` - 保存UI设置

### 8. 页面路由
- `GET /` - 根路径重定向到定时任务管理界面
- `GET /scheduler/dashboard` - 定时任务管理界面
- `GET /chrome/config` - Chrome配置管理界面

## 重复接口分析

### 🔴 发现的重复接口

#### 1. 状态检查接口重复
- `GET /api/status` 和 `GET /api/browser/status` 功能重叠
  - `/api/status` 返回简单的用户数量
  - `/api/browser/status` 返回详细的浏览器状态信息
  - **建议**: 保留 `/api/browser/status`，移除 `/api/status`

#### 2. 健康检查接口冗余
- `GET /api/health` 和 `/api/browser/status` 都可以用于健康检查
  - **建议**: 保留 `/api/health` 作为轻量级健康检查，`/api/browser/status` 用于详细状态

### 🟡 功能相似但保留的接口

#### 1. 浏览器启动接口
- `POST /api/start/{user_id}` - 单个启动
- `POST /api/start_all` - 批量启动
- **分析**: 功能互补，都需要保留

#### 2. 浏览器连接接口
- `POST /api/connect/{user_id}` - 单个连接
- `POST /api/connect_batch` - 批量连接
- **分析**: 功能互补，都需要保留

#### 3. 扩展状态接口
- `GET /api/extensions/status` - 通用扩展状态
- `GET /api/extensions/{user_id}` - 特定用户扩展状态
- **分析**: 功能不同，都需要保留

## 优化建议

### 需要移除的接口
1. `GET /api/status` - 功能被 `/api/browser/status` 覆盖

### 需要优化的接口
1. `GET /api/scheduler/recent` - 当前返回空数据，需要实现或移除
2. `GET /api/system/logs` - 当前返回空数据，需要实现或移除
3. `GET /api/extensions/status` - 当前返回空数据，需要实现或移除

### 接口命名优化建议
1. 保持 RESTful 风格一致性
2. 使用复数形式表示资源集合
3. 使用动词表示操作

## 最终优化方案

### 保留的核心接口（共17个）

#### 健康检查 (1个)
- `GET /api/health`

#### 浏览器管理 (6个)
- `GET /api/browser/status`
- `GET /api/active_instances`
- `POST /api/start/{user_id}`
- `POST /api/start_all`
- `POST /api/stop`
- `GET /api/detect_browser/{port}`

#### 浏览器连接 (2个)
- `POST /api/connect/{user_id}`
- `POST /api/connect_batch`

#### 扩展管理 (2个)
- `GET /api/extensions/status`
- `GET /api/extensions/{user_id}`

#### 系统管理 (2个)
- `GET /api/scheduler/recent`
- `GET /api/system/logs`

#### UI设置 (2个)
- `GET /api/settings/ui`
- `POST /api/settings/ui`

#### 页面路由 (3个)
- `GET /`
- `GET /scheduler/dashboard`
- `GET /chrome/config`

### 需要移除的接口 (1个)
- `GET /api/status` - 被 `/api/browser/status` 替代