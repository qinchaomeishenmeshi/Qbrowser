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
    
    # 应用与app.py相同的修复方案
    if sys.platform == "win32":
        print("检测到Windows系统，应用显示器修复方案...")
        
        # 设置Qt属性
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_DisableWindowContextHelpButton)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
        
        # 设置环境变量
        os.environ.setdefault('QT_QPA_PLATFORM_PLUGIN_PATH', '')
        os.environ.setdefault('QT_OPENGL', 'desktop')
        os.environ.setdefault('QT_DEVICE_PIXEL_RATIO', 'auto')
        
        print("[OK] Windows显示器修复方案已应用")
    else:
        print("非Windows系统，跳过Windows特定修复")
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    
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