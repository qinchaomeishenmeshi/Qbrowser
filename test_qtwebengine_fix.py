#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试QtWebEngineWidgets导入修复

这个脚本用于验证QtWebEngineWidgets导入问题的修复是否有效。
它模拟了应用程序的启动过程，检查是否能够正确处理QtWebEngine的导入。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_qtwebengine_import():
    """测试QtWebEngineWidgets导入是否正常"""
    print("开始测试QtWebEngineWidgets导入...")
    
    try:
        # 测试在QApplication创建前导入QtWebEngineWidgets
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            print("[OK] QtWebEngineWidgets导入成功")
            webengine_available = True
        except ImportError as e:
            print(f"[WARNING] QtWebEngineWidgets导入失败: {e}")
            webengine_available = False
        
        # 模拟app.py中的导入顺序
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication
        
        # 设置Qt属性
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        print("[OK] Qt.AA_ShareOpenGLContexts属性设置成功")
        
        # 测试现代UI导入（不创建实例）
        try:
            from ui.modern_app import ModernApp
            print("[OK] ModernApp导入成功")
            
        except Exception as e:
            print(f"[ERROR] ModernApp导入失败: {e}")
            return False
        
        print("\n测试结果:")
        print(f"- QtWebEngine可用: {'是' if webengine_available else '否'}")
        print("- Qt属性设置: 成功")
        print("- 现代UI导入: 成功")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_mechanism():
    """测试降级机制是否正常工作"""
    print("\n测试降级机制...")
    
    try:
        # 检查modern_app.py中是否有正确的降级处理
        with open('ui/modern_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否包含降级处理代码
        if 'QWebEngineView is not None' in content:
            print("[OK] 发现QtWebEngine可用性检查代码")
        else:
            print("[ERROR] 未发现QtWebEngine可用性检查代码")
            return False
            
        if 'fallback_label' in content:
            print("[OK] 发现降级UI代码")
        else:
            print("[ERROR] 未发现降级UI代码")
            return False
            
        if 'open_scheduler_in_browser' in content:
            print("[OK] 发现外部浏览器打开功能")
        else:
            print("[ERROR] 未发现外部浏览器打开功能")
            return False
            
        print("[OK] 降级机制代码检查通过")
        return True
        
    except Exception as e:
        print(f"[ERROR] 降级机制测试失败: {e}")
        return False

if __name__ == "__main__":
    print("QW-Browser QtWebEngine修复测试")
    print("=" * 50)
    
    success1 = test_qtwebengine_import()
    success2 = test_fallback_mechanism()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("[OK] 所有测试通过！QtWebEngine修复成功。")
        sys.exit(0)
    else:
        print("[ERROR] 部分测试失败，请检查修复代码。")
        sys.exit(1)