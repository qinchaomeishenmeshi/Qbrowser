from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QCursor
from ..config import THEMES, CURRENT_THEME, FONTS, LAYOUT, ANIMATIONS


class ChromeButton(QPushButton):
    """真正的Chrome风格按钮组件
    
    完全模仿Chrome浏览器的按钮设计：
    - Material Design风格
    - 微妙的交互效果
    - Chrome原生的颜色和尺寸
    - 扁平化设计
    """
    
    def __init__(self, text="", variant="filled", size="medium", parent=None):
        """初始化Chrome按钮
        
        Args:
            text (str): 按钮文本
            variant (str): 按钮样式变体 - "filled", "outlined", "text", "tonal", "primary", "secondary", "success", "warning", "error"
            size (str): 按钮大小 - "small", "medium", "large"
            parent: 父组件
        """
        super().__init__(text, parent)
        self.variant = variant
        self.button_size = size  # 避免与size()方法冲突
        self.theme = THEMES[CURRENT_THEME]
        self._is_hovered = False
        self._is_pressed = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI属性"""
        # 设置光标
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 设置字体 - 使用Chrome标准字体
        font = QFont()
        font.setFamily(FONTS["button"][0])
        if len(FONTS["button"]) > 2:
            font.setWeight(int(FONTS["button"][2]))
        
        # 根据大小设置尺寸
        if self.button_size == "small":
            self.setFixedHeight(28)
            font.setPointSize(12)
            self.setMinimumWidth(64)
        elif self.button_size == "large":
            self.setFixedHeight(44)
            font.setPointSize(14)
            self.setMinimumWidth(120)
        else:  # medium - Chrome标准尺寸
            self.setFixedHeight(LAYOUT['button_height'])
            font.setPointSize(FONTS["button"][1])
            self.setMinimumWidth(80)
        
        self.setFont(font)
    
    def _apply_styles(self):
        """应用Chrome风格样式"""
        # 移除阴影效果（Chrome按钮是扁平的）
        self.setGraphicsEffect(None)
        
        # 获取颜色配置
        colors = self._get_variant_colors()
        
        # Chrome风格样式表
        hover_text_color = colors.get('text_hover', colors['text'])
        self.setStyleSheet(f"""
            ChromeButton {{
                background-color: {colors['bg']};
                color: {colors['text']};
                border: {colors['border']};
                border-radius: {LAYOUT['border_radius']}px;
                padding: 0 16px;
                font-weight: 500;
                text-align: center;
            }}
            ChromeButton:hover {{
                background-color: {colors['bg_hover']};
                color: {hover_text_color};
                border: {colors['border_hover']};
            }}
            ChromeButton:pressed {{
                background-color: {colors['bg_pressed']};
                border: {colors['border_pressed']};
            }}
            ChromeButton:disabled {{
                background-color: {self.theme['surface']};
                color: {self.theme['text_disabled']};
                border: 1px solid {self.theme['divider']};
            }}
            ChromeButton:focus {{
                outline: 2px solid {self.theme['focus']};
                outline-offset: 2px;
            }}
        """)
    
    def _get_variant_colors(self):
        """获取Chrome风格的颜色配置"""
        # 兼容原有的variant名称
        if self.variant == "primary":
            variant = "filled"
        elif self.variant == "secondary":
            variant = "outlined"
        else:
            variant = self.variant
            
        if variant == "filled":
            # Chrome填充按钮（主要操作）
            return {
                'bg': self.theme['primary'],
                'bg_hover': self._overlay_color(self.theme['primary'], self.theme['text_light'], 0.08),
                'bg_pressed': self._overlay_color(self.theme['primary'], self.theme['text_light'], 0.12),
                'text': self.theme['text_light'],
                'border': 'none',
                'border_hover': 'none',
                'border_pressed': 'none'
            }
        elif variant == "outlined":
            # Chrome轮廓按钮（次要操作）
            return {
                'bg': 'transparent',
                'bg_hover': self._overlay_color(self.theme['primary'], self.theme['primary'], 0.04),
                'bg_pressed': self._overlay_color(self.theme['primary'], self.theme['primary'], 0.08),
                'text': self.theme['primary'],
                'text_hover': self.theme['text'],  # hover状态使用主文本颜色确保可读性
                'border': f'1px solid {self.theme["card_border"]}',
                'border_hover': f'1px solid {self.theme["primary"]}',
                'border_pressed': f'1px solid {self.theme["primary"]}'
            }
        elif variant == "text":
            # Chrome文本按钮（最不重要的操作）
            return {
                'bg': 'transparent',
                'bg_hover': self._overlay_color(self.theme['primary'], self.theme['primary'], 0.04),
                'bg_pressed': self._overlay_color(self.theme['primary'], self.theme['primary'], 0.08),
                'text': self.theme['primary'],
                'border': 'none',
                'border_hover': 'none',
                'border_pressed': 'none'
            }
        elif variant == "success":
            # 成功状态按钮
            return {
                'bg': self.theme['success'],
                'bg_hover': self._overlay_color(self.theme['success'], self.theme['text_light'], 0.08),
                'bg_pressed': self._overlay_color(self.theme['success'], self.theme['text_light'], 0.12),
                'text': self.theme['text_light'],
                'border': 'none',
                'border_hover': 'none',
                'border_pressed': 'none'
            }
        elif variant == "warning":
            # 警告状态按钮
            return {
                'bg': self.theme['warning'],
                'bg_hover': self._overlay_color(self.theme['warning'], self.theme['text_light'], 0.08),
                'bg_pressed': self._overlay_color(self.theme['warning'], self.theme['text_light'], 0.12),
                'text': self.theme['text_light'],
                'border': 'none',
                'border_hover': 'none',
                'border_pressed': 'none'
            }
        elif variant == "error":
            # 错误状态按钮
            return {
                'bg': self.theme['error'],
                'bg_hover': self._overlay_color(self.theme['error'], self.theme['text_light'], 0.08),
                'bg_pressed': self._overlay_color(self.theme['error'], self.theme['text_light'], 0.12),
                'text': self.theme['text_light'],
                'border': 'none',
                'border_hover': 'none',
                'border_pressed': 'none'
            }
        else:
            # 默认为filled样式
            return {
                'bg': self.theme['primary'],
                'bg_hover': self._overlay_color(self.theme['primary'], self.theme['text_light'], 0.08),
                'bg_pressed': self._overlay_color(self.theme['primary'], self.theme['text_light'], 0.12),
                'text': self.theme['text_light'],
                'border': 'none',
                'border_hover': 'none',
                'border_pressed': 'none'
            }

    def _overlay_color(self, base_color, overlay_color, opacity):
        """颜色叠加效果（模拟Chrome的颜色叠加）"""
        base = QColor(base_color)
        overlay = QColor(overlay_color)
        
        # 简单的颜色混合
        r = int(base.red() * (1 - opacity) + overlay.red() * opacity)
        g = int(base.green() * (1 - opacity) + overlay.green() * opacity)
        b = int(base.blue() * (1 - opacity) + overlay.blue() * opacity)
        
        return QColor(r, g, b).name()

    def enterEvent(self, event):
        """鼠标进入事件"""
        self._is_hovered = True
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self._is_hovered = False
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        self._is_pressed = True
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self._is_pressed = False
        super().mouseReleaseEvent(event)

    def set_variant(self, variant):
        """动态设置按钮变体"""
        self.variant = variant
        self._apply_styles()

    def set_size(self, size):
        """动态设置按钮大小"""
        self.button_size = size
        self._setup_ui()
        self._apply_styles()