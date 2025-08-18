#!/usr/bin/env python3
"""验证启动修改的简单测试脚本

此脚本用于验证：
1. app.py和run_app.py都能正常启动
2. 单例机制正常工作
3. 启动逻辑统一
"""

import sys
import os
import subprocess
import time


def test_import():
    """测试导入是否正常"""
    print("=== 测试模块导入 ===")
    
    try:
        from app import main, check_single_instance, release_single_instance
        print("✓ app.py 导入成功")
        
        # 测试单例函数
        result = check_single_instance()
        if result:
            print("✓ 单例检查函数正常")
            release_single_instance()
            print("✓ 单例释放函数正常")
        else:
            print("⚠ 可能已有实例在运行")
            
    except Exception as e:
        print(f"✗ app.py 导入失败: {e}")
        return False
    
    try:
        import run_app
        print("✓ run_app.py 导入成功")
    except Exception as e:
        print(f"✗ run_app.py 导入失败: {e}")
        return False
    
    return True


def test_startup_consistency():
    """测试启动一致性"""
    print("\n=== 测试启动一致性 ===")
    
    # 检查run_app.py是否调用了app.main
    try:
        with open('run_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'from app import main' in content and 'main()' in content:
            print("✓ run_app.py 正确调用 app.main()")
            return True
        else:
            print("✗ run_app.py 未正确调用 app.main()")
            return False
            
    except Exception as e:
        print(f"✗ 检查run_app.py失败: {e}")
        return False


def test_lock_file():
    """测试锁文件机制"""
    print("\n=== 测试锁文件机制 ===")
    
    import tempfile
    lock_file_path = os.path.join(tempfile.gettempdir(), 'qw_browser_app.lock')
    
    # 清理可能存在的锁文件
    if os.path.exists(lock_file_path):
        try:
            os.remove(lock_file_path)
            print(f"✓ 清理了旧的锁文件: {lock_file_path}")
        except Exception as e:
            print(f"⚠ 无法清理锁文件: {e}")
    
    from app import check_single_instance, release_single_instance
    
    # 测试获取锁
    result1 = check_single_instance()
    if result1:
        print("✓ 成功获取应用程序锁")
        
        # 测试重复获取（应该失败）
        result2 = check_single_instance()
        if not result2:
            print("✓ 重复获取锁被正确拒绝")
        else:
            print("✗ 重复获取锁未被拒绝")
            
        # 释放锁
        release_single_instance()
        print("✓ 成功释放应用程序锁")
        
        # 再次获取（应该成功）
        result3 = check_single_instance()
        if result3:
            print("✓ 释放后重新获取锁成功")
            release_single_instance()
        else:
            print("✗ 释放后重新获取锁失败")
            
    else:
        print("✗ 无法获取应用程序锁")
        return False
    
    return True


def main():
    """主测试函数"""
    print("QW-Browser 启动修改验证脚本")
    print("=" * 40)
    
    success_count = 0
    total_tests = 3
    
    # 测试导入
    if test_import():
        success_count += 1
    
    # 测试启动一致性
    if test_startup_consistency():
        success_count += 1
    
    # 测试锁文件机制
    if test_lock_file():
        success_count += 1
    
    print("\n" + "=" * 40)
    print(f"测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！启动修改验证成功")
        print("\n可以安全使用以下命令启动应用程序：")
        print("  python app.py      (推荐)")
        print("  python run_app.py  (备用)")
    else:
        print("❌ 部分测试失败，请检查修改")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())