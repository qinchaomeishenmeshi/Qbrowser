import asyncio
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Set
from collections import defaultdict
from dataclasses import dataclass
from functools import wraps
import hashlib

from conf import BASE_DIR, resource_path
from service.browser_service import browser_service
from utils.common_logger import get_logger
from utils.cookies_manager_optimized import OptimizedCookiesManager

logger = get_logger(__name__)

# 配置不同站点的URL和API监听路径
SITE_CONFIGS = {
    "baiying": {
        "name": "百应",
        "login_url": "https://buyin.jinritemai.com/mpa/account/login",
        "target_url": "https://buyin.jinritemai.com/dashboard/marketing/coupon-manager",
        "api_paths": ["/selection/common/btm_mapping"],
        "required_cookies": ["MSESSIONID", "passport_csrf_token"],
        "required_headers": ["x-secsdk-csrf-token", "user-agent"],
    },
    "screen": {
        "name": "百应大屏",
        "login_url": "",
        "target_url": "https://compass.jinritemai.com/screen/live/talent",
        "api_paths": ["/config_center/common/config"],
        "required_cookies": ["COMPASS_LUOPAN_DT", "LUOPAN_DT"],
        "required_headers": ["referer", "user-agent"],
    },
    "eos": {
        "name": "EOS抖音",
        "login_url": "",
        "target_url": "https://eos.douyin.com/livesite/live/history?tab=diagnosis",
        "api_paths": ["/life/api/live_screen/v4/replay/anchor_info"],
        "required_cookies": ["eos_s_token"],
        "required_headers": ["referer", "user-agent", "x-secsdk-csrf-token"],
    },
}


@dataclass
class RequestTask:
    """请求任务数据类"""
    user_id: str
    site_key: str
    url: str
    api_paths: List[str]
    max_retries: int = 2
    retry_delay: int = 1
    task_id: str = None
    
    def __post_init__(self):
        if self.task_id is None:
            # 生成唯一任务ID用于去重
            content = f"{self.user_id}_{self.site_key}_{self.url}_{','.join(self.api_paths)}"
            self.task_id = hashlib.md5(content.encode()).hexdigest()[:16]


