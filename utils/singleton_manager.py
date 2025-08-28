"""
基于 QLocalServer/QLocalSocket 的单例管理器
提供跨平台的应用程序单例检查功能
"""
import os
import sys
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from utils.common_logger import get_logger

logger = get_logger(__name__)


class SingletonManager(QObject):
    """单例管理器
    
    使用 QLocalServer/QLocalSocket 实现跨平台的单例检查
    比 filelock 更适合 Qt 应用程序
    """
    
    # 信号：当检测到另一个实例尝试启动时发出
    another_instance_started = pyqtSignal()
    
    def __init__(self, app_name="qw_browser"):
        super().__init__()
        self.app_name = app_name
        self.server = None
        self.socket = None
        
        # 生成唯一的服务器名称，避免不同用户间的冲突
        self.server_name = f"{app_name}_{self._get_user_id()}"
        
    def _get_user_id(self):
        """获取用户标识，确保不同用户的实例不冲突"""
        try:
            if sys.platform == "win32":
                # Windows: 使用用户名
                return os.getenv('USERNAME', 'unknown')
            else:
                # Unix-like: 使用用户ID
                return str(os.getuid())
        except Exception:
            return "default"
    
    def is_already_running(self):
        """检查应用是否已经在运行
        
        Returns:
            bool: True表示已有实例在运行，False表示没有
        """
        # 检查环境变量，允许跳过单例检查
        if os.getenv('QW_BROWSER_SKIP_SINGLETON_CHECK', '').lower() in ('1', 'true', 'yes'):
            logger.info("跳过单例检查（通过环境变量配置）")
            return False
            
        # 尝试连接到现有的本地服务器
        self.socket = QLocalSocket()
        self.socket.connectToServer(self.server_name)
        
        # 等待连接结果
        if self.socket.waitForConnected(1000):  # 等待1秒
            logger.info(f"检测到应用程序已在运行（服务器名: {self.server_name}）")
            
            # 发送启动信号给已存在的实例
            self.socket.write(b"ACTIVATE")
            self.socket.waitForBytesWritten(1000)
            self.socket.disconnectFromServer()
            return True
        
        # 连接失败，说明没有现有实例，尝试创建服务器
        return not self._create_server()
    
    def _create_server(self):
        """创建本地服务器
        
        Returns:
            bool: True表示创建成功，False表示创建失败
        """
        try:
            self.server = QLocalServer()
            
            # 移除可能存在的旧服务器（处理异常退出的情况）
            QLocalServer.removeServer(self.server_name)
            
            # 监听新连接
            self.server.newConnection.connect(self._handle_new_connection)
            
            # 开始监听
            if self.server.listen(self.server_name):
                logger.info(f"单例服务器创建成功，服务器名: {self.server_name}")
                return True
            else:
                error = self.server.errorString()
                logger.error(f"创建单例服务器失败: {error}")
                return False
                
        except Exception as e:
            logger.error(f"创建单例服务器时发生异常: {e}")
            return False
    
    def _handle_new_connection(self):
        """处理新的连接（其他实例尝试启动）"""
        if self.server is None:
            return
            
        socket = self.server.nextPendingConnection()
        if socket is None:
            return
            
        logger.info("检测到另一个实例尝试启动")
        
        # 读取消息
        if socket.waitForReadyRead(1000):
            data = socket.readAll().data()
            if data == b"ACTIVATE":
                logger.info("收到激活信号，发出another_instance_started信号")
                self.another_instance_started.emit()
        
        socket.disconnectFromServer()
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.socket:
                self.socket.disconnectFromServer()
                self.socket = None
                
            if self.server:
                self.server.close()
                QLocalServer.removeServer(self.server_name)
                self.server = None
                logger.info("单例服务器已关闭")
        except Exception as e:
            logger.error(f"清理单例管理器资源时发生错误: {e}")


# 全局单例管理器实例
_singleton_manager = None


def get_singleton_manager():
    """获取全局单例管理器实例"""
    global _singleton_manager
    if _singleton_manager is None:
        _singleton_manager = SingletonManager()
    return _singleton_manager


def check_single_instance():
    """检查是否已有应用程序实例在运行
    
    Returns:
        bool: True表示可以启动（没有其他实例），False表示已有实例在运行
    """
    manager = get_singleton_manager()
    return not manager.is_already_running()


def release_single_instance():
    """释放单例资源"""
    global _singleton_manager
    if _singleton_manager:
        _singleton_manager.cleanup()
        _singleton_manager = None


def setup_activate_on_second_instance(callback):
    """设置当第二个实例尝试启动时的回调函数
    
    Args:
        callback: 回调函数，当检测到另一个实例启动时调用
    """
    manager = get_singleton_manager()
    manager.another_instance_started.connect(callback)