"""UI组件模块

本模块包含了应用程序中使用的所有UI组件，包括：
- StatCard: 统计数据卡片组件
- ActionCard: 操作面板卡片组件
- ChromeButton: Chrome风格按钮组件
- NavigationButton: 导航按钮组件
- LogArea: 日志显示区域组件
- ProgressBar: 进度条组件
- TextEdit: 文本编辑器组件

所有组件都采用Chrome风格设计，支持主题切换和现代化UI交互。
"""

from .stat_card import StatCard
from .action_card import ActionCard
from .chrome_button import ChromeButton
from .navigation_button import NavigationButton
from .log_area import LogArea
from .progress_bar import ProgressBar
from .text_edit import TextEdit

__all__ = [
    'StatCard',
    'ActionCard', 
    'ChromeButton',
    'NavigationButton',
    'LogArea',
    'ProgressBar',
    'TextEdit'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'QW Browser Team'
__description__ = 'Chrome风格UI组件库'