class ConnectionPool:
    """浏览器连接池管理器"""
    
    def __init__(self, max_connections: int = 10, connection_timeout: int = 30):
        """
        初始化连接池
        
        Args:
            max_connections: 最大连接数
            connection_timeout: 连接超时时间（秒）
        """
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self._pool: Dict[str, Any] = {}  # user_id -> browser_manager
        self._pool_lock = asyncio.Lock()
        self._usage_count: Dict[str, int] = defaultdict(int)
        self._last_used: Dict[str, float] = {}
        
        # 启动连接池清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_idle_connections())
    
    async def get_connection(self, user_id: str) -> Optional[Any]:
        """
        从连接池获取浏览器连接
        
        Args:
            user_id: 用户ID
            
        Returns:
            浏览器管理器实例
        """
        async with self._pool_lock:
            # 检查现有连接
            if user_id in self._pool:
                manager = self._pool[user_id]
                if manager and manager.is_running:
                    self._usage_count[user_id] += 1
                    self._last_used[user_id] = time.time()
                    logger.debug(f"复用连接池中的浏览器实例: {user_id}")
                    return manager
                else:
                    # 连接已失效，移除
                    self._remove_connection(user_id)
            
            # 检查连接池是否已满
            if len(self._pool) >= self.max_connections:
                # 移除最久未使用的连接
                await self._evict_least_used()
            
            # 创建新连接
            try:
                manager = await browser_service.get_or_create_browser(user_id)
                if manager and manager.is_running:
                    self._pool[user_id] = manager
                    self._usage_count[user_id] = 1
                    self._last_used[user_id] = time.time()
                    logger.info(f"创建新的浏览器连接: {user_id}")
                    return manager
            except Exception as e:
                logger.error(f"创建浏览器连接失败 {user_id}: {e}")
            
            return None
    
    def _remove_connection(self, user_id: str) -> None:
        """移除连接（内部方法，需要在锁内调用）"""
        if user_id in self._pool:
            del self._pool[user_id]
        if user_id in self._usage_count:
            del self._usage_count[user_id]
        if user_id in self._last_used:
            del self._last_used[user_id]
    
    async def _evict_least_used(self) -> None:
        """移除最久未使用的连接"""
        if not self._last_used:
            return
        
        # 找到最久未使用的连接
        oldest_user = min(self._last_used.items(), key=lambda x: x[1])[0]
        
        try:
            # 尝试优雅关闭
            if oldest_user in self._pool:
                manager = self._pool[oldest_user]
                if manager:
                    await browser_service.stop_browser(oldest_user)
        except Exception as e:
            logger.error(f"关闭浏览器连接失败 {oldest_user}: {e}")
        finally:
            self._remove_connection(oldest_user)
            logger.info(f"从连接池移除最久未使用的连接: {oldest_user}")
    
    async def _cleanup_idle_connections(self) -> None:
        """定期清理空闲连接"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                current_time = time.time()
                idle_connections = []
                
                async with self._pool_lock:
                    for user_id, last_used in self._last_used.items():
                        if current_time - last_used > self.connection_timeout:
                            idle_connections.append(user_id)
                
                # 清理空闲连接
                for user_id in idle_connections:
                    try:
                        await browser_service.stop_browser(user_id)
                        async with self._pool_lock:
                            self._remove_connection(user_id)
                        logger.info(f"清理空闲连接: {user_id}")
                    except Exception as e:
                        logger.error(f"清理空闲连接失败 {user_id}: {e}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"连接池清理任务出错: {e}")
    
    async def close_all(self) -> None:
        """关闭所有连接"""
        self._cleanup_task.cancel()
        
        async with self._pool_lock:
            for user_id in list(self._pool.keys()):
                try:
                    await browser_service.stop_browser(user_id)
                except Exception as e:
                    logger.error(f"关闭连接失败 {user_id}: {e}")
            
            self._pool.clear()
            self._usage_count.clear()
            self._last_used.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        return {
            'active_connections': len(self._pool),
            'max_connections': self.max_connections,
            'usage_count': dict(self._usage_count),
            'pool_utilization': f"{len(self._pool) / self.max_connections * 100:.1f}%"
        }


class RequestDeduplicator:
    """请求去重器"""
    
    def __init__(self, ttl: int = 300):
        """
        初始化请求去重器
        
        Args:
            ttl: 去重缓存生存时间（秒）
        """
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def is_duplicate(self, task: RequestTask) -> bool:
        """
        检查是否为重复请求
        
        Args:
            task: 请求任务
            
        Returns:
            True表示重复请求，False表示新请求
        """
        async with self._lock:
            current_time = time.time()
            
            # 清理过期缓存
            expired_keys = [
                key for key, data in self._cache.items()
                if current_time - data['timestamp'] > self.ttl
            ]
            for key in expired_keys:
                del self._cache[key]
            
            # 检查是否重复
            if task.task_id in self._cache:
                logger.debug(f"检测到重复请求: {task.task_id}")
                return True
            
            # 记录新请求
            self._cache[task.task_id] = {
                'timestamp': current_time,
                'task': task
            }
            return False
    
    async def get_cached_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的请求结果"""
        async with self._lock:
            if task_id in self._cache:
                return self._cache[task_id].get('result')
            return None
    
    async def cache_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """缓存请求结果"""
        async with self._lock:
            if task_id in self._cache:
                self._cache[task_id]['result'] = result


