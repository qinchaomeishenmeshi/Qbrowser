#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务使用示例

展示如何使用定时任务功能来自动化直播间数据采集：
1. 创建不同类型的定时任务
2. 管理任务状态
3. 查看执行结果

运行前请确保：
1. 已安装所需依赖：pip install apscheduler fastapi uvicorn
2. 已配置好浏览器和 cookies
3. 已启动定时任务服务：python start_scheduler_server.py
"""

import asyncio
import json
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from worker.scheduler_client import (
    scheduler_client,
    create_cron_task,
    create_interval_task
)
from utils.common_logger import get_logger

logger = get_logger(__name__)


async def example_1_create_cron_tasks():
    """示例1：创建 Cron 定时任务"""
    print("\n=== 示例1：创建 Cron 定时任务 ===")
    
    # 每30分钟获取直播间核心数据
    success = await create_cron_task(
        task_id="core_data_30min",
        name="直播间核心数据监控（30分钟）",
        description="每30分钟获取指定直播间的核心数据",
        cron_expression="0 */30 * * * *",  # 每30分钟执行
        target_function="get_core_data",
        function_params={
            "user_id": "001",
            "room_id": "7318296342189853503",
            "user_name": "测试用户",
            "buyin_account_id": "123456"
        },
        enabled=True
    )
    print(f"✅ 30分钟核心数据任务创建: {'成功' if success else '失败'}")
    
    # 每天8点获取历史直播列表
    success = await create_cron_task(
        task_id="history_daily_8am",
        name="历史直播列表（每日8点）",
        description="每天早上8点获取用户历史直播列表",
        cron_expression="0 0 8 * * *",  # 每天8点执行
        target_function="get_history_live_list",
        function_params={
            "user_id": "001"
        },
        enabled=True
    )
    print(f"✅ 每日8点历史列表任务创建: {'成功' if success else '失败'}")
    
    # 工作日每2小时批量获取数据
    success = await create_cron_task(
        task_id="batch_workdays_2h",
        name="批量数据获取（工作日2小时）",
        description="工作日每2小时批量获取多个直播间数据",
        cron_expression="0 0 */2 * * 1-5",  # 工作日每2小时执行
        target_function="get_core_data_main",
        function_params={
            "data": [
                {
                    "user_id": "001",
                    "room_id": "7318296342189853503",
                    "user_name": "用户1",
                    "buyin_account_id": "123456"
                },
                {
                    "user_id": "002",
                    "room_id": "7318296342189853504",
                    "user_name": "用户2",
                    "buyin_account_id": "123457"
                }
            ]
        },
        enabled=True
    )
    print(f"✅ 工作日批量数据任务创建: {'成功' if success else '失败'}")


async def example_2_create_interval_tasks():
    """示例2：创建间隔定时任务"""
    print("\n=== 示例2：创建间隔定时任务 ===")
    
    # 每15分钟获取核心数据（高频监控）
    success = await create_interval_task(
        task_id="core_data_15min",
        name="高频核心数据监控（15分钟）",
        description="每15分钟获取直播间核心数据，用于实时监控",
        interval_seconds=900,  # 15分钟 = 900秒
        target_function="get_core_data",
        function_params={
            "user_id": "001",
            "room_id": "7318296342189853503",
            "user_name": "高频监控用户",
            "buyin_account_id": "123456"
        },
        enabled=False  # 先创建但不启用，避免过于频繁
    )
    print(f"✅ 15分钟高频监控任务创建: {'成功' if success else '失败'}")
    
    # 每小时获取历史列表
    success = await create_interval_task(
        task_id="history_hourly",
        name="历史列表监控（每小时）",
        description="每小时获取用户历史直播列表",
        interval_seconds=3600,  # 1小时 = 3600秒
        target_function="get_history_live_list",
        function_params={
            "user_id": "001"
        },
        enabled=True
    )
    print(f"✅ 每小时历史列表任务创建: {'成功' if success else '失败'}")


async def example_3_manage_tasks():
    """示例3：管理任务状态"""
    print("\n=== 示例3：管理任务状态 ===")
    
    # 获取所有任务配置
    tasks = scheduler_client.get_task_configs()
    print(f"📋 当前共有 {len(tasks)} 个任务:")
    
    for task_id, config in tasks.items():
        status = "启用" if config.enabled else "禁用"
        trigger_info = config.cron_expression if config.trigger_type.value == 'cron' else f"{config.interval_seconds}秒"
        print(f"  - {task_id}: {config.name} ({status}) - {trigger_info}")
    
    # 禁用高频任务（演示）
    if "core_data_15min" in tasks:
        success = await scheduler_client.disable_task("core_data_15min")
        print(f"🔴 禁用高频任务: {'成功' if success else '失败'}")
    
    # 启用一个任务（演示）
    if "core_data_30min" in tasks:
        success = await scheduler_client.enable_task("core_data_30min")
        print(f"🟢 启用30分钟任务: {'成功' if success else '失败'}")


async def example_4_view_results():
    """示例4：查看执行结果"""
    print("\n=== 示例4：查看执行结果 ===")
    
    # 获取最近的执行结果
    results = scheduler_client.get_task_results(limit=10)
    print(f"📊 最近 {len(results)} 次执行结果:")
    
    if not results:
        print("  暂无执行结果")
        return
    
    for result in results:
        status_icon = "✅" if result.get('status') == 'success' else "❌"
        execution_time = result.get('execution_time', 'Unknown')
        task_id = result.get('task_id', 'Unknown')
        
        print(f"  {status_icon} {task_id} - {execution_time}")
        
        if result.get('error_message'):
            print(f"    错误: {result['error_message']}")
        
        if result.get('result_data'):
            print(f"    结果: {str(result['result_data'])[:100]}...")


async def example_5_scheduler_control():
    """示例5：调度器控制"""
    print("\n=== 示例5：调度器控制 ===")
    
    # 检查调度器状态
    is_running = scheduler_client.scheduler.running if scheduler_client.scheduler else False
    print(f"📡 调度器状态: {'运行中' if is_running else '已停止'}")
    
    if not is_running:
        print("🚀 启动调度器...")
        await scheduler_client.start()
        print("✅ 调度器已启动")
    
    # 等待一段时间让任务执行
    print("⏳ 等待任务执行（10秒）...")
    await asyncio.sleep(10)
    
    # 再次查看结果
    await example_4_view_results()


async def example_6_cleanup():
    """示例6：清理演示任务"""
    print("\n=== 示例6：清理演示任务 ===")
    
    # 获取所有演示任务
    demo_task_ids = [
        "core_data_30min",
        "history_daily_8am", 
        "batch_workdays_2h",
        "core_data_15min",
        "history_hourly"
    ]
    
    print("🧹 清理演示任务...")
    for task_id in demo_task_ids:
        if task_id in scheduler_client.task_configs:
            success = await scheduler_client.remove_task(task_id)
            print(f"  - 删除 {task_id}: {'成功' if success else '失败'}")
        else:
            print(f"  - {task_id}: 不存在")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("🕐 定时任务功能使用示例")
    print("="*60)
    
    try:
        # 启动调度器
        await scheduler_client.start()
        print("✅ 调度器已启动")
        
        # 运行示例
        await example_1_create_cron_tasks()
        await example_2_create_interval_tasks()
        await example_3_manage_tasks()
        await example_4_view_results()
        await example_5_scheduler_control()
        
        # 询问是否清理
        print("\n" + "="*60)
        cleanup = input("是否清理演示任务？(y/N): ").lower().strip()
        if cleanup == 'y':
            await example_6_cleanup()
        
        print("\n🎉 示例演示完成！")
        print("\n💡 提示:")
        print("  - 启动 Web 服务: python start_scheduler_server.py")
        print("  - 访问管理界面: http://localhost:8000/scheduler/dashboard")
        print("  - 查看 API 文档: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"示例运行失败: {e}")
        print(f"❌ 示例运行失败: {e}")
    
    finally:
        # 停止调度器
        await scheduler_client.stop()
        print("🛑 调度器已停止")


if __name__ == "__main__":
    asyncio.run(main())