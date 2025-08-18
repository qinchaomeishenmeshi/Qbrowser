import asyncio
import time
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """缓存策略枚举"""
    PASSIVE = "passive"  # 被动刷新（仅在过期时刷新）
    PROACTIVE = "proactive"  # 主动刷新（预测性刷新）
    ADAPTIVE = "adaptive"  # 自适应刷新（基于使用模式）


@dataclass
class CacheMetrics:
    """缓存指标数据类"""
    key: str
    access_count: int = 0
    last_access_time: float = field(default_factory=time.time)
    creation_time: float = field(default_factory=time.time)
    refresh_count: int = 0
    last_refresh_time: float = field(default_factory=time.time)
    access_intervals: deque = field(default_factory=lambda: deque(maxlen=10))
    refresh_durations: deque = field(default_factory=lambda: deque(maxlen=5))
    failure_count: int = 0
    success_rate: float = 1.0
    
    def record_access(self):
        """记录访问"""
        current_time = time.time()
        if self.access_count > 0:
            interval = current_time - self.last_access_time
            self.access_intervals.append(interval)
        
        self.access_count += 1
        self.last_access_time = current_time
    
    def record_refresh(self, duration: float, success: bool = True):
        """记录刷新"""
        current_time = time.time()
        self.refresh_count += 1
        self.last_refresh_time = current_time
        self.refresh_durations.append(duration)
        
        if not success:
            self.failure_count += 1
        
        # 更新成功率
        self.success_rate = (self.refresh_count - self.failure_count) / self.refresh_count
    
    def get_average_access_interval(self) -> float:
        """获取平均访问间隔"""
        if not self.access_intervals:
            return 3600.0  # 默认1小时
        return statistics.mean(self.access_intervals)
    
    def get_average_refresh_duration(self) -> float:
        """获取平均刷新时长"""
        if not self.refresh_durations:
            return 5.0  # 默认5秒
        return statistics.mean(self.refresh_durations)
    
    def predict_next_access(self) -> float:
        """预测下次访问时间"""
        avg_interval = self.get_average_access_interval()
        # 基于历史模式预测，考虑访问频率的变化趋势
        if len(self.access_intervals) >= 3:
            recent_intervals = list(self.access_intervals)[-3:]
            trend = statistics.mean(recent_intervals)
            # 加权平均：70%历史平均 + 30%近期趋势
            predicted_interval = 0.7 * avg_interval + 0.3 * trend
        else:
            predicted_interval = avg_interval
        
        return self.last_access_time + predicted_interval


