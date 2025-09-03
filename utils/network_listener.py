import re
import time
from typing import List, Dict, Any, Optional, Union, Callable
from pathlib import Path
import json
from datetime import datetime
from loguru import logger

from utils.common_logger import get_logger

logger = get_logger(__name__)


class EnhancedNetworkListener:
    """
    增强版网络监听器
    
    基于DrissionPage的网络监听功能，提供更多高级特性：
    - 支持指定URL过滤
    - 支持正则表达式匹配
    - 支持批量监听多个URL
    - 支持实时获取数据包
    - 支持数据包过滤和分析
    - 支持数据导出功能
    """

    def __init__(self, tab: Any) -> None:
        """
        初始化增强版网络监听器
        
        Args:
            tab: 浏览器标签页对象（DrissionPage的ChromiumPage或ChromiumTab实例）
        """
        self.tab = tab
        self.is_listening = False
        self.captured_packets = []
        self.url_filters = []
        self.callback = None
        
    def start_listening(self, url_patterns: Optional[Union[str, List[str]]] = None, callback: Optional[Callable] = None) -> None:
        """
        开始监听网络请求
        
        Args:
            url_patterns: 要监听的URL模式，可以是字符串或字符串列表，支持正则表达式
                          如果为None，则监听所有请求
            callback: 可选的回调函数，当捕获到匹配的请求时调用
        """
        # 停止之前的监听（如果有）
        if self.is_listening:
            self.stop_listening()
            
        # 设置URL过滤器
        self.url_filters = []
        if url_patterns:
            if isinstance(url_patterns, str):
                self.url_filters = [url_patterns]
            else:
                self.url_filters = url_patterns
                
        # 设置回调函数
        self.callback = callback
        
        # 清空之前捕获的数据包
        self.captured_packets = []
        
        # 开始监听
        if self.url_filters:
            logger.info(f"开始监听URL模式: {self.url_filters}")
            # 如果有指定URL模式，为每个模式启动监听
            for pattern in self.url_filters:
                self.tab.listen.start(pattern)
        else:
            logger.info("开始监听所有网络请求")
            # 监听所有请求
            self.tab.listen.start()
            
        self.is_listening = True
        
    def stop_listening(self) -> None:
        """
        停止网络请求监听
        """
        if self.is_listening:
            self.tab.listen.stop()
            self.is_listening = False
            logger.info(f"停止网络监听，共捕获 {len(self.captured_packets)} 个数据包")
            
    def wait_for_packet(self, timeout: int = 10, url_pattern: Optional[str] = None) -> Optional[Any]:
        """
        等待并捕获匹配的数据包
        
        Args:
            timeout: 等待超时时间（秒）
            url_pattern: 要匹配的URL模式，如果为None则使用之前设置的过滤器
            
        Returns:
            捕获到的数据包，如果超时则返回None
        """
        try:
            # 如果提供了新的URL模式，则使用它
            if url_pattern and not self.is_listening:
                self.tab.listen.start(url_pattern)
                self.is_listening = True
                
            # 等待匹配的请求
            packet = self.tab.listen.wait(timeout=timeout)
            
            # 如果捕获到数据包，添加到列表并处理回调
            if packet:
                self.captured_packets.append(packet)
                if self.callback:
                    self.callback(packet)
                    
            return packet
        except Exception as e:
            logger.error(f"等待数据包超时或发生错误: {e}")
            return None
            
    def start_realtime_capture(self, duration: int = 30, url_pattern: Optional[str] = None) -> List[Any]:
        """
        开始实时捕获网络请求，持续指定时间
        
        Args:
            duration: 捕获持续时间（秒）
            url_pattern: 要匹配的URL模式，如果为None则使用之前设置的过滤器
            
        Returns:
            捕获到的数据包列表
        """
        # 如果提供了新的URL模式，重新启动监听
        if url_pattern:
            self.start_listening(url_pattern)
        elif not self.is_listening:
            self.start_listening()
            
        captured = []
        start_time = time.time()
        logger.info(f"开始实时捕获网络请求，持续 {duration} 秒")
        
        try:
            while time.time() - start_time < duration:
                # 使用非阻塞方式获取数据包
                packet = self.tab.listen.steps()
                if packet:
                    # 检查是否匹配URL过滤器
                    if self._match_url_filters(packet):
                        captured.append(packet)
                        self.captured_packets.append(packet)
                        if self.callback:
                            self.callback(packet)
                        logger.debug(f"捕获到数据包: {packet.url}")
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.01)
        except Exception as e:
            logger.error(f"实时捕获过程中发生错误: {e}")
        finally:
            logger.info(f"实时捕获完成，共捕获 {len(captured)} 个数据包")
            return captured
            
    def _match_url_filters(self, packet: Any) -> bool:
        """
        检查数据包是否匹配URL过滤器
        
        Args:
            packet: 要检查的数据包
            
        Returns:
            是否匹配
        """
        # 如果没有过滤器，则匹配所有
        if not self.url_filters:
            return True
            
        # 获取数据包的URL
        url = packet.url
        
        # 检查是否匹配任一过滤器
        for pattern in self.url_filters:
            try:
                if re.search(pattern, url):
                    return True
            except re.error:
                # 如果正则表达式无效，则尝试简单字符串匹配
                if pattern in url:
                    return True
                    
        return False
        
    def get_request_headers(self, packet: Any) -> Dict[str, str]:
        """
        获取请求头信息
        
        Args:
            packet: 数据包
            
        Returns:
            请求头字典
        """
        if packet:
            return dict(packet.request.headers)
        return {}
        
    def get_response_headers(self, packet: Any) -> Dict[str, str]:
        """
        获取响应头信息
        
        Args:
            packet: 数据包
            
        Returns:
            响应头字典
        """
        if packet and hasattr(packet, 'response') and packet.response:
            return dict(packet.response.headers)
        return {}
        
    def get_request_data(self, packet: Any) -> Any:
        """
        获取请求数据
        
        Args:
            packet: 数据包
            
        Returns:
            请求数据
        """
        if packet and hasattr(packet, 'request'):
            return packet.request.data
        return None
        
    def get_response_data(self, packet: Any) -> Any:
        """
        获取响应数据
        
        Args:
            packet: 数据包
            
        Returns:
            响应数据
        """
        if packet and hasattr(packet, 'response'):
            return packet.response.data
        return None
        
    def filter_packets(self, filter_func: Callable[[Any], bool]) -> List[Any]:
        """
        根据自定义过滤函数筛选数据包
        
        Args:
            filter_func: 过滤函数，接收数据包作为参数，返回布尔值
            
        Returns:
            过滤后的数据包列表
        """
        return [packet for packet in self.captured_packets if filter_func(packet)]
        
    def filter_by_url(self, url_pattern: str) -> List[Any]:
        """
        根据URL模式筛选数据包
        
        Args:
            url_pattern: URL模式，支持正则表达式
            
        Returns:
            过滤后的数据包列表
        """
        try:
            return [packet for packet in self.captured_packets 
                   if re.search(url_pattern, packet.url)]
        except re.error:
            # 如果正则表达式无效，则尝试简单字符串匹配
            return [packet for packet in self.captured_packets 
                   if url_pattern in packet.url]
                   
    def filter_by_status_code(self, status_code: int) -> List[Any]:
        """
        根据HTTP状态码筛选数据包
        
        Args:
            status_code: HTTP状态码
            
        Returns:
            过滤后的数据包列表
        """
        return [packet for packet in self.captured_packets 
               if hasattr(packet, 'response') and 
               packet.response and 
               packet.response.status_code == status_code]
               
    def export_to_json(self, file_path: str) -> bool:
        """
        将捕获的数据包导出为JSON文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            # 准备导出数据
            export_data = []
            for packet in self.captured_packets:
                try:
                    packet_data = {
                        'url': packet.url,
                        'method': packet.request.method if hasattr(packet, 'request') else '',
                        'request_headers': self.get_request_headers(packet),
                        'response_headers': self.get_response_headers(packet),
                        'status_code': packet.response.status_code if hasattr(packet, 'response') and packet.response else None,
                        'timestamp': datetime.now().isoformat(),
                    }
                    
                    # 尝试添加请求和响应数据
                    request_data = self.get_request_data(packet)
                    response_data = self.get_response_data(packet)
                    
                    if request_data:
                        try:
                            # 尝试解析为JSON
                            if isinstance(request_data, str):
                                packet_data['request_data'] = json.loads(request_data)
                            else:
                                packet_data['request_data'] = request_data
                        except (json.JSONDecodeError, TypeError):
                            packet_data['request_data'] = str(request_data)
                            
                    if response_data:
                        try:
                            # 尝试解析为JSON
                            if isinstance(response_data, str):
                                packet_data['response_data'] = json.loads(response_data)
                            else:
                                packet_data['response_data'] = response_data
                        except (json.JSONDecodeError, TypeError):
                            packet_data['response_data'] = str(response_data)
                            
                    export_data.append(packet_data)
                except Exception as e:
                    logger.error(f"处理数据包时出错: {e}")
                    continue
                    
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"成功导出 {len(export_data)} 个数据包到 {file_path}")
            return True
        except Exception as e:
            logger.error(f"导出数据包到JSON文件失败: {e}")
            return False
            
    def clear_captured_packets(self) -> None:
        """
        清空已捕获的数据包
        """
        self.captured_packets = []
        logger.info("已清空捕获的数据包")