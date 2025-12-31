#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面重定向规则管理器
主要负责管理和存储重定向规则，具体的页面操作由 PlaywrightOperator 负责。
"""

import time
from typing import Dict, List, Optional, Any
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
    """页面重定向固规则管理器"""

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

    async def add_rule(self, rule: RedirectRule) -> bool:
        """添加重定向规则"""
        try:
            await self._ensure_loaded()
            self.rules[rule.name] = rule
            await db_manager.save_redirect_rule(asdict(rule))
            logger.info(f"添加重定向规则成功: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"添加重定向规则失败: {str(e)}")
            return False

    async def remove_rule(self, rule_name: str) -> bool:
        """移除重定向规则"""
        try:
            await self._ensure_loaded()
            if rule_name in self.rules:
                del self.rules[rule_name]
                await db_manager.delete_redirect_rule(rule_name)
                logger.info(f"移除重定向规则成功: {rule_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"移除重定向规则失败: {str(e)}")
            return False

    async def get_rule(self, rule_name: str) -> Optional[RedirectRule]:
        """获取重定向规则"""
        await self._ensure_loaded()
        return self.rules.get(rule_name)

    async def list_rules(self) -> List[RedirectRule]:
        """获取所有重定向规则"""
        await self._ensure_loaded()
        return list(self.rules.values())

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        await self._ensure_loaded()
        enabled_rules = sum(1 for rule in self.rules.values() if rule.enabled)
        return {
            "total_rules": len(self.rules),
            "enabled_rules": enabled_rules,
            "disabled_rules": len(self.rules) - enabled_rules,
            "storage": "sqlite",
        }


# 全局重定向管理器实例
redirect_manager = PageRedirectManager()
