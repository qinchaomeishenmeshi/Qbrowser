import asyncio
import json
import os
import subprocess
import sys
import threading

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QProgressBar, QFileDialog, QMessageBox
)
from qasync import QEventLoop, asyncSlot

from api_server import run_server
from browser_manager import BrowserManager
from conf import CACHE_FILE, PORTS_FILE, BASE_DIR
from log.logger import logger
from worker.main import BrowserOperator


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
        self.load_ports()
        # 启动 FastAPI（独立类管理）
        run_server(host="127.0.0.1", port=6001)
        # self.api_server = ApiServer()
        # self.api_server.start()
        logger.info("FastAPI started")

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

        self.save_ports()  # 启动后保存端口映射
        # 并行启动 frpc 服务
        # 启动 frpc 服务（仅一次）
        # 如果是mac系统不执行
        if not sys.platform.startswith('darwin'):
            self.frpc_process = self.start_frpc()
            self.log_signal.log_updated.emit("All browsers and frpc services started.")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.log_signal.log_updated.emit("All browsers started.")
        operator = BrowserOperator()
        operator.attach_get_cookies()

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

    # 在 App 类中添加
    def start_frpc(self):
        """启动 frpc 服务，使用固定配置文件，并确保可执行文件与配置文件存在"""
        frpc_path = os.path.join(BASE_DIR, "frp_client", "frpc.exe")
        toml_path = os.path.join(BASE_DIR, "frp_client", "frpc.toml")
        print(f'frpc_path: {frpc_path}')

        for path, name in [(frpc_path, "frpc.exe"), (toml_path, "frpc.toml")]:
            if not os.path.exists(path):
                logger.error("%s 文件未找到 at %s", name, path)
                return None

        try:
            proc = subprocess.Popen(
                [frpc_path, "-c", toml_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            logger.info("Started frpc with default config: PID=%d", proc.pid)

            # 并行读取 stdout / stderr
            def reader(stream, name):
                for line in stream:
                    line = line.rstrip()
                    print(f"FRP {name}：{line}")

            t1 = threading.Thread(target=reader, args=(proc.stdout, "输出"))
            t2 = threading.Thread(target=reader, args=(proc.stderr, "错误"))
            t1.daemon = True
            t2.daemon = True
            t1.start()
            t2.start()

            exit_code = proc.wait()
            if exit_code != 0:
                logger.warning("frpc 进程非正常退出，exit_code=%d", exit_code)
            return proc

        except Exception as e:
            logger.error(f"Failed to start frpc: {e}", exc_info=True)
            return None

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
        self.clear_ports()  # 清理端口映射
        self.text_edit.clear()
        self.log_signal.log_updated.emit("Cache cleared.")

    def save_ports(self):
        mapping = {m.user_id: {"port": m.port} for m in self.browser_managers}
        with open(PORTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved ports mapping for {len(mapping)} instances.")

    def load_ports(self):
        if os.path.exists(PORTS_FILE):
            try:
                mapping = json.load(open(PORTS_FILE, encoding='utf-8'))
                logger.info(f"Loaded ports mapping: {mapping}")
            except Exception:
                logger.warning("Failed to load ports mapping.")

    def clear_ports(self):
        """清除端口映射文件"""
        if os.path.exists(PORTS_FILE):
            os.remove(PORTS_FILE)
            self.log_signal.log_updated.emit("Ports mapping cleared.")


def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    w = App()
    w.show()
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
