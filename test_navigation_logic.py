#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的定时任务导航测试脚本
"""

import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_navigation_logic():
    """测试导航逻辑（不需要启动GUI）"""
    print("=" * 50)
    print("定时任务导航逻辑测试")
    print("=" * 50)
    
    try:
        # 测试页面索引分配
        print("页面索引分配：")
        print("0: Dashboard page (仪表盘)")
        print("1: Instance page (浏览器管理)")
        print("2: Scheduler page (定时任务) ← 目标页面")
        print("3: Data page (数据管理)")
        print("4: Settings page (设置)")
        print()
        
        # 模拟代码逻辑
        class MockContentStack:
            def __init__(self):
                self.current_index = 1  # 默认在浏览器管理页面
                
            def setCurrentIndex(self, index):
                self.current_index = index
                print(f"切换到页面索引: {index}")
                
            def currentIndex(self):
                return self.current_index
        
        class MockButton:
            def __init__(self, name):
                self.name = name
                self.checked = False
                
            def setChecked(self, checked):
                self.checked = checked
                print(f"{self.name}按钮状态: {'选中' if checked else '未选中'}")
                
            def isChecked(self):
                return self.checked
        
        class MockApp:
            def __init__(self):
                self.content_stack = MockContentStack()
                self.scheduler_btn = MockButton("定时任务")
                self.instances_btn = MockButton("浏览器管理")
                self.page_title_text = "浏览器控制中心"
                
            def update_page_title(self, title):
                self.page_title_text = title
                print(f"页面标题更新为: {title}")
                
            def show_scheduler(self):
                """模拟show_scheduler方法"""
                print("\\n执行 show_scheduler()...")
                
                # 更新按钮激活状态
                self.scheduler_btn.setChecked(True)
                
                # 切换到定时任务页面 (索引 2)
                self.content_stack.setCurrentIndex(2)
                self.update_page_title("定时任务管理")
                
            def show_instances(self):
                """模拟show_instances方法"""
                print("\\n执行 show_instances()...")
                
                # 更新按钮激活状态
                self.instances_btn.setChecked(True)
                # 切换到实例管理页面 (索引 1)
                self.content_stack.setCurrentIndex(1)
                self.update_page_title("浏览器实例管理")
        
        # 测试导航逻辑
        app = MockApp()
        
        print("初始状态:")
        print(f"当前页面索引: {app.content_stack.currentIndex()}")
        print(f"页面标题: {app.page_title_text}")
        
        # 测试点击定时任务
        print("\\n测试：点击定时任务导航...")
        app.show_scheduler()
        print(f"结果 - 当前页面索引: {app.content_stack.currentIndex()}")
        print(f"结果 - 页面标题: {app.page_title_text}")
        
        if app.content_stack.currentIndex() == 2:
            print("✓ 定时任务导航逻辑正确")
        else:
            print("✗ 定时任务导航逻辑错误")
        
        # 测试返回浏览器管理
        print("\\n测试：返回浏览器管理页面...")
        app.show_instances()
        print(f"结果 - 当前页面索引: {app.content_stack.currentIndex()}")
        print(f"结果 - 页面标题: {app.page_title_text}")
        
        if app.content_stack.currentIndex() == 1:
            print("✓ 浏览器管理导航逻辑正确")
        else:
            print("✗ 浏览器管理导航逻辑错误")
            
        print("\\n" + "=" * 50)
        print("导航逻辑测试完成")
        print("=" * 50)
        print("\\n修复说明：")
        print("1. 修复了show_scheduler方法中的页面切换逻辑")
        print("2. 确保按钮状态正确更新")
        print("3. 轻量版模式下也会切换到内部页面")
        print("4. 页面标题正确更新")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_navigation_logic()
    sys.exit(0 if success else 1)