from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QCursor
from ..config import THEMES, CURRENT_THEME, FONTS, LAYOUT, ANIMATIONS


class ChromeButton(QPushButton):
    """Chrome风格按钮组件
    
    具有现代化外观的按钮组件，支持多种样式变体和状态效果。
    包含悬停、按下状态的动画效果和阴影。
    """
    
    def __init__(self, text="", variant="primary", size="medium", parent=None):
        """初始化Chrome按钮
        
        Args:
            text (str): 按钮文本
            variant (str): 按钮样式变体 - "primary", "secondary", "success", "warning", "error"
            size (str): 按钮大小 - "small", "medium", "large"
            parent: 父组件
        """
        super().__init__(text, parent)
        self.variant = variant
        self.size = size
        self.theme = THEMES[CURRENT_THEME]
        self._is_pressed = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI属性"""
        # 设置光标
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 设置字体
        font = QFont()
        font.setFamily(FONTS["regular"][0])
        
        # 根据大小设置尺寸和字体
        if self.size == "small":
            self.setFixedHeight(28)
            font.setPointSize(10)
            self.setMinimumWidth(60)
        elif self.size == "large":
            self.setFixedHeight(44)
            font.setPointSize(14)
            self.setMinimumWidth(100)
        else:  # medium
            self.setFixedHeight(36)
            font.setPointSize(12)
            self.setMinimumWidth(80)
        
        font.setWeight(QFont.Weight.Medium)
        self.setFont(font)
    
    def _apply_styles(self):
        """应用样式"""
        # 添加阴影效果
        self._update_shadow()
        
        # 获取颜色配置
        colors = self._get_variant_colors()
        
        # 设置样式表
        self.setStyleSheet(f"""
            ChromeButton {{
                background-color: {colors['bg']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: {LAYOUT['border_radius']}px;
                padding: 0 16px;
                font-weight: 500;
            }}
            ChromeButton:hover {{
                background-color: {colors['bg_hover']};
                border-color: {colors['border_hover']};
            }}
            ChromeButton:pressed {{
                background-color: {colors['bg_pressed']};
                border-color: {colors['border_pressed']};
            }}
            ChromeButton:disabled {{
                background-color: {self.theme['card']};
                color: {self.theme['text_tertiary']};
                border-color: {self.theme['card_border']};
                opacity: 0.6;
            }}
        """)
    
    def _get_variant_colors(self):
        """获取样式变体对应的颜色配置
        
        Returns:
            dict: 包含各种状态颜色的字典
        """
        if self.variant == "primary":
            return {
                'bg': self.theme['primary'],
                'bg_hover': self._lighten_color(self.theme['primary'], 0.1),
                'bg_pressed': self._darken_color(self.theme['primary'], 0.1),
                'text': self.theme['text_light'],
                'border': self.theme['primary'],
                'border_hover': self._lighten_color(self.theme['primary'], 0.1),
                'border_pressed': self._darken_color(self.theme['primary'], 0.1)
            }
        elif self.variant == "secondary":
            return {
                'bg': self.theme['card'],
                'bg_hover': self.theme['card_hover'],
                'bg_pressed': self._darken_color(self.theme['card_hover'], 0.05),
                'text': self.theme['text'],
                'border': self.theme['card_border'],
                'border_hover': self.theme['primary'],
                'border_pressed': self._darken_color(self.theme['primary'], 0.1)
            }
        elif self.variant == "success":
            return {
                'bg': self.theme['success'],
                'bg_hover': self._lighten_color(self.theme['success'], 0.1),
                'bg_pressed': self._darken_color(self.theme['success'], 0.1),
                'text': self.theme['text_light'],
                'border': self.theme['success'],
                'border_hover': self._lighten_color(self.theme['success'], 0.1),
                'border_pressed': self._darken_color(self.theme['success'], 0.1)
            }
        elif self.variant == "warning":
            return {
                'bg': self.theme['warning'],
                'bg_hover': self._lighten_color(self.theme['warning'], 0.1),
                'bg_pressed': self._darken_color(self.theme['warning'], 0.1),
                'text': self.theme['text_light'],
                'border': self.theme['warning'],
                'border_hover': self._lighten_color(self.theme['warning'], 0.1),
                'border_pressed': self._darken_color(self.theme['warning'], 0.1)
            }
        elif self.variant == "error":
            return {
                'bg': self.theme['error'],
                'bg_hover': self._lighten_color(self.theme['error'], 0.1),
                'bg_pressed': self._darken_color(self.theme['error'], 0.1),
                'text': self.theme['text_light'],
                'border': self.theme['error'],
                'border_hover': self._lighten_color(self.theme['error'], 0.1),
                'border_pressed': self._darken_color(self.theme['error'], 0.1)
            }
        else:
            # 默认为primary样式
            return {
                'bg': self.theme['primary'],
                'bg_hover': self._lighten_color(self.theme['primary'], 0.1),
                'bg_pressed': self._darken_color(self.theme['primary'], 0.1),
                'text': self.theme['text_light'],
                'border': self.theme['primary'],
                'border_hover': self._lighten_color(self.theme['primary'], 0.1),
                'border_pressed': self._darken_color(self.theme['primary'], 0.1)
            }
    
    def _lighten_color(self, color_str, factor):
        """使颜色变亮
        
        Args:
            color_str (str): 颜色字符串
            factor (float): 变亮因子 (0-1)
            
        Returns:
            str: 变亮后的颜色字符串
        """
        color = QColor(color_str)
        h, s, l, a = color.getHsl()
        l = min(255, int(l + (255 - l) * factor))
        color.setHsl(h, s, l, a)
        return color.name()
    
    def _darken_color(self, color_str, factor):
        """使颜色变暗
        
        Args:
            color_str (str): 颜色字符串
            factor (float): 变暗因子 (0-1)
            
        Returns:
            str: 变暗后的颜色字符串
        """
        color = QColor(color_str)
        h, s, l, a = color.getHsl()
        l = max(0, int(l * (1 - factor)))
        color.setHsl(h, s, l, a)
        return color.name()
    
    def _update_shadow(self, pressed=False):
        """更新阴影效果
        
        Args:
            pressed (bool): 是否为按下状态
        """
        shadow = QGraphicsDropShadowEffect()
        
        if pressed:
            # 按下时的阴影效果
            shadow.setBlurRadius(5)
            shadow.setXOffset(0)
            shadow.setYOffset(1)
            shadow.setColor(QColor(0, 0, 0, 30))
        else:
            # 默认阴影效果
            shadow.setBlurRadius(8)
            shadow.setXOffset(0)
            shadow.setYOffset(2)
            shadow.setColor(QColor(0, 0, 0, 20))
        
        self.setGraphicsEffect(shadow)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = True
            self._update_shadow(pressed=True)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_pressed = False
            self._update_shadow(pressed=False)
        super().mouseReleaseEvent(event)
    
    def set_variant(self, variant):
        """设置按钮样式变体
        
        Args:
            variant (str): 样式变体名称
        """
        self.variant = variant
        self._apply_styles()
    
    def set_size(self, size):
        """设置按钮大小
        
        Args:
            size (str): 大小名称
        """
        self.size = size
        self._setup_ui()
        self._apply_styles()