class SmartCachePredictor:
    """
    智能缓存预测器
    
    功能：
    - 基于历史访问模式预测缓存过期时间
    - 智能调整刷新策略
    - 优化缓存命中率
    """
    
    def __init__(self, default_ttl: int = 3600, prediction_window: int = 86400):
        """
        初始化智能缓存预测器
        
        Args:
            default_ttl: 默认缓存生存时间（秒）
            prediction_window: 预测时间窗口（秒）
        """
        self.default_ttl = default_ttl
        self.prediction_window = prediction_window
        self.metrics: Dict[str, CacheMetrics] = {}
        self._lock = asyncio.Lock()
    
    async def record_access(self, key: str) -> None:
        """
        记录缓存访问
        
        Args:
            key: 缓存键
        """
        async with self._lock:
            if key not in self.metrics:
                self.metrics[key] = CacheMetrics(key=key)
            
            self.metrics[key].record_access()
            logger.debug(f"记录缓存访问: {key}")
    
    async def record_refresh(self, key: str, duration: float, success: bool = True) -> None:
        """
        记录缓存刷新
        
        Args:
            key: 缓存键
            duration: 刷新耗时
            success: 是否成功
        """
        async with self._lock:
            if key not in self.metrics:
                self.metrics[key] = CacheMetrics(key=key)
            
            self.metrics[key].record_refresh(duration, success)
            logger.debug(f"记录缓存刷新: {key}, 耗时: {duration:.2f}s, 成功: {success}")
    
    async def predict_optimal_ttl(self, key: str) -> int:
        """
        预测最优缓存生存时间
        
        Args:
            key: 缓存键
            
        Returns:
            预测的最优TTL（秒）
        """
        async with self._lock:
            if key not in self.metrics:
                return self.default_ttl
            
            metrics = self.metrics[key]
            
            # 基于访问频率调整TTL
            avg_interval = metrics.get_average_access_interval()
            
            # 如果访问频率很高，适当延长TTL
            if avg_interval < 300:  # 5分钟内频繁访问
                optimal_ttl = min(self.default_ttl * 2, 7200)  # 最多2小时
            elif avg_interval < 1800:  # 30分钟内访问
                optimal_ttl = self.default_ttl
            else:  # 访问频率较低
                optimal_ttl = max(self.default_ttl // 2, 600)  # 最少10分钟
            
            # 考虑成功率调整
            if metrics.success_rate < 0.8:
                optimal_ttl = max(optimal_ttl // 2, 300)  # 降低TTL，增加刷新频率
            
            logger.debug(f"预测最优TTL {key}: {optimal_ttl}s (访问间隔: {avg_interval:.1f}s, 成功率: {metrics.success_rate:.2f})")
            return optimal_ttl
    
    async def should_proactive_refresh(self, key: str, current_ttl_remaining: int) -> bool:
        """
        判断是否应该主动刷新
        
        Args:
            key: 缓存键
            current_ttl_remaining: 当前TTL剩余时间（秒）
            
        Returns:
            是否应该主动刷新
        """
        async with self._lock:
            if key not in self.metrics:
                return False
            
            metrics = self.metrics[key]
            
            # 预测下次访问时间
            predicted_next_access = metrics.predict_next_access()
            current_time = time.time()
            time_to_next_access = predicted_next_access - current_time
            
            # 如果预测在缓存过期前会被访问，且剩余时间不足，则主动刷新
            refresh_threshold = min(current_ttl_remaining * 0.2, 300)  # 20%剩余时间或5分钟
            
            should_refresh = (
                time_to_next_access > 0 and  # 预测会有下次访问
                time_to_next_access < current_ttl_remaining and  # 下次访问在过期前
                current_ttl_remaining <= refresh_threshold  # 剩余时间不足
            )
            
            if should_refresh:
                logger.info(f"建议主动刷新 {key}: 剩余TTL={current_ttl_remaining}s, 预测下次访问={time_to_next_access:.1f}s后")
            
            return should_refresh
    
    async def get_refresh_priority(self, keys: List[str]) -> List[Tuple[str, float]]:
        """
        获取缓存刷新优先级排序
        
        Args:
            keys: 缓存键列表
            
        Returns:
            按优先级排序的(key, priority_score)列表
        """
        priorities = []
        
        async with self._lock:
            for key in keys:
                if key not in self.metrics:
                    priorities.append((key, 0.0))
                    continue
                
                metrics = self.metrics[key]
                
                # 计算优先级分数（0-1之间）
                # 因素：访问频率、成功率、上次刷新时间
                access_frequency = 1.0 / max(metrics.get_average_access_interval(), 1.0)
                success_factor = metrics.success_rate
                time_since_refresh = time.time() - metrics.last_refresh_time
                freshness_factor = min(time_since_refresh / 3600, 1.0)  # 1小时内为新鲜
                
                priority_score = (
                    0.4 * access_frequency +
                    0.3 * success_factor +
                    0.3 * freshness_factor
                )
                
                priorities.append((key, priority_score))
        
        # 按优先级降序排序
        priorities.sort(key=lambda x: x[1], reverse=True)
        return priorities
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取预测器统计信息
        
        Returns:
            统计信息字典
        """
        total_keys = len(self.metrics)
        if total_keys == 0:
            return {'total_keys': 0}
        
        total_accesses = sum(m.access_count for m in self.metrics.values())
        total_refreshes = sum(m.refresh_count for m in self.metrics.values())
        avg_success_rate = statistics.mean(m.success_rate for m in self.metrics.values())
        
        return {
            'total_keys': total_keys,
            'total_accesses': total_accesses,
            'total_refreshes': total_refreshes,
            'average_success_rate': f"{avg_success_rate:.2%}",
            'prediction_window': self.prediction_window,
            'default_ttl': self.default_ttl
        }


class SmartCacheManager:
    """
    智能缓存管理器
    
    集成预测器和自动刷新机制，提供完整的智能缓存解决方案
    """
    
    def __init__(
        self,
        predictor: SmartCachePredictor,
        refresh_callback: Callable[[str], Any],
        strategy: CacheStrategy = CacheStrategy.ADAPTIVE,
        max_concurrent_refreshes: int = 5
    ):
        """
        初始化智能缓存管理器
        
        Args:
            predictor: 缓存预测器
            refresh_callback: 缓存刷新回调函数
            strategy: 缓存策略
            max_concurrent_refreshes: 最大并发刷新数
        """
        self.predictor = predictor
        self.refresh_callback = refresh_callback
        self.strategy = strategy
        self.max_concurrent_refreshes = max_concurrent_refreshes
        
        # 缓存数据和元数据
        self._cache: Dict[str, Any] = {}
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}
        self._refresh_semaphore = asyncio.Semaphore(max_concurrent_refreshes)
        self._refresh_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        
        # 启动后台任务
        self._background_task = asyncio.create_task(self._background_refresh_loop())
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值
        """
        await self.predictor.record_access(key)
        
        async with self._lock:
            if key in self._cache:
                metadata = self._cache_metadata.get(key, {})
                
                # 检查是否过期
                if self._is_expired(metadata):
                    logger.debug(f"缓存已过期: {key}")
                    del self._cache[key]
                    del self._cache_metadata[key]
                    return default
                
                # 检查是否需要主动刷新
                if self.strategy in [CacheStrategy.PROACTIVE, CacheStrategy.ADAPTIVE]:
                    ttl_remaining = self._get_ttl_remaining(metadata)
                    if await self.predictor.should_proactive_refresh(key, ttl_remaining):
                        # 异步启动刷新任务
                        asyncio.create_task(self._refresh_cache_item(key))
                
                return self._cache[key]
            
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用预测的最优TTL
        """
        if ttl is None:
            ttl = await self.predictor.predict_optimal_ttl(key)
        
        async with self._lock:
            self._cache[key] = value
            self._cache_metadata[key] = {
                'created_at': time.time(),
                'ttl': ttl,
                'expires_at': time.time() + ttl
            }
            
        logger.debug(f"设置缓存: {key}, TTL: {ttl}s")
    
    async def delete(self, key: str) -> bool:
        """
        删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        async with self._lock:
            deleted = False
            if key in self._cache:
                del self._cache[key]
                deleted = True
            if key in self._cache_metadata:
                del self._cache_metadata[key]
            
            # 取消相关的刷新任务
            if key in self._refresh_tasks:
                self._refresh_tasks[key].cancel()
                del self._refresh_tasks[key]
            
            return deleted
    
    async def clear(self) -> None:
        """清空所有缓存"""
        async with self._lock:
            self._cache.clear()
            self._cache_metadata.clear()
            
            # 取消所有刷新任务
            for task in self._refresh_tasks.values():
                task.cancel()
            self._refresh_tasks.clear()
    
    def _is_expired(self, metadata: Dict[str, Any]) -> bool:
        """检查缓存是否过期"""
        expires_at = metadata.get('expires_at', 0)
        return time.time() > expires_at
    
    def _get_ttl_remaining(self, metadata: Dict[str, Any]) -> int:
        """获取TTL剩余时间"""
        expires_at = metadata.get('expires_at', 0)
        remaining = int(expires_at - time.time())
        return max(remaining, 0)
    
    async def _refresh_cache_item(self, key: str) -> None:
        """
        刷新单个缓存项
        
        Args:
            key: 缓存键
        """
        # 避免重复刷新
        if key in self._refresh_tasks and not self._refresh_tasks[key].done():
            return
        
        async with self._refresh_semaphore:
            start_time = time.time()
            success = False
            
            try:
                logger.debug(f"开始刷新缓存: {key}")
                
                # 调用刷新回调
                new_value = await self.refresh_callback(key)
                
                if new_value is not None:
                    await self.set(key, new_value)
                    success = True
                    logger.info(f"成功刷新缓存: {key}")
                else:
                    logger.warning(f"刷新缓存返回空值: {key}")
                
            except Exception as e:
                logger.error(f"刷新缓存失败 {key}: {e}")
            finally:
                duration = time.time() - start_time
                await self.predictor.record_refresh(key, duration, success)
                
                # 清理任务记录
                if key in self._refresh_tasks:
                    del self._refresh_tasks[key]
    
    async def _background_refresh_loop(self) -> None:
        """
        后台刷新循环
        """
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                if self.strategy == CacheStrategy.PASSIVE:
                    continue
                
                # 获取需要刷新的缓存项
                async with self._lock:
                    keys_to_check = list(self._cache.keys())
                
                if not keys_to_check:
                    continue
                
                # 获取刷新优先级
                priorities = await self.predictor.get_refresh_priority(keys_to_check)
                
                # 处理高优先级的缓存项
                refresh_count = 0
                for key, priority in priorities:
                    if refresh_count >= self.max_concurrent_refreshes:
                        break
                    
                    async with self._lock:
                        if key not in self._cache_metadata:
                            continue
                        
                        metadata = self._cache_metadata[key]
                        ttl_remaining = self._get_ttl_remaining(metadata)
                    
                    # 根据策略决定是否刷新
                    should_refresh = False
                    
                    if self.strategy == CacheStrategy.PROACTIVE:
                        should_refresh = await self.predictor.should_proactive_refresh(key, ttl_remaining)
                    elif self.strategy == CacheStrategy.ADAPTIVE:
                        # 自适应策略：结合优先级和预测
                        should_refresh = (
                            priority > 0.5 and
                            await self.predictor.should_proactive_refresh(key, ttl_remaining)
                        )
                    
                    if should_refresh:
                        task = asyncio.create_task(self._refresh_cache_item(key))
                        self._refresh_tasks[key] = task
                        refresh_count += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"后台刷新循环出错: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取缓存管理器统计信息
        
        Returns:
            统计信息字典
        """
        cache_stats = {
            'total_items': len(self._cache),
            'active_refresh_tasks': len([t for t in self._refresh_tasks.values() if not t.done()]),
            'strategy': self.strategy.value,
            'max_concurrent_refreshes': self.max_concurrent_refreshes
        }
        
        predictor_stats = self.predictor.get_statistics()
        
        return {
            'cache_manager': cache_stats,
            'predictor': predictor_stats
        }
    
    async def close(self) -> None:
        """关闭缓存管理器"""
        self._background_task.cancel()
        
        # 取消所有刷新任务
        for task in self._refresh_tasks.values():
            task.cancel()
        
        # 等待任务完成
        if self._refresh_tasks:
            await asyncio.gather(*self._refresh_tasks.values(), return_exceptions=True)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()