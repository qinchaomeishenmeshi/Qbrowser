#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的浏览器操作器

本模块提供了优化的浏览器操作功能，包括：
1. 连接池管理 - 复用浏览器连接，减少创建开销
2. 请求去重 - 避免重复操作，提高效率
3. 异步重试机制 - 提高操作稳定性
4. 批量处理支持 - 提升并发能力
5. 性能监控 - 统计操作指标

作者: Assistant
创建时间: 2024
"""

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Dict, List, Optional, Any, Callable, Set, Tuple, Union
from weakref import WeakSet

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    # 如果DrissionPage不可用，提供模拟类
    class ChromiumPage:
        def __init__(self, *args, **kwargs):
            pass
    
    class ChromiumOptions:
        def __init__(self, *args, **kwargs):
            pass

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """连接信息数据类"""
    page: ChromiumPage
    created_at: float
    last_used: float
    use_count: int = 0
    is_busy: bool = False
    domain: Optional[str] = None
    error_count: int = 0
    max_errors: int = 3
    
    def is_expired(self, max_age: float = 3600) -> bool:
        """检查连接是否过期"""
        return time.time() - self.created_at > max_age
    
    def is_idle_too_long(self, max_idle: float = 1800) -> bool:
        """检查连接是否空闲过久"""
        return time.time() - self.last_used > max_idle
    
    def should_retire(self) -> bool:
        """检查连接是否应该退役"""
        return (
            self.error_count >= self.max_errors or
            self.is_expired() or
            self.is_idle_too_long()
        )


@dataclass
class OperationStats:
    """操作统计数据类"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    deduplicated_operations: int = 0
    retry_operations: int = 0
    total_execution_time: float = 0.0
    connection_reuses: int = 0
    connection_creates: int = 0
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_operations == 0:
            return 0.0
        return self.successful_operations / self.total_operations
    
    @property
    def average_execution_time(self) -> float:
        """计算平均执行时间"""
        if self.successful_operations == 0:
            return 0.0
        return self.total_execution_time / self.successful_operations
    
    @property
    def deduplication_rate(self) -> float:
        """计算去重率"""
        if self.total_operations == 0:
            return 0.0
        return self.deduplicated_operations / self.total_operations
    
    @property
    def connection_reuse_rate(self) -> float:
        """计算连接复用率"""
        total_connections = self.connection_reuses + self.connection_creates
        if total_connections == 0:
            return 0.0
        return self.connection_reuses / total_connections


