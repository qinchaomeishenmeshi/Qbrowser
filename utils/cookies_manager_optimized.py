import asyncio
import json
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple
from functools import lru_cache

from utils.common_logger import get_logger
from utils.async_file_manager import AsyncFileManager

logger = get_logger(__name__)


class LRUCache:
    """LRU缓存实现，用于优化内存使用"""
    
    def __init__(self, max_size: int = 1000):
        """初始化LRU缓存
        
        Args:
            max_size: 缓存最大容量
        """
        self.max_size = max_size
        self.cache = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项，并将其移到最近使用位置"""
        if key in self.cache:
            # 移动到末尾（最近使用）
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any) -> None:
        """添加或更新缓存项"""
        if key in self.cache:
            # 更新现有项
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.max_size:
            # 删除最久未使用的项
            self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def remove(self, key: str) -> bool:
        """删除缓存项"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def size(self) -> int:
        """获取当前缓存大小"""
        return len(self.cache)


class OptimizedCookiesManager:
    """
    优化版Cookies管理器，提供高性能的cookies和headers存储、检索功能。
    
    性能优化特性：
    - LRU内存缓存机制，减少磁盘I/O
    - 批量操作支持，提高并发处理效率
    - 智能过期检查，避免不必要的文件读取
    - 异步锁优化，减少锁竞争
    - 内存使用监控和自动清理
    """
    
    def __init__(self, storage_dir: Path, cache_size: int = 1000, 
                 auto_cleanup_interval: int = 3600) -> None:
        """
        初始化优化版Cookies管理器。
        
        Args:
            storage_dir: cookies存储目录路径
            cache_size: LRU缓存大小，默认1000
            auto_cleanup_interval: 自动清理间隔（秒），默认1小时
        """
        self.storage_dir = storage_dir
        
        # 初始化异步文件管理器
        self.file_manager = AsyncFileManager(self.storage_dir)
        
        # 使用读写锁优化并发性能
        self._write_lock = asyncio.Lock()
        self._read_locks: Dict[str, asyncio.Lock] = {}
        
        # LRU缓存
        self._cache = LRUCache(cache_size)
        
        # 批量操作队列
        self._batch_queue: List[Tuple[str, str, Dict]] = []
        self._batch_lock = asyncio.Lock()
        
        # 性能统计
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'disk_reads': 0,
            'disk_writes': 0,
            'batch_operations': 0
        }
        
        # 启动自动清理任务
        self._cleanup_task = None
        if auto_cleanup_interval > 0:
            self._start_auto_cleanup(auto_cleanup_interval)
    
    def _start_auto_cleanup(self, interval: int) -> None:
        """启动自动清理任务"""
        async def cleanup_task():
            while True:
                try:
                    await asyncio.sleep(interval)
                    await self._cleanup_expired_cache()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"自动清理任务出错: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_task())
    
    async def _cleanup_expired_cache(self) -> None:
        """清理过期的缓存项"""
        expired_keys = []
        
        for key, data in self._cache.cache.items():
            if self._is_expired(data):
                expired_keys.append(key)
        
        for key in expired_keys:
            self._cache.remove(key)
        
        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    def _get_read_lock(self, key: str) -> asyncio.Lock:
        """获取读锁（按键分离锁）"""
        if key not in self._read_locks:
            self._read_locks[key] = asyncio.Lock()
        return self._read_locks[key]
    
    def _get_cookie_file(self, user_id: str, site_key: str = None) -> Path:
        """获取用户cookie文件路径"""
        if site_key:
            return self.storage_dir / f"{user_id}_{site_key}_cookies.json"
        return self.storage_dir / f"{user_id}_cookies.json"
    
    def _get_cache_key(self, user_id: str, site_key: str = None) -> str:
        """获取缓存键"""
        if site_key:
            return f"{user_id}_{site_key}"
        return user_id
    
    async def save_cookies_batch(self, 
                                batch_data: List[Tuple[str, dict, Optional[dict], int, str]]) -> List[bool]:
        """
        批量保存cookies，提高并发处理性能
        
        Args:
            batch_data: 批量数据列表，每项包含(user_id, cookies, headers, expires_in_days, site_key)
        
        Returns:
            操作结果列表，True表示成功，False表示失败
        """
        async with self._batch_lock:
            results = []
            now = datetime.now()
            
            # 准备批量数据
            batch_cache_updates = {}
            batch_file_operations = []
            
            for user_id, cookies, headers, expires_in_days, site_key in batch_data:
                try:
                    data = {
                        'cookies': cookies,
                        'headers': headers or {},
                        'updated_at': now.isoformat(),
                        'expires_at': (now + timedelta(days=expires_in_days)).isoformat(),
                        'site_key': site_key
                    }
                    
                    cache_key = self._get_cache_key(user_id, site_key)
                    cookie_file = self._get_cookie_file(user_id, site_key)
                    
                    batch_cache_updates[cache_key] = data
                    batch_file_operations.append((cookie_file, data))
                    results.append(True)
                    
                except Exception as e:
                    logger.error(f"准备批量数据失败 - 用户 {user_id}: {e}")
                    results.append(False)
            
            # 批量更新缓存
            for cache_key, data in batch_cache_updates.items():
                self._cache.put(cache_key, data)
            
            # 批量写入文件
            async with self._write_lock:
                for cookie_file, data in batch_file_operations:
                    try:
                        success = await self.file_manager.write_json_file(cookie_file, data, create_dirs=True)
                        if success:
                            self._stats['disk_writes'] += 1
                        else:
                            logger.error(f"批量写入文件失败 {cookie_file}: 文件写入失败")
                    except Exception as e:
                        logger.error(f"批量写入文件失败 {cookie_file}: {e}")
            
            self._stats['batch_operations'] += 1
            logger.info(f"批量保存完成，处理 {len(batch_data)} 个用户的cookies")
            
            return results
    
    async def save_cookies(self, 
                          user_id: str, 
                          cookies: dict, 
                          headers: Optional[dict] = None,
                          expires_in_days: int = 7,
                          site_key: str = None) -> None:
        """
        保存用户的cookies和headers信息（单个操作）
        """
        results = await self.save_cookies_batch([
            (user_id, cookies, headers, expires_in_days, site_key)
        ])
        
        if not results[0]:
            raise Exception(f"保存用户 {user_id} 的cookies失败")
    
    async def get_cookies(self, user_id: str, site_key: str = None) -> Optional[Dict]:
        """
        获取用户的cookies信息（优化版）
        """
        cache_key = self._get_cache_key(user_id, site_key)
        
        # 尝试从缓存获取
        data = self._cache.get(cache_key)
        if data:
            self._stats['cache_hits'] += 1
            if not self._is_expired(data):
                return data.get('cookies')
            else:
                # 缓存过期，移除
                self._cache.remove(cache_key)
        
        # 缓存未命中，从文件加载
        self._stats['cache_misses'] += 1
        read_lock = self._get_read_lock(cache_key)
        
        async with read_lock:
            # 双重检查，避免重复加载
            data = self._cache.get(cache_key)
            if data and not self._is_expired(data):
                return data.get('cookies')
            
            await self._load_cookies(user_id, site_key)
            data = self._cache.get(cache_key)
            
            if data and not self._is_expired(data):
                return data.get('cookies')
        
        return None
    
    async def get_headers(self, user_id: str, site_key: str = None) -> Optional[Dict]:
        """
        获取用户的headers信息（优化版）
        """
        cache_key = self._get_cache_key(user_id, site_key)
        
        # 尝试从缓存获取
        data = self._cache.get(cache_key)
        if data:
            self._stats['cache_hits'] += 1
            if not self._is_expired(data):
                return data.get('headers')
            else:
                self._cache.remove(cache_key)
        
        # 缓存未命中，从文件加载
        self._stats['cache_misses'] += 1
        read_lock = self._get_read_lock(cache_key)
        
        async with read_lock:
            data = self._cache.get(cache_key)
            if data and not self._is_expired(data):
                return data.get('headers')
            
            await self._load_cookies(user_id, site_key)
            data = self._cache.get(cache_key)
            
            if data and not self._is_expired(data):
                return data.get('headers')
        
        return None
    
    async def _load_cookies(self, user_id: str, site_key: str = None) -> None:
        """
        从文件加载用户的cookies信息（优化版）
        """
        cookie_file = self._get_cookie_file(user_id, site_key)
        if not cookie_file.exists():
            return
        
        try:
            # 使用异步文件管理器读取
            data = await self.file_manager.read_json_file(cookie_file)
            if data is not None:
                cache_key = self._get_cache_key(user_id, site_key)
                self._cache.put(cache_key, data)
                self._stats['disk_reads'] += 1
            
        except Exception as e:
            logger.error(f"加载用户 {user_id} 的cookies失败: {e}")
    
    def _is_expired(self, data: Dict) -> bool:
        """
        检查cookies是否过期（优化版）
        """
        try:
            expires_at = datetime.fromisoformat(data['expires_at'])
            return datetime.now() > expires_at
        except (KeyError, ValueError, TypeError):
            return True
    
    async def get_cookies_batch(self, user_ids: List[str], site_key: str = None) -> Dict[str, Optional[Dict]]:
        """
        批量获取多个用户的cookies
        
        Args:
            user_ids: 用户ID列表
            site_key: 站点标识
        
        Returns:
            用户ID到cookies的映射字典
        """
        results = {}
        
        # 并发获取
        async def get_user_cookies(user_id: str):
            cookies = await self.get_cookies(user_id, site_key)
            return user_id, cookies
        
        tasks = [get_user_cookies(user_id) for user_id in user_ids]
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_tasks:
            if isinstance(result, Exception):
                logger.error(f"批量获取cookies时出错: {result}")
            else:
                user_id, cookies = result
                results[user_id] = cookies
        
        return results
    
    async def remove_cookies(self, user_id: str, site_key: str = None) -> None:
        """
        删除用户的cookies信息（优化版）
        """
        async with self._write_lock:
            if site_key is None:
                # 删除所有站点的cookies
                for file in self.storage_dir.glob(f"{user_id}_*_cookies.json"):
                    try:
                        await self.file_manager.delete_file(file)
                    except Exception as e:
                        logger.error(f"删除cookies文件失败 {file}: {e}")
                
                # 删除默认cookies
                default_file = self._get_cookie_file(user_id)
                try:
                    await self.file_manager.delete_file(default_file)
                except Exception as e:
                    logger.error(f"删除默认cookies文件失败: {e}")
                
                # 清除相关缓存
                keys_to_remove = []
                for key in self._cache.cache.keys():
                    if key.startswith(f"{user_id}_") or key == user_id:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    self._cache.remove(key)
            else:
                # 删除特定站点的cookies
                cookie_file = self._get_cookie_file(user_id, site_key)
                try:
                    await self.file_manager.delete_file(cookie_file)
                except Exception as e:
                    logger.error(f"删除cookies文件失败: {e}")
                
                # 清除缓存
                cache_key = self._get_cache_key(user_id, site_key)
                self._cache.remove(cache_key)
    
    async def clear_all(self) -> None:
        """
        清除所有用户的cookies信息（优化版）
        """
        async with self._write_lock:
            try:
                for file in self.storage_dir.glob("*_cookies.json"):
                    await self.file_manager.delete_file(file)
                self._cache.clear()
                logger.info("已清除所有用户的cookies信息")
            except Exception as e:
                logger.error(f"清除所有cookies失败: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            包含缓存命中率、磁盘操作次数等统计信息的字典
        """
        total_requests = self._stats['cache_hits'] + self._stats['cache_misses']
        cache_hit_rate = (self._stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': self._cache.size(),
            'cache_hit_rate': f"{cache_hit_rate:.2f}%",
            'cache_hits': self._stats['cache_hits'],
            'cache_misses': self._stats['cache_misses'],
            'disk_reads': self._stats['disk_reads'],
            'disk_writes': self._stats['disk_writes'],
            'batch_operations': self._stats['batch_operations']
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass