#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础依赖测试脚本
用于验证项目的核心依赖是否正确安装和可用
"""

import sys
import importlib
from typing import List, Tuple


def test_import(module_name: str) -> Tuple[bool, str]:
    """
    测试模块导入
    
    Args:
        module_name: 模块名称
        
    Returns:
        (是否成功, 错误信息)
    """
    try:
        importlib.import_module(module_name)
        return True, ""
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    """
    主测试函数
    """
    print("🔍 开始测试基础依赖...")
    
    # 核心依赖列表（基于 pyproject.toml 和 requirements.txt）
    core_dependencies = [
        "aiohttp",
        "PyQt6",
        "qasync",
        "DrissionPage",
        "httpx",
        "ujson",
        "loguru",
        "requests",
        "uvicorn",
        "fastapi",
        "pydantic",
        "psutil",
    ]
    
    # 调度器相关依赖（基于 requirements_scheduler.txt）
    scheduler_dependencies = [
        "apscheduler",
        "jinja2",
        "aiofiles",
        "multipart",  # python-multipart 的导入名称是 multipart
        "dateutil",   # python-dateutil 的导入名称是 dateutil
        "orjson",
    ]
    
    # 可选依赖列表
    optional_dependencies = [
        "pandas",
        "numpy",
        "pillow",
    ]
    
    failed_core = []
    failed_scheduler = []
    failed_optional = []
    
    # 测试核心依赖
    print("\n📦 测试核心依赖:")
    for dep in core_dependencies:
        success, error = test_import(dep)
        if success:
            print(f"  ✅ {dep}")
        else:
            print(f"  ❌ {dep}: {error}")
            failed_core.append(dep)
    
    # 测试调度器依赖
    print("\n📦 测试调度器依赖:")
    for dep in scheduler_dependencies:
        success, error = test_import(dep)
        if success:
            print(f"  ✅ {dep}")
        else:
            print(f"  ❌ {dep}: {error}")
            failed_scheduler.append(dep)
    
    # 测试可选依赖
    print("\n📦 测试可选依赖:")
    for dep in optional_dependencies:
        success, error = test_import(dep)
        if success:
            print(f"  ✅ {dep}")
        else:
            print(f"  ⚠️  {dep}: {error}")
            failed_optional.append(dep)
    
    # 测试 Python 版本
    print(f"\n🐍 Python 版本: {sys.version}")
    
    # 结果汇总
    print("\n📊 测试结果汇总:")
    print(f"  核心依赖: {len(core_dependencies) - len(failed_core)}/{len(core_dependencies)} 通过")
    print(f"  调度器依赖: {len(scheduler_dependencies) - len(failed_scheduler)}/{len(scheduler_dependencies)} 通过")
    print(f"  可选依赖: {len(optional_dependencies) - len(failed_optional)}/{len(optional_dependencies)} 通过")
    
    # 检查核心依赖失败
    if failed_core:
        print(f"\n❌ 核心依赖失败: {', '.join(failed_core)}")
        print("请运行以下命令安装缺失的核心依赖:")
        print(f"  uv add {' '.join(failed_core)}")
        sys.exit(1)
    
    # 检查调度器依赖失败
    if failed_scheduler:
        print(f"\n❌ 调度器依赖失败: {', '.join(failed_scheduler)}")
        print("请运行以下命令安装缺失的调度器依赖:")
        print(f"  uv add {' '.join(failed_scheduler)}")
        print("注意: 调度器依赖失败可能影响定时任务功能")
        # 调度器依赖失败不退出，但给出警告
    
    if failed_optional:
        print(f"\n⚠️  可选依赖失败: {', '.join(failed_optional)}")
        print("这些依赖不是必需的，但可能影响某些功能")
    
    print("\n🎉 基础依赖测试完成!")
    return 0


if __name__ == "__main__":
    sys.exit(main())