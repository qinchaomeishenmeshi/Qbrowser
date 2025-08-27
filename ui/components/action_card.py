from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor
from ..config import THEMES, CURRENT_THEME, FONTS, LAYOUT


class ActionCard(QWidget):
    """操作面板卡片组件
    
    带有Chrome风格阴影和悬停效果的卡片组件，用于显示操作项目。
    包含标题和描述文本，支持点击事件。
    """
    
    # 点击信号
    clicked = pyqtSignal()
    
    def __init__(self, title="", description="", parent=None):
        """初始化操作卡片
        
        Args:
            title (str): 卡片标题
            description (str): 描述文本
            parent: 父组件
        """
        super().__init__(parent)
        self.title = title
        self.description = description
        self.theme = THEMES[CURRENT_THEME]
        self._is_hovered = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI布局"""
        self.setFixedHeight(80)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(LAYOUT["card_padding"], LAYOUT["card_padding"], 
                                LAYOUT["card_padding"], LAYOUT["card_padding"])
        layout.setSpacing(5)
        
        # 标题标签
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        font = QFont()
        font.setFamily(FONTS["heading"][0])
        font.setPointSize(FONTS["heading"][1])
        font.setBold(True)
        self.title_label.setFont(font)
        
        # 描述标签
        self.desc_label = QLabel(self.description)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.desc_label.setWordWrap(True)
        font = QFont()
        font.setFamily(FONTS["regular"][0])
        font.setPointSize(FONTS["regular"][1])
        self.desc_label.setFont(font)
        
        # 添加到布局
        layout.addWidget(self.title_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()
    
    def _apply_styles(self):
        """应用样式"""
        # 添加阴影效果
        self._update_shadow()
        
        # 设置基础样式
        self.setStyleSheet(f"""
            ActionCard {{
                background-color: {self.theme['card']};
                border: 1px solid {self.theme['card_border']};
                border-radius: {LAYOUT['border_radius']}px;
            }}
        """)
        
        # 设置文本颜色
        self.title_label.setStyleSheet(f"color: {self.theme['text']};")
        self.desc_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
    
    def _update_shadow(self, hovered=False):
        """更新阴影效果
        
        Args:
            hovered (bool): 是否为悬停状态
        """
        shadow = QGraphicsDropShadowEffect()
        
        if hovered:
            # 悬停时的阴影效果
            shadow.setBlurRadius(20)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QColor(0, 0, 0, 40))  # 更深的阴影
        else:
            # 默认阴影效果
            shadow.setBlurRadius(10)
            shadow.setXOffset(0)
            shadow.setYOffset(2)
            shadow.setColor(QColor(0, 0, 0, 20))  # 轻微阴影
        
        self.setGraphicsEffect(shadow)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        self._is_hovered = True
        self._update_shadow(hovered=True)
        
        # 更新背景色
        self.setStyleSheet(f"""
            ActionCard {{
                background-color: {self.theme['card_hover']};
                border: 1px solid {self.theme['card_border']};
                border-radius: {LAYOUT['border_radius']}px;
            }}
        """)
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self._is_hovered = False
        self._update_shadow(hovered=False)
        
        # 恢复背景色
        self.setStyleSheet(f"""
            ActionCard {{
                background-color: {self.theme['card']};
                border: 1px solid {self.theme['card_border']};
                border-radius: {LAYOUT['border_radius']}px;
            }}
        """)
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def update_content(self, title=None, description=None):
        """更新卡片内容
        
        Args:
            title (str, optional): 新标题
            description (str, optional): 新描述
        """
        if title is not None:
            self.title = title
            self.title_label.setText(title)
        
        if description is not None:
            self.description = description
            self.desc_label.setText(description)
    
    def set_enabled(self, enabled):
        """设置卡片启用状态
        
        Args:
            enabled (bool): 是否启用
        """
        super().setEnabled(enabled)
        
        if enabled:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.title_label.setStyleSheet(f"color: {self.theme['text']};")
            self.desc_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.title_label.setStyleSheet(f"color: {self.theme['inactive']};")
            self.desc_label.setStyleSheet(f"color: {self.theme['inactive']};")