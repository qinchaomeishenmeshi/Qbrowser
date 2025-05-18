import asyncio
import socket
from typing import Set, Optional
from utils.common_logger import get_logger

logger = get_logger(__name__)

class PortManager:
    def __init__(self, start_port: int = 9000, end_port: int = 10000):
        self.start_port = start_port
        self.end_port = end_port
        self.used_ports: Set[int] = set()
        self._lock = asyncio.Lock()

    async def allocate_port(self) -> int:
        """
        分配一个可用的端口
        """
        async with self._lock:
            for port in range(self.start_port, self.end_port):
                if port not in self.used_ports and await self._is_port_available(port):
                    self.used_ports.add(port)
                    logger.info(f"Allocated port: {port}")
                    return port
            raise RuntimeError("没有可用的端口")

    @staticmethod
    async def _is_port_available(port: int) -> bool:
        """
        检查端口是否可用
        """
        try:
            # 创建 TCP 套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)  # 设置超时时间
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            # 如果连接失败（端口未被使用），返回True
            return result != 0
        except Exception as e:
            logger.error(f"检查端口 {port} 可用性时出错: {e}")
            return False

    async def release_port(self, port: int):
        """
        释放已使用的端口
        """
        async with self._lock:
            if port in self.used_ports:
                self.used_ports.discard(port)
                logger.info(f"Released port: {port}")

    async def load_ports(self, ports: Set[int]):
        """
        加载已使用的端口列表
        """
        async with self._lock:
            self.used_ports = {
                port for port in ports 
                if self.start_port <= port <= self.end_port
            }
            logger.info(f"Loaded used ports: {self.used_ports}")

    def get_used_ports(self) -> Set[int]:
        """
        获取当前使用中的端口列表
        """
        return self.used_ports.copy()

    async def clear_ports(self):
        """
        清除所有端口分配
        """
        async with self._lock:
            self.used_ports.clear()
            logger.info("Cleared all port allocations") 