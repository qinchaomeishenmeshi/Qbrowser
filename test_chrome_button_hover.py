#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome按钮hover状态测试脚本
测试外部浏览器按钮的hover状态修复效果
"""

import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
    from PyQt6.QtCore import Qt
    from ui.components.chrome_button import ChromeButton
    from ui.config import THEMES, CURRENT_THEME
    
    class ButtonTestWindow(QWidget):
        """按钮测试窗口"""
        
        def __init__(self):
            super().__init__()
            self.init_ui()
        
        def init_ui(self):
            """初始化UI"""
            self.setWindowTitle("Chrome按钮Hover状态测试")
            self.setGeometry(100, 100, 400, 300)
            
            theme = THEMES[CURRENT_THEME]
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {theme['background']};
                    color: {theme['text']};
                }}
            """)
            
            layout = QVBoxLayout(self)
            layout.setSpacing(20)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 标题
            title = QLabel("Chrome按钮Hover状态测试")
            title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {theme['text']};")
            layout.addWidget(title)
            
            # 说明
            desc = QLabel("将鼠标悬停在按钮上，检查文字是否清晰可见")
            desc.setStyleSheet(f"color: {theme['text_secondary']};")
            layout.addWidget(desc)
            
            # 按钮测试区域
            button_layout = QHBoxLayout()
            
            # 不同variant的按钮
            variants = [
                ("filled", "主要按钮"),
                ("outlined", "外部浏览器按钮"),
                ("text", "文本按钮"),
                ("success", "成功按钮"),
                ("error", "错误按钮")
            ]
            
            for variant, text in variants:
                btn = ChromeButton(text, variant=variant)
                btn.clicked.connect(lambda checked, v=variant: self.on_button_clicked(v))
                button_layout.addWidget(btn)
            
            layout.addLayout(button_layout)
            
            # 测试结果显示
            self.result_label = QLabel("请测试每个按钮的hover状态...")
            self.result_label.setStyleSheet(f"color: {theme['text_secondary']}; margin-top: 20px;")
            layout.addWidget(self.result_label)
            
            layout.addStretch()
        
        def on_button_clicked(self, variant):
            """按钮点击处理"""
            self.result_label.setText(f"点击了 {variant} 按钮 - 检查hover状态是否正常")
    
    def test_chrome_button_hover():
        """测试Chrome按钮hover状态"""
        print("=" * 60)
        print("Chrome按钮Hover状态测试")
        print("=" * 60)
        
        app = QApplication(sys.argv)
        
        # 创建测试窗口
        window = ButtonTestWindow()
        window.show()
        
        print("测试窗口已打开，请执行以下测试步骤：")
        print("1. 将鼠标悬停在 'outlined' 样式的按钮上（外部浏览器按钮）")
        print("2. 检查hover状态下文字是否清晰可见")
        print("3. 与其他按钮的hover效果进行对比")
        print("4. 确认修复是否成功")
        
        print("\n修复详情：")
        print("• 为outlined样式添加了text_hover颜色配置")
        print("• hover状态下使用主文本颜色确保可读性")
        print("• 保持了原有的背景和边框效果")
        
        # 运行应用
        return app.exec()

    if __name__ == "__main__":
        sys.exit(test_chrome_button_hover())
        
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)
except Exception as e:
    print(f"测试运行失败: {e}")
    sys.exit(1)