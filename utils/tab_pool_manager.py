import asyncio
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
from urllib.parse import urlparse

from utils.common_logger import get_logger

logger = get_logger(__name__)


class TabState(Enum):
    """标签页状态枚举"""
    IDLE = "idle"  # 空闲状态
    BUSY = "busy"  # 忙碌状态
    LOADING = "loading"  # 加载中
    ERROR = "error"  # 错误状态
    CLOSED = "closed"  # 已关闭


@dataclass
class TabInfo:
    """标签页信息数据类"""
    tab_id: str
    page: Any  # Playwright Page对象
    url: str = ""
    domain: str = ""
    state: TabState = TabState.IDLE
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    use_count: int = 0
    task_id: Optional[str] = None
    cookies_loaded: bool = False
    user_agent: str = ""
    viewport_size: Tuple[int, int] = (1920, 1080)
    
    def update_usage(self, task_id: Optional[str] = None):
        """更新使用信息"""
        self.last_used_at = time.time()
        self.use_count += 1
        self.task_id = task_id
        self.state = TabState.BUSY
    
    def mark_idle(self):
        """标记为空闲状态"""
        self.state = TabState.IDLE
        self.task_id = None
    
    def is_reusable(self, target_domain: str, max_idle_time: int = 1800) -> bool:
        """判断是否可复用"""
        if self.state != TabState.IDLE:
            return False
        
        # 检查域名匹配
        if self.domain != target_domain:
            return False
        
        # 检查空闲时间
        idle_time = time.time() - self.last_used_at
        if idle_time > max_idle_time:
            return False
        
        return True
    
    def get_age(self) -> float:
        """获取标签页年龄（秒）"""
        return time.time() - self.created_at
    
    def get_idle_time(self) -> float:
        """获取空闲时间（秒）"""
        return time.time() - self.last_used_at


