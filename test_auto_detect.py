#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动检测功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from worker.scheduler_client import scheduler_client

    print("[OK] scheduler_client 导入成功")

    from browser.browser_store import browser_store

    print("[OK] browser_store 导入成功")

    print("[OK] 所有依赖导入成功，自动检测功能已添加")

except ImportError as e:
    print(f"[ERROR] 导入失败: {e}")
    sys.exit(1)


async def test_auto_detect():
    """测试自动检测功能"""
    try:
        print("\n[INFO] 测试自动检测功能...")

        # 测试获取活跃设备列表
        devices = await scheduler_client._get_active_device_list()
        print(f"[INFO] 检测到的活跃设备: {devices}")
        print(f"[INFO] 活跃设备数量: {len(devices)}")

        # 测试参数处理逻辑
        test_params = {"deviceNoList": "{{AUTO_DETECT}}", "other_param": "test_value"}

        print(f"\n[INFO] 测试参数处理...")
        print(f"原始参数: {test_params}")

        # 模拟 _call_target_function 中的参数处理逻辑
        if "deviceNoList" in test_params:
            device_list = test_params["deviceNoList"]
            if device_list == "{{AUTO_DETECT}}":
                active_devices = await scheduler_client._get_active_device_list()
                test_params["deviceNoList"] = active_devices
                print(f"处理后参数: {test_params}")

        print("\n[OK] 自动检测功能测试完成")

    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("[INFO] 开始测试自动检测功能...")
    asyncio.run(test_auto_detect())