class ConnectionPool:
    """浏览器连接池管理器"""
    
    def __init__(self, max_size: int = 10, max_age: float = 3600, max_idle: float = 1800):
        """初始化连接池
        
        Args:
            max_size: 最大连接数
            max_age: 连接最大存活时间（秒）
            max_idle: 连接最大空闲时间（秒）
        """
        self.max_size = max_size
        self.max_age = max_age
        self.max_idle = max_idle
        
        # 连接存储
        self._connections: Dict[str, ConnectionInfo] = {}
        self._available_connections: deque = deque()
        self._busy_connections: Set[str] = set()
        
        # 同步控制
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_size)
        
        # 统计信息
        self._stats = OperationStats()
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self):
        """启动连接池"""
        if self._is_running:
            return
        
        self._is_running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"连接池已启动，最大连接数: {self.max_size}")
    
    async def stop(self):
        """停止连接池"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 关闭所有连接
        async with self._lock:
            for conn_id, conn_info in self._connections.items():
                try:
                    if hasattr(conn_info.page, 'quit'):
                        conn_info.page.quit()
                except Exception as e:
                    logger.warning(f"关闭连接 {conn_id} 时出错: {e}")
            
            self._connections.clear()
            self._available_connections.clear()
            self._busy_connections.clear()
        
        logger.info("连接池已停止")
    
    @asynccontextmanager
    async def get_connection(self, domain: Optional[str] = None):
        """获取连接的上下文管理器
        
        Args:
            domain: 目标域名，用于连接复用优化
        
        Yields:
            ConnectionInfo: 连接信息对象
        """
        await self._semaphore.acquire()
        
        conn_info = None
        conn_id = None
        
        try:
            # 获取连接
            conn_id, conn_info = await self._acquire_connection(domain)
            yield conn_info
            
        except Exception as e:
            if conn_info:
                conn_info.error_count += 1
                logger.error(f"连接 {conn_id} 操作失败: {e}")
            raise
        
        finally:
            # 释放连接
            if conn_id and conn_info:
                await self._release_connection(conn_id, conn_info)
            
            self._semaphore.release()
    
    async def _acquire_connection(self, domain: Optional[str] = None) -> Tuple[str, ConnectionInfo]:
        """获取可用连接
        
        Args:
            domain: 目标域名
        
        Returns:
            Tuple[str, ConnectionInfo]: 连接ID和连接信息
        """
        async with self._lock:
            # 1. 尝试复用现有连接
            conn_id, conn_info = await self._find_reusable_connection(domain)
            
            if conn_info:
                # 标记为忙碌
                conn_info.is_busy = True
                conn_info.last_used = time.time()
                conn_info.use_count += 1
                
                self._available_connections.remove(conn_id)
                self._busy_connections.add(conn_id)
                
                self._stats.connection_reuses += 1
                logger.debug(f"复用连接 {conn_id}，使用次数: {conn_info.use_count}")
                
                return conn_id, conn_info
            
            # 2. 创建新连接
            if len(self._connections) >= self.max_size:
                # 清理过期连接
                await self._cleanup_expired_connections()
                
                # 如果仍然达到上限，等待
                if len(self._connections) >= self.max_size:
                    raise RuntimeError(f"连接池已满，当前连接数: {len(self._connections)}")
            
            # 创建新连接
            conn_id, conn_info = await self._create_connection(domain)
            
            # 添加到池中
            self._connections[conn_id] = conn_info
            self._busy_connections.add(conn_id)
            
            self._stats.connection_creates += 1
            logger.debug(f"创建新连接 {conn_id}，当前连接数: {len(self._connections)}")
            
            return conn_id, conn_info
    
    async def _find_reusable_connection(self, domain: Optional[str] = None) -> Tuple[Optional[str], Optional[ConnectionInfo]]:
        """查找可复用的连接
        
        Args:
            domain: 目标域名
        
        Returns:
            Tuple[Optional[str], Optional[ConnectionInfo]]: 连接ID和连接信息
        """
        if not self._available_connections:
            return None, None
        
        # 优先选择相同域名的连接
        if domain:
            for conn_id in list(self._available_connections):
                conn_info = self._connections.get(conn_id)
                if conn_info and conn_info.domain == domain and not conn_info.should_retire():
                    return conn_id, conn_info
        
        # 选择任意可用连接
        for conn_id in list(self._available_connections):
            conn_info = self._connections.get(conn_id)
            if conn_info and not conn_info.should_retire():
                return conn_id, conn_info
        
        return None, None
    
    async def _create_connection(self, domain: Optional[str] = None) -> Tuple[str, ConnectionInfo]:
        """创建新连接
        
        Args:
            domain: 目标域名
        
        Returns:
            Tuple[str, ConnectionInfo]: 连接ID和连接信息
        """
        try:
            # 创建浏览器选项
            options = ChromiumOptions()
            options.headless(True)  # 无头模式
            options.set_argument('--no-sandbox')
            options.set_argument('--disable-dev-shm-usage')
            options.set_argument('--disable-gpu')
            
            # 创建页面
            page = ChromiumPage(options)
            
            # 生成连接ID
            conn_id = f"conn_{int(time.time() * 1000)}_{id(page)}"
            
            # 创建连接信息
            conn_info = ConnectionInfo(
                page=page,
                created_at=time.time(),
                last_used=time.time(),
                is_busy=True,
                domain=domain
            )
            
            return conn_id, conn_info
            
        except Exception as e:
            logger.error(f"创建连接失败: {e}")
            raise
    
    async def _release_connection(self, conn_id: str, conn_info: ConnectionInfo):
        """释放连接
        
        Args:
            conn_id: 连接ID
            conn_info: 连接信息
        """
        async with self._lock:
            if conn_id not in self._connections:
                return
            
            # 检查连接是否应该退役
            if conn_info.should_retire():
                await self._remove_connection(conn_id)
                return
            
            # 标记为可用
            conn_info.is_busy = False
            conn_info.last_used = time.time()
            
            self._busy_connections.discard(conn_id)
            self._available_connections.append(conn_id)
            
            logger.debug(f"释放连接 {conn_id}，当前可用连接数: {len(self._available_connections)}")
    
    async def _remove_connection(self, conn_id: str):
        """移除连接
        
        Args:
            conn_id: 连接ID
        """
        conn_info = self._connections.get(conn_id)
        if not conn_info:
            return
        
        try:
            # 关闭浏览器页面
            if hasattr(conn_info.page, 'quit'):
                conn_info.page.quit()
        except Exception as e:
            logger.warning(f"关闭连接 {conn_id} 时出错: {e}")
        
        # 从池中移除
        self._connections.pop(conn_id, None)
        
        # 从队列中移除
        try:
            self._available_connections.remove(conn_id)
        except ValueError:
            pass
        
        self._busy_connections.discard(conn_id)
        
        logger.debug(f"移除连接 {conn_id}，当前连接数: {len(self._connections)}")
    
    async def _cleanup_expired_connections(self):
        """清理过期连接"""
        expired_connections = []
        
        for conn_id, conn_info in self._connections.items():
            if not conn_info.is_busy and conn_info.should_retire():
                expired_connections.append(conn_id)
        
        for conn_id in expired_connections:
            await self._remove_connection(conn_id)
        
        if expired_connections:
            logger.info(f"清理了 {len(expired_connections)} 个过期连接")
    
    async def _cleanup_loop(self):
        """定期清理循环"""
        while self._is_running:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                await self._cleanup_expired_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理循环出错: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取连接池统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        return {
            "total_connections": len(self._connections),
            "available_connections": len(self._available_connections),
            "busy_connections": len(self._busy_connections),
            "max_size": self.max_size,
            "connection_reuses": self._stats.connection_reuses,
            "connection_creates": self._stats.connection_creates,
            "connection_reuse_rate": self._stats.connection_reuse_rate
        }


class RequestDeduplicator:
    """请求去重器"""
    
    def __init__(self, max_cache_size: int = 1000, ttl: float = 300):
        """初始化去重器
        
        Args:
            max_cache_size: 最大缓存大小
            ttl: 缓存生存时间（秒）
        """
        self.max_cache_size = max_cache_size
        self.ttl = ttl
        
        # 请求缓存：{request_hash: (result, timestamp)}
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._access_order: deque = deque()
        
        # 进行中的请求：{request_hash: Future}
        self._pending_requests: Dict[str, asyncio.Future] = {}
        
        # 同步控制
        self._lock = asyncio.Lock()
    
    def _generate_request_hash(self, operation: str, *args, **kwargs) -> str:
        """生成请求哈希
        
        Args:
            operation: 操作名称
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            str: 请求哈希值
        """
        # 创建请求标识
        request_data = {
            'operation': operation,
            'args': args,
            'kwargs': {k: v for k, v in kwargs.items() if k not in ['timeout', 'retry_count']}
        }
        
        # 生成哈希
        request_str = str(sorted(request_data.items()))
        return hashlib.md5(request_str.encode()).hexdigest()
    
    async def deduplicate_request(self, operation: str, func: Callable, *args, **kwargs) -> Any:
        """去重请求
        
        Args:
            operation: 操作名称
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        Returns:
            Any: 函数执行结果
        """
        request_hash = self._generate_request_hash(operation, *args, **kwargs)
        
        async with self._lock:
            # 1. 检查缓存
            if request_hash in self._cache:
                result, timestamp = self._cache[request_hash]
                if time.time() - timestamp < self.ttl:
                    # 更新访问顺序
                    try:
                        self._access_order.remove(request_hash)
                    except ValueError:
                        pass
                    self._access_order.append(request_hash)
                    
                    logger.debug(f"请求去重命中: {operation}")
                    return result
                else:
                    # 缓存过期，移除
                    self._cache.pop(request_hash, None)
            
            # 2. 检查是否有相同请求正在进行
            if request_hash in self._pending_requests:
                logger.debug(f"等待相同请求完成: {operation}")
                return await self._pending_requests[request_hash]
            
            # 3. 创建新请求
            future = asyncio.Future()
            self._pending_requests[request_hash] = future
        
        try:
            # 执行请求
            result = await func(*args, **kwargs)
            
            # 缓存结果
            async with self._lock:
                self._cache[request_hash] = (result, time.time())
                self._access_order.append(request_hash)
                
                # 清理过期缓存
                await self._cleanup_cache()
                
                # 通知等待的请求
                future.set_result(result)
            
            return result
            
        except Exception as e:
            # 通知等待的请求
            async with self._lock:
                if not future.done():
                    future.set_exception(e)
            raise
        
        finally:
            # 清理进行中的请求
            async with self._lock:
                self._pending_requests.pop(request_hash, None)
    
    async def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        
        # 移除过期项
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp >= self.ttl
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            try:
                self._access_order.remove(key)
            except ValueError:
                pass
        
        # 如果缓存仍然过大，移除最旧的项
        while len(self._cache) > self.max_cache_size and self._access_order:
            oldest_key = self._access_order.popleft()
            self._cache.pop(oldest_key, None)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取去重器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        return {
            "cached_requests": len(self._cache),
            "pending_requests": len(self._pending_requests),
            "max_cache_size": self.max_cache_size,
            "cache_ttl": self.ttl
        }


def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """异步重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避倍数
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败: {e}")
                        raise
                    
                    logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}，{current_delay}秒后重试")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # 这行代码理论上不会执行到
            raise last_exception
        
        return wrapper
    return decorator