class TabPoolManager:
    """
    标签页池管理器
    
    功能：
    - 智能复用标签页，减少创建开销
    - 按域名分组管理标签页
    - 自动清理过期和无用的标签页
    - 支持并发任务的标签页分配
    """
    
    def __init__(
        self,
        max_tabs_per_domain: int = 3,
        max_total_tabs: int = 20,
        max_idle_time: int = 1800,  # 30分钟
        max_tab_age: int = 7200,  # 2小时
        cleanup_interval: int = 300  # 5分钟
    ):
        """
        初始化标签页池管理器
        
        Args:
            max_tabs_per_domain: 每个域名最大标签页数
            max_total_tabs: 总最大标签页数
            max_idle_time: 最大空闲时间（秒）
            max_tab_age: 最大标签页年龄（秒）
            cleanup_interval: 清理间隔（秒）
        """
        self.max_tabs_per_domain = max_tabs_per_domain
        self.max_total_tabs = max_total_tabs
        self.max_idle_time = max_idle_time
        self.max_tab_age = max_tab_age
        self.cleanup_interval = cleanup_interval
        
        # 标签页存储
        self._tabs: Dict[str, TabInfo] = {}  # tab_id -> TabInfo
        self._domain_tabs: Dict[str, Set[str]] = defaultdict(set)  # domain -> set of tab_ids
        self._busy_tabs: Set[str] = set()  # 忙碌的标签页ID
        
        # 锁和信号量
        self._lock = asyncio.Lock()
        self._tab_semaphore = asyncio.Semaphore(max_total_tabs)
        
        # 统计信息
        self._stats = {
            'created_tabs': 0,
            'reused_tabs': 0,
            'closed_tabs': 0,
            'cleanup_runs': 0
        }
        
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def get_tab(self, url: str, browser_context: Any, task_id: Optional[str] = None) -> Tuple[Any, str]:
        """
        获取或创建标签页
        
        Args:
            url: 目标URL
            browser_context: 浏览器上下文
            task_id: 任务ID
            
        Returns:
            (page对象, tab_id)元组
        """
        domain = self._extract_domain(url)
        
        async with self._lock:
            # 尝试复用现有标签页
            reusable_tab = await self._find_reusable_tab(domain)
            
            if reusable_tab:
                reusable_tab.update_usage(task_id)
                self._busy_tabs.add(reusable_tab.tab_id)
                self._stats['reused_tabs'] += 1
                
                logger.debug(f"复用标签页 {reusable_tab.tab_id} for {domain}")
                return reusable_tab.page, reusable_tab.tab_id
            
            # 检查是否需要清理以腾出空间
            if len(self._tabs) >= self.max_total_tabs:
                await self._cleanup_excess_tabs()
            
            # 检查域名标签页数量限制
            if len(self._domain_tabs[domain]) >= self.max_tabs_per_domain:
                await self._cleanup_domain_tabs(domain)
        
        # 创建新标签页（在锁外执行，避免阻塞）
        await self._tab_semaphore.acquire()
        
        try:
            page = await browser_context.new_page()
            tab_id = self._generate_tab_id(url, task_id)
            
            # 配置页面
            await self._configure_page(page)
            
            # 创建标签页信息
            tab_info = TabInfo(
                tab_id=tab_id,
                page=page,
                url=url,
                domain=domain,
                state=TabState.BUSY,
                task_id=task_id
            )
            tab_info.update_usage(task_id)
            
            async with self._lock:
                self._tabs[tab_id] = tab_info
                self._domain_tabs[domain].add(tab_id)
                self._busy_tabs.add(tab_id)
                self._stats['created_tabs'] += 1
            
            logger.info(f"创建新标签页 {tab_id} for {domain}")
            return page, tab_id
            
        except Exception as e:
            self._tab_semaphore.release()
            logger.error(f"创建标签页失败: {e}")
            raise
    
    async def release_tab(self, tab_id: str, keep_alive: bool = True) -> None:
        """
        释放标签页
        
        Args:
            tab_id: 标签页ID
            keep_alive: 是否保持标签页活跃以供复用
        """
        async with self._lock:
            if tab_id not in self._tabs:
                logger.warning(f"尝试释放不存在的标签页: {tab_id}")
                return
            
            tab_info = self._tabs[tab_id]
            
            if keep_alive and tab_info.state != TabState.ERROR:
                # 标记为空闲，保留以供复用
                tab_info.mark_idle()
                self._busy_tabs.discard(tab_id)
                logger.debug(f"释放标签页到池中: {tab_id}")
            else:
                # 关闭标签页
                await self._close_tab(tab_id)
                logger.debug(f"关闭标签页: {tab_id}")
    
    async def close_tab(self, tab_id: str) -> None:
        """
        强制关闭标签页
        
        Args:
            tab_id: 标签页ID
        """
        async with self._lock:
            await self._close_tab(tab_id)
    
    async def close_domain_tabs(self, domain: str) -> int:
        """
        关闭指定域名的所有标签页
        
        Args:
            domain: 域名
            
        Returns:
            关闭的标签页数量
        """
        async with self._lock:
            tab_ids = list(self._domain_tabs.get(domain, set()))
            
            for tab_id in tab_ids:
                await self._close_tab(tab_id)
            
            return len(tab_ids)
    
    async def close_all_tabs(self) -> int:
        """
        关闭所有标签页
        
        Returns:
            关闭的标签页数量
        """
        async with self._lock:
            tab_ids = list(self._tabs.keys())
            
            for tab_id in tab_ids:
                await self._close_tab(tab_id)
            
            return len(tab_ids)
    
    async def get_tab_info(self, tab_id: str) -> Optional[TabInfo]:
        """
        获取标签页信息
        
        Args:
            tab_id: 标签页ID
            
        Returns:
            标签页信息或None
        """
        async with self._lock:
            return self._tabs.get(tab_id)
    
    async def list_tabs(self, domain: Optional[str] = None, state: Optional[TabState] = None) -> List[TabInfo]:
        """
        列出标签页
        
        Args:
            domain: 过滤域名
            state: 过滤状态
            
        Returns:
            标签页信息列表
        """
        async with self._lock:
            tabs = list(self._tabs.values())
            
            if domain:
                tabs = [tab for tab in tabs if tab.domain == domain]
            
            if state:
                tabs = [tab for tab in tabs if tab.state == state]
            
            return tabs
    
    def _extract_domain(self, url: str) -> str:
        """提取URL的域名"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return "unknown"
    
    def _generate_tab_id(self, url: str, task_id: Optional[str] = None) -> str:
        """生成标签页ID"""
        timestamp = str(time.time())
        content = f"{url}_{task_id or ''}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def _configure_page(self, page: Any) -> None:
        """配置页面设置"""
        try:
            # 设置视口大小
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # 设置用户代理
            await page.set_extra_http_headers({
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            })
            
            # 禁用图片加载以提高性能（可选）
            # await page.route("**/*.{png,jpg,jpeg,gif,svg,webp}", lambda route: route.abort())
            
        except Exception as e:
            logger.warning(f"配置页面设置失败: {e}")
    
    async def _find_reusable_tab(self, domain: str) -> Optional[TabInfo]:
        """查找可复用的标签页"""
        domain_tab_ids = self._domain_tabs.get(domain, set())
        
        if not domain_tab_ids:
            return None
        
        # 查找空闲的标签页
        idle_tabs = []
        for tab_id in domain_tab_ids:
            if tab_id in self._tabs:
                tab_info = self._tabs[tab_id]
                if tab_info.is_reusable(domain, self.max_idle_time):
                    idle_tabs.append(tab_info)
        
        if not idle_tabs:
            return None
        
        # 选择最近使用的标签页
        idle_tabs.sort(key=lambda x: x.last_used_at, reverse=True)
        return idle_tabs[0]
    
    async def _close_tab(self, tab_id: str) -> None:
        """关闭单个标签页"""
        if tab_id not in self._tabs:
            return
        
        tab_info = self._tabs[tab_id]
        
        try:
            # 关闭页面
            if tab_info.page and not tab_info.page.is_closed():
                await tab_info.page.close()
        except Exception as e:
            logger.warning(f"关闭页面失败 {tab_id}: {e}")
        
        # 更新状态
        tab_info.state = TabState.CLOSED
        
        # 从管理结构中移除
        domain = tab_info.domain
        self._domain_tabs[domain].discard(tab_id)
        if not self._domain_tabs[domain]:
            del self._domain_tabs[domain]
        
        self._busy_tabs.discard(tab_id)
        del self._tabs[tab_id]
        
        # 释放信号量
        self._tab_semaphore.release()
        
        self._stats['closed_tabs'] += 1
        logger.debug(f"已关闭标签页: {tab_id}")
    
    async def _cleanup_excess_tabs(self) -> None:
        """清理多余的标签页"""
        if len(self._tabs) <= self.max_total_tabs:
            return
        
        # 获取空闲标签页，按最后使用时间排序
        idle_tabs = []
        for tab_info in self._tabs.values():
            if tab_info.state == TabState.IDLE:
                idle_tabs.append(tab_info)
        
        idle_tabs.sort(key=lambda x: x.last_used_at)
        
        # 关闭最旧的空闲标签页
        excess_count = len(self._tabs) - self.max_total_tabs + 1
        for i in range(min(excess_count, len(idle_tabs))):
            await self._close_tab(idle_tabs[i].tab_id)
    
    async def _cleanup_domain_tabs(self, domain: str) -> None:
        """清理指定域名的多余标签页"""
        domain_tab_ids = self._domain_tabs.get(domain, set())
        
        if len(domain_tab_ids) <= self.max_tabs_per_domain:
            return
        
        # 获取该域名的空闲标签页
        idle_tabs = []
        for tab_id in domain_tab_ids:
            if tab_id in self._tabs:
                tab_info = self._tabs[tab_id]
                if tab_info.state == TabState.IDLE:
                    idle_tabs.append(tab_info)
        
        idle_tabs.sort(key=lambda x: x.last_used_at)
        
        # 关闭最旧的空闲标签页
        excess_count = len(domain_tab_ids) - self.max_tabs_per_domain + 1
        for i in range(min(excess_count, len(idle_tabs))):
            await self._close_tab(idle_tabs[i].tab_id)
    
    async def _cleanup_loop(self) -> None:
        """清理循环任务"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._periodic_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理循环出错: {e}")
    
    async def _periodic_cleanup(self) -> None:
        """定期清理任务"""
        async with self._lock:
            current_time = time.time()
            tabs_to_close = []
            
            for tab_info in self._tabs.values():
                should_close = False
                
                # 检查年龄
                if tab_info.get_age() > self.max_tab_age:
                    should_close = True
                    logger.debug(f"标签页 {tab_info.tab_id} 超过最大年龄")
                
                # 检查空闲时间
                elif tab_info.state == TabState.IDLE and tab_info.get_idle_time() > self.max_idle_time:
                    should_close = True
                    logger.debug(f"标签页 {tab_info.tab_id} 空闲时间过长")
                
                # 检查页面状态
                elif tab_info.page and tab_info.page.is_closed():
                    should_close = True
                    logger.debug(f"标签页 {tab_info.tab_id} 页面已关闭")
                
                if should_close:
                    tabs_to_close.append(tab_info.tab_id)
            
            # 关闭需要清理的标签页
            for tab_id in tabs_to_close:
                await self._close_tab(tab_id)
            
            if tabs_to_close:
                logger.info(f"定期清理关闭了 {len(tabs_to_close)} 个标签页")
            
            self._stats['cleanup_runs'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        total_tabs = len(self._tabs)
        idle_tabs = len([t for t in self._tabs.values() if t.state == TabState.IDLE])
        busy_tabs = len(self._busy_tabs)
        
        domain_stats = {}
        for domain, tab_ids in self._domain_tabs.items():
            domain_stats[domain] = len(tab_ids)
        
        return {
            'total_tabs': total_tabs,
            'idle_tabs': idle_tabs,
            'busy_tabs': busy_tabs,
            'domains': len(self._domain_tabs),
            'domain_distribution': domain_stats,
            'max_tabs_per_domain': self.max_tabs_per_domain,
            'max_total_tabs': self.max_total_tabs,
            'created_tabs': self._stats['created_tabs'],
            'reused_tabs': self._stats['reused_tabs'],
            'closed_tabs': self._stats['closed_tabs'],
            'cleanup_runs': self._stats['cleanup_runs'],
            'reuse_rate': f"{self._stats['reused_tabs'] / max(self._stats['created_tabs'] + self._stats['reused_tabs'], 1) * 100:.1f}%"
        }
    
    async def close(self) -> None:
        """关闭标签页池管理器"""
        # 取消清理任务
        self._cleanup_task.cancel()
        
        # 关闭所有标签页
        await self.close_all_tabs()
        
        logger.info("标签页池管理器已关闭")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class OptimizedBrowserService:
    """
    优化的浏览器服务
    
    集成标签页池管理器，提供高效的浏览器操作接口
    """
    
    def __init__(self, tab_pool_manager: TabPoolManager):
        """
        初始化优化的浏览器服务
        
        Args:
            tab_pool_manager: 标签页池管理器
        """
        self.tab_pool = tab_pool_manager
        self._browser_context = None
    
    async def set_browser_context(self, context: Any) -> None:
        """
        设置浏览器上下文
        
        Args:
            context: 浏览器上下文
        """
        self._browser_context = context
    
    async def navigate_to_url(self, url: str, task_id: Optional[str] = None) -> Tuple[Any, str]:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            task_id: 任务ID
            
        Returns:
            (page对象, tab_id)元组
        """
        if not self._browser_context:
            raise ValueError("浏览器上下文未设置")
        
        page, tab_id = await self.tab_pool.get_tab(url, self._browser_context, task_id)
        
        try:
            # 导航到URL
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            logger.info(f"成功导航到 {url} (标签页: {tab_id})")
            return page, tab_id
        except Exception as e:
            # 导航失败，释放标签页
            await self.tab_pool.release_tab(tab_id, keep_alive=False)
            logger.error(f"导航到 {url} 失败: {e}")
            raise
    
    async def execute_with_tab(self, url: str, task_func: Callable, task_id: Optional[str] = None, **kwargs) -> Any:
        """
        使用标签页执行任务
        
        Args:
            url: 目标URL
            task_func: 任务函数，接收page作为第一个参数
            task_id: 任务ID
            **kwargs: 传递给任务函数的额外参数
            
        Returns:
            任务函数的返回值
        """
        page, tab_id = await self.navigate_to_url(url, task_id)
        
        try:
            # 执行任务
            result = await task_func(page, **kwargs)
            
            # 成功完成，释放标签页但保持活跃
            await self.tab_pool.release_tab(tab_id, keep_alive=True)
            return result
            
        except Exception as e:
            # 任务失败，关闭标签页
            await self.tab_pool.release_tab(tab_id, keep_alive=False)
            raise
    
    async def batch_execute(self, tasks: List[Tuple[str, Callable, Optional[str]]], max_concurrent: int = 5) -> List[Any]:
        """
        批量执行任务
        
        Args:
            tasks: 任务列表，每个元素为(url, task_func, task_id)
            max_concurrent: 最大并发数
            
        Returns:
            结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single_task(url: str, task_func: Callable, task_id: Optional[str]) -> Any:
            async with semaphore:
                return await self.execute_with_tab(url, task_func, task_id)
        
        # 创建并发任务
        coroutines = [
            execute_single_task(url, task_func, task_id)
            for url, task_func, task_id in tasks
        ]
        
        # 执行所有任务
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'browser_service': {
                'has_context': self._browser_context is not None
            },
            'tab_pool': self.tab_pool.get_statistics()
        }