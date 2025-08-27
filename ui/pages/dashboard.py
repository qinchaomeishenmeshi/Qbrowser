import asyncio

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QLinearGradient, QBrush
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)

from ui.config import THEMES, CURRENT_THEME, FONTS, LAYOUT
# 导入UI组件
from ui.components import StatCard, ActionCard, ChromeButton


class DashboardPage(QWidget):
    """仪表盘页面 - 简化版，只包含快捷操作面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        theme = THEMES[CURRENT_THEME]

        self.setStyleSheet(
            f"""
            background-color: {theme['background']};
            color: {theme['text']};
            padding: 0px;
        """
        )

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

        # 创建快捷操作面板
        self.action_panel = ActionCard("快捷操作面板", "使用下方按钮进行浏览器的批量管理")
        main_layout.addWidget(self.action_panel)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 批量启动按钮
        start_button = ChromeButton("批量启动", variant="success", size="medium")
        start_button.clicked.connect(self._on_batch_start_clicked)

        # 一键关闭按钮
        stop_button = ChromeButton("一键关闭", variant="error", size="medium")
        stop_button.clicked.connect(self._on_batch_stop_clicked)
        
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)

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
        if hasattr(self.parent(), "start_browsers"):
            try:
                await self.parent().start_browsers()
            except Exception as e:
                print(f"批量启动出错: {e}")

    # 实际执行一键关闭的异步方法
    async def _do_batch_stop(self):
        """执行一键关闭操作"""
        if hasattr(self.parent(), "stop_browsers"):
            try:
                await self.parent().stop_browsers()
            except Exception as e:
                print(f"一键关闭出错: {e}")

    def update_stats(self, instance_stats=None, resource_stats=None):
        """更新仪表盘统计数据 - 此方法保留空实现以兼容现有调用"""
        # 我们已移除统计卡片，此方法仅作为兼容保留
        pass
