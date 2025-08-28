#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务导航修复测试脚本
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_scheduler_navigation():
    """测试定时任务页面导航"""
    try:
        # 导入优化后的应用
        from ui.modern_app import ModernApp
        
        # 创建应用实例
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = ModernApp()
        window.show()
        
        print("=" * 50)
        print("定时任务导航测试")
        print("=" * 50)
        
        # 检查页面初始化
        dashboard_index = window.content_stack.indexOf(window.dashboard_page) if hasattr(window, 'dashboard_page') else -1
        scheduler_index = window.content_stack.indexOf(window.scheduler_page) if hasattr(window, 'scheduler_page') else -1
        
        print(f"仪表盘页面索引: {dashboard_index}")
        print(f"定时任务页面索引: {scheduler_index}")
        print(f"当前页面索引: {window.content_stack.currentIndex()}")
        print(f"内容栈总页面数: {window.content_stack.count()}")
        
        # 模拟点击定时任务按钮
        def test_scheduler_click():
            print("\\n测试点击定时任务按钮...")
            print(f"点击前当前页面索引: {window.content_stack.currentIndex()}")
            print(f"点击前定时任务按钮状态: {window.scheduler_btn.isChecked()}")
            
            # 模拟点击
            window.show_scheduler()
            
            print(f"点击后当前页面索引: {window.content_stack.currentIndex()}")
            print(f"点击后定时任务按钮状态: {window.scheduler_btn.isChecked()}")
            print(f"页面标题: {window.page_title.text()}")
            
            # 检查是否成功切换
            if window.content_stack.currentIndex() == 2:
                print("✓ 定时任务页面导航成功！")
            else:
                print("✗ 定时任务页面导航失败！")
        
        # 延迟测试，确保界面完全加载
        QTimer.singleShot(1000, test_scheduler_click)
        
        # 测试返回浏览器管理页面
        def test_instances_click():
            print("\\n测试返回浏览器管理页面...")
            print(f"点击前当前页面索引: {window.content_stack.currentIndex()}")
            
            window.show_instances()
            
            print(f"点击后当前页面索引: {window.content_stack.currentIndex()}")
            print(f"页面标题: {window.page_title.text()}")
            
            if window.content_stack.currentIndex() == 1:
                print("✓ 浏览器管理页面导航成功！")
            else:
                print("✗ 浏览器管理页面导航失败！")
                
            print("\\n测试完成，请手动点击导航按钮进行验证。")
        
        # 延迟测试返回
        QTimer.singleShot(3000, test_instances_click)
        
        return app.exec()
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return 1
    except Exception as e:
        print(f"✗ 测试过程中出现错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_scheduler_navigation())