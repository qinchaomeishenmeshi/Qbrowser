import asyncio
import json
import logging
import os
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, \
    QProgressBar, QFileDialog, QMessageBox
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from qasync import QEventLoop, asyncSlot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CACHE_FILE = "user_ids_cache.json"


def get_absolute_extension_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent
    extension_path = base_dir / relative_path
    absolute_path = extension_path.resolve(strict=True)
    if platform.system() == 'Windows':
        win_path = str(absolute_path)
        if any(c in win_path for c in (' ', '&', '^')):
            win_path = f'"{win_path}"'
        try:
            from ctypes import windll, create_unicode_buffer
            buffer = create_unicode_buffer(256)
            if windll.kernel32.GetShortPathNameW(win_path, buffer, 256):
                win_path = buffer.value
        except Exception:
            pass
        return win_path
    return str(absolute_path)


@dataclass
class BrowserConfig:
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    base_url: str = "https://eos.douyin.com"
    extension_path = get_absolute_extension_path("extensions/live_room")
    data_dir_base: Path = Path("browser_data") / "douyin"


class BrowserManager:
    def __init__(self, user_id: str, config: Optional[BrowserConfig] = None):
        self.user_id = user_id
        self.config = config or BrowserConfig()
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.user_data_dir = self.config.data_dir_base / user_id
        self._playwright: Optional[Playwright] = None
        self._startup_time = None
        self.last_urls_file = self.user_data_dir / "last_urls.json"

    async def inject_user_tag(self, page: Page):
        await page.evaluate(f"""
            (() => {{
                const div = document.createElement('div');
                div.innerText = 'Browser ID: {self.user_id}';
                div.style.position = 'fixed';
                div.style.top = '10px';
                div.style.left = '10px';
                div.style.background = 'rgba(0,0,0,0.6)';
                div.style.color = 'white';
                div.style.padding = '5px 10px';
                div.style.zIndex = '999999';
                div.style.borderRadius = '8px';
                div.style.fontSize = '14px';
                div.style.pointerEvents = 'none';
                document.body.appendChild(div);
            }})()
        """)

    async def initialize(self) -> bool:
        try:
            lock_file = self.user_data_dir / "SingletonLock"
            retry_count = 0
            while lock_file.exists():
                if retry_count >= 5:
                    logger.error(f"User data dir {self.user_data_dir} is occupied, aborting.")
                    return False
                logger.warning(f"User data dir {self.user_data_dir} is occupied, waiting...")
                await asyncio.sleep(2)
                retry_count += 1

            self._playwright = await async_playwright().start()
            logger.info(f"Extension path: {self.config.extension_path}")

            self.context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=False,
                channel="chrome",
                no_viewport=True,
                args=[
                    f"--disable-extensions-except={self.config.extension_path}",
                    f"--load-extension={self.config.extension_path}",
                ],
            )

            blank_page = None
            for page in self.context.pages:
                if page.url == "about:blank" and blank_page is None:
                    blank_page = page
                else:
                    await page.close()
            if not blank_page:
                blank_page = await self.context.new_page()
            self.page = blank_page
            await self.page.evaluate(f"document.title = '{self.user_id}'")

            if self.last_urls_file.exists():
                try:
                    with open(self.last_urls_file, 'r', encoding='utf-8') as f:
                        urls = json.load(f)
                    if isinstance(urls, list) and urls:
                        for url in urls:
                            page = await self.context.new_page()
                            await page.goto(url)
                            await self.inject_user_tag(page)
                        logger.info(f"Restored {len(urls)} pages.")
                except Exception as e:
                    logger.warning(f"Failed to restore URLs: {str(e)}")

            self._startup_time = time.time()
            logger.info(f"Browser started for user: {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}", exc_info=True)
            await self.cleanup()
            return False

    async def cleanup(self):
        try:
            if self.context:
                urls = [page.url for page in self.context.pages if
                        page.url and not page.url.startswith('chrome://') and page.url != 'about:blank']
                if urls:
                    self.user_data_dir.mkdir(parents=True, exist_ok=True)
                    with open(self.last_urls_file, 'w', encoding='utf-8') as f:
                        json.dump(urls, f, ensure_ascii=False, indent=2)
                    logger.info(f"Saved {len(urls)} open page URLs.")

            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}", exc_info=True)
        finally:
            await asyncio.sleep(2)
            self.page = None
            self.context = None
            self._playwright = None

    @property
    def is_running(self) -> bool:
        return bool(self.context)

    @property
    def uptime(self) -> Optional[float]:
        if self._startup_time and self.is_running:
            return time.time() - self._startup_time
        return None


