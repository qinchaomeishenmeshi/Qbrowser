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

from DrissionPage import Chromium, ChromiumOptions  # DrissionPage API
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QProgressBar, QFileDialog, QMessageBox
)
from qasync import QEventLoop, asyncSlot

# ——— 日志配置 ———
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CACHE_FILE = "user_ids_cache.json"


def get_absolute_extension_path(relative_path: str) -> str:
    # 与原 Playwright 版一致，用于加载本地扩展（若仍需）
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent
    p = (base_dir / relative_path).resolve(strict=True)
    return str(p) if platform.system() != 'Windows' else f'"{p}"'


@dataclass
class BrowserConfig:
    extension_path: str = get_absolute_extension_path("extensions/live_room")
    data_dir_base: Path = Path("browser_data") / "douyin"


class BrowserManager:
    def __init__(self, user_id: str, port=9111):
        self.user_id = user_id
        self.port = port
        self.config = BrowserConfig()
        self.user_data_dir = self.config.data_dir_base / user_id
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.last_urls_file = self.user_data_dir / "last_urls.json"
        if not self.last_urls_file.exists():
            self.last_urls_file.touch()
        self.browser: Optional[Chromium] = None

    def initialize(self) -> bool:
        try:
            # 配置并启动 Chromium（持久化用户数据）
            co = ChromiumOptions().set_local_port(self.port).set_user_data_path(str(self.user_data_dir))
            co.add_extension(self.config.extension_path)
            # 如需加载扩展，可用 co.set_args([...])
            co.set_argument('--start-maximized')
            self.browser = Chromium(co)
            logger.info(f"Browser started for user: {self.user_id}")
            urls = json.loads(self.last_urls_file.read_text() or "[]")
            for url in urls:
                tab = self.browser.new_tab(url=url)  # 新标签页并访问
                # 注入用户标签
                tab.run_js(f"""
                    const d = document.createElement('div');
                    d.innerText = 'Browser ID: {self.user_id}';
                    Object.assign(d.style, {{
                      position:'fixed',top:'10px',left:'10px',
                      background:'rgba(0,0,0,0.6)',color:'white',
                      padding:'5px 10px',zIndex:999999,
                      borderRadius:'8px',fontSize:'14px'
                    }});
                    document.body.appendChild(d);
                """)
            tab = self.browser.new_tab(url="")
            tab.run_js(f"""document.title='{self.user_id}'""")

            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            self.cleanup()
            return False

    def cleanup(self):
        try:
            if self.browser:
                # 保存所有非空白标签页 URL
                tabs = self.browser.tabs_count
                urls = [self.browser.get_tab(i).url for i in range(tabs)
                        if (u := self.browser.get_tab(i).url) not in ('about:blank', '')]
                if urls:
                    self.last_urls_file.write_text(json.dumps(urls, ensure_ascii=False, indent=2))
                    logger.info(f"Saved {len(urls)} URLs.")
                self.browser.quit()
        except Exception as e:
            logger.error(f"Cleanup error: {e}", exc_info=True)

    @property
    def is_running(self) -> bool:
        return self.browser is not None

    @property
    def uptime(self) -> Optional[float]:
        return time.time() - self.browser.start_time if self.browser else None


class LogSignal(QObject):
    log_updated = pyqtSignal(str)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.browser_managers = []
        self.log_signal = LogSignal()
        self.log_signal.log_updated.connect(self.update_log)
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

        # 信号连接
        self.start_btn.clicked.connect(self.start_browsers)
        self.stop_btn.clicked.connect(self.stop_browsers)
        self.load_btn.clicked.connect(self.load_user_ids)
        self.clear_btn.clicked.connect(self.clear_cache)

    def update_log(self, msg: str):
        self.log_area.append(msg)
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

    def load_user_ids(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select user_ids.txt", "", "Text Files (*.txt)")
        if path:
            self.text_edit.setText(open(path, encoding='utf-8').read())
            self.save_cache()

    @asyncSlot()
    async def start_browsers(self):
        ids = [l.strip() for l in self.text_edit.toPlainText().splitlines() if l.strip()]
        if not ids:
            QMessageBox.critical(self, "Error", "请输入至少一个 user_id。")
            return
        if len(ids) != len(set(ids)):
            QMessageBox.critical(self, "Error", "不允许重复的 user_id。")
            return

        self.save_cache()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.browser_managers = []

        # 生成9000-9999的端口号
        available_ports = list(range(9000, 10000))  # 生成9000到9999的端口号列表
        used_ports = set()  # 用于记录已分配的端口号

        self.progress.setMaximum(len(ids))
        self.progress.setValue(0)

        for idx, user_id in enumerate(ids, 1):
            # 从可用端口号中分配一个未使用的端口号
            port = available_ports.pop(0)  # 从列表中取出第一个端口号
            while port in used_ports:  # 如果端口号已被使用，则尝试下一个
                port = available_ports.pop(0)
            used_ports.add(port)  # 将分配的端口号加入已使用集合

            # 初始化 BrowserManager 并分配端口号
            manager = BrowserManager(user_id, port)
            manager.port = port  # 假设 BrowserManager 有一个 port 属性
            self.browser_managers.append(manager)

            ok = await asyncio.to_thread(manager.initialize)  # 在后台线程运行同步初始化
            self.log_signal.log_updated.emit(
                f"[{idx}/{len(ids)}] {manager.user_id} {'启动成功' if ok else '启动失败'} (端口: {manager.port})"
            )
            self.progress.setValue(idx)
            await asyncio.sleep(0.01)

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.log_signal.log_updated.emit("All browsers started.")

    @asyncSlot()
    async def stop_browsers(self):
        self.start_btn.setEnabled(False);
        self.stop_btn.setEnabled(False)
        self.log_signal.log_updated.emit("Stopping all browsers…")
        await asyncio.gather(*(asyncio.to_thread(m.cleanup) for m in self.browser_managers if m.is_running))
        self.progress.setValue(0)
        self.start_btn.setEnabled(True);
        self.stop_btn.setEnabled(True)
        self.log_signal.log_updated.emit("All browsers closed.")

    def save_cache(self):
        json.dump(
            [l for l in self.text_edit.toPlainText().splitlines() if l.strip()],
            open(CACHE_FILE, 'w', encoding='utf-8'),
            ensure_ascii=False, indent=2
        )

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                ids = json.load(open(CACHE_FILE, encoding='utf-8'))
                self.text_edit.setText('\n'.join(ids))
            except:
                pass

    def clear_cache(self):
        if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
        self.text_edit.clear()
        self.log_signal.log_updated.emit("Cache cleared.")


def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    w = App();
    w.show()
    with loop: loop.run_forever()


if __name__ == "__main__":
    main()
