import asyncio
import os
import subprocess
import sys
import threading
import ctypes

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QProgressBar,
    QFileDialog,
    QMessageBox,
)

from qasync import QEventLoop, asyncSlot

from api.api_server import run_server
from conf import BASE_DIR
from service.browser_service import browser_service
from browser.browser_operator import browser_operator

from utils.common_logger import get_logger

logger = get_logger(__name__)

def is_admin():
    """检查程序是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() if sys.platform == 'win32' else True
    except:
        return False

class LogSignal(QObject):
    log_updated = pyqtSignal(str)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log_area = None
        self.progress = None
        self.clear_btn = None
        self.load_btn = None
        self.stop_btn = None
        self.start_btn = None
        self.text_edit = None
        self.browser_managers = []
        self.log_signal = LogSignal()
        self.log_signal.log_updated.connect(self.update_log)
        self.browser_service = browser_service
        self.browser_operator = browser_operator
        self.frpc_process = None
        
        # 检查管理员权限
        if sys.platform == 'win32' and not is_admin():
            logger.warning("程序未以管理员权限运行，某些功能可能受限")
            QMessageBox.warning(self, "权限提示", 
                          "程序没有以管理员权限运行。\n在Windows上，浏览器自动化和frpc服务可能需要管理员权限。\n请考虑以管理员身份重新运行程序。")
        
        # 初始化UI
        self.init_ui()
        
        # 使用同步方法加载基本缓存
        self.load_cache()
        
        # 使用QTimer在Qt事件循环启动后执行异步初始化
        QTimer.singleShot(0, self._schedule_async_init)
    
    def _schedule_async_init(self):
        """使用事件循环安排异步初始化任务"""
        loop = asyncio.get_event_loop()
        loop.create_task(self.async_init())
        
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
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            self.log_signal.log_updated.emit(f"初始化失败: {e}")

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
        self.text_edit.setStyleSheet(
            """
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
        """
        )
        font = QFont("Arial", 12)
        self.text_edit.setFont(font)
        main_layout.addWidget(self.text_edit)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # 启动浏览器按钮样式
        self.start_btn = QPushButton("启动浏览器")
        self.start_btn.setFixedWidth(120)
        self.start_btn.setStyleSheet(
            """
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
        """
        )

        self.start_btn.setFont(font)

        # 一键关闭按钮样式
        self.stop_btn = QPushButton("一键关闭")
        self.stop_btn.setFixedWidth(120)
        self.stop_btn.setStyleSheet(
            """
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
        """
        )
        self.stop_btn.setFont(font)

        # 加载 user_ids.txt 按钮样式
        self.load_btn = QPushButton("加载 user_ids.txt")
        self.load_btn.setFixedWidth(160)
        self.load_btn.setStyleSheet(
            """
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
        """
        )
        self.load_btn.setFont(font)

        # 清除缓存按钮样式
        self.clear_btn = QPushButton("清除缓存")
        self.clear_btn.setFixedWidth(120)
        self.clear_btn.setStyleSheet(
            """
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
        """
        )
        self.clear_btn.setFont(font)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.clear_btn)
        main_layout.addLayout(btn_layout)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setStyleSheet(
            """
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
        """
        )
        main_layout.addWidget(self.progress)

        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(
            """
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
        """
        )
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
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 user_ids.txt 文件", "", "文本文件 (*.txt)"
        )
        if path:
            try:
                with open(path, encoding="utf-8") as f:
                    self.text_edit.setText(f.read())
                self.save_cache()
                self.log_signal.log_updated.emit(f"加载文件 {path} 成功")
            except Exception as e:
                self.log_signal.log_updated.emit(f"加载文件失败: {e}")

    @asyncSlot()
    async def start_browsers(self):
        try:
            # 在Windows上检查权限
            if sys.platform == 'win32' and not is_admin():
                result = QMessageBox.warning(
                    self, 
                    "权限不足", 
                    "程序没有以管理员权限运行，浏览器可能无法正常启动。\n是否继续尝试？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if result == QMessageBox.StandardButton.No:
                    self.log_signal.log_updated.emit("操作已取消")
                    return
            
            ids = [
                l.strip() for l in self.text_edit.toPlainText().splitlines() if l.strip()
            ]
            if not ids:
                QMessageBox.critical(self, "错误", "请输入至少一个 user_id。")
                return
            if len(ids) != len(set(ids)):
                QMessageBox.critical(self, "错误", "不允许重复的 user_id。")
                return

            self.browser_service.save_cache(ids)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.progress.setMaximum(len(ids))
            self.progress.setValue(0)

            results = await self.browser_service.start_browsers(ids)
            success_count = 0
            for idx, result in enumerate(results, 1):
                status = result['status']
                if status == 'started' or status == 'already_running':
                    success_count += 1
                    
                self.log_signal.log_updated.emit(
                    f"[{idx}/{len(results)}] {result['user_id']} {result['status']} (端口: {result.get('port', 'N/A')})"
                )
                self.progress.setValue(idx)
                await asyncio.sleep(0.01)

            # 收集cookies
            if success_count > 0:
                self.log_signal.log_updated.emit("开始收集 cookies 信息...")
                try:
                    await self.browser_operator.attach_get_cookies(ids)
                    self.log_signal.log_updated.emit("完成收集 cookies 信息")
                except Exception as e:
                    self.log_signal.log_updated.emit(f"收集 cookies 失败: {e}")
            else:
                self.log_signal.log_updated.emit("没有成功启动的浏览器，无法收集 cookies")
                if sys.platform == 'win32':
                    self.log_signal.log_updated.emit("提示：Windows系统需要以管理员权限运行此程序")
        except Exception as e:
            self.log_signal.log_updated.emit(f"启动浏览器时发生错误: {e}")
            logger.error(f"启动浏览器失败: {e}", exc_info=True)
        finally:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.log_signal.log_updated.emit("启动浏览器操作已完成")

    @asyncSlot()
    async def stop_browsers(self):
        try:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.log_signal.log_updated.emit("正在关闭所有浏览器...")
            await self.browser_service.stop_all_browsers()
            self.progress.setValue(0)
            self.log_signal.log_updated.emit("所有浏览器已关闭")
        except Exception as e:
            self.log_signal.log_updated.emit(f"关闭浏览器时发生错误: {e}")
            logger.error(f"关闭浏览器失败: {e}", exc_info=True)
        finally:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)

    @staticmethod
    def _start_frpc():
        """
        启动 frpc 服务，使用固定配置文件，并确保可执行文件与配置文件存在
        
        注意：在Windows上可能需要管理员权限
        """
        frpc_path = os.path.join(BASE_DIR, "frp_client", "frpc.exe")
        toml_path = os.path.join(BASE_DIR, "frp_client", "frpc.toml")
        logger.info(f"frpc_path: {frpc_path}")

        for path, name in [(frpc_path, "frpc.exe"), (toml_path, "frpc.toml")]:
            if not os.path.exists(path):
                logger.error("%s 文件未找到 at %s", name, path)
                return None

        # 检查Windows权限
        if sys.platform == 'win32' and not is_admin():
            logger.warning("frpc服务可能需要管理员权限才能运行")

        try:
            proc = subprocess.Popen(
                [frpc_path, "-c", toml_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=0x08000000 if sys.platform == 'win32' else 0  # 隐藏窗口
            )
            logger.info("启动 frpc 服务: PID=%d", proc.pid)

            # 并行读取 stdout / stderr
            def reader(stream, name):
                for line in stream:
                    line = line.rstrip()
                    logger.info(f"FRP {name}：{line}")

            t1 = threading.Thread(target=reader, args=(proc.stdout, "输出"))
            t2 = threading.Thread(target=reader, args=(proc.stderr, "错误"))
            t1.daemon = True
            t2.daemon = True
            t1.start()
            t2.start()

            return proc

        except Exception as e:
            logger.error(f"启动 frpc 服务失败: {e}", exc_info=True)
            return None

    def save_cache(self):
        try:
            ids = [l for l in self.text_edit.toPlainText().splitlines() if l.strip()]
            self.browser_service.save_cache(ids)
            logger.info(f"保存用户缓存成功: {ids}")
        except Exception as e:
            logger.error(f"保存用户缓存失败: {e}")

    def load_cache(self):
        try:
            ids = self.browser_service.load_cache()
            self.text_edit.setText("\n".join(ids))
            logger.info(f"加载用户缓存成功: {ids}")
        except Exception as e:
            logger.error(f"加载用户缓存失败: {e}")

    @asyncSlot()
    async def clear_cache(self):
        """清除用户数据缓存和cookies信息"""
        try:
            self.browser_service.clear_cache()
            await self.browser_operator.clear_all_data()
            self.text_edit.clear()
            self.log_signal.log_updated.emit("缓存已清除")
            logger.info("缓存清除成功")
        except Exception as e:
            self.log_signal.log_updated.emit(f"清除缓存失败: {e}")
            logger.error(f"清除缓存失败: {e}")

    async def load_ports(self):
        """异步加载端口映射"""
        try:
            await self.browser_service.load_ports()
            logger.info("端口映射加载成功")
        except Exception as e:
            logger.error(f"加载端口映射失败: {e}")

    async def save_ports(self):
        """异步保存端口映射"""
        try:
            await self.browser_service.save_ports()
            logger.info("端口映射保存成功")
        except Exception as e:
            logger.error(f"保存端口映射失败: {e}")


def main():
    # 显示管理员权限提示
    if sys.platform == 'win32' and not is_admin():
        print("警告: 程序未以管理员权限运行。在Windows上，浏览器自动化功能可能受限。")
        print("建议: 右键点击程序，选择'以管理员身份运行'")
    
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    w = App()
    w.show()
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
