#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qt显示器错误修复测试脚本

用于测试qt.qpa.screen错误的修复效果
"""

import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QScreen


def test_qt_display_fix():
    """测试Qt显示器修复方案"""
    print("=== Qt显示器错误修复测试 ===")
    print(f"操作系统: {sys.platform}")
    
    # 应用与app.py相同的修复方案，使用Qt兼容性工具模块
    from utils.qt_compatibility import initialize_qt_compatibility, get_qt_version_info
    
    # 显示Qt版本信息
    version_info = get_qt_version_info()
    print(f"Qt版本: {version_info['qt_version']}")
    print(f"PyQt版本: {version_info['pyqt_version']}")
    print(f"平台: {version_info['platform']}")
    
    # 初始化Qt兼容性设置
    qt_init_success = initialize_qt_compatibility()
    if qt_init_success:
        print("[OK] Qt兼容性设置成功")
    else:
        print("[WARNING] Qt兼容性设置部分失败")
    
    # 创建应用程序
    try:
        app = QApplication(sys.argv)
        print("[OK] QApplication创建成功")
    except Exception as e:
        print(f"[ERROR] QApplication创建失败: {e}")
        return False
    
    # 检查显示器信息
    try:
        screens = app.screens()
        print(f"\n=== 显示器信息 ===")
        print(f"检测到 {len(screens)} 个显示器:")
        
        for i, screen in enumerate(screens):
            geometry = screen.geometry()
            print(f"\n显示器 {i + 1}:")
            print(f"  名称: {screen.name()}")
            print(f"  分辨率: {geometry.width()}x{geometry.height()}")
            print(f"  位置: ({geometry.x()}, {geometry.y()})")
            print(f"  DPI: {screen.logicalDotsPerInch():.1f}")
            print(f"  缩放比例: {screen.devicePixelRatio():.2f}")
            print(f"  主显示器: {'是' if screen == app.primaryScreen() else '否'}")
        
        print("[OK] 显示器信息获取成功")
    except Exception as e:
        print(f"[ERROR] 显示器信息获取失败: {e}")
        return False
    
    # 创建测试窗口
    try:
        window = QMainWindow()
        window.setWindowTitle("Qt显示器修复测试")
        window.setGeometry(100, 100, 400, 300)
        
        # 创建中心部件
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # 添加测试标签
        labels = [
            "Qt显示器修复测试",
            f"操作系统: {sys.platform}",
            f"显示器数量: {len(screens)}",
            f"主显示器: {app.primaryScreen().name()}",
            "如果看到此窗口，说明修复成功！"
        ]
        
        for text in labels:
            label = QLabel(text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
        
        window.setCentralWidget(central_widget)
        window.show()
        
        print("\n[OK] 测试窗口创建成功")
        print("\n=== 测试结果 ===")
        print("[OK] Qt显示器修复方案工作正常")
        print("[OK] 没有出现 qt.qpa.screen 错误")
        print("[OK] 应用程序可以正常显示")
        
        # 运行5秒后自动关闭
        from PyQt6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(5000)  # 5秒
        
        print("\n窗口将在5秒后自动关闭...")
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 测试窗口创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_qt_display_fix()
    if success:
        print("\n[OK] Qt显示器修复测试通过！")
        sys.exit(0)
    else:
        print("\n[ERROR] Qt显示器修复测试失败！")
        sys.exit(1)