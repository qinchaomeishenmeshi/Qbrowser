import asyncio
import os
import subprocess
import sys
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
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QPushButton, QTextEdit, QProgressBar, QButtonGroup,
    QMessageBox, QSizePolicy, QFrame, QScrollArea,
    QGraphicsDropShadowEffect
)
from qasync import asyncSlot

# 项目内部导入
from api.api_server import run_server
from app import LogSignal, is_admin, App
from browser.browser_operator import browser_operator
from conf import BASE_DIR, resource_path
from service.browser_service import browser_service
from ui.config import THEMES, CURRENT_THEME, LAYOUT, FONTS
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

        # 初始化UI
        self.setup_fonts()
        self.init_ui()

        # 检查管理员权限，与原始代码相同
        if sys.platform == 'win32' and not is_admin():
            logger.warning("程序未以管理员权限运行，某些功能可能受限")
            QMessageBox.warning(self, "权限提示",
                                "程序没有以管理员权限运行。\n在Windows上，浏览器自动化和frpc服务可能需要管理员权限。\n请考虑以管理员身份重新运行程序。")

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

    def init_ui(self):
        # 设置窗口属性
        theme = THEMES[CURRENT_THEME]
        self.setWindowTitle("QW-Browser 浏览器管理工具")
        self.setGeometry(100, 100, 1280, 800)

        # 设置全局样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['background']};
                color: {theme['text']};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {theme['background']};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['inactive']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: {theme['background']};
                height: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {theme['inactive']};
                border-radius: 4px;
                min-width: 20px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {theme['primary']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)

        # 创建主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建左侧导航栏
        self.create_sidebar()

        # 创建右侧内容区
        self.create_content_area()

        # 默认显示浏览器实例页面
        self.show_instances()

    def create_sidebar(self):
        # 创建左侧导航栏
        theme = THEMES[CURRENT_THEME]

        # 创建一个容器来包含导航栏
        self.sidebar_container = QWidget()
        self.sidebar_container.setFixedWidth(LAYOUT["sidebar_width"])
        self.sidebar_container.setStyleSheet(f"""
            background-color: {theme['secondary']};
            color: {theme['text_light']};
            border: none;
        """)

        sidebar_container_layout = QVBoxLayout(self.sidebar_container)
        sidebar_container_layout.setSpacing(0)
        sidebar_container_layout.setContentsMargins(0, 0, 0, 0)

        # 创建导航栏滚动区域
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {theme['secondary']};
                border: none;
            }}
        """)

        # 创建实际的导航栏内容
        self.sidebar = QWidget()
        self.sidebar.setStyleSheet(f"""
            background-color: {theme['secondary']};
            color: {theme['text_light']};
        """)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(5)

        # 应用标题和logo区域
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(10, 10, 10, 20)

        # 应用标题
        title = QLabel("QW-Browser")
        title.setFont(QFont(FONTS["title"][0], FONTS["title"][1], QFont.Weight.Bold))
        title.setStyleSheet(f"""
            color: {theme['text_light']};
            font-weight: bold;
        """)
        title_layout.addWidget(title)
        sidebar_layout.addWidget(title_container)

        # 添加分隔线
        self.add_sidebar_separator(sidebar_layout)

        # 创建导航按钮组
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)  # 确保只有一个按钮被选中

        # 仅保留浏览器实例按钮
        self.instances_btn = self.create_nav_button("浏览器", "browser")
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

        # 添加底部版本信息
        version_label = QLabel("QW-Browser v2.0.0")
        version_label.setStyleSheet(f"""
            color: {theme['text_tertiary']};
            font-size: 10px;
            padding: 10px;
            qproperty-alignment: AlignCenter;
        """)
        sidebar_layout.addWidget(version_label)

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
        """创建导航按钮"""
        theme = THEMES[CURRENT_THEME]
        button = QPushButton(text)
        button.setCheckable(True)
        button.setFont(QFont(FONTS["regular"][0], FONTS["regular"][1]))

        # 设置固定高度并左对齐文本
        button.setMinimumHeight(44)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme['text_light']};
                border: none;
                border-radius: {LAYOUT["border_radius"]}px;
                padding: 10px 15px;
                text-align: left;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:checked {{
                background-color: {theme['primary']};
                color: white;
                font-weight: bold;
            }}
        """)
        return button

    def create_content_area(self):
        # 创建右侧内容区
        theme = THEMES[CURRENT_THEME]

        # 创建内容区域容器
        self.content_container = QWidget()
        self.content_container.setStyleSheet(f"""
            background-color: {theme['background']};
        """)

        content_container_layout = QVBoxLayout(self.content_container)
        content_container_layout.setContentsMargins(0, 0, 0, 0)
        content_container_layout.setSpacing(0)

        # 创建顶部工具栏
        self.create_topbar()

        # 创建内容区域
        self.content_area = QWidget()
        self.content_area.setStyleSheet(f"""
            background-color: {theme['background']};
            color: {theme['text']};
        """)

        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(LAYOUT["margin"], LAYOUT["margin"], LAYOUT["margin"], LAYOUT["margin"])

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
        self.topbar.setStyleSheet(f"""
            background-color: {theme['card']};
            border-bottom: 1px solid {theme['divider']};
        """)

        # 添加阴影效果
        topbar_shadow = QGraphicsDropShadowEffect(self.topbar)
        topbar_shadow.setBlurRadius(10)
        topbar_shadow.setColor(QColor(0, 0, 0, 15))
        topbar_shadow.setOffset(0, 2)
        self.topbar.setGraphicsEffect(topbar_shadow)

        topbar_layout = QHBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(20, 0, 20, 0)

        # 页面标题
        self.page_title = QLabel("浏览器控制中心")
        self.page_title.setFont(QFont(FONTS["title"][0], FONTS["title"][1], QFont.Weight.Bold))
        self.page_title.setStyleSheet(f"color: {theme['text']};")
        topbar_layout.addWidget(self.page_title)

        # 添加伸缩项，将右侧按钮推到最右边
        topbar_layout.addStretch()

        # 添加topbar到内容容器
        self.content_container.layout().addWidget(self.topbar)

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
        self.content_stack.setCurrentIndex(1)
        self.update_page_title("浏览器实例管理")

    def show_scheduler(self):
        """显示定时任务页面"""
        if LITE_MODE or QWebEngineView is None:
            # 轻量版模式：使用外部浏览器打开
            import webbrowser
            try:
                webbrowser.open("http://127.0.0.1:6001/")
                QMessageBox.information(self, "定时任务管理", 
                    "已在外部浏览器中打开定时任务页面\n\n" +
                    "URL: http://127.0.0.1:6001/\n\n" +
                    "注意：请确保后台服务正在运行")
            except Exception as e:
                QMessageBox.warning(self, "打开失败", f"无法打开外部浏览器：{e}")
            return
            
        if hasattr(self, 'scheduler_page'):
            index = self.content_stack.indexOf(self.scheduler_page)
            if index != -1:
                self.content_stack.setCurrentIndex(index)
                self.update_page_title("定时任务管理")

    def init_scheduler_page(self):
        """初始化定时任务管理页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if QWebEngineView is not None:
            # 使用WebEngine视图
            web_view = QWebEngineView()
            web_view.setUrl(QUrl("http://127.0.0.1:6001/"))
            layout.addWidget(web_view)
        else:
            # WebEngine不可用时的备用方案
            fallback_label = QLabel("定时任务管理功能需要QtWebEngine支持")
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    color: #666;
                    padding: 20px;
                    background-color: #f5f5f5;
                    border-radius: 8px;
                }
            """)
            layout.addWidget(fallback_label)
            
            # 添加打开浏览器按钮
            open_browser_btn = QPushButton("在浏览器中打开")
            open_browser_btn.clicked.connect(lambda: self.open_scheduler_in_browser())
            layout.addWidget(open_browser_btn)
        
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
        page.setStyleSheet(f"""
            background-color: {theme['background']};
            color: {theme['text']};
        """)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 创建用户ID输入卡片 - Chrome风格卡片
        input_card = QWidget()
        input_card.setStyleSheet(f"""
            background-color: {theme['card']};
            color: {theme['text']};
            border-radius: {LAYOUT["border_radius"]}px;
            border: 1px solid rgba(0, 0, 0, 0.06);
        """)

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
        card_title.setFont(QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Bold))
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
        self.text_edit = self._create_text_edit()
        self.text_edit.setMinimumHeight(100)  # 增加文本编辑区高度
        input_layout.addWidget(self.text_edit)

        # 添加输入卡片到主布局
        layout.addWidget(input_card)

        # 创建操作按钮卡片 - Chrome风格卡片
        action_card = QWidget()
        action_card.setStyleSheet(f"""
            background-color: {theme['card']};
            color: {theme['text']};
            border-radius: {LAYOUT["border_radius"]}px;
            border: 1px solid rgba(0, 0, 0, 0.06);
        """)

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
        action_title.setFont(QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Bold))
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
        from ui.pages.dashboard import ChromeButton

        self.start_btn = ChromeButton("启动浏览器", theme["success"])
        self.stop_btn = ChromeButton("一键关闭", theme["error"])
        self.load_btn = ChromeButton("加载配置", theme["primary"])
        self.clear_btn = ChromeButton("清除缓存", theme["warning"])

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
        log_card.setStyleSheet(f"""
            background-color: {theme['card']};
            color: {theme['text']};
            border-radius: {LAYOUT["border_radius"]}px;
            border: 1px solid rgba(0, 0, 0, 0.06);
        """)
        log_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

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
        log_title.setFont(QFont(FONTS["heading"][0], FONTS["heading"][1], QFont.Weight.Bold))
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
        progress_title.setFont(QFont(FONTS["regular"][0], FONTS["regular"][1], QFont.Weight.Bold))
        progress_title.setStyleSheet(f"color: {theme['text']};")
        log_layout.addWidget(progress_title)

        self.progress = self._create_progressbar()
        log_layout.addWidget(self.progress)

        # 日志标题和日志区域
        log_area_title = QLabel("操作日志")
        log_area_title.setFont(QFont(FONTS["regular"][0], FONTS["regular"][1], QFont.Weight.Bold))
        log_area_title.setStyleSheet(f"color: {theme['text']};")
        log_layout.addWidget(log_area_title)

        self.log_area = self._create_log_area()
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
        """初始化设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("设置页面 - 待开发")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.settings_page = page
        self.content_stack.addWidget(self.settings_page)

    def update_log(self, msg: str):
        # 确保 self.log_area 存在
        if self.log_area:
            self.log_area.append(msg)
            self.log_area.verticalScrollBar().setValue(
                self.log_area.verticalScrollBar().maximum()
            )

    def load_cache(self):
        try:
            ids = self.browser_service.load_cache()
            if self.text_edit:
                self.text_edit.setText("\n".join(ids))
            logger.info(f"加载用户缓存成功: {ids}")
        except Exception as e:
            logger.error(f"加载用户缓存失败: {e}")

    async def async_init(self):
        """异步初始化，加载端口和启动服务"""
        try:
            # 加载端口配置
            await self.browser_service.load_ports()

            # 启动API服务
            try:
                run_server(host="127.0.0.1", port=6001)
                logger.info("FastAPI服务已启动")
                self.log_signal.log_updated.emit("FastAPI服务已启动")
            except Exception as e:
                logger.error(f"FastAPI服务启动失败: {e}")
                self.log_signal.log_updated.emit(f"FastAPI服务启动失败: {e}")

            # 启动定时任务服务
            try:
                await self.scheduler_client.start()
                task_count = len(self.scheduler_client.task_configs)
                enabled_count = sum(1 for config in self.scheduler_client.task_configs.values() if config.enabled)
                logger.info(f"定时任务调度器启动成功，已加载 {task_count} 个任务配置，其中 {enabled_count} 个已启用")
                self.log_signal.log_updated.emit(f"定时任务调度器启动成功，已加载 {task_count} 个任务配置，其中 {enabled_count} 个已启用")
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

            # 更新所有任务的设备列表
            self.log_signal.log_updated.emit("定时任务配置已更新")
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            self.log_signal.log_updated.emit(f"初始化失败: {e}")

    def _create_text_edit(self):
        """创建文本编辑区 - Chrome风格"""
        theme = THEMES[CURRENT_THEME]

        text_edit = QTextEdit()
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['background']};
                color: {theme['text']};
                border: 1px solid {theme['card_border']};
                border-radius: {LAYOUT["border_radius"]}px;
                padding: 10px;
            }}
            QTextEdit:focus {{
                border: 1px solid {theme['primary']};
            }}
        """)
        text_edit.setFont(QFont(FONTS["regular"][0], FONTS["regular"][1]))
        return text_edit

    def _create_progressbar(self):
        """创建进度条 - Chrome风格"""
        theme = THEMES[CURRENT_THEME]

        progress = QProgressBar()
        progress.setFixedHeight(6)  # 更薄的进度条，更符合Chrome风格
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {theme['background']};
                text-align: center;
                color: transparent;  /* 隐藏文本 */
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {theme['success']};
                border-radius: 3px;
            }}
        """)
        return progress

    def _create_log_area(self):
        """创建日志区域 - Chrome风格"""
        theme = THEMES[CURRENT_THEME]

        log_area = QTextEdit()
        log_area.setReadOnly(True)
        log_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['background']};
                color: {theme['text']};
                border: 1px solid {theme['card_border']};
                border-radius: {LAYOUT["border_radius"]}px;
                padding: 10px;
                font-family: {FONTS["mono"][0]};
                font-size: {FONTS["mono"][1]}px;
            }}
        """)
        return log_area

    # 页面切换函数
    def show_dashboard(self):
        self.dashboard_btn.setChecked(True)
        self.content_stack.setCurrentIndex(0)
        self.update_page_title("仪表盘")

        # 直接使用事件循环创建任务
        loop = asyncio.get_event_loop()
        loop.create_task(self.update_dashboard_stats())

    def show_instances(self):
        self.instances_btn.setChecked(True)
        self.content_stack.setCurrentIndex(1)
        self.update_page_title("浏览器控制中心")

    def show_data_management(self):
        self.data_btn.setChecked(True)
        self.content_stack.setCurrentIndex(2)
        self.update_page_title("数据管理")

    def show_settings(self):
        self.settings_btn.setChecked(True)
        self.content_stack.setCurrentIndex(3)
        self.update_page_title("系统设置")

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
                instance_stats=instance_stats,
                resource_stats=resource_stats
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

            # 启动定时任务服务
            try:
                await self.scheduler_client.start()
                task_count = len(self.scheduler_client.task_configs)
                enabled_count = sum(1 for config in self.scheduler_client.task_configs.values() if config.enabled)
                logger.info(f"定时任务调度器启动成功，已加载 {task_count} 个任务配置，其中 {enabled_count} 个已启用")
                self.log_signal.log_updated.emit(f"定时任务调度器启动成功，已加载 {task_count} 个任务配置，其中 {enabled_count} 个已启用")
            except Exception as e:
                logger.error(f"定时任务调度器启动失败: {e}")
                self.log_signal.log_updated.emit(f"定时任务调度器启动失败: {e}")

            # 仅在Windows系统上尝试启动frpc服务
            if sys.platform == 'win32':
                try:
                    self.frpc_process = self._start_frpc()
                    if self.frpc_process:
                        self.log_signal.log_updated.emit("frpc服务已启动")
                    else:
                        self.log_signal.log_updated.emit("frpc服务启动失败，请确保以管理员权限运行程序")
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
        # 保留原始方法的所有功能
        await App.start_browsers(self)

        # 禁用UI，防止多次点击
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

        # 操作完成后更新仪表盘
        try:
            # 恢复UI
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
        except Exception as e:
            logger.error(f"更新状态失败: {e}")

    # 覆盖原始应用的stop_browsers方法，添加更新仪表盘的调用
    @asyncSlot()
    async def stop_browsers(self):
        # 保留原始方法的所有功能
        await App.stop_browsers(self)

        # 禁用UI，防止多次点击
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

        # 操作完成后更新仪表盘
        try:
            # 恢复UI
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
        except Exception as e:
            logger.error(f"更新状态失败: {e}")

    # 其他方法保持与原始App相同
    update_log = App.update_log
    # load_user_ids已重新实现
    save_cache = App.save_cache
    load_cache = App.load_cache

    # clear_cache是异步方法，需要装饰器
    @asyncSlot()
    async def clear_cache(self):
        await App.clear_cache(self)

    load_ports = App.load_ports
    save_ports = App.save_ports
    _start_frpc = App._start_frpc

    def load_user_ids_on_startup(self):
        """应用启动时自动加载用户ID配置文件"""
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
                    if ids and self.text_edit:  # 确保text_edit已初始化且有数据
                        self.text_edit.setText("\n".join(ids))
                        self.save_cache()  # 同步到缓存
                        logger.info(f"启动时自动加载了 {len(ids)} 个用户ID配置")
                    elif not ids:
                        logger.info("user_ids.txt文件为空")
            else:
                logger.info("未找到user_ids.txt文件，将使用空配置")
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
                    self.text_edit.setText("\n".join(ids))
                    self.log_signal.log_updated.emit(f"已加载 {len(ids)} 个用户ID配置")
                    self.save_cache()
            else:
                self.log_signal.log_updated.emit("未找到user_ids.txt文件")
        except Exception as e:
            self.log_signal.log_updated.emit(f"加载配置失败: {e}")
            logger.error(f"加载user_ids.txt失败: {e}")
            
    def save_user_ids_to_file(self):
        """保存当前用户ID到user_ids.txt配置文件"""
        try:
            from conf import writable_path
            # 获取当前文本编辑器中的用户ID
            current_text = self.text_edit.toPlainText().strip()
            if not current_text:
                self.log_signal.log_updated.emit("没有用户ID需要保存")
                return
                
            # 处理用户ID列表，去除空行和重复项
            user_ids = [line.strip() for line in current_text.split('\n') if line.strip()]
            user_ids = list(dict.fromkeys(user_ids))  # 去重但保持顺序
            
            # 保存到可写目录的user_ids.txt文件
            file_path = writable_path("user_ids.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(user_ids))
                
            self.log_signal.log_updated.emit(f"已保存 {len(user_ids)} 个用户ID到配置文件")
            logger.info(f"成功保存用户ID到 {file_path}，共 {len(user_ids)} 个")
            
        except Exception as e:
            self.log_signal.log_updated.emit(f"保存用户ID配置失败: {e}")
            logger.error(f"保存user_ids.txt失败: {e}")
            
    def closeEvent(self, event):
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
        
        event.accept()

    async def _stop_scheduler(self):
        """异步停止定时任务调度器"""
        try:
            await self.scheduler_client.stop()
            logger.info("定时任务调度器已停止")
        except Exception as e:
            logger.error(f"停止定时任务调度器失败: {e}")
    
    def show_settings(self):
        """显示设置页面 - 启动Chrome配置服务并在浏览器中打开"""
        try:
            # 检查设置服务器是否已经运行
            if self.settings_server_process is None or self.settings_server_process.poll() is not None:
                self._start_settings_server()
            
            # 在浏览器中打开Chrome配置页面
            webbrowser.open('http://127.0.0.1:7010/chrome/config')
            self.log_signal.log_updated.emit("已打开Chrome配置页面")
            
        except Exception as e:
            self.log_signal.log_updated.emit(f"打开设置页面失败: {e}")
            logger.error(f"打开设置页面失败: {e}")
    
    def _start_settings_server(self):
        """启动设置服务器"""
        try:
            # 启动API服务器，指定端口7010并禁用调试模式
            self.settings_server_process = subprocess.Popen([
                sys.executable, "start_api_server.py", 
                "--port", "7010", "--no-debug"
            ])
            
            # 等待服务器启动
            time.sleep(2)
            
            self.log_signal.log_updated.emit("设置服务器已启动 (端口: 7010)")
            logger.info("设置服务器已启动")
            
        except Exception as e:
             self.log_signal.log_updated.emit(f"启动设置服务器失败: {e}")
             logger.error(f"启动设置服务器失败: {e}")