def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """异步重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}，{current_delay}秒后重试")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"函数 {func.__name__} 重试 {max_retries} 次后仍然失败: {e}")
            
            raise last_exception
        return wrapper
    return decorator


class OptimizedRequestListener:
    """优化版请求监听器"""

    def __init__(self, tab: Any, api_uri: str, timeout: int = 5) -> None:
        """
        初始化优化版请求监听器
        
        Args:
            tab: 浏览器标签页对象
            api_uri: 要监听的API路径
            timeout: 监听超时时间（秒）
        """
        self.tab = tab
        self.api_uri = api_uri
        self.timeout = timeout
        self.packet = None

    @async_retry(max_retries=2, delay=0.5)
    async def listen_for(self) -> Optional[Any]:
        """
        开始监听并等待请求（异步优化版）
        
        Returns:
            捕获到的请求包，如果超时则返回None
        """
        try:
            # 使用异步方式启动监听
            self.tab.listen.start(self.api_uri)
            
            # 异步等待请求
            loop = asyncio.get_event_loop()
            self.packet = await loop.run_in_executor(
                None, 
                lambda: self.tab.listen.wait(timeout=self.timeout)
            )
            
            return self.packet
            
        except Exception as e:
            logger.error(f"监听 {self.api_uri} 失败: {e}")
            return None
        finally:
            try:
                self.tab.listen.stop()
            except Exception as e:
                logger.debug(f"停止监听时出错: {e}")

    def get_request_headers(self) -> Optional[Dict[str, str]]:
        """
        获取请求头信息
        
        Returns:
            请求头字典，如果没有捕获到请求则返回None
        """
        if self.packet and hasattr(self.packet, 'request'):
            try:
                return dict(self.packet.request.headers)
            except Exception as e:
                logger.error(f"获取请求头失败: {e}")
        return None


class OptimizedBrowserOperator:
    """
    优化版浏览器操作类
    
    性能优化特性：
    - 连接池管理，减少浏览器实例创建开销
    - 请求去重，避免重复操作
    - 异步并发处理，提高吞吐量
    - 智能标签页复用，减少资源消耗
    - 性能监控和统计
    """

    def __init__(self, max_connections: int = 10, cache_size: int = 1000):
        """
        初始化优化版浏览器操作器
        
        Args:
            max_connections: 最大浏览器连接数
            cache_size: cookies缓存大小
        """
        self.cookies_manager = OptimizedCookiesManager(
            Path(resource_path("data/cookies")), 
            cache_size=cache_size
        )
        self.connection_pool = ConnectionPool(max_connections=max_connections)
        self.deduplicator = RequestDeduplicator()
        
        # 性能统计
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'duplicate_requests': 0,
            'tab_reuses': 0,
            'new_tabs_created': 0
        }
    
    def get_or_create_tab(self, browser: Any, url: str) -> Any:
        """
        智能获取现有标签页或创建新标签页
        
        Args:
            browser: 浏览器实例
            url: 目标URL
            
        Returns:
            浏览器标签页对象
        """
        try:
            # 查找现有tabs中是否有匹配的URL或相似域名
            from urllib.parse import urlparse
            target_domain = urlparse(url).netloc
            
            for tab in browser.get_tabs():
                if tab.url:
                    tab_domain = urlparse(tab.url).netloc
                    # 精确匹配或同域名匹配
                    if url in tab.url or target_domain == tab_domain:
                        logger.debug(f"复用现有标签页: {tab.url}")
                        self._stats['tab_reuses'] += 1
                        return tab
        except Exception as e:
            logger.debug(f"查找现有标签页时出错: {e}")

        # 没找到匹配的tab，创建新的
        logger.debug(f"创建新标签页: {url}")
        self._stats['new_tabs_created'] += 1
        return browser.new_tab()
    
    @async_retry(max_retries=2, delay=1.0)
    async def fetch_cookies_and_headers_optimized(
        self,
        browser,
        user_id: str,
        url: str,
        api_paths: List[str],
        max_retries: int = 2,
        retry_delay: int = 1,
    ) -> Dict[str, Any]:
        """
        优化版获取cookies和headers方法
        
        Args:
            browser: 浏览器实例
            user_id: 用户ID
            url: 目标URL
            api_paths: 要监听的API路径列表
            max_retries: 最大重试次数
            retry_delay: 重试间隔(秒)

        Returns:
            包含cookies和headers的字典
        """
        results = {"cookies": {}, "headers": {}, "api_results": {}}
        
        try:
            # 检查登录状态
            tabs = browser.get_tabs()
            for tab in tabs:
                if "eos.douyin.com/livesite/login" in tab.url:
                    raise Exception("EOS未登录，操作失败")

            # 智能获取或创建标签页
            tab = self.get_or_create_tab(browser, url)
            
            # 异步加载页面
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, tab.get, url)
            await asyncio.sleep(1)  # 异步等待页面加载

            # 获取cookies（优化处理）
            raw_cookies = await loop.run_in_executor(None, tab.cookies)
            results["cookies"] = self._process_cookies(raw_cookies)
            
            logger.info(f"获取用户 {user_id} 的cookies，共 {len(results['cookies'])} 项")

            # 并发监听多个API路径
            api_tasks = []
            for api_path in api_paths:
                task = self._listen_api_path(tab, api_path, max_retries, retry_delay)
                api_tasks.append(task)
            
            # 等待所有API监听完成
            api_results = await asyncio.gather(*api_tasks, return_exceptions=True)
            
            # 处理API监听结果
            for i, result in enumerate(api_results):
                api_path = api_paths[i]
                if isinstance(result, Exception):
                    logger.error(f"API监听失败 {api_path}: {result}")
                    results["api_results"][api_path] = {"status": "failed", "error": str(result)}
                elif result:
                    results["headers"][api_path] = result
                    results["api_results"][api_path] = {"status": "success"}

            return results

        except Exception as e:
            logger.error(f"获取用户 {user_id} 的cookies和headers失败: {e}")
            raise
    
    def _process_cookies(self, raw_cookies) -> Dict[str, str]:
        """
        处理cookies格式转换（优化版）
        """
        try:
            if hasattr(raw_cookies, "as_dict"):
                return raw_cookies.as_dict()
            elif isinstance(raw_cookies, list):
                return {
                    c.get("name", ""): c.get("value", "")
                    for c in raw_cookies
                    if isinstance(c, dict) and "name" in c
                }
            elif isinstance(raw_cookies, dict):
                return raw_cookies
            else:
                return dict(raw_cookies)
        except (TypeError, ValueError) as e:
            logger.warning(f"cookies格式转换失败: {e}")
            return {}
    
    async def _listen_api_path(self, tab, api_path: str, max_retries: int, retry_delay: int) -> Optional[Dict[str, str]]:
        """
        监听单个API路径（异步优化版）
        """
        for retry in range(max_retries):
            try:
                logger.debug(f"监听 {api_path} (第 {retry + 1}/{max_retries} 次)")
                
                listener = OptimizedRequestListener(tab, api_path)
                
                # 刷新页面触发API请求
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, tab.refresh)
                
                # 异步监听
                packet = await listener.listen_for()
                if packet:
                    headers = listener.get_request_headers()
                    if headers:
                        logger.info(f"成功获取 {api_path} 的请求头")
                        return headers
                
                # 重试延迟
                if retry < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    
            except Exception as e:
                logger.error(f"监听 {api_path} 第 {retry + 1} 次尝试失败: {e}")
                if retry < max_retries - 1:
                    await asyncio.sleep(retry_delay)
        
        return None
    
    async def collect_site_cookies_optimized(
        self, user_id: str, site_key: str = "baiying", custom_config: Dict = None
    ) -> bool:
        """
        优化版收集特定站点的cookies
        
        Args:
            user_id: 用户ID
            site_key: 站点配置键名
            custom_config: 自定义配置

        Returns:
            操作成功与否
        """
        self._stats['total_requests'] += 1
        
        # 创建请求任务
        config = custom_config or SITE_CONFIGS.get(site_key)
        if not config:
            logger.error(f"站点 {site_key} 的配置不存在")
            self._stats['failed_requests'] += 1
            return False
        
        task = RequestTask(
            user_id=user_id,
            site_key=site_key,
            url=config["target_url"],
            api_paths=config["api_paths"]
        )
        
        # 检查请求去重
        if await self.deduplicator.is_duplicate(task):
            self._stats['duplicate_requests'] += 1
            logger.info(f"跳过重复请求: {user_id} - {site_key}")
            
            # 尝试获取缓存结果
            cached_result = await self.deduplicator.get_cached_result(task.task_id)
            return cached_result.get('success', False) if cached_result else False
        
        try:
            # 从连接池获取浏览器实例
            manager = await self.connection_pool.get_connection(user_id)
            if not manager or not manager.is_running:
                logger.error(f"用户 {user_id} 的浏览器实例获取失败")
                self._stats['failed_requests'] += 1
                return False

            # 获取cookies和headers
            raw_data = await self.fetch_cookies_and_headers_optimized(
                manager.browser, user_id, config["target_url"], config["api_paths"]
            )

            # 处理数据
            filtered_data = self.filter_data(raw_data)

            # 保存cookies和headers
            await self.cookies_manager.save_cookies(
                user_id,
                filtered_data["cookies"],
                filtered_data["headers"],
                site_key=site_key,
            )

            # 缓存结果
            result = {'success': True, 'data': filtered_data}
            await self.deduplicator.cache_result(task.task_id, result)
            
            logger.info(f"成功保存用户 {user_id} 的 {site_key} 站点数据")
            self._stats['successful_requests'] += 1
            return True

        except Exception as e:
            logger.error(f"收集用户 {user_id} 的 {site_key} 站点数据失败: {e}")
            
            # 缓存失败结果
            result = {'success': False, 'error': str(e)}
            await self.deduplicator.cache_result(task.task_id, result)
            
            self._stats['failed_requests'] += 1
            return False
    
    def filter_data(
        self,
        data: Dict[str, Any],
        required_cookies: List[str] = None,
        required_headers: List[str] = None,
    ) -> Dict[str, Any]:
        """
        过滤和处理数据（优化版）
        """
        result = {"cookies": {}, "headers": {}}

        # 收集全量cookies
        result["cookies"] = data.get("cookies", {})

        # 收集全量headers
        all_headers = {}
        for headers_dict in data.get("headers", {}).values():
            if isinstance(headers_dict, dict):
                all_headers.update(headers_dict)

        result["headers"] = all_headers
        return result
    
    async def batch_collect_cookies(
        self, user_ids: List[str], site_key: str = "baiying", max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量收集多个用户的cookies（高性能并发版）
        
        Args:
            user_ids: 用户ID列表
            site_key: 站点标识
            max_concurrent: 最大并发数
            
        Returns:
            操作结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_user_with_semaphore(user_id: str):
            async with semaphore:
                try:
                    success = await self.collect_site_cookies_optimized(user_id, site_key)
                    return {"user_id": user_id, "success": success}
                except Exception as e:
                    logger.error(f"批量处理用户 {user_id} 时出错: {e}")
                    return {"user_id": user_id, "success": False, "error": str(e)}
        
        tasks = [process_user_with_semaphore(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks)
        
        logger.info(f"批量收集完成，处理 {len(user_ids)} 个用户")
        return results
    
    # 保持与原版本兼容的方法
    async def get_user_cookies(self, user_id: str, site_key: str = "baiying") -> Optional[Dict]:
        """获取用户的cookies信息"""
        return await self.cookies_manager.get_cookies(user_id, site_key)

    async def get_user_headers(self, user_id: str, site_key: str = "baiying") -> Optional[Dict]:
        """获取用户的headers信息"""
        return await self.cookies_manager.get_headers(user_id, site_key)

    async def clear_user_data(self, user_id: str, site_key: str = None):
        """清除用户的cookies信息"""
        await self.cookies_manager.remove_cookies(user_id, site_key)

    async def clear_all_data(self):
        """清除所有用户的cookies信息"""
        await self.cookies_manager.clear_all()

    async def check_and_refresh_cookies(self, user_id: str, site_key: str = "baiying") -> bool:
        """检查并在需要时刷新cookies"""
        cookies = await self.cookies_manager.get_cookies(user_id, site_key)
        if not cookies:
            logger.info(f"用户 {user_id} 的cookies不存在，尝试收集")
            return await self.collect_site_cookies_optimized(user_id, site_key)
        return True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            包含各种性能指标的字典
        """
        cookies_stats = self.cookies_manager.get_performance_stats()
        pool_stats = self.connection_pool.get_stats()
        
        success_rate = 0
        if self._stats['total_requests'] > 0:
            success_rate = (self._stats['successful_requests'] / self._stats['total_requests']) * 100
        
        return {
            'browser_operator': {
                'total_requests': self._stats['total_requests'],
                'successful_requests': self._stats['successful_requests'],
                'failed_requests': self._stats['failed_requests'],
                'duplicate_requests': self._stats['duplicate_requests'],
                'success_rate': f"{success_rate:.2f}%",
                'tab_reuses': self._stats['tab_reuses'],
                'new_tabs_created': self._stats['new_tabs_created']
            },
            'cookies_manager': cookies_stats,
            'connection_pool': pool_stats
        }
    
    async def close(self):
        """关闭所有资源"""
        await self.connection_pool.close_all()
        if hasattr(self.cookies_manager, '__aexit__'):
            await self.cookies_manager.__aexit__(None, None, None)


# 创建优化版实例
optimized_browser_operator = OptimizedBrowserOperator()