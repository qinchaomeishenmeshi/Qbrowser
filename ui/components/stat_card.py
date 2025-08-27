from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QFont
from ..config import THEMES, CURRENT_THEME, FONTS, LAYOUT


class StatCard(QWidget):
    """统计数据卡片组件
    
    支持渐变背景和普通背景两种样式，用于显示统计数据。
    包含标题、数值和描述文本的显示。
    """
    
    # 点击信号
    clicked = pyqtSignal()
    
    def __init__(self, title="", value="0", description="", variant="normal", parent=None):
        """初始化统计卡片
        
        Args:
            title (str): 卡片标题
            value (str): 统计数值
            description (str): 描述文本
            variant (str): 卡片样式，"gradient" 或 "normal"
            parent: 父组件
        """
        super().__init__(parent)
        self.title = title
        self.value = value
        self.description = description
        self.variant = variant
        self.theme = THEMES[CURRENT_THEME]
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI布局"""
        self.setFixedSize(200, 120)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(LAYOUT["card_padding"], LAYOUT["card_padding"], 
                                LAYOUT["card_padding"], LAYOUT["card_padding"])
        layout.setSpacing(5)
        
        # 标题标签
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = QFont()
        font.setFamily(FONTS["small"][0])
        font.setPointSize(FONTS["small"][1])
        self.title_label.setFont(font)
        
        # 数值标签
        self.value_label = QLabel(self.value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = QFont()
        font.setFamily(FONTS["title"][0])
        font.setPointSize(FONTS["title"][1])
        font.setBold(True)
        self.value_label.setFont(font)
        
        # 描述标签
        self.desc_label = QLabel(self.description)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.desc_label.setWordWrap(True)
        font = QFont()
        font.setFamily(FONTS["small"][0])
        font.setPointSize(FONTS["small"][1])
        self.desc_label.setFont(font)
        
        # 添加到布局
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()
    
    def _apply_styles(self):
        """应用样式"""
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(self.theme["shadow"]))
        self.setGraphicsEffect(shadow)
        
        # 设置样式
        if self.variant == "gradient":
            # 渐变背景样式
            self.title_label.setStyleSheet(f"color: {self.theme['text_light']};")
            self.value_label.setStyleSheet(f"color: {self.theme['text_light']};")
            self.desc_label.setStyleSheet(f"color: {self.theme['text_light']};")
        else:
            # 普通背景样式
            self.setStyleSheet(f"""
                StatCard {{
                    background-color: {self.theme['card']};
                    border: 1px solid {self.theme['card_border']};
                    border-radius: {LAYOUT['border_radius']}px;
                }}
                StatCard:hover {{
                    background-color: {self.theme['card_hover']};
                }}
            """)
            
            self.title_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
            self.value_label.setStyleSheet(f"color: {self.theme['text']};")
            self.desc_label.setStyleSheet(f"color: {self.theme['text_tertiary']};")
    
    def paintEvent(self, event):
        """自定义绘制事件，用于渐变背景"""
        if self.variant == "gradient":
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 创建渐变
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(self.theme["primary"]))
            gradient.setColorAt(1, QColor(self.theme["accent"]))
            
            # 绘制圆角矩形
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), LAYOUT["border_radius"], LAYOUT["border_radius"])
        else:
            super().paintEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def update_content(self, title=None, value=None, description=None):
        """更新卡片内容
        
        Args:
            title (str, optional): 新标题
            value (str, optional): 新数值
            description (str, optional): 新描述
        """
        if title is not None:
            self.title = title
            self.title_label.setText(title)
        
        if value is not None:
            self.value = value
            self.value_label.setText(value)
        
        if description is not None:
            self.description = description
            self.desc_label.setText(description)
    
    def set_variant(self, variant):
        """设置卡片样式变体
        
        Args:
            variant (str): "gradient" 或 "normal"
        """
        self.variant = variant
        self._apply_styles()
        self.update()