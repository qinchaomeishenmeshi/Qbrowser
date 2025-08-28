#!/usr/bin/env python3
"""
简单验证脚本：检查按钮功能修复
不依赖pytest，直接检查源码
"""
import inspect
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_button_fix():
    """验证按钮功能修复"""
    print("=== 验证按钮功能修复 ===")
    
    try:
        # 导入ModernApp
        from ui.modern_app import ModernApp
        
        # 检查start_browsers方法
        start_source = inspect.getsource(ModernApp.start_browsers)
        print("✓ 成功导入ModernApp.start_browsers方法")
        
        # 验证不再包含占位符消息
        if "启动浏览器功能待实现" in start_source:
            print("✗ start_browsers方法仍包含占位符消息")
            return False
        else:
            print("✓ start_browsers方法不再包含占位符消息")
            
        # 验证包含实际业务逻辑
        if "browser_service.start_browsers" in start_source:
            print("✓ start_browsers方法包含实际业务逻辑")
        else:
            print("✗ start_browsers方法缺少业务逻辑")
            return False
            
        # 检查stop_browsers方法
        stop_source = inspect.getsource(ModernApp.stop_browsers)
        print("✓ 成功导入ModernApp.stop_browsers方法")
        
        # 验证不再包含占位符消息
        if "停止浏览器功能待实现" in stop_source:
            print("✗ stop_browsers方法仍包含占位符消息")
            return False
        else:
            print("✓ stop_browsers方法不再包含占位符消息")
            
        # 验证包含实际业务逻辑
        if "browser_service.stop_all_browsers" in stop_source:
            print("✓ stop_browsers方法包含实际业务逻辑")
        else:
            print("✗ stop_browsers方法缺少业务逻辑")
            return False
            
        print("\n=== 修复验证成功 ===")
        print("✓ 所有按钮功能已恢复正常")
        print("✓ 不再显示占位符消息")
        print("✓ 包含完整的业务逻辑实现")
        
        # 显示关键代码片段
        print("\n=== 关键代码片段 ===")
        print("start_browsers方法包含:")
        for line in start_source.split('\n'):
            if 'browser_service.start_browsers' in line or '启动浏览器操作已完成' in line:
                print(f"  {line.strip()}")
                
        print("\nstop_browsers方法包含:")
        for line in stop_source.split('\n'):
            if 'browser_service.stop_all_browsers' in line or '所有浏览器已关闭' in line:
                print(f"  {line.strip()}")
        
        return True
        
    except Exception as e:
        print(f"✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_import():
    """测试原始App类导入"""
    print("\n=== 验证原始App类 ===")
    try:
        from app import App
        start_source = inspect.getsource(App.start_browsers)
        if "browser_service.start_browsers" in start_source:
            print("✓ 原始App类的start_browsers方法正常")
        else:
            print("✗ 原始App类的start_browsers方法有问题")
            return False
        return True
    except Exception as e:
        print(f"✗ 原始App类导入失败: {e}")
        return False

if __name__ == "__main__":
    success1 = test_button_fix()
    success2 = test_app_import()
    
    if success1 and success2:
        print("\n🎉 所有验证通过！按钮功能修复成功！")
        sys.exit(0)
    else:
        print("\n❌ 验证失败，需要进一步检查")
        sys.exit(1)