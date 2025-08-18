#!/usr/bin/env python3
"""测试单例启动功能

此脚本用于验证应用程序的单例启动机制是否正常工作。
运行此脚本两次，第二次应该显示已有实例在运行的提示。
"""

import sys
import time
import subprocess
from app import check_single_instance, release_single_instance


def test_single_instance_check():
    """测试单例检查功能"""
    print("=== 测试单例启动检查功能 ===")
    
    # 第一次检查，应该成功
    print("\n1. 第一次检查单例...")
    result1 = check_single_instance()
    print(f"   结果: {'成功' if result1 else '失败'}")
    
    if result1:
        # 第二次检查，应该失败（因为已经获取了锁）
        print("\n2. 第二次检查单例（应该失败）...")
        result2 = check_single_instance()
        print(f"   结果: {'成功' if result2 else '失败（符合预期）'}")
        
        # 释放锁
        print("\n3. 释放单例锁...")
        release_single_instance()
        print("   锁已释放")
        
        # 第三次检查，应该成功
        print("\n4. 第三次检查单例（应该成功）...")
        result3 = check_single_instance()
        print(f"   结果: {'成功' if result3 else '失败'}")
        
        if result3:
            release_single_instance()
            print("   锁已释放")
    
    print("\n=== 测试完成 ===")


def test_multiple_process():
    """测试多进程启动"""
    print("\n=== 测试多进程启动 ===")
    print("启动第一个进程...")
    
    # 启动第一个进程（后台运行）
    process1 = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待一秒让第一个进程启动
    time.sleep(1)
    
    print("启动第二个进程（应该被拒绝）...")
    
    # 启动第二个进程
    process2 = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待第二个进程结束
    stdout2, stderr2 = process2.communicate(timeout=5)
    
    print(f"第二个进程退出码: {process2.returncode}")
    if stdout2:
        print(f"第二个进程输出: {stdout2.decode('utf-8')}")
    if stderr2:
        print(f"第二个进程错误: {stderr2.decode('utf-8')}")
    
    # 终止第一个进程
    process1.terminate()
    process1.wait()
    
    print("=== 多进程测试完成 ===")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--process-test":
        test_multiple_process()
    else:
        test_single_instance_check()
        print("\n提示: 运行 'python test_single_instance.py --process-test' 可测试多进程启动")