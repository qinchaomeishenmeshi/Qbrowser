#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面重定向管理器
实现纯Python端的浏览器页面重定向功能
"""

import json
import time
import asyncio
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from utils.common_logger import get_logger

from utils.database_manager import db_manager

# 获取带有模块名称的logger
logger = get_logger(__name__)


@dataclass
class RedirectRule:
    """重定向规则数据类"""

    name: str  # 规则名称
    source_pattern: str  # 源URL模式
    target_url: str  # 目标URL
    condition: Optional[str] = None  # 条件表达式
    enabled: bool = True  # 是否启用
    created_at: float = None  # 创建时间

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class PageRedirectManager:
    """页面重定向管理器"""

    def __init__(self):
        """初始化重定向管理器"""
        self.rules: Dict[str, RedirectRule] = {}
        self._loaded = False

    async def _ensure_loaded(self) -> None:
        """从数据库加载重定向规则"""
        if self._loaded:
            return
        try:
            db_rules = await db_manager.get_all_redirect_rules()
            self.rules = {rule["name"]: RedirectRule(**rule) for rule in db_rules}
            self._loaded = True
            logger.info(f"从数据库加载了 {len(self.rules)} 条重定向规则")
        except Exception as e:
            logger.error(f"加载重定向规则失败: {e}")
            self.rules = {}

    async def redirect_page(self, tab, target_url: str, wait_time: float = 1.0) -> bool:
        """重定向页面到指定URL (DrissionPage 兼容)

        Args:
            tab: DrissionPage标签页对象
            target_url: 目标URL
            wait_time: 等待时间（秒）

        Returns:
            bool: 重定向是否成功
        """
        try:
            logger.info(f"正在重定向页面到: {target_url}")

            # 使用DrissionPage的get方法进行页面导航
            tab.get(target_url)

            # 等待页面加载 (异步等待)
            await asyncio.sleep(wait_time)

            # 验证重定向是否成功
            current_url = tab.url
            if current_url:
                logger.info(f"页面重定向成功，当前URL: {current_url}")
                return True
            else:
                logger.error("页面重定向失败，无法获取当前URL")
                return False

        except Exception as e:
            logger.error(f"页面重定向失败: {str(e)}")
            return False

    async def batch_redirect(
        self, tabs_urls: List[tuple], wait_time: float = 1.0
    ) -> Dict[str, bool]:
        """批量重定向多个页面 (DrissionPage 兼容)

        Args:
            tabs_urls: [(tab, url), ...] 标签页和URL的元组列表
            wait_time: 每次重定向后的等待时间

        Returns:
            Dict[str, bool]: 每个URL的重定向结果
        """
        results = {}

        for i, (tab, url) in enumerate(tabs_urls):
            try:
                logger.info(f"批量重定向 {i+1}/{len(tabs_urls)}: {url}")
                success = await self.redirect_page(tab, url, wait_time)
                results[url] = success

                # 批量操作间隔
                if i < len(tabs_urls) - 1:
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"批量重定向失败 {url}: {str(e)}")
                results[url] = False

        logger.info(f"批量重定向完成，成功: {sum(results.values())}/{len(results)}")
        return results

    async def conditional_redirect(
        self, tab, condition_func: Callable, target_url: str, wait_time: float = 1.0
    ) -> bool:
        """条件重定向

        Args:
            tab: DrissionPage标签页对象
            condition_func: 条件判断函数，返回bool
            target_url: 目标URL
            wait_time: 等待时间

        Returns:
            bool: 重定向是否成功
        """
        try:
            if condition_func(tab):
                logger.info(f"条件满足，执行重定向到: {target_url}")
                return await self.redirect_page(tab, target_url, wait_time)
            else:
                logger.info("条件不满足，跳过重定向")
                return False

        except Exception as e:
            logger.error(f"条件重定向失败: {str(e)}")
            return False

    async def add_rule(self, rule: RedirectRule) -> bool:
        """添加重定向规则

        Args:
            rule: 重定向规则

        Returns:
            bool: 添加是否成功
        """
        try:
            await self._ensure_loaded()
            self.rules[rule.name] = rule
            await db_manager.save_redirect_rule(asdict(rule))
            logger.info(f"添加重定向规则成功并保存至数据库: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"添加重定向规则失败: {str(e)}")
            return False

    async def remove_rule(self, rule_name: str) -> bool:
        """移除重定向规则

        Args:
            rule_name: 规则名称

        Returns:
            bool: 移除是否成功
        """
        try:
            await self._ensure_loaded()
            if rule_name in self.rules:
                del self.rules[rule_name]
                await db_manager.delete_redirect_rule(rule_name)
                logger.info(f"从数据库移除重定向规则成功: {rule_name}")
                return True
            else:
                logger.warning(f"重定向规则不存在: {rule_name}")
                return False
        except Exception as e:
            logger.error(f"移除重定向规则失败: {str(e)}")
            return False

    async def get_rule(self, rule_name: str) -> Optional[RedirectRule]:
        """获取重定向规则

        Args:
            rule_name: 规则名称

        Returns:
            Optional[RedirectRule]: 重定向规则或None
        """
        await self._ensure_loaded()
        return self.rules.get(rule_name)

    async def list_rules(self) -> List[RedirectRule]:
        """获取所有重定向规则

        Returns:
            List[RedirectRule]: 重定向规则列表
        """
        await self._ensure_loaded()
        return list(self.rules.values())

    async def apply_rule(
        self, tab, rule_name_or_url: str, wait_time: float = 1.0
    ) -> bool:
        """应用重定向规则

        Args:
            tab: DrissionPage标签页对象
            rule_name_or_url: 规则名称或当前URL（自动匹配规则）
            wait_time: 等待时间

        Returns:
            bool: 应用是否成功
        """
        await self._ensure_loaded()
        # 如果传入的是URL而不是规则名称，尝试查找匹配的规则
        current_url = ""
        try:
            current_url = tab.url
        except Exception as e:
            logger.error(f"获取当前URL失败: {str(e)}")
            return False

        # 检查是否传入的是URL而不是规则名称
        if rule_name_or_url.startswith("http"):
            # 查找匹配当前URL的规则
            matched_rule = None
            for rule in self.rules.values():
                if rule.enabled and rule.source_pattern in rule_name_or_url:
                    matched_rule = rule
                    break

            if matched_rule:
                logger.info(f"找到匹配的规则: {matched_rule.name}")
                return await self.redirect_page(tab, matched_rule.target_url, wait_time)
            else:
                logger.warning(f"没有找到匹配URL的规则: {rule_name_or_url}")
                return False

        # 正常通过规则名称查找
        rule = await self.get_rule(rule_name_or_url)
        if not rule or not rule.enabled:
            logger.warning(f"重定向规则不存在或已禁用: {rule_name_or_url}")
            return False

        try:
            # 简单的URL模式匹配
            if rule.source_pattern in current_url:
                logger.info(f"应用重定向规则: {rule_name_or_url}")
                return await self.redirect_page(tab, rule.target_url, wait_time)
            else:
                logger.info(f"当前URL不匹配规则模式: {rule.source_pattern}")
                return False

        except Exception as e:
            logger.error(f"应用重定向规则失败: {str(e)}")
            return False

    def save_rules(self) -> bool:
        """保存重定向规则 (弃用)"""
        logger.warning("save_rules 已弃用，规则已自动同步至数据库")
        return True

    def load_rules(self) -> bool:
        """加载重定向规则 (弃用)"""
        logger.warning("load_rules 已弃用，请使用异步方法 ensure_loaded")
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """获取重定向管理器统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        await self._ensure_loaded()
        enabled_rules = sum(1 for rule in self.rules.values() if rule.enabled)
        disabled_rules = len(self.rules) - enabled_rules

        return {
            "total_rules": len(self.rules),
            "enabled_rules": enabled_rules,
            "disabled_rules": disabled_rules,
            "storage": "sqlite",
            "last_loaded": time.time(),
        }


# 全局重定向管理器实例
redirect_manager = PageRedirectManager()


# 全局重定向管理器实例
redirect_manager = PageRedirectManager()
