# 🕐 定时任务功能使用指南

本文档介绍如何使用定时任务功能来自动化直播间数据采集。

## 📋 功能概述

定时任务系统提供以下核心功能：

- ⏰ **Cron 定时任务**：基于 Cron 表达式的精确时间调度
- 🔄 **间隔定时任务**：基于固定时间间隔的循环执行
- 🎛️ **Web 管理界面**：直观的任务管理和监控面板
- 📡 **RESTful API**：完整的任务管理 API 接口
- 📊 **执行结果追踪**：详细的任务执行历史和状态监控
- 🔧 **任务模板**：预定义的常用任务配置模板

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装定时任务相关依赖
pip install -r requirements_scheduler.txt
```

### 2. 启动服务

```bash
# 启动定时任务服务
python start_scheduler_server.py
```

服务启动后，你可以访问：

- 🎛️ **管理界面**: http://localhost:8000/scheduler/dashboard
- 📖 **API 文档**: http://localhost:8000/docs
- 🔍 **健康检查**: http://localhost:8000/health

### 3. 运行示例

```bash
# 运行使用示例（可选）
python examples/scheduler_examples.py
```

## 🎛️ Web 管理界面使用

### 界面功能

1. **状态监控**：实时显示调度器状态和任务统计
2. **任务创建**：通过表单创建 Cron 或间隔定时任务
3. **任务管理**：启用、禁用、删除已创建的任务
4. **执行结果**：查看最近的任务执行历史
5. **调度器控制**：启动、停止调度器服务

### 创建任务步骤

1. 选择任务类型（Cron 或间隔）
2. 填写任务基本信息（ID、名称、描述）
3. 设置触发条件：
   - **Cron 任务**：填写 Cron 表达式
   - **间隔任务**：设置间隔秒数
4. 选择目标函数和参数
5. 点击创建任务

### Cron 表达式示例

```
# 格式：秒 分 时 日 月 周
0 */30 * * * *    # 每30分钟执行
0 0 8 * * *      # 每天8点执行
0 0 0 1 * *      # 每月1号执行
0 0 9 * * 1-5    # 工作日9点执行
0 */15 9-17 * * 1-5  # 工作日9-17点每15分钟执行
```

## 📡 API 接口使用

### 创建 Cron 定时任务

```bash
curl -X POST "http://localhost:8000/scheduler/tasks/cron" \
     -H "Content-Type: application/json" \
     -d '{
       "task_id": "core_data_30min",
       "name": "直播间核心数据监控",
       "description": "每30分钟获取直播间核心数据",
       "cron_expression": "0 */30 * * * *",
       "target_function": "get_core_data",
       "function_params": {
         "user_id": "001",
         "room_id": "7318296342189853503"
       },
       "enabled": true
     }'
```

### 创建间隔定时任务

```bash
curl -X POST "http://localhost:8000/scheduler/tasks/interval" \
     -H "Content-Type: application/json" \
     -d '{
       "task_id": "history_hourly",
       "name": "历史列表监控",
       "description": "每小时获取历史直播列表",
       "interval_seconds": 3600,
       "target_function": "get_history_live_list",
       "function_params": {
         "user_id": "001"
       },
       "enabled": true
     }'
```

### 管理任务

```bash
# 获取所有任务
curl "http://localhost:8000/scheduler/tasks"

# 启用任务
curl -X POST "http://localhost:8000/scheduler/tasks/enable" \
     -H "Content-Type: application/json" \
     -d '{"task_id": "core_data_30min"}'

# 禁用任务
curl -X POST "http://localhost:8000/scheduler/tasks/disable" \
     -H "Content-Type: application/json" \
     -d '{"task_id": "core_data_30min"}'

# 删除任务
curl -X DELETE "http://localhost:8000/scheduler/tasks/core_data_30min"
```

### 查看执行结果

```bash
# 获取所有执行结果
curl "http://localhost:8000/scheduler/results?limit=50"

# 获取特定任务的执行结果
curl "http://localhost:8000/scheduler/tasks/core_data_30min/results?limit=20"
```

## 🔧 编程接口使用

### 基本使用

```python
import asyncio
from worker.scheduler_client import (
    scheduler_client,
    create_cron_task,
    create_interval_task
)

async def main():
    # 启动调度器
    await scheduler_client.start()
    
    # 创建 Cron 任务
    await create_cron_task(
        task_id="daily_report",
        name="每日数据报告",
        cron_expression="0 0 8 * * *",  # 每天8点
        target_function="get_core_data",
        function_params={"user_id": "001", "room_id": "123456"}
    )
    
    # 创建间隔任务
    await create_interval_task(
        task_id="realtime_monitor",
        name="实时监控",
        interval_seconds=1800,  # 30分钟
        target_function="get_history_live_list",
        function_params={"user_id": "001"}
    )
    
    # 管理任务
    await scheduler_client.enable_task("daily_report")
    await scheduler_client.disable_task("realtime_monitor")
    
    # 查看结果
    results = scheduler_client.get_task_results(limit=10)
    for result in results:
        print(f"任务: {result['task_id']}, 状态: {result['status']}")

asyncio.run(main())
```

### 高级配置

```python
from worker.scheduler_client import TaskConfig, TriggerType

# 手动创建任务配置
config = TaskConfig(
    task_id="custom_task",
    name="自定义任务",
    description="高级配置示例",
    trigger_type=TriggerType.CRON,
    cron_expression="0 */15 * * * *",
    target_function="get_core_data",
    function_params={
        "user_id": "001",
        "room_id": "123456",
        "extra_config": {
            "timeout": 30,
            "retry_count": 3
        }
    },
    enabled=True
)

# 添加到调度器
await scheduler_client.add_task(config)
```

## 📊 任务模板

系统提供了预定义的任务模板，可以通过 API 获取：

```bash
curl "http://localhost:8000/scheduler/templates"
```

### 常用模板

#### 1. 直播间数据监控

```json
{
  "name": "直播间数据监控",
  "target_function": "get_core_data",
  "function_params": {
    "user_id": "请填写用户ID",
    "room_id": "请填写直播间ID"
  },
  "cron_examples": {
    "每30分钟": "0 */30 * * * *",
    "每小时": "0 0 * * * *",
    "每天8点": "0 0 8 * * *"
  }
}
```

#### 2. 历史直播列表监控

```json
{
  "name": "历史直播列表监控",
  "target_function": "get_history_live_list",
  "function_params": {
    "user_id": "请填写用户ID"
  },
  "cron_examples": {
    "每小时": "0 0 * * * *",
    "每天8点": "0 0 8 * * *"
  }
}
```

#### 3. 批量数据获取

```json
{
  "name": "批量数据获取",
  "target_function": "get_core_data_main",
  "function_params": {
    "data": [
      {
        "user_id": "001",
        "room_id": "123456",
        "user_name": "用户1",
        "buyin_account_id": "账户1"
      }
    ]
  }
}
```

## 🗂️ 文件结构

```
qw-browser/
├── worker/
│   └── scheduler_client.py          # 定时任务核心模块
├── api/
│   └── scheduler_api.py             # RESTful API 接口
├── templates/
│   └── scheduler_dashboard.html     # Web 管理界面
├── examples/
│   └── scheduler_examples.py        # 使用示例
├── data/
│   ├── tasks/                       # 任务配置存储
│   └── results/                     # 执行结果存储
├── start_scheduler_server.py        # 服务启动脚本
├── requirements_scheduler.txt       # 依赖包列表
└── README_SCHEDULER.md             # 本文档
```

## ⚙️ 配置说明

### 环境变量

```bash
# 可选配置
export SCHEDULER_HOST=0.0.0.0        # 服务监听地址
export SCHEDULER_PORT=8000            # 服务端口
export SCHEDULER_LOG_LEVEL=info       # 日志级别
export SCHEDULER_DATA_DIR=./data      # 数据存储目录
```

### 日志配置

日志文件位置：`logs/scheduler.log`

可以通过修改 `utils/common_logger.py` 来调整日志配置。

## 🔍 故障排除

### 常见问题

#### 1. 调度器无法启动

**问题**：调度器启动失败

**解决方案**：
- 检查依赖是否正确安装
- 确认端口 8000 未被占用
- 查看日志文件获取详细错误信息

#### 2. 任务不执行

**问题**：创建的任务不执行

**解决方案**：
- 确认调度器处于运行状态
- 检查任务是否已启用
- 验证 Cron 表达式或间隔时间设置
- 检查目标函数是否存在

#### 3. Cookie 相关错误

**问题**：任务执行时出现 Cookie 错误

**解决方案**：
- 确认已正确配置浏览器 cookies
- 检查 `data/cookies` 目录下的 cookie 文件
- 验证 `site_key` 参数是否正确

#### 4. 函数参数错误

**问题**：函数参数格式错误

**解决方案**：
- 确保 `function_params` 是有效的 JSON 格式
- 检查参数名称和类型是否匹配目标函数
- 参考任务模板中的参数示例

### 调试技巧

1. **查看日志**：
   ```bash
   tail -f logs/scheduler.log
   ```

2. **检查任务状态**：
   ```bash
   curl "http://localhost:8000/scheduler/status"
   ```

3. **查看执行结果**：
   ```bash
   curl "http://localhost:8000/scheduler/results?limit=10"
   ```

4. **手动测试函数**：
   ```python
   from living_client import LivingClient
   
   client = LivingClient()
   result = client.get_core_data(user_id="001", room_id="123456")
   print(result)
   ```

## 🔒 安全注意事项

1. **访问控制**：生产环境建议配置访问控制和身份验证
2. **数据保护**：敏感数据（如 cookies）应加密存储
3. **网络安全**：建议使用 HTTPS 和防火墙保护
4. **权限管理**：限制文件系统访问权限

## 📈 性能优化

1. **任务频率**：避免设置过于频繁的任务执行
2. **并发控制**：合理设置任务并发数量
3. **资源监控**：监控 CPU 和内存使用情况
4. **日志管理**：定期清理旧的日志和结果文件

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进定时任务功能！

## 📄 许可证

本项目采用 MIT 许可证。