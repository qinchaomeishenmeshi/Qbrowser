#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化示例

本示例展示如何使用所有优化组件来提升浏览器操作性能：
1. 优化的CookiesManager（LRU缓存 + 批量操作）
2. 优化的BrowserOperator（连接池 + 请求去重）
3. 异步文件管理器（aiofiles）
4. 智能缓存策略（预测性刷新）
5. 标签页池管理器（标签页复用）
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

# 导入优化组件
from utils.cookies_manager_optimized import OptimizedCookiesManager
from utils.browser_operator_optimized import OptimizedBrowserOperator
from utils.async_file_manager import AsyncFileManager
from utils.smart_cache_strategy import SmartCachePredictor, SmartCacheManager, CacheStrategy
from utils.tab_pool_manager import TabPoolManager, OptimizedBrowserService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceOptimizedBrowserSystem:
    """
    性能优化的浏览器系统
    
    集成所有优化组件，提供高性能的浏览器自动化解决方案
    """
    
    def __init__(self, cookies_dir: str = "cookies_optimized"):
        """
        初始化性能优化的浏览器系统
        
        Args:
            cookies_dir: cookies存储目录
        """
        self.cookies_dir = Path(cookies_dir)
        self.cookies_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        self.file_manager = None
        self.cookies_manager = None
        self.cache_predictor = None
        self.cache_manager = None
        self.tab_pool = None
        self.browser_service = None
        self.browser_operator = None
        
        # 性能统计
        self.stats = {
            'start_time': time.time(),
            'operations_count': 0,
            'cache_hits': 0,
            'tab_reuses': 0
        }
    
    async def initialize(self):
        """
        初始化所有组件
        """
        logger.info("初始化性能优化浏览器系统...")
        
        # 1. 异步文件管理器
        self.file_manager = AsyncFileManager(base_path=Path.cwd() / "temp_data")
        
        # 2. 优化的Cookies管理器
        self.cookies_manager = OptimizedCookiesManager(
            storage_dir=Path(self.cookies_dir),
            cache_size=1000,  # LRU缓存大小
            auto_cleanup_interval=300  # 5分钟自动清理
        )
        
        # 3. 智能缓存预测器和管理器
        self.cache_predictor = SmartCachePredictor(
            default_ttl=3600,  # 1小时默认TTL
            prediction_window=86400  # 24小时预测窗口
        )
        
        # 缓存刷新回调函数
        async def cache_refresh_callback(key: str) -> Any:
            """缓存刷新回调"""
            logger.debug(f"刷新缓存: {key}")
            # 这里可以实现具体的数据刷新逻辑
            # 例如重新获取cookies或headers
            return f"refreshed_data_{key}_{time.time()}"
        
        self.cache_manager = SmartCacheManager(
            predictor=self.cache_predictor,
            refresh_callback=cache_refresh_callback,
            strategy=CacheStrategy.ADAPTIVE,  # 自适应策略
            max_concurrent_refreshes=3
        )
        
        # 4. 标签页池管理器
        self.tab_pool = TabPoolManager(
            max_tabs_per_domain=3,  # 每个域名最多3个标签页
            max_total_tabs=15,  # 总共最多15个标签页
            max_idle_time=1800,  # 30分钟空闲时间
            max_tab_age=7200,  # 2小时最大年龄
            cleanup_interval=300  # 5分钟清理间隔
        )
        
        # 5. 优化的浏览器服务
        self.browser_service = OptimizedBrowserService(self.tab_pool)
        
        # 6. 优化的浏览器操作器
        self.browser_operator = OptimizedBrowserOperator(
            max_pool_size=10,  # 最大连接池大小
            connection_max_age=3600,  # 连接最大存活时间
            enable_request_deduplication=True,  # 启用请求去重
            dedup_cache_size=500,
            dedup_ttl=300
        )
        
        logger.info("所有组件初始化完成")
    
    async def demonstrate_cookies_optimization(self):
        """
        演示Cookies管理优化
        """
        logger.info("=== 演示Cookies管理优化 ===")
        
        # 批量保存cookies
        batch_data = [
            ('user1', {'session_id': 'abc123', 'token': 'token1'}, None, 30, 'test_site'),
            ('user2', {'session_id': 'def456', 'token': 'token2'}, None, 30, 'test_site'),
            ('user3', {'session_id': 'ghi789', 'token': 'token3'}, None, 30, 'test_site')
        ]
        
        start_time = time.time()
        results = await self.cookies_manager.save_cookies_batch(batch_data)
        batch_save_time = time.time() - start_time
        
        logger.info(f"批量保存3个用户cookies耗时: {batch_save_time:.3f}秒")
        
        # 批量获取cookies
        start_time = time.time()
        retrieved_cookies = await self.cookies_manager.get_cookies_batch(
            ['user1', 'user2', 'user3'], 'test_site'
        )
        batch_get_time = time.time() - start_time
        
        logger.info(f"批量获取3个用户cookies耗时: {batch_get_time:.3f}秒")
        logger.info(f"缓存命中情况: {len([c for c in retrieved_cookies.values() if c is not None])}/3")
        
        # 显示性能统计
        stats = self.cookies_manager.get_performance_stats()
        logger.info(f"Cookies管理器统计: {stats}")
    
    async def demonstrate_smart_caching(self):
        """
        演示智能缓存策略
        """
        logger.info("=== 演示智能缓存策略 ===")
        
        # 模拟缓存访问模式
        cache_keys = ['api_data_1', 'api_data_2', 'api_data_3']
        
        for key in cache_keys:
            # 设置初始缓存
            await self.cache_manager.set(key, f"initial_data_{key}")
            
            # 模拟多次访问
            for i in range(5):
                await asyncio.sleep(0.1)  # 模拟访问间隔
                data = await self.cache_manager.get(key)
                logger.debug(f"访问缓存 {key}: {data is not None}")
        
        # 显示预测器统计
        predictor_stats = self.cache_predictor.get_statistics()
        logger.info(f"缓存预测器统计: {predictor_stats}")
        
        # 显示缓存管理器统计
        cache_stats = self.cache_manager.get_statistics()
        logger.info(f"缓存管理器统计: {cache_stats}")
    
    async def demonstrate_tab_pooling(self, browser_context):
        """
        演示标签页池管理
        
        Args:
            browser_context: 浏览器上下文
        """
        logger.info("=== 演示标签页池管理 ===")
        
        # 设置浏览器上下文
        await self.browser_service.set_browser_context(browser_context)
        
        # 定义测试任务
        async def test_task(page, task_name: str):
            """测试任务函数"""
            await asyncio.sleep(0.5)  # 模拟页面操作
            title = await page.title()
            logger.info(f"任务 {task_name} 完成，页面标题: {title[:50]}...")
            return f"result_{task_name}"
        
        # 测试URL列表（相同域名以测试复用）
        test_urls = [
            'https://www.baidu.com',
            'https://www.baidu.com/s?wd=test1',
            'https://www.baidu.com/s?wd=test2',
            'https://www.google.com',
            'https://www.google.com/search?q=test'
        ]
        
        # 批量执行任务
        tasks = [
            (url, test_task, f"task_{i}")
            for i, url in enumerate(test_urls)
        ]
        
        start_time = time.time()
        results = await self.browser_service.batch_execute(tasks, max_concurrent=3)
        execution_time = time.time() - start_time
        
        logger.info(f"批量执行5个任务耗时: {execution_time:.3f}秒")
        logger.info(f"成功完成任务数: {len([r for r in results if not isinstance(r, Exception)])}")
        
        # 显示标签页统计
        tab_stats = self.tab_pool.get_statistics()
        logger.info(f"标签页池统计: {tab_stats}")
    
    async def demonstrate_file_operations(self):
        """
        演示异步文件操作
        """
        logger.info("=== 演示异步文件操作 ===")
        
        test_dir = self.cookies_dir / "test_files"
        test_files = {
            'file1.json': {'data': 'test1', 'timestamp': time.time()},
            'file2.json': {'data': 'test2', 'timestamp': time.time()},
            'file3.json': {'data': 'test3', 'timestamp': time.time()}
        }
        
        # 批量写入文件
        start_time = time.time()
        write_tasks = {
            test_dir / filename: content
            for filename, content in test_files.items()
        }
        await self.file_manager.batch_write_json_files(write_tasks)
        write_time = time.time() - start_time
        
        logger.info(f"批量写入3个文件耗时: {write_time:.3f}秒")
        
        # 批量读取文件
        start_time = time.time()
        file_paths = [test_dir / filename for filename in test_files.keys()]
        read_results = await self.file_manager.batch_read_json_files(file_paths)
        read_time = time.time() - start_time
        
        logger.info(f"批量读取3个文件耗时: {read_time:.3f}秒")
        logger.info(f"成功读取文件数: {len([r for r in read_results if r is not None])}")
        
        # 清理测试文件
        await self.file_manager.batch_delete_files(file_paths)
        logger.info("清理测试文件完成")
    
    async def run_performance_benchmark(self, browser_context):
        """
        运行性能基准测试
        
        Args:
            browser_context: 浏览器上下文
        """
        logger.info("=== 开始性能基准测试 ===")
        
        start_time = time.time()
        
        # 1. Cookies管理优化测试
        await self.demonstrate_cookies_optimization()
        
        # 2. 智能缓存策略测试
        await self.demonstrate_smart_caching()
        
        # 3. 异步文件操作测试
        await self.demonstrate_file_operations()
        
        # 4. 标签页池管理测试
        await self.demonstrate_tab_pooling(browser_context)
        
        total_time = time.time() - start_time
        
        # 汇总统计信息
        logger.info("=== 性能基准测试完成 ===")
        logger.info(f"总耗时: {total_time:.3f}秒")
        
        # 显示各组件统计
        all_stats = {
            'cookies_manager': self.cookies_manager.get_performance_stats(),
            'cache_manager': self.cache_manager.get_statistics(),
            'tab_pool': self.tab_pool.get_statistics(),
            'browser_service': self.browser_service.get_statistics()
        }
        
        logger.info("=== 各组件性能统计 ===")
        for component, stats in all_stats.items():
            logger.info(f"{component}: {stats}")
    
    async def cleanup(self):
        """
        清理资源
        """
        logger.info("清理系统资源...")
        
        if self.cache_manager:
            await self.cache_manager.close()
        
        if self.tab_pool:
            await self.tab_pool.close()
        
        if self.browser_operator:
            await self.browser_operator.stop()
        
        logger.info("资源清理完成")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


async def main():
    """
    主函数 - 运行性能优化示例
    """
    logger.info("启动性能优化示例程序")
    
    # 这里需要实际的浏览器上下文
    # 在实际使用中，你需要创建Playwright浏览器实例
    browser_context = None  # 替换为实际的浏览器上下文
    
    try:
        async with PerformanceOptimizedBrowserSystem() as system:
            if browser_context:
                await system.run_performance_benchmark(browser_context)
            else:
                logger.warning("未提供浏览器上下文，跳过标签页相关测试")
                
                # 运行不需要浏览器的测试
                await system.demonstrate_cookies_optimization()
                await system.demonstrate_smart_caching()
                await system.demonstrate_file_operations()
    
    except Exception as e:
        logger.error(f"示例程序执行出错: {e}")
        raise
    
    logger.info("性能优化示例程序完成")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())