class LogSignal(QObject):
    """用于线程安全的日志输出信号"""
    log_updated = pyqtSignal(str)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.browser_managers = []
        self.log_signal = LogSignal()
        self.log_signal.log_updated.connect(self.update_log)

        # 初始化UI
        self.init_ui()
        self.load_cache()

    def init_ui(self):
        self.setWindowTitle("Browser Manager")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #f0f0f0;")

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 输入文本框
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(100)
        self.text_edit.setStyleSheet("""
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
        """)
        font = QFont("Arial", 12)
        self.text_edit.setFont(font)
        main_layout.addWidget(self.text_edit)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # 启动浏览器按钮样式
        self.start_btn = QPushButton("启动浏览器")
        self.start_btn.setFixedWidth(120)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #388E3C;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #66BB6A;
                border: 1px solid #66BB6A;  
            }
            QPushButton:pressed {
                background-color: #388E3C;
                border: 1px solid #388E3C;  
            }
        """)

        self.start_btn.setFont(font)

        # 一键关闭按钮样式
        self.stop_btn = QPushButton("一键关闭")
        self.stop_btn.setFixedWidth(120)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: 1px solid #D32F2F;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
            QPushButton:pressed {
                background-color: #D32F2F;
            }
        """)
        self.stop_btn.setFont(font)

        # 加载 user_ids.txt 按钮样式
        self.load_btn = QPushButton("加载 user_ids.txt")
        self.load_btn.setFixedWidth(160)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 1px solid #1976D2;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
            QPushButton:pressed {
                background-color: #1976D2;
            }
        """)
        self.load_btn.setFont(font)

        # 清除缓存按钮样式
        self.clear_btn = QPushButton("清除缓存")
        self.clear_btn.setFixedWidth(120)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: 1px solid #F57C00;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #FFB74D;
            }
            QPushButton:pressed {
                background-color: #F57C00;
            }
        """)
        self.clear_btn.setFont(font)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.clear_btn)
        main_layout.addLayout(btn_layout)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        main_layout.addWidget(self.progress)

        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
        """)
        self.log_area.setFont(font)
        main_layout.addWidget(self.log_area)

        # 连接信号
        self.start_btn.clicked.connect(self.start_browsers)
        self.stop_btn.clicked.connect(self.stop_browsers)
        self.load_btn.clicked.connect(self.load_user_ids)
        self.clear_btn.clicked.connect(self.clear_cache)

    def update_log(self, message: str):
        """线程安全的日志更新"""
        self.log_area.append(message)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def load_user_ids(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select user_ids.txt", "", "Text Files (*.txt)"
        )
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.text_edit.setText(f.read())
            self.save_cache()

    @asyncSlot()
    async def start_browsers(self):
        user_ids = [line.strip() for line in self.text_edit.toPlainText().splitlines() if line.strip()]
        if not user_ids:
            QMessageBox.critical(self, "Error", "Please enter at least one user_id.")
            return
        if len(user_ids) != len(set(user_ids)):
            QMessageBox.critical(self, "Error", "Duplicate user_ids are not allowed.")
            return

        self.save_cache()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)

        self.browser_managers = [BrowserManager(user_id) for user_id in user_ids]
        self.progress.setMaximum(len(user_ids))
        self.progress.setValue(0)

        for idx, manager in enumerate(self.browser_managers, start=1):
            try:
                result = await manager.initialize()
                msg = f"[{idx}/{len(user_ids)}] Browser for {manager.user_id} {'started successfully' if result else 'failed to start'}"
                self.log_signal.log_updated.emit(msg)
            except Exception as e:
                self.log_signal.log_updated.emit(f"[{idx}/{len(user_ids)}] Error starting {manager.user_id}: {e}")

            self.progress.setValue(idx)
            await asyncio.sleep(0.01)  # 让出事件循环

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.log_signal.log_updated.emit("All browsers started.")

    @asyncSlot()
    async def stop_browsers(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.log_signal.log_updated.emit("Stopping all browsers...")

        await asyncio.gather(*(manager.cleanup() for manager in self.browser_managers if manager.is_running))

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.progress.setValue(0)
        self.log_signal.log_updated.emit("All browsers closed.")

    def save_cache(self):
        user_ids = [line.strip() for line in self.text_edit.toPlainText().splitlines() if line.strip()]
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_ids, f, ensure_ascii=False, indent=2)

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                try:
                    user_ids = json.load(f)
                    if isinstance(user_ids, list):
                        self.text_edit.setText('\n'.join(user_ids))
                except Exception:
                    pass

    def clear_cache(self):
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        self.text_edit.clear()
        self.log_signal.log_updated.emit("Cache cleared.")


def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)  # 使用qasync的事件循环
    asyncio.set_event_loop(loop)

    window = App()
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
