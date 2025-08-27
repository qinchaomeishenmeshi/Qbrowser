from PyQt6.QtWidgets import QPushButton, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from ..config import THEMES, CURRENT_THEME, FONTS, LAYOUT


class NavigationButton(QPushButton):
    """Chrome风格导航按钮组件
    
    仿照Chrome浏览器的导航按钮设计，采用简洁的纯文本样式，
    具有微妙的悬停效果和清晰的选中状态指示。
    """
    
    def __init__(self, text="", icon_text="", parent=None):
        """初始化Chrome风格导航按钮
        
        Args:
            text (str): 按钮文本
            icon_text (str): 图标文本（已弃用，保持兼容性）
            parent: 父组件
        """
        super().__init__(parent)
        self.text = text
        self.theme = THEMES[CURRENT_THEME]
        self._is_selected = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI布局"""
        # 优化的导航按钮样式
        self.setFixedHeight(LAYOUT['nav_button_height'])
        self.setText(self.text)
        
        # 设置字体
        font = QFont(FONTS["regular"][0], 13)
        font.setWeight(QFont.Weight.Medium)
        self.setFont(font)
        
        # 设置鼠标样式
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 添加状态记忆功能
        self._persistent_state = False
        self.setCheckable(True)  # 使按钮可选中
        
        # 连接信号以确保状态变化时更新外观
        self.toggled.connect(self._on_toggled)
    
    def _apply_styles(self):
        """应用样式"""
        self._update_appearance()
    
    def _on_toggled(self, checked):
        """处理按钮状态切换信号
        
        Args:
            checked (bool): 按钮是否被选中
        """
        self._is_selected = checked
        self._persistent_state = checked
        self._update_appearance()
    
    def _update_appearance(self):
        """更新按钮外观"""
        if self._is_selected or self.isChecked():
            # 选中状态：高亮背景和左侧指示条
            self.setStyleSheet(f"""
                NavigationButton {{
                    background-color: {self._lighten_color(self.theme['primary'], 0.9)};
                    border: none;
                    border-left: 3px solid {self.theme['primary']};
                    border-radius: {LAYOUT['border_radius']}px;
                    color: {self.theme['primary']};
                    font-weight: 600;
                    padding: 12px 20px;
                    margin: {LAYOUT['nav_button_spacing']}px {LAYOUT['sidebar_margin']}px;
                    text-align: left;
                }}
            """)
            
        else:
            # 未选中状态：透明背景，悬停时显示磨砂效果
            self.setStyleSheet(f"""
                NavigationButton {{
                    background-color: transparent;
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: {LAYOUT['border_radius']}px;
                    color: {self.theme['text_secondary']};
                    font-weight: 500;
                    padding: 12px 20px;
                    margin: {LAYOUT['nav_button_spacing']}px {LAYOUT['sidebar_margin']}px;
                    text-align: left;
                }}
                NavigationButton:hover {{
                    background-color: {self._create_glass_effect(self.theme['card_hover'])};
                    color: {self.theme['text']};
                    border-left: 3px solid {self._lighten_color(self.theme['primary'], 0.7)};
                }}
            """)
    
    def _lighten_color(self, color_str, factor):
        """使颜色变亮
        
        Args:
            color_str (str): 颜色字符串
            factor (float): 变亮因子 (0-1)
            
        Returns:
            str: 变亮后的颜色字符串
        """
        from PyQt6.QtGui import QColor
        color = QColor(color_str)
        h, s, l, a = color.getHsl()
        l = min(255, int(l + (255 - l) * factor))
        color.setHsl(h, s, l, a)
        return color.name()
    
    def _create_glass_effect(self, base_color):
        """创建磨砂玻璃效果颜色
        
        Args:
            base_color (str): 基础颜色
            
        Returns:
            str: 磨砂玻璃效果颜色
        """
        from PyQt6.QtGui import QColor
        color = QColor(base_color)
        # 增加透明度和亮度来模拟磨砂玻璃效果
        h, s, l, a = color.getHsl()
        l = min(255, int(l * 1.2))  # 增加亮度
        color.setHsl(h, s, l, int(a * 0.8))  # 增加透明度
        return color.name()
    
    def setChecked(self, checked):
        """设置选中状态
        
        Args:
            checked (bool): 是否选中
        """
        super().setChecked(checked)
        self._is_selected = checked
        self._persistent_state = checked  # 保存持久化状态
        self._update_appearance()
    
    def set_selected(self, selected):
        """设置选中状态（别名方法）
        
        Args:
            selected (bool): 是否选中
        """
        self.setChecked(selected)
    
    def is_selected(self):
        """获取选中状态
        
        Returns:
            bool: 是否选中
        """
        return self._is_selected
    
    def get_persistent_state(self):
        """获取持久化状态
        
        Returns:
            bool: 持久化的选中状态
        """
        return self._persistent_state
    
    def restore_persistent_state(self):
        """恢复持久化状态"""
        if hasattr(self, '_persistent_state'):
            self.setChecked(self._persistent_state)
    
    def update_text(self, text):
        """更新按钮文本
        
        Args:
            text (str): 新文本
        """
        self.text = text
        self.setText(text)
    
    def update_icon(self, icon_text):
        """更新按钮图标（Chrome风格已弃用图标）
        
        Args:
            icon_text (str): 图标文本（已弃用，保持兼容性）
        """
        # Chrome风格不使用图标，此方法保持兼容性但不执行任何操作
        pass
    
    def set_enabled(self, enabled):
        """设置按钮启用状态
        
        Args:
            enabled (bool): 是否启用
        """
        super().setEnabled(enabled)
        
        if enabled:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._update_appearance()  # 恢复正常样式
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            
            # Chrome风格禁用状态样式
            self.setStyleSheet(f"""
                NavigationButton {{
                    background-color: transparent;
                    border: none;
                    border-bottom: 2px solid transparent;
                    border-radius: 0px;
                    color: {self.theme['inactive']};
                    font-weight: 400;
                    padding: 8px 16px;
                    text-align: center;
                }}
            """)