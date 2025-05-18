import asyncio

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPainter, QColor, QLinearGradient, QBrush
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy, QGraphicsDropShadowEffect
)

from ui.config import THEMES, CURRENT_THEME, FONTS, LAYOUT


class StatCard(QWidget):
    """统计数据卡片组件"""

    def __init__(self, title, content="", icon=None, gradient=False, parent=None):
        super().__init__(parent)
        self.title = title
        self.content = content
        self.icon = icon
        self.gradient = gradient
        self.init_ui()

    def init_ui(self):
        theme = THEMES[CURRENT_THEME]

        # 基础样式设置，两种卡片类型共有
        base_style = f"""
            border-radius: {LAYOUT['border_radius']}px;
            min-height: 160px;
        """

        # 使用渐变背景，如果指定了gradient=True
        if self.gradient:
            # 渐变样式将在paintEvent中处理
            self.setStyleSheet(f"""
                {base_style}
                color: {theme['text_light']};
            """)
        else:
            # 非渐变背景，使用普通卡片背景色
            self.setStyleSheet(f"""
                {base_style}
                background-color: {theme['card']};
                color: {theme['text']};
                border: 1px solid {theme['card_border']};
            """)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # 使用垂直布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 标题容器
        title_container = QWidget()
        title_container.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 标题
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Bold))
        if self.gradient:
            self.title_label.setStyleSheet(f"color: {theme['text_light']}; background: transparent;")
        else:
            self.title_label.setStyleSheet(f"color: {theme['text']}; background: transparent;")
        title_layout.addWidget(self.title_label)

        # 添加标题容器
        layout.addWidget(title_container)

        # 内容容器
        content_container = QWidget()
        content_container.setStyleSheet("background: transparent;")
        content_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 内容标签
        self.content_label = QLabel(self.content)
        # 两种卡片类型使用相同大小的字体，确保视觉统一
        self.content_label.setFont(QFont(FONTS["title"][0], 24, QFont.Weight.Bold))
        
        # 设置标签样式
        if self.gradient:
            self.content_label.setStyleSheet(f"""
                color: {theme['text_light']};
                background: transparent;
                qproperty-alignment: AlignCenter;
            """)
        else:
            self.content_label.setStyleSheet(f"""
                color: {theme['primary']};
                background: transparent;
                qproperty-alignment: AlignCenter;
            """)
        
        content_layout.addWidget(self.content_label)

        # 添加内容容器
        layout.addWidget(content_container)

    def set_content(self, content):
        """设置卡片内容"""
        self.content = content
        self.content_label.setText(content)

    def paintEvent(self, event):
        """自定义绘制事件，用于实现渐变背景"""
        if self.gradient:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 创建渐变
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            theme = THEMES[CURRENT_THEME]

            # 使用主题色和强调色创建渐变
            gradient.setColorAt(0, QColor(theme['primary']))
            gradient.setColorAt(1, QColor(theme['accent']))

            # 绘制圆角矩形
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(0, 0, self.width(), self.height(),
                                    LAYOUT['border_radius'], LAYOUT['border_radius'])
        else:
            super().paintEvent(event)


