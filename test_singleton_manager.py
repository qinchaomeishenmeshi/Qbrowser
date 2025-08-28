#!/usr/bin/env python3
"""
测试 QLocalServer 单例管理器功能
验证新的实现是否正常工作
"""
import sys
import os
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """测试基本功能"""
    print("=== QLocalServer 单例管理器基本功能测试 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from utils.singleton_manager import SingletonManager
        
        app = QApplication(sys.argv if hasattr(sys, 'argv') else [])
        
        # 创建第一个单例管理器
        manager1 = SingletonManager("test_app")
        
        print("测试 1: 第一个实例检查...")
        is_running1 = manager1.is_already_running()
        print(f"第一个实例 - 已有实例运行: {is_running1}")
        
        if is_running1:
            print("❌ 第一个实例不应该检测到已有实例")
            return False
        else:
            print("✅ 第一个实例正确，没有检测到已有实例")
        
        # 创建第二个单例管理器（模拟第二个实例）
        manager2 = SingletonManager("test_app")
        
        print("\n测试 2: 第二个实例检查...")
        is_running2 = manager2.is_already_running()
        print(f"第二个实例 - 已有实例运行: {is_running2}")
        
        if is_running2:
            print("✅ 第二个实例正确检测到已有实例")
        else:
            print("❌ 第二个实例应该检测到已有实例")
            return False
        
        # 清理
        manager1.cleanup()
        manager2.cleanup()
        
        print("\n✅ 基本功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_variable_skip():
    """测试环境变量跳过功能"""
    print("\n=== 环境变量跳过功能测试 ===")
    
    try:
        # 设置环境变量
        os.environ['QW_BROWSER_SKIP_SINGLETON_CHECK'] = '1'
        
        from PyQt6.QtWidgets import QApplication
        from utils.singleton_manager import SingletonManager
        
        app = QApplication(sys.argv if hasattr(sys, 'argv') else [])
        
        # 创建两个单例管理器
        manager1 = SingletonManager("test_app_skip")
        manager2 = SingletonManager("test_app_skip")
        
        print("测试环境变量跳过...")
        is_running1 = manager1.is_already_running()
        is_running2 = manager2.is_already_running()
        
        print(f"第一个实例 - 已有实例运行: {is_running1}")
        print(f"第二个实例 - 已有实例运行: {is_running2}")
        
        if not is_running1 and not is_running2:
            print("✅ 环境变量跳过功能正常工作")
            result = True
        else:
            print("❌ 环境变量跳过功能不工作")
            result = False
        
        # 清理环境变量
        del os.environ['QW_BROWSER_SKIP_SINGLETON_CHECK']
        
        # 清理
        manager1.cleanup()
        manager2.cleanup()
        
        return result
        
    except Exception as e:
        print(f"❌ 环境变量测试失败: {e}")
        # 确保清理环境变量
        if 'QW_BROWSER_SKIP_SINGLETON_CHECK' in os.environ:
            del os.environ['QW_BROWSER_SKIP_SINGLETON_CHECK']
        return False

def test_cross_platform_compatibility():
    """测试跨平台兼容性"""
    print("\n=== 跨平台兼容性测试 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from utils.singleton_manager import SingletonManager
        
        app = QApplication(sys.argv if hasattr(sys, 'argv') else [])
        
        manager = SingletonManager("test_cross_platform")
        
        # 测试服务器名称生成
        server_name = manager.server_name
        print(f"生成的服务器名称: {server_name}")
        
        # 检查服务器名称是否包含用户标识
        if sys.platform == "win32":
            username = os.getenv('USERNAME', 'unknown')
            expected_suffix = username
        else:
            expected_suffix = str(os.getuid()) if hasattr(os, 'getuid') else 'default'
        
        if expected_suffix in server_name:
            print("✅ 服务器名称包含正确的用户标识")
            result = True
        else:
            print(f"❌ 服务器名称不包含预期的用户标识: {expected_suffix}")
            result = False
        
        # 测试基本运行
        is_running = manager.is_already_running()
        print(f"平台 {sys.platform} - 单例检查结果: {is_running}")
        
        manager.cleanup()
        return result
        
    except Exception as e:
        print(f"❌ 跨平台兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_compatibility():
    """测试导入兼容性"""
    print("\n=== 导入兼容性测试 ===")
    
    try:
        # 测试各种导入方式
        from utils.singleton_manager import (
            check_single_instance,
            release_single_instance,
            setup_activate_on_second_instance,
            get_singleton_manager
        )
        
        print("✅ 所有函数导入成功")
        
        # 测试 check_single_instance 函数
        result1 = check_single_instance()
        print(f"check_single_instance() 返回: {result1}")
        
        if isinstance(result1, bool):
            print("✅ check_single_instance 返回类型正确")
        else:
            print("❌ check_single_instance 返回类型错误")
            return False
        
        # 测试 get_singleton_manager 函数
        manager = get_singleton_manager()
        if manager is not None:
            print("✅ get_singleton_manager 返回有效实例")
        else:
            print("❌ get_singleton_manager 返回None")
            return False
        
        # 清理
        release_single_instance()
        
        return True
        
    except Exception as e:
        print(f"❌ 导入兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("QLocalServer 单例管理器测试")
    print("=" * 50)
    
    # 检查系统要求
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtNetwork import QLocalServer, QLocalSocket
        print("✅ PyQt6 和网络模块导入成功")
    except ImportError as e:
        print(f"❌ PyQt6 导入失败: {e}")
        print("请确保安装了 PyQt6: pip install PyQt6")
        return False
    
    # 运行各项测试
    tests = [
        ("导入兼容性", test_import_compatibility),
        ("基本功能", test_basic_functionality),
        ("环境变量跳过", test_environment_variable_skip),
        ("跨平台兼容性", test_cross_platform_compatibility),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    # 总结
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！QLocalServer 单例管理器工作正常。")
        return True
    else:
        print("❌ 部分测试失败，需要检查实现。")
        return False

if __name__ == "__main__":
    success = main()
    print("\n按任意键退出...")
    try:
        input()
    except:
        pass
    sys.exit(0 if success else 1)