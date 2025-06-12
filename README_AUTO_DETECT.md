# 定时任务自动检测活跃浏览器实例功能

## 🎯 功能概述

本功能实现了定时任务中自动获取当前活跃的浏览器实例，无需手动维护设备列表，大大提升了任务配置的智能化和自动化水平。

## ✨ 主要特性

- **🔄 动态检测**：实时获取正在运行的浏览器实例
- **🎛️ 灵活配置**：支持自动检测、环境变量、固定列表三种模式
- **🔧 向后兼容**：完全兼容现有的固定设备列表配置
- **📊 智能日志**：详细记录检测过程和结果
- **⚡ 高效执行**：避免对已关闭浏览器的无效调用

## 🚀 使用方法

### 1. 自动检测模式（推荐）

在任务配置的 `function_params` 中设置：

```json
{
  "function_params": {
    "deviceNoList": "{{AUTO_DETECT}}"
  }
}
```

### 2. 环境变量模式

```json
{
  "function_params": {
    "deviceNoList": ["{{DEVICE_LIST}}"]
  }
}
```

### 3. 固定列表模式（原有方式）

```json
{
  "function_params": {
    "deviceNoList": "wh041,wh042,wh043"
  }
}
```

或者：

```json
{
  "function_params": {
    "deviceNoList": ["wh041", "wh042", "wh043"]
  }
}
```

## 📋 完整配置示例

### EOS 直播复盘记录（自动检测）

```json
{
  "task_id": "eos1_auto",
  "name": "eos直播复盘记录（自动检测设备）",
  "description": "使用自动检测功能获取活跃浏览器实例",
  "trigger_type": "cron",
  "trigger_config": {
    "second": "0",
    "minute": "0",
    "hour": "10",
    "day": "*",
    "month": "*",
    "day_of_week": "*"
  },
  "target_function": "get_live_room_list_main",
  "function_params": {
    "deviceNoList": "{{AUTO_DETECT}}"
  },
  "enabled": true,
  "max_instances": 1
}
```

### 直播间核心数据监控（自动检测）

```json
{
  "task_id": "core_data_auto",
  "name": "直播间核心数据监控（自动检测设备）",
  "description": "每30分钟获取活跃设备的直播间核心数据",
  "trigger_type": "cron",
  "trigger_config": {
    "second": "0",
    "minute": "*/30",
    "hour": "*",
    "day": "*",
    "month": "*",
    "day_of_week": "*"
  },
  "target_function": "get_core_data_main",
  "function_params": {
    "deviceNoList": "{{AUTO_DETECT}}",
    "data": {
      "room_id": "7512002735768865571"
    }
  },
  "enabled": true,
  "max_instances": 1
}
```

## 🔍 工作原理

1. **检测触发**：当任务执行时，系统检查 `deviceNoList` 参数
2. **条件判断**：如果值为 `{{AUTO_DETECT}}` 或 `["{{DEVICE_LIST}}"]`，触发自动检测
3. **获取实例**：从 `browser_store` 获取所有浏览器管理器实例
4. **状态筛选**：筛选出 `is_running` 为 `true` 的实例
5. **提取ID**：提取这些实例的 `user_id`（设备号）
6. **参数替换**：将检测到的设备列表替换原参数值
7. **执行任务**：使用新的设备列表执行具体的业务逻辑

## 📊 返回值示例

### 生产环境示例
```python
# 返回活跃设备列表
['wh041', 'wh042', 'wh045', 'wh048', 'wh052']
```

### 测试环境示例
```python
# 返回测试设备列表
['test001', 'test002', 'test005']
```

### 空列表情况
```python
# 无活跃浏览器时返回空列表
[]
```

## ⚠️ 注意事项

### 1. 空列表处理
- 当没有活跃浏览器实例时，系统会记录警告日志
- 任务会继续执行，但可能无法获取到有效数据
- 可根据业务需求选择是否在空列表时终止任务

### 2. 错误处理
- 如果获取设备列表过程中出现异常，会返回空列表
- 系统会记录详细的错误日志便于排查
- 建议监控相关日志确保功能正常运行

### 3. 性能考虑
- 每次任务执行都会实时获取设备列表
- 获取过程是异步的，不会阻塞其他任务
- 对于高频任务，建议评估性能影响

## 🔧 配置迁移指南

### 从固定列表迁移到自动检测

**原配置：**
```json
{
  "function_params": {
    "deviceNoList": "wh041,wh042,wh043,wh044,wh045"
  }
}
```

**新配置：**
```json
{
  "function_params": {
    "deviceNoList": "{{AUTO_DETECT}}"
  }
}
```

### 渐进式迁移策略

1. **测试阶段**：创建新的任务ID使用自动检测功能
2. **验证阶段**：对比自动检测和固定列表的执行结果
3. **切换阶段**：确认无误后，更新现有任务配置
4. **清理阶段**：删除不再需要的固定列表配置

## 📈 优势对比

| 特性 | 固定列表模式 | 自动检测模式 |
|------|-------------|-------------|
| 配置复杂度 | 高 | 低 |
| 维护成本 | 高 | 低 |
| 动态适应性 | 无 | 强 |
| 执行效率 | 可能调用无效实例 | 只调用活跃实例 |
| 错误率 | 较高 | 较低 |
| 扩展性 | 差 | 优 |

## 🛠️ 故障排查

### 常见问题

1. **检测到空列表**
   - 检查是否有浏览器实例正在运行
   - 确认 `browser_store` 中是否有注册的管理器
   - 查看浏览器实例的 `is_running` 状态

2. **检测失败**
   - 查看错误日志了解具体异常信息
   - 检查 `browser_store` 的导入和初始化
   - 确认异步调用的正确性

3. **任务执行异常**
   - 确认自动检测的设备列表格式正确
   - 检查后续API调用是否支持动态设备列表
   - 验证设备ID的有效性

### 调试方法

```python
# 手动测试自动检测功能
from worker.scheduler_client import scheduler_client

async def test_auto_detect():
    devices = await scheduler_client._get_active_device_list()
    print(f"检测到的活跃设备: {devices}")

# 在异步环境中运行
import asyncio
asyncio.run(test_auto_detect())
```

## 📝 更新日志

### v1.0.0 (2025-01-27)
- ✅ 实现基础的自动检测功能
- ✅ 支持 `{{AUTO_DETECT}}` 和 `{{DEVICE_LIST}}` 标识符
- ✅ 添加详细的日志记录
- ✅ 提供完整的错误处理机制
- ✅ 保持向后兼容性

---

**💡 提示**：建议在生产环境使用前，先在测试环境充分验证自动检测功能的稳定性和准确性。