class OptimizedBrowserOperator:
    """优化的浏览器操作器
    
    提供高性能的浏览器操作功能，包括连接池管理、请求去重、
    异步重试等优化特性。
    """
    
    def __init__(
        self,
        max_pool_size: int = 10,
        enable_request_deduplication: bool = True,
        dedup_cache_size: int = 1000,
        dedup_ttl: float = 300,
        connection_max_age: float = 3600,
        connection_max_idle: float = 1800
    ):
        """初始化优化的浏览器操作器
        
        Args:
            max_pool_size: 最大连接池大小
            enable_request_deduplication: 是否启用请求去重
            dedup_cache_size: 去重缓存大小
            dedup_ttl: 去重缓存TTL（秒）
            connection_max_age: 连接最大存活时间（秒）
            connection_max_idle: 连接最大空闲时间（秒）
        """
        # 连接池
        self.connection_pool = ConnectionPool(
            max_size=max_pool_size,
            max_age=connection_max_age,
            max_idle=connection_max_idle
        )
        
        # 请求去重器
        self.enable_deduplication = enable_request_deduplication
        if enable_request_deduplication:
            self.deduplicator = RequestDeduplicator(
                max_cache_size=dedup_cache_size,
                ttl=dedup_ttl
            )
        else:
            self.deduplicator = None
        
        # 统计信息
        self.stats = OperationStats()
        
        # 运行状态
        self._is_started = False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()
    
    async def start(self):
        """启动浏览器操作器"""
        if self._is_started:
            return
        
        await self.connection_pool.start()
        self._is_started = True
        logger.info("优化的浏览器操作器已启动")
    
    async def stop(self):
        """停止浏览器操作器"""
        if not self._is_started:
            return
        
        await self.connection_pool.stop()
        self._is_started = False
        logger.info("优化的浏览器操作器已停止")
    
    @async_retry(max_retries=3, delay=1.0, backoff=2.0)
    async def navigate_to_url(self, url: str, domain: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """导航到指定URL
        
        Args:
            url: 目标URL
            domain: 域名（用于连接复用优化）
            **kwargs: 其他参数
        
        Returns:
            Dict[str, Any]: 操作结果
        """
        start_time = time.time()
        
        try:
            # 提取域名
            if not domain:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc
            
            # 执行操作
            if self.enable_deduplication and self.deduplicator:
                result = await self.deduplicator.deduplicate_request(
                    'navigate_to_url',
                    self._navigate_to_url_impl,
                    url, domain, **kwargs
                )
            else:
                result = await self._navigate_to_url_impl(url, domain, **kwargs)
            
            # 更新统计
            execution_time = time.time() - start_time
            self.stats.total_operations += 1
            self.stats.successful_operations += 1
            self.stats.total_execution_time += execution_time
            
            return result
            
        except Exception as e:
            self.stats.total_operations += 1
            self.stats.failed_operations += 1
            logger.error(f"导航到 {url} 失败: {e}")
            raise
    
    async def _navigate_to_url_impl(self, url: str, domain: str, **kwargs) -> Dict[str, Any]:
        """导航到URL的实现
        
        Args:
            url: 目标URL
            domain: 域名
            **kwargs: 其他参数
        
        Returns:
            Dict[str, Any]: 操作结果
        """
        async with self.connection_pool.get_connection(domain) as conn_info:
            try:
                # 导航到URL
                conn_info.page.get(url)
                
                # 等待页面加载
                timeout = kwargs.get('timeout', 10)
                await asyncio.sleep(0.5)  # 简单的等待，实际应该等待页面加载完成
                
                # 获取页面信息
                title = getattr(conn_info.page, 'title', 'Unknown')
                current_url = getattr(conn_info.page, 'url', url)
                
                return {
                    'success': True,
                    'url': current_url,
                    'title': title,
                    'connection_id': id(conn_info.page),
                    'use_count': conn_info.use_count
                }
                
            except Exception as e:
                logger.error(f"页面导航失败: {e}")
                raise
    
    async def batch_navigate(self, urls: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """批量导航到多个URL
        
        Args:
            urls: URL列表
            max_concurrent: 最大并发数
        
        Returns:
            List[Dict[str, Any]]: 操作结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def navigate_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                try:
                    return await self.navigate_to_url(url)
                except Exception as e:
                    return {
                        'success': False,
                        'url': url,
                        'error': str(e)
                    }
        
        # 并发执行
        tasks = [navigate_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'url': urls[i],
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取操作统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        stats = {
            'operations': {
                'total': self.stats.total_operations,
                'successful': self.stats.successful_operations,
                'failed': self.stats.failed_operations,
                'success_rate': self.stats.success_rate,
                'average_execution_time': self.stats.average_execution_time
            },
            'connection_pool': self.connection_pool.get_statistics()
        }
        
        if self.deduplicator:
            stats['deduplication'] = self.deduplicator.get_statistics()
            stats['deduplication']['deduplication_rate'] = self.stats.deduplication_rate
        
        return stats
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = OperationStats()
        logger.info("统计信息已重置")


# 便捷函数
async def create_optimized_browser_operator(**kwargs) -> OptimizedBrowserOperator:
    """创建并启动优化的浏览器操作器
    
    Args:
        **kwargs: 初始化参数
    
    Returns:
        OptimizedBrowserOperator: 已启动的浏览器操作器
    """
    operator = OptimizedBrowserOperator(**kwargs)
    await operator.start()
    return operator


if __name__ == "__main__":
    # 示例用法
    async def main():
        """主函数示例"""
        async with OptimizedBrowserOperator(
            max_pool_size=5,
            enable_request_deduplication=True
        ) as operator:
            
            # 单个URL导航
            result = await operator.navigate_to_url("https://www.example.com")
            print(f"导航结果: {result}")
            
            # 批量URL导航
            urls = [
                "https://www.example.com",
                "https://www.google.com",
                "https://www.github.com"
            ]
            
            batch_results = await operator.batch_navigate(urls, max_concurrent=3)
            print(f"批量导航结果: {len(batch_results)} 个URL")
            
            # 获取统计信息
            stats = operator.get_statistics()
            print(f"操作统计: {stats}")
    
    # 运行示例
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        print(f"程序执行出错: {e}")