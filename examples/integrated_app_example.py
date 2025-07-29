#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成定时任务的应用使用示例

本示例展示如何使用集成了定时任务功能的主应用程序：
1. 启动应用时自动启动定时任务服务
2. 创建和管理定时任务
3. 监控任务执行状态
4. 应用关闭时自动停止定时任务服务

使用方法：
1. 直接运行主应用：python app.py
2. 或运行本示例：python examples/integrated_app_example.py
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker.scheduler_client import (
    scheduler_client,
    create_cron_task,
    create_interval_task
)
from utils.common_logger import get_logger

logger = get_logger(__name__)


async def demo_scheduler_integration():
    """
    演示定时任务集成功能
    
    注意：当你运行 app.py 时，定时任务服务会自动启动，
    你可以通过以下方式与之交互：
    """
    print("\n=== 定时任务集成演示 ===")
    print("\n[INFO] 当前应用集成状态：")
    
    # 检查调度器状态
    is_running = scheduler_client.scheduler.running if scheduler_client.scheduler else False
    print(f"  - 调度器运行状态: {'[OK] 运行中' if is_running else '[ERROR] 未运行'}")
    
    if not is_running:
        print("\n[WARNING] 调度器未运行，请先启动主应用 (python app.py)")
        return
    
    # 显示当前任务配置
    tasks = scheduler_client.get_task_configs()
    print(f"  - 当前任务数量: {len(tasks)}")
    
    if tasks:
        print("\n[INFO] 当前任务列表：")
        for task in tasks:
            status = "[OK] 启用" if task['enabled'] else "[ERROR] 禁用"
            print(f"  - {task['name']} ({task['task_id']}): {status}")
    
    # 创建示例任务（如果不存在）
    print("\n[INFO] 创建示例任务...")
    
    # 创建一个简单的定时任务
    demo_task_id = "demo_integrated_task"
    existing_tasks = {task['task_id'] for task in tasks}
    
    if demo_task_id not in existing_tasks:
        success = await create_interval_task(
            task_id=demo_task_id,
            name="集成演示任务",
            description="演示应用集成定时任务功能",
            target_function="get_core_data_main",
            interval_seconds=300,  # 5分钟执行一次
            function_params={"user_ids": ["demo_user"]}
        )
        
        if success:
            print(f"  [OK] 创建任务成功: {demo_task_id}")
        else:
            print(f"  [ERROR] 创建任务失败: {demo_task_id}")
    else:
        print(f"  ℹ️  任务已存在: {demo_task_id}")
    
    # 显示最近的执行结果
    print("\n[INFO] 最近执行结果：")
    results = scheduler_client.get_task_results(limit=5)
    
    if results:
        for result in results:
            status_icon = "[OK]" if result['status'] == 'SUCCESS' else "[ERROR]" if result['status'] == 'FAILED' else "[INFO]"
            print(f"  {status_icon} {result['task_id']} - {result['start_time']}")
    else:
        print("  [INFO] 暂无执行记录")
    
    print("\n[INFO] 提示：")
    print("  - 主应用启动时会自动启动定时任务服务")
    print("  - 应用关闭时会自动停止定时任务服务")
    print("  - 可以通过 Web 界面管理任务: http://localhost:8000/scheduler/dashboard")
    print("  - 任务配置保存在: data/scheduler/task_configs.json")
    print("  - 执行结果保存在: data/scheduler/task_results.json")


async def main():
    """
    主函数
    """
    print("[INFO] 定时任务集成功能演示")
    print("\n说明：")
    print("  本演示展示了如何在主应用中集成定时任务功能。")
    print("  现在你只需要运行 'python app.py'，就可以同时获得：")
    print("  1. 浏览器管理功能")
    print("  2. FastAPI 服务 (端口 6001)")
    print("  3. 定时任务调度服务")
    print("  4. frpc 服务 (仅 Windows)")
    
    try:
        await demo_scheduler_integration()
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"\n[ERROR] 演示失败: {e}")
    
    print("\n[INFO] 下一步：")
    print("  1. 运行主应用: python app.py")
    print("  2. 访问管理界面: http://localhost:8000/scheduler/dashboard")
    print("  3. 创建和管理你的定时任务")


if __name__ == "__main__":
    asyncio.run(main())