class ActionCard(QWidget):
    """操作面板卡片组件 - Chrome风格"""

    def __init__(self, title, actions=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.actions = actions or []
        self.init_ui()
        
        # 添加阴影效果
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.shadow.setOffset(0, 2)
        self.setGraphicsEffect(self.shadow)
        
        # 设置鼠标光标为手型
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def init_ui(self):
        theme = THEMES[CURRENT_THEME]

        # 设置固定高度为128px
        self.setFixedHeight(128)
        self.setStyleSheet(f"""
            background-color: {theme['card']};
            color: {theme['text']};
            border-radius: {LAYOUT['border_radius']}px;
            border: 1px solid rgba(0, 0, 0, 0.06);
        """)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # 主布局 - 减小内边距以节省空间
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        # 标题容器
        title_container = QWidget()
        title_container.setStyleSheet("background: transparent;")
        title_container.setFixedHeight(30)  # 标题区域高度固定
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 标题 - Chrome风格标题
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Medium))
        self.title_label.setStyleSheet(f"""
            color: {theme['text']};
            padding-left: 2px;
        """)
        title_layout.addWidget(self.title_label)

        # 添加标题容器
        layout.addWidget(title_container)

        # 添加分割线 - Chrome风格分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.08); margin: 0px;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # 按钮容器 - 使用流式布局容器
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background: transparent;")
        buttons_container.setFixedHeight(40)  # 按钮区域高度固定40px
        
        # 使用流式布局
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(12)  # 按钮之间的间距
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 添加按钮 - Chrome风格按钮
        for action in self.actions:
            btn = ChromeButton(
                text=action['text'],
                color=action.get('color', theme['primary']),
                hover_color=action.get('hover_color', None),
                callback=action.get('callback', None)
            )
            buttons_layout.addWidget(btn)

        # 添加弹性间隔，使按钮靠左对齐
        buttons_layout.addStretch()
            
        # 添加按钮容器
        layout.addWidget(buttons_container)
        
        # 添加底部间隔，保持总高度128px
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spacer.setStyleSheet("background: transparent;")
        layout.addWidget(spacer)
        
    def enterEvent(self, event):
        """鼠标进入事件 - 加深阴影效果"""
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        self.shadow.setOffset(0, 3)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件 - 恢复阴影效果"""
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.shadow.setOffset(0, 2)
        super().leaveEvent(event)


class ChromeButton(QPushButton):
    """Chrome风格按钮"""
    
    def __init__(self, text, color, hover_color=None, callback=None, parent=None):
        super().__init__(text, parent)
        self.base_color = color
        self.hover_color = hover_color or QColor(color).lighter(110).name()
        self.pressed_color = QColor(color).darker(110).name()
        
        # 设置按钮属性
        self.setFixedHeight(36)
        self.setMinimumWidth(100)
        self.setFont(QFont(FONTS["bold"][0], FONTS["bold"][1], QFont.Weight.Medium))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 应用Chrome风格
        self.apply_chrome_style()
        
        # 连接回调
        if callback:
            self.clicked.connect(callback)
            
    def apply_chrome_style(self):
        """应用Chrome风格样式"""
        theme = THEMES[CURRENT_THEME]
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.base_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0px 16px;
                font-weight: medium;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {self.hover_color};
            }}
            QPushButton:pressed {{
                background-color: {self.pressed_color};
            }}
            QPushButton:disabled {{
                background-color: {theme['inactive']};
                color: rgba(255, 255, 255, 0.7);
            }}
        """)
        
        # 使用QGraphicsDropShadowEffect替代CSS的box-shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(4)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.shadow.setOffset(0, 1)
        self.setGraphicsEffect(self.shadow)
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        self.shadow.setBlurRadius(8)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setOffset(0, 2)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.shadow.setBlurRadius(4)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.shadow.setOffset(0, 1)
        super().leaveEvent(event)


class DashboardPage(QWidget):
    """仪表盘页面 - 简化版，只包含快捷操作面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        theme = THEMES[CURRENT_THEME]

        self.setStyleSheet(f"""
            background-color: {theme['background']};
            color: {theme['text']};
            padding: 0px;
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        # 创建简化版标题
        title_label = QLabel("浏览器控制中心")
        title_label.setFont(QFont(FONTS["title"][0], 20, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {theme['text']};")
        main_layout.addWidget(title_label)
        
        # 说明文字
        description = QLabel("使用下方按钮进行浏览器的批量管理")
        description.setFont(QFont(FONTS["regular"][0], 14))
        description.setStyleSheet(f"color: {theme['text_secondary']};")
        main_layout.addWidget(description)
        
        # 添加一点间距
        main_layout.addSpacing(10)

        # 创建快捷操作面板 - 直接连接到类方法
        actions = [
            {
                "text": "批量启动", 
                "color": theme["success"],
                "hover_color": QColor(theme["success"]).lighter(110).name(),
                "callback": self._on_batch_start_clicked
            },
            {
                "text": "一键关闭", 
                "color": theme["error"],
                "hover_color": QColor(theme["error"]).lighter(110).name(),
                "callback": self._on_batch_stop_clicked
            }
        ]
        self.action_panel = ActionCard("快捷操作面板", actions)
        
        # 将操作面板直接添加到主布局
        main_layout.addWidget(self.action_panel)
        
        # 添加伸缩项，使操作面板位于顶部
        main_layout.addStretch()

    # 非异步的点击处理方法
    def _on_batch_start_clicked(self):
        """处理批量启动按钮点击"""
        # 使用事件循环创建任务
        loop = asyncio.get_event_loop()
        loop.create_task(self._do_batch_start())

    def _on_batch_stop_clicked(self):
        """处理一键关闭按钮点击"""
        # 使用事件循环创建任务
        loop = asyncio.get_event_loop()
        loop.create_task(self._do_batch_stop())

    # 实际执行批量启动的异步方法
    async def _do_batch_start(self):
        """执行批量启动操作"""
        if hasattr(self.parent(), 'start_browsers'):
            try:
                await self.parent().start_browsers()
            except Exception as e:
                print(f"批量启动出错: {e}")

    # 实际执行一键关闭的异步方法
    async def _do_batch_stop(self):
        """执行一键关闭操作"""
        if hasattr(self.parent(), 'stop_browsers'):
            try:
                await self.parent().stop_browsers()
            except Exception as e:
                print(f"一键关闭出错: {e}")

    def update_stats(self, instance_stats=None, resource_stats=None):
        """更新仪表盘统计数据 - 此方法保留空实现以兼容现有调用"""
        # 我们已移除统计卡片，此方法仅作为兼容保留
        pass
