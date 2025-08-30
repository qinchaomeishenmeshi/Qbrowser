import asyncio
import os
import subprocess
import sys
import time
import webbrowser

from utils.common_logger import get_logger

logger = get_logger(__name__)

# PyQt导入
from PyQt6.QtCore import Qt, QTimer, QUrl

# 安全导入 QtWebEngineWidgets
# 检查是否为轻量版模式
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    LITE_MODE = False
except ImportError as e:
    print(f"[WARNING] QtWebEngineWidgets 导入失败: {e}")
    print("[INFO] 轻量版模式 - 将使用外部浏览器")
    QWebEngineView = None
    LITE_MODE = True
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QLabel,
    QButtonGroup,
    QMessageBox,
    QSizePolicy,
    QFrame,
    QScrollArea,
    QGraphicsDropShadowEffect,
)
from qasync import asyncSlot

# 项目内部导入
from api.api_server import run_server
from app import LogSignal, is_admin, App
from browser.browser_operator import browser_operator
from conf import BASE_DIR, resource_path
from service.browser_service import browser_service
from ui.config import THEMES, CURRENT_THEME, LAYOUT, FONTS
from utils.user_data_manager import get_user_data_manager

# 导入UI组件
from ui.components import (
    StatCard,
    ActionCard,
    ChromeButton,
    NavigationButton,
    LogArea,
    ProgressBar,
    TextEdit,
)

# 导入定时任务相关模块
from worker.scheduler_client import scheduler_client


class ModernApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 保持与当前App相同的属性名称，便于功能迁移
        self.text_edit = None
        self.progress = None
        self.clear_btn = None
        self.load_btn = None
        self.stop_btn = None
        self.start_btn = None
        self.log_area = None

        # 继承原始App的信号和服务
        self.log_signal = LogSignal()
        self.log_signal.log_updated.connect(self.update_log)
        self.browser_service = browser_service
        self.browser_operator = browser_operator
        self.frpc_process = None
        self.scheduler_client = scheduler_client
        self.settings_server_process = None
        
        # 初始化用户数据管理器
        self.user_data_manager = get_user_data_manager()

        # 初始化UI
        self.setup_fonts()
        self.init_ui()

        # 检查管理员权限，与原始代码相同
        if sys.platform == "win32" and not is_admin():
            logger.warning("程序未以管理员权限运行，某些功能可能受限")
            QMessageBox.warning(
                self,
                "权限提示",
                "程序没有以管理员权限运行。\n在Windows上，浏览器自动化和frpc服务可能需要管理员权限。\n请考虑以管理员身份重新运行程序。",
            )

        # 使用同步方法加载基本缓存
        self.load_cache()

        # 使用QTimer在Qt事件循环启动后执行异步初始化和配置加载
        QTimer.singleShot(0, self._schedule_async_init)

        # 延迟加载user_ids.txt配置文件，确保UI完全初始化
        QTimer.singleShot(100, self.load_user_ids_on_startup)

    def setup_fonts(self):
        """设置应用字体"""
        # 可以在这里添加字体加载逻辑
        pass

    def _hex_to_rgba(self, hex_color, opacity):
        """将十六进制颜色转换为RGBA格式

        Args:
            hex_color (str): 十六进制颜色值
            opacity (float): 透明度 (0-1)

        Returns:
            str: RGBA颜色值
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}, {opacity}"

    def init_ui(self):
        # Chrome风格窗口设置
        theme = THEMES[CURRENT_THEME]
        self.setWindowTitle("QW-Browser")
        self.setGeometry(100, 100, 1200, 800)  # Chrome典型尺寸

        # Chrome风格全局样式
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {theme['background']};
                color: {theme['text']};
                border: none;
            }}
            /* Chrome风格滚动条 */
            QScrollBar:vertical {{
                border: none;
                background: {theme['background']};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['inactive']};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: {theme['background']};
                height: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {theme['inactive']};
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {theme['text_secondary']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """
        )

        # 创建主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建Chrome风格侧边栏
        self.create_sidebar()

        # 创建Chrome风格内容区
        self.create_content_area()

        # 默认显示浏览器实例页面
        QTimer.singleShot(0, self.show_instances)

    def create_sidebar(self):
        """创建Chrome风格侧边栏"""
        theme = THEMES[CURRENT_THEME]

        # Chrome风格侧边栏容器
        self.sidebar_container = QWidget()
        self.sidebar_container.setFixedWidth(LAYOUT["sidebar_width"])

        # Chrome风格侧边栏样式 - 简洁的背景色和边框
        self.sidebar_container.setStyleSheet(
            f"""
            QWidget {{
                background-color: {theme['surface']};
                border: none;
                border-right: 1px solid {theme['divider']};
            }}
        """
        )

        sidebar_container_layout = QVBoxLayout(self.sidebar_container)
        sidebar_container_layout.setSpacing(0)
        sidebar_container_layout.setContentsMargins(0, 0, 0, 0)

        # Chrome风格标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(LAYOUT["toolbar_height"])
        title_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['surface']};
                border: none;
            }}
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 0, 16, 0)
        
        # 应用标题 - Chrome风格
        title = QLabel("QW-Browser")
        title.setFont(QFont(FONTS["title"][0], FONTS["title"][1], QFont.Weight.Medium))
        title.setStyleSheet(f"""
            QLabel {{
                color: {theme['text']};
                font-weight: 500;
                padding: 4px 0;
                margin: 0;
                border: none;
                background: transparent;
            }}
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        sidebar_container_layout.addWidget(title_bar)

        # 创建导航栏滚动区域
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.sidebar_scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: {theme['surface']};
                border: none;
            }}
        """
        )

        # 创建实际的导航栏内容
        self.sidebar = QWidget()
        self.sidebar.setStyleSheet(
            f"""
            QWidget {{
                background-color: transparent;
                color: {theme['text']};
            }}
        """
        )

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(
            LAYOUT["sidebar_padding"],
            LAYOUT["sidebar_padding"],
            LAYOUT["sidebar_padding"],
            LAYOUT["sidebar_padding"],
        )
        sidebar_layout.setSpacing(LAYOUT["nav_button_spacing"])

        # 创建导航按钮组
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)  # 确保只有一个按钮被选中

        # 保留浏览器实例按钮
        self.instances_btn = self.create_nav_button("浏览器管理", "browser")
        self.instances_btn.clicked.connect(self.show_instances)
        self.instances_btn.setChecked(True)  # 默认选中
        self.nav_button_group.addButton(self.instances_btn)
        sidebar_layout.addWidget(self.instances_btn)

        self.scheduler_btn = self.create_nav_button("定时任务", "schedule")
        self.scheduler_btn.clicked.connect(self.show_scheduler)
        self.nav_button_group.addButton(self.scheduler_btn)
        sidebar_layout.addWidget(self.scheduler_btn)

        # 添加设置按钮
        self.settings_btn = self.create_nav_button("设置", "settings")
        self.settings_btn.clicked.connect(self.show_settings)
        self.nav_button_group.addButton(self.settings_btn)
        sidebar_layout.addWidget(self.settings_btn)

        # 添加伸缩项，使按钮靠上对齐
        sidebar_layout.addStretch()

        # Chrome风格底部区域
        bottom_container = QWidget()
        bottom_container.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['surface']};
                border: none;
                border-top: 1px solid {theme['divider']};
                padding: 12px 16px;
            }}
        """)
        
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 8, 0, 8)
        
        # 版本信息
        version_label = QLabel("QW-Browser v2.0.0")
        version_label.setStyleSheet(
            f"""
            QLabel {{
                color: {theme['text_tertiary']};
                font-size: 10px;
                font-weight: 400;
                padding: 2px 0;
                margin: 0;
                border: none;
                background: transparent;
            }}
        """
        )
        bottom_layout.addWidget(version_label)
        
        sidebar_layout.addWidget(bottom_container)

        # 设置滚动区域的widget
        self.sidebar_scroll.setWidget(self.sidebar)

        # 将滚动区域添加到容器
        sidebar_container_layout.addWidget(self.sidebar_scroll)

        # 添加到主布局
        self.main_layout.addWidget(self.sidebar_container)

    def add_sidebar_separator(self, layout):
        """添加侧边栏分隔线"""
        theme = THEMES[CURRENT_THEME]
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {theme['divider']};")
        layout.addWidget(separator)
        layout.addSpacing(10)  # 分隔线下方添加间距

    def create_nav_button(self, text, icon_name=None):
        """创建Chrome风格导航按钮"""
        # Chrome风格不使用图标，icon_name参数保持兼容性但不使用

        button = NavigationButton(text)
        button.setCheckable(True)
        return button

    def create_content_area(self):
        # 创建右侧内容区
        theme = THEMES[CURRENT_THEME]

        # 创建内容区域容器
        self.content_container = QWidget()
        self.content_container.setStyleSheet(
            f"""
            background-color: {theme['background']};
        """
        )

        content_container_layout = QVBoxLayout(self.content_container)
        content_container_layout.setContentsMargins(0, 0, 0, 0)
        content_container_layout.setSpacing(0)

        # 创建顶部工具栏
        self.create_topbar()

        # 创建内容区域
        self.content_area = QWidget()
        self.content_area.setStyleSheet(
            f"""
            background-color: {theme['background']};
            color: {theme['text']};
        """
        )

        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(
            LAYOUT["margin"], LAYOUT["margin"], LAYOUT["margin"], LAYOUT["margin"]
        )

        # 内容页面栈
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)

        # 添加各页面到栈
        self.init_dashboard_page()
        self.init_instance_page()
        self.init_scheduler_page()
        self.init_data_page()
        self.init_settings_page()

        # 将内容区域添加到容器
        content_container_layout.addWidget(self.content_area)

        # 添加到主布局
        self.main_layout.addWidget(self.content_container)

    def create_topbar(self):
        """创建顶部工具栏 - Chrome风格"""
        theme = THEMES[CURRENT_THEME]

        # 创建顶部工具栏
        self.topbar = QWidget()
        self.topbar.setFixedHeight(60)
        self.topbar.setStyleSheet(
            f"""
            QWidget {{
                background-color: {theme['background']};
                border: none;
                border-bottom: 1px solid {theme['divider']};
            }}
        """)

        # 添加阴影效果
        topbar_shadow = QGraphicsDropShadowEffect(self.topbar)
        topbar_shadow.setBlurRadius(8)
        topbar_shadow.setColor(QColor(0, 0, 0, 8))
        topbar_shadow.setOffset(0, 1)
        self.topbar.setGraphicsEffect(topbar_shadow)

        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(24, 0, 24, 0)

        # 页面标题
        self.page_title = QLabel("浏览器控制中心")
        self.page_title.setFont(
            QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Medium)
        )
        self.page_title.setStyleSheet(f"""
            QLabel {{
                color: {theme['text']};
                font-weight: 500;
                padding: 0;
                margin: 0;
                border: none;
                background: transparent;
            }}
        """)
        topbar_layout.addWidget(self.page_title)

        # 添加伸缩项，将右侧按钮推到最右边
        topbar_layout.addStretch()
        
        # 在外部浏览器中打开按钮（只在定时任务页面显示）
        self.external_browser_btn = ChromeButton("在外部浏览器中打开", variant="secondary", size="small")
        self.external_browser_btn.clicked.connect(self.open_scheduler_in_browser)
        self.external_browser_btn.setVisible(False)  # 默认隐藏
        topbar_layout.addWidget(self.external_browser_btn)

        # 添加topbar到内容容器
        container_layout = self.content_container.layout()
        if container_layout is not None:
            container_layout.addWidget(self.topbar)

    def refresh_current_page(self):
        """刷新当前页面"""
        current_index = self.content_stack.currentIndex()

        if current_index == 0:  # 仪表盘
            # 直接使用事件循环创建任务
            loop = asyncio.get_event_loop()
            loop.create_task(self.update_dashboard_stats())
        # 根据需要添加其他页面的刷新逻辑

    def update_page_title(self, title):
        """更新页面标题"""
        self.page_title.setText(title)

    def init_dashboard_page(self):
        """初始化仪表盘页面"""
        # 确保DashboardPage已正确导入
        from ui.pages.dashboard import DashboardPage

        self.dashboard_page = DashboardPage(self)
        self.content_stack.addWidget(self.dashboard_page)

    def show_instances(self):
        """显示实例管理页面"""
        # 更新按钮激活状态
        self.instances_btn.setChecked(True)
        # 切换到实例管理页面 (索引 1)
        self.content_stack.setCurrentIndex(1)
        self.update_page_title("浏览器实例管理")
        
        # 隐藏顶部工具栏的外部浏览器按钮
        if hasattr(self, 'external_browser_btn'):
            self.external_browser_btn.setVisible(False)

    def show_scheduler(self):
        """显示定时任务页面"""
        # 更新按钮激活状态
        self.scheduler_btn.setChecked(True)
        
        # 先切换到定时任务页面 (索引 2)
        self.content_stack.setCurrentIndex(2)
        self.update_page_title("定时任务管理")
        
        # 显示顶部工具栏的外部浏览器按钮
        if hasattr(self, 'external_browser_btn'):
            self.external_browser_btn.setVisible(True)
        
        # 如果有WebEngine视图，确保加载正确的URL
        if hasattr(self, 'scheduler_web_view') and self.scheduler_web_view is not None:
            # 使用延迟加载，确保页面切换完成后再加载URL
            QTimer.singleShot(100, self._load_scheduler_url)

        if LITE_MODE or QWebEngineView is None:
            # 轻量版模式：页面已经切换，但同时在外部浏览器中打开
            import webbrowser

            try:
                webbrowser.open("http://127.0.0.1:6001/")
                # 不显示对话框，让用户可以在内部页面和外部浏览器之间选择
            except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开外部浏览器：{e}")
    
    def _load_scheduler_url(self):
        """延迟加载定时任务URL"""
        if hasattr(self, 'scheduler_web_view') and self.scheduler_web_view is not None:
            target_url = "http://127.0.0.1:6001/"
            current_url = self.scheduler_web_view.url().toString()
            
            if not current_url or current_url == "about:blank" or current_url != target_url:
                # 如果没有URL或URL不正确，设置新URL
                self.scheduler_web_view.setUrl(QUrl(target_url))
            else:
                # 如果URL正确，刷新页面
                self.scheduler_web_view.reload()

    def init_scheduler_page(self):
        """初始化定时任务管理页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if QWebEngineView is not None:
            # 使用WebEngine视图，去掉控制栏，让WebEngine占据全部空间
            self.scheduler_web_view = QWebEngineView()
            # 先不设置URL，等待页面切换时再加载
            layout.addWidget(self.scheduler_web_view)
        else:
            # WebEngine不可用时的备用方案
            fallback_container = QWidget()
            fallback_layout = QVBoxLayout(fallback_container)
            fallback_layout.setContentsMargins(40, 40, 40, 40)
            fallback_layout.setSpacing(20)
            
            fallback_label = QLabel("定时任务管理功能需要QtWebEngine支持")
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_label.setStyleSheet(
                """
                QLabel {
                    font-size: 16px;
                    color: #666;
                    padding: 20px;
                    background-color: #f5f5f5;
                    border-radius: 8px;
                }
            """
            )
            fallback_layout.addWidget(fallback_label)

            # 添加打开浏览器按钮
            open_browser_btn = ChromeButton(
                "在浏览器中打开", variant="primary", size="medium"
            )
            open_browser_btn.clicked.connect(lambda: self.open_scheduler_in_browser())
            fallback_layout.addWidget(open_browser_btn, 0, Qt.AlignmentFlag.AlignCenter)
            
            fallback_layout.addStretch()
            layout.addWidget(fallback_container)

        self.scheduler_page = page
        self.content_stack.addWidget(self.scheduler_page)

    def open_scheduler_in_browser(self):
        """在外部浏览器中打开定时任务管理页面"""
        import webbrowser

        try:
            webbrowser.open("http://127.0.0.1:6001/")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开浏览器: {e}")


    def init_instance_page(self):
        """初始化实例管理页面 - Chrome风格"""
        theme = THEMES[CURRENT_THEME]

        # 创建与原始App相同功能的实例管理页面，但使用Chrome风格设计
        page = QWidget()
        page.setStyleSheet(
            f"""
            background-color: {theme['background']};
            color: {theme['text']};
        """
        )

        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 创建用户ID输入卡片 - Chrome风格卡片
        input_card = QWidget()
        input_card.setStyleSheet(
            f"""
            background-color: {theme['card']};
            color: {theme['text']};
            border-radius: {LAYOUT["border_radius"]}px;
            border: 1px solid rgba(0, 0, 0, 0.06);
        """
        )

        # 添加卡片阴影
        card_shadow = QGraphicsDropShadowEffect(input_card)
        card_shadow.setBlurRadius(15)
        card_shadow.setColor(QColor(0, 0, 0, 20))
        card_shadow.setOffset(0, 2)
        input_card.setGraphicsEffect(card_shadow)

        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 15, 20, 15)
        input_layout.setSpacing(10)

        # 添加卡片标题
        card_title = QLabel("用户ID配置")
        card_title.setFont(
            QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Bold)
        )
        card_title.setStyleSheet(f"color: {theme['text']};")
        input_layout.addWidget(card_title)

        # 添加分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.08); margin: 0px;")
        separator.setFixedHeight(1)
        input_layout.addWidget(separator)

        # 输入提示文本
        input_hint = QLabel("请输入浏览器实例的用户ID，每行一个ID")
        input_hint.setFont(QFont(FONTS["regular"][0], FONTS["regular"][1]))
        input_hint.setStyleSheet(f"color: {theme['text_secondary']};")
        input_layout.addWidget(input_hint)

        # 文本输入区
        self.text_edit = TextEdit()
        self.text_edit.setMinimumHeight(100)  # 增加文本编辑区高度
        # 设置自动保存回调
        self.text_edit.set_auto_save_callback(self.save_user_ids_auto)
        input_layout.addWidget(self.text_edit)

        # 添加输入卡片到主布局
        layout.addWidget(input_card)

        # 创建操作按钮卡片 - Chrome风格卡片
        action_card = QWidget()
        action_card.setStyleSheet(
            f"""
            background-color: {theme['card']};
            color: {theme['text']};
            border-radius: {LAYOUT["border_radius"]}px;
            border: 1px solid rgba(0, 0, 0, 0.06);
        """
        )

        # 添加卡片阴影
        action_shadow = QGraphicsDropShadowEffect(action_card)
        action_shadow.setBlurRadius(15)
        action_shadow.setColor(QColor(0, 0, 0, 20))
        action_shadow.setOffset(0, 2)
        action_card.setGraphicsEffect(action_shadow)

        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(20, 15, 20, 15)
        action_layout.setSpacing(10)

        # 添加卡片标题
        action_title = QLabel("操作控制")
        action_title.setFont(
            QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Bold)
        )
        action_title.setStyleSheet(f"color: {theme['text']};")
        action_layout.setContentsMargins(20, 15, 20, 15)
        action_layout.addWidget(action_title)

        # 添加分割线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.08); margin: 0px;")
        separator2.setFixedHeight(1)
        action_layout.addWidget(separator2)

        # 按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.setSpacing(15)

        # 创建Chrome风格按钮
        self.start_btn = ChromeButton("启动浏览器", variant="success", size="medium")
        self.stop_btn = ChromeButton("一键关闭", variant="error", size="medium")
        self.load_btn = ChromeButton("加载配置", variant="primary", size="medium")
        self.clear_btn = ChromeButton("清除缓存", variant="warning", size="medium")

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()

        action_layout.addWidget(button_container)

        # 添加操作卡片到主布局
        layout.addWidget(action_card)

        # 创建进度与日志卡片 - Chrome风格卡片
        log_card = QWidget()
        log_card.setStyleSheet(
            f"""
            background-color: {theme['card']};
            color: {theme['text']};
            border-radius: {LAYOUT["border_radius"]}px;
            border: 1px solid rgba(0, 0, 0, 0.06);
        """
        )
        log_card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )

        # 添加卡片阴影
        log_shadow = QGraphicsDropShadowEffect(log_card)
        log_shadow.setBlurRadius(15)
        log_shadow.setColor(QColor(0, 0, 0, 20))
        log_shadow.setOffset(0, 2)
        log_card.setGraphicsEffect(log_shadow)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 15, 20, 15)
        log_layout.setSpacing(10)

        # 添加卡片标题
        log_title = QLabel("进度与日志")
        log_title.setFont(
            QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Bold)
        )
        log_title.setStyleSheet(f"color: {theme['text']};")
        log_layout.addWidget(log_title)

        # 添加分割线
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setStyleSheet(f"background-color: rgba(0, 0, 0, 0.08); margin: 0px;")
        separator3.setFixedHeight(1)
        log_layout.addWidget(separator3)

        # 进度条标题和进度条
        progress_title = QLabel("操作进度")
        progress_title.setFont(
            QFont(FONTS["regular"][0], FONTS["regular"][1], QFont.Weight.Bold)
        )
        progress_title.setStyleSheet(f"color: {theme['text']};")
        log_layout.addWidget(progress_title)

        self.progress = ProgressBar()
        log_layout.addWidget(self.progress)

        # 日志标题和日志区域
        log_area_title = QLabel("操作日志")
        log_area_title.setFont(
            QFont(FONTS["regular"][0], FONTS["regular"][1], QFont.Weight.Bold)
        )
        log_area_title.setStyleSheet(f"color: {theme['text']};")
        log_layout.addWidget(log_area_title)

        self.log_area = LogArea()
        log_layout.addWidget(self.log_area)

        # 添加日志卡片到主布局
        layout.addWidget(log_card)

        # 连接按钮信号到类的方法
        self.start_btn.clicked.connect(self.start_browsers)
        self.stop_btn.clicked.connect(self.stop_browsers)
        self.load_btn.clicked.connect(self.load_user_ids)
        self.clear_btn.clicked.connect(self.clear_cache)

        # 添加到栈
        self.content_stack.addWidget(page)

    def init_data_page(self):
        """初始化数据分析页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("数据分析页面 - 待开发")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.data_page = page
        self.content_stack.addWidget(self.data_page)

    def init_settings_page(self):
        """初始化设置页面 - 简化版本，因为直接在外部浏览器打开"""
        theme = THEMES[CURRENT_THEME]
        
        # 创建一个空白页面，因为设置功能直接在外部浏览器打开
        page = QWidget()
        page.setStyleSheet(f"""
            background-color: {theme['background']};
            color: {theme['text']};
        """)
        
        layout = QVBoxLayout(page)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # 显示提示信息
        info_label = QLabel("设置页面已在外部浏览器打开")
        info_label.setFont(QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Normal))
        info_label.setStyleSheet(f"color: {theme['text_secondary']}; text-align: center;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(info_label)
        layout.addStretch()
        
        self.settings_page = page
        self.content_stack.addWidget(self.settings_page)
        


    def update_log(self, msg: str):
        # 确保 self.log_area 存在
        if self.log_area:
            # LogArea组件使用append方法添加日志
            if hasattr(self.log_area, 'append'):
                self.log_area.append(msg)

    def load_cache(self):
        try:
            ids = self.browser_service.load_cache()
            if self.text_edit:
                # TextEdit组件使用setPlainText方法
                if hasattr(self.text_edit, 'setPlainText'):
                    self.text_edit.setPlainText("\n".join(ids))
                elif hasattr(self.text_edit, 'set_text'):
                    self.text_edit.set_text("\n".join(ids))
            logger.info(f"加载用户缓存成功: {ids}")
        except Exception as e:
            logger.error(f"加载用户缓存失败: {e}")


    async def update_dashboard_stats(self):
        """更新仪表盘统计数据"""
        try:
            # 获取实例数据
            managers = await self.browser_service.browser_store.get_all()
            running = sum(1 for m in managers if m.is_running)
            stopped = len(managers) - running

            instance_stats = f"运行: {running}  停止: {stopped}"
            resource_stats = "CPU: --  内存: --"  # 未来可扩展为实际资源监控

            # 更新仪表盘
            self.dashboard_page.update_stats(
                instance_stats=instance_stats, resource_stats=resource_stats
            )

        except Exception as e:
            logger.error(f"更新仪表盘统计数据失败: {e}")

    # 以下方法从原始App继承，保持功能一致性
    def _schedule_async_init(self):
        """使用事件循环安排异步初始化任务"""
        # 直接使用事件循环创建任务
        loop = asyncio.get_event_loop()
        loop.create_task(self.async_init())

    # 覆盖原始应用的async_init方法，添加仪表盘数据更新
    async def async_init(self):
        """异步初始化，加载端口和启动服务"""
        try:
            # 加载端口配置
            await self.load_ports()

            # 启动API服务
            try:
                run_server(host="127.0.0.1", port=6001)
                logger.info("FastAPI服务已启动")
                self.log_signal.log_updated.emit("FastAPI服务已启动")
            except Exception as e:
                logger.error(f"FastAPI服务启动失败: {e}")
                self.log_signal.log_updated.emit(f"FastAPI服务启动失败: {e}")

            # 启动配置服务器（Chrome配置服务）
            try:
                self._start_settings_server()
                logger.info("Chrome配置服务已启动")
            except Exception as e:
                logger.warning(f"Chrome配置服务启动失败: {e}")
                # 配置服务失败不影响主应用的运行，只是警告
                self.log_signal.log_updated.emit(f"注意: Chrome配置服务启动失败: {e}")

            # 启动定时任务服务
            try:
                await self.scheduler_client.start()
                task_count = len(self.scheduler_client.task_configs)
                enabled_count = sum(
                    1
                    for config in self.scheduler_client.task_configs.values()
                    if config.enabled
                )
                logger.info(
                    f"定时任务调度器启动成功，已加载 {task_count} 个任务配置，其中 {enabled_count} 个已启用"
                )
                self.log_signal.log_updated.emit(
                    f"定时任务调度器启动成功，已加载 {task_count} 个任务配置，其中 {enabled_count} 个已启用"
                )
            except Exception as e:
                logger.error(f"定时任务调度器启动失败: {e}")
                self.log_signal.log_updated.emit(f"定时任务调度器启动失败: {e}")

            # 仅在Windows系统上尝试启动frpc服务
            if sys.platform == "win32":
                try:
                    self.frpc_process = self._start_frpc()
                    if self.frpc_process:
                        self.log_signal.log_updated.emit("frpc服务已启动")
                    else:
                        self.log_signal.log_updated.emit(
                            "frpc服务启动失败，请确保以管理员权限运行程序"
                        )
                except Exception as e:
                    logger.error(f"frpc服务启动错误: {e}")
                    self.log_signal.log_updated.emit(f"frpc服务启动错误: {e}")

            logger.info("应用初始化完成")
            self.log_signal.log_updated.emit("应用初始化完成")

            # 更新仪表盘数据
            await self.update_dashboard_stats()

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            self.log_signal.log_updated.emit(f"初始化失败: {e}")

    # 覆盖原始应用的start_browsers方法，添加更新仪表盘的调用
    @asyncSlot()
    async def start_browsers(self):
        try:
            # 在Windows上检查权限
            if sys.platform == "win32" and not is_admin():
                from PyQt6.QtWidgets import QMessageBox
                result = QMessageBox.warning(
                    self,
                    "权限不足",
                    "程序没有以管理员权限运行，浏览器可能无法正常启动。\n是否继续尝试？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if result == QMessageBox.StandardButton.No:
                    self.log_signal.log_updated.emit("操作已取消")
                    return

            if not self.text_edit:
                self.log_signal.log_updated.emit("错误：文本输入框未初始化")
                return
                
            # 获取用户ID列表
            if hasattr(self.text_edit, 'toPlainText'):
                text = self.text_edit.toPlainText()
            else:
                text = ""
                
            ids = [
                l.strip()
                for l in text.splitlines()
                if l.strip()
            ]
            if not ids:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", "请输入至少一个 user_id。")
                return
            if len(ids) != len(set(ids)):
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "错误", "不允许重复的 user_id。")
                return

            self.browser_service.save_cache(ids)
            if self.start_btn:
                self.start_btn.setEnabled(False)
            if self.stop_btn:
                self.stop_btn.setEnabled(False)
            if self.progress:
                self.progress.setMaximum(len(ids))
                self.progress.setValue(0)

            results = await self.browser_service.start_browsers(ids)
            success_count = 0
            for idx, result in enumerate(results, 1):
                status = result["status"]
                if status == "started" or status == "already_running":
                    success_count += 1

                self.log_signal.log_updated.emit(
                    f"[{idx}/{len(results)}] {result['user_id']} {result['status']} (端口: {result.get('port', 'N/A')})"
                )
                if self.progress:
                    self.progress.setValue(idx)
                await asyncio.sleep(0.01)

        except Exception as e:
            self.log_signal.log_updated.emit(f"启动浏览器时发生错误: {e}")
            logger.error(f"启动浏览器失败: {e}", exc_info=True)
        finally:
            if self.start_btn:
                self.start_btn.setEnabled(True)
            if self.stop_btn:
                self.stop_btn.setEnabled(True)
            self.log_signal.log_updated.emit("启动浏览器操作已完成")
            await self.scheduler_client.update_all_task_configs()

    # 覆盖原始应用的stop_browsers方法，添加更新仪表盘的调用
    @asyncSlot()
    async def stop_browsers(self):
        try:
            if self.start_btn:
                self.start_btn.setEnabled(False)
            if self.stop_btn:
                self.stop_btn.setEnabled(False)
            self.log_signal.log_updated.emit("正在关闭所有浏览器...")
            await self.browser_service.stop_all_browsers()
            if self.progress:
                self.progress.setValue(0)
            self.log_signal.log_updated.emit("所有浏览器已关闭")
        except Exception as e:
            self.log_signal.log_updated.emit(f"关闭浏览器时发生错误: {e}")
            logger.error(f"关闭浏览器失败: {e}", exc_info=True)
        finally:
            if self.start_btn:
                self.start_btn.setEnabled(True)
            if self.stop_btn:
                self.stop_btn.setEnabled(True)

    # clear_cache是异步方法，需要装饰器
    @asyncSlot()
    async def clear_cache(self):
        try:
            # 实现清理缓存的逻辑
            self.browser_service.clear_cache()
            await self.browser_operator.clear_all_data()
            if self.text_edit:
                if hasattr(self.text_edit, 'clear'):
                    self.text_edit.clear()
                elif hasattr(self.text_edit, 'setPlainText'):
                    self.text_edit.setPlainText("")
            self.log_signal.log_updated.emit("缓存已清除")
            logger.info("缓存清除成功")
        except Exception as e:
            self.log_signal.log_updated.emit(f"清除缓存失败: {e}")
            logger.error(f"清除缓存失败: {e}")

    def save_cache(self):
        """保存缓存"""
        try:
            if self.text_edit:
                if hasattr(self.text_edit, 'toPlainText'):
                    text = self.text_edit.toPlainText()
                else:
                    text = ""
                ids = [l for l in text.splitlines() if l.strip()]
                self.browser_service.save_cache(ids)
                logger.info(f"保存用户缓存成功: {ids}")
        except Exception as e:
            logger.error(f"保存用户缓存失败: {e}")

    async def load_ports(self):
        """异步加载端口映射"""
        try:
            await self.browser_service.load_ports()
            logger.info("端口映射加载成功")
        except Exception as e:
            logger.error(f"加载端口映射失败: {e}")

    def _start_frpc(self):
        """启动frpc服务的占位实现"""
        logger.info("frpc服务启动功能待实现")
        return None

    def load_user_ids_on_startup(self):
        """应用启动时自动加载用户ID配置文件"""
        try:
            # 使用新的用户数据管理器加载用户ID
            ids = self.user_data_manager.load_user_ids()
            
            if ids and self.text_edit:  # 确保text_edit已初始化且有数据
                if hasattr(self.text_edit, 'setPlainText'):
                    self.text_edit.setPlainText("\n".join(ids))
                elif hasattr(self.text_edit, 'set_text'):
                    self.text_edit.set_text("\n".join(ids))
                logger.info(f"启动时自动加载了 {len(ids)} 个用户ID配置")
            elif not ids:
                logger.info("user_ids.txt文件为空")
        except Exception as e:
            logger.error(f"启动时加载user_ids.txt失败: {e}")

    def load_user_ids(self):
        """手动加载用户ID配置文件 - 基于App类但改进UI交互"""
        try:
            from conf import writable_path

            # 优先从可写目录加载，如果不存在则从资源目录加载
            writable_file_path = writable_path("user_ids.txt")
            resource_file_path = resource_path("user_ids.txt")

            file_path = None
            if os.path.exists(writable_file_path):
                file_path = writable_file_path
            elif os.path.exists(resource_file_path):
                file_path = resource_file_path

            if file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    ids = [line.strip() for line in f.readlines() if line.strip()]
                    if self.text_edit:
                        if hasattr(self.text_edit, 'setPlainText'):
                            self.text_edit.setPlainText("\n".join(ids))
                        elif hasattr(self.text_edit, 'set_text'):
                            self.text_edit.set_text("\n".join(ids))
                    self.log_signal.log_updated.emit(f"已加载 {len(ids)} 个用户ID配置")
                    # self.save_cache()
            else:
                self.log_signal.log_updated.emit("未找到user_ids.txt文件")
        except Exception as e:
            self.log_signal.log_updated.emit(f"加载配置失败: {e}")
            logger.error(f"加载user_ids.txt失败: {e}")

    def save_user_ids_to_file(self):
        """保存当前用户ID到user_ids.txt配置文件"""
        try:
            if not self.text_edit:
                self.log_signal.log_updated.emit("错误：文本输入框未初始化")
                return
                
            # 获取当前文本编辑器中的用户ID
            if hasattr(self.text_edit, 'toPlainText'):
                current_text = self.text_edit.toPlainText().strip()
            else:
                current_text = ""
            if not current_text:
                self.log_signal.log_updated.emit("没有用户ID需要保存")
                return

            # 处理用户ID列表，去除空行和重复项
            user_ids = [
                line.strip() for line in current_text.split("\n") if line.strip()
            ]
            user_ids = list(dict.fromkeys(user_ids))  # 去重但保持顺序

            # 使用新的用户数据管理器保存用户ID
            self.user_data_manager.save_user_ids(user_ids)

            self.log_signal.log_updated.emit(
                f"已保存 {len(user_ids)} 个用户ID到配置文件"
            )
            logger.info(f"成功保存用户ID，共 {len(user_ids)} 个")

        except Exception as e:
            self.log_signal.log_updated.emit(f"保存用户ID配置失败: {e}")
            logger.error(f"保存user_ids.txt失败: {e}")
    
    def save_user_ids_auto(self):
        """自动保存用户ID（用于实时保存功能）"""
        try:
            if not self.text_edit:
                return
                
            # 获取当前文本编辑器中的用户ID
            if hasattr(self.text_edit, 'toPlainText'):
                current_text = self.text_edit.toPlainText().strip()
            else:
                current_text = ""
            
            if not current_text:
                # 如果文本为空，保存空列表
                self.user_data_manager.save_user_ids([])
                return

            # 处理用户ID列表，去除空行和重复项
            user_ids = [
                line.strip() for line in current_text.split("\n") if line.strip()
            ]
            user_ids = list(dict.fromkeys(user_ids))  # 去重但保持顺序

            # 使用新的用户数据管理器保存用户ID
            self.user_data_manager.save_user_ids(user_ids)
            logger.debug(f"自动保存用户ID，共 {len(user_ids)} 个")

        except Exception as e:
            logger.error(f"自动保存user_ids.txt失败: {e}")

    def closeEvent(self, a0):
        """窗口关闭时自动关闭 frpc 服务和定时任务服务，并保存用户ID配置"""
        # 保存当前用户ID到配置文件
        try:
            self.save_user_ids_to_file()
        except Exception as e:
            logger.error(f"关闭时保存用户ID失败: {e}")

        # 停止定时任务服务
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务来停止调度器
                loop.create_task(self._stop_scheduler())
            else:
                # 如果事件循环未运行，直接运行停止操作
                asyncio.run(self.scheduler_client.stop())
            self.log_signal.log_updated.emit("定时任务调度器已停止")
        except Exception as e:
            logger.error(f"停止定时任务调度器失败: {e}")
            self.log_signal.log_updated.emit(f"停止定时任务调度器失败: {e}")

        # 停止 frpc 服务
        if self.frpc_process is not None:
            try:
                self.frpc_process.terminate()
                self.frpc_process.wait(timeout=5)
                self.log_signal.log_updated.emit("frpc 服务已关闭")
            except Exception as e:
                self.log_signal.log_updated.emit(f"关闭 frpc 失败: {e}")

        # 停止设置服务器进程
        if self.settings_server_process is not None:
            try:
                self.settings_server_process.terminate()
                self.settings_server_process.wait(timeout=5)
                self.log_signal.log_updated.emit("设置服务器已关闭")
            except Exception as e:
                self.log_signal.log_updated.emit(f"关闭设置服务器失败: {e}")

        if a0:
            a0.accept()

    async def _stop_scheduler(self):
        """异步停止定时任务调度器"""
        try:
            await self.scheduler_client.stop()
            logger.info("定时任务调度器已停止")
        except Exception as e:
            logger.error(f"停止定时任务调度器失败: {e}")

    def show_settings(self):
        """显示设置页面 - 直接在外部浏览器打开"""
        # 更新按钮激活状态
        self.settings_btn.setChecked(True)
        
        # 直接在外部浏览器打开Chrome配置页面
        self.open_chrome_config_in_browser()
        
        # 重置按钮状态，因为没有实际切换到设置页面
        self.settings_btn.setChecked(False)
    
    def open_chrome_config_in_browser(self):
        """在外部浏览器中打开Chrome配置页面"""
        try:
            # 检查设置服务器是否已经运行
            if (
                self.settings_server_process is None
                or self.settings_server_process.poll() is not None
            ):
                self._start_settings_server()

            # 在浏览器中打开Chrome配置页面
            webbrowser.open("http://127.0.0.1:7010/chrome/config")
            self.log_signal.log_updated.emit("已在外部浏览器打开Chrome配置页面")

        except Exception as e:
            self.log_signal.log_updated.emit(f"打开Chrome配置页面失败: {e}")
            logger.error(f"打开Chrome配置页面失败: {e}")

    def _start_settings_server(self):
        """启动设置服务器"""
        try:
            # 启动API服务器，指定端口7010并禁用调试模式
            self.settings_server_process = subprocess.Popen(
                [sys.executable, "start_api_server.py", "--port", "7010", "--no-debug"]
            )

            # 等待服务器启动
            time.sleep(2)

            self.log_signal.log_updated.emit("设置服务器已启动 (端口: 7010)")
            logger.info("设置服务器已启动")

        except Exception as e:
            self.log_signal.log_updated.emit(f"启动设置服务器失败: {e}")
            logger.error(f"启动设置服务器失败: {e}")
