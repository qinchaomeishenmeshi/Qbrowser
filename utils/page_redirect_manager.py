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
    
    def __init__(self, config_file: str = "redirect_rules.json"):
        """初始化重定向管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.rules: Dict[str, RedirectRule] = {}
        self.load_rules()
    
    def redirect_page(self, tab, target_url: str, wait_time: float = 1.0) -> bool:
        """重定向页面到指定URL
        
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
            
            # 等待页面加载
            time.sleep(wait_time)
            
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
    
    def batch_redirect(self, tabs_urls: List[tuple], wait_time: float = 1.0) -> Dict[str, bool]:
        """批量重定向多个页面
        
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
                success = self.redirect_page(tab, url, wait_time)
                results[url] = success
                
                # 批量操作间隔
                if i < len(tabs_urls) - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"批量重定向失败 {url}: {str(e)}")
                results[url] = False
        
        logger.info(f"批量重定向完成，成功: {sum(results.values())}/{len(results)}")
        return results
    
    def conditional_redirect(self, tab, condition_func: Callable, target_url: str, 
                           wait_time: float = 1.0) -> bool:
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
                return self.redirect_page(tab, target_url, wait_time)
            else:
                logger.info("条件不满足，跳过重定向")
                return False
                
        except Exception as e:
            logger.error(f"条件重定向失败: {str(e)}")
            return False
    
    def add_rule(self, rule: RedirectRule) -> bool:
        """添加重定向规则
        
        Args:
            rule: 重定向规则
            
        Returns:
            bool: 添加是否成功
        """
        try:
            self.rules[rule.name] = rule
            self.save_rules()
            logger.info(f"添加重定向规则成功: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"添加重定向规则失败: {str(e)}")
            return False
    
    def remove_rule(self, rule_name: str) -> bool:
        """移除重定向规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if rule_name in self.rules:
                del self.rules[rule_name]
                self.save_rules()
                logger.info(f"移除重定向规则成功: {rule_name}")
                return True
            else:
                logger.warning(f"重定向规则不存在: {rule_name}")
                return False
        except Exception as e:
            logger.error(f"移除重定向规则失败: {str(e)}")
            return False
    
    def get_rule(self, rule_name: str) -> Optional[RedirectRule]:
        """获取重定向规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            Optional[RedirectRule]: 重定向规则或None
        """
        return self.rules.get(rule_name)
    
    def list_rules(self) -> List[RedirectRule]:
        """获取所有重定向规则
        
        Returns:
            List[RedirectRule]: 重定向规则列表
        """
        return list(self.rules.values())
    
    def apply_rule(self, tab, rule_name_or_url: str, wait_time: float = 1.0) -> bool:
        """应用重定向规则
        
        Args:
            tab: DrissionPage标签页对象
            rule_name_or_url: 规则名称或当前URL（自动匹配规则）
            wait_time: 等待时间
            
        Returns:
            bool: 应用是否成功
        """
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
                return self.redirect_page(tab, matched_rule.target_url, wait_time)
            else:
                logger.warning(f"没有找到匹配URL的规则: {rule_name_or_url}")
                return False
        
        # 正常通过规则名称查找
        rule = self.get_rule(rule_name_or_url)
        if not rule or not rule.enabled:
            logger.warning(f"重定向规则不存在或已禁用: {rule_name_or_url}")
            return False
        
        try:
            # 简单的URL模式匹配
            if rule.source_pattern in current_url:
                logger.info(f"应用重定向规则: {rule_name_or_url}")
                return self.redirect_page(tab, rule.target_url, wait_time)
            else:
                logger.info(f"当前URL不匹配规则模式: {rule.source_pattern}")
                return False
                
        except Exception as e:
            logger.error(f"应用重定向规则失败: {str(e)}")
            return False
    
    def save_rules(self) -> bool:
        """保存重定向规则到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保规则字典不为空，即使没有规则也创建一个空字典
            rules_data = {}
            for name, rule in self.rules.items():
                # 将规则转换为字典，但排除name字段，因为name已经作为键名
                rule_dict = asdict(rule)
                if 'name' in rule_dict:
                    del rule_dict['name']
                rules_data[name] = rule_dict
            
            # 确保配置文件目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存规则到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"重定向规则保存成功: {self.config_file}，共 {len(rules_data)} 条规则")
            return True
            
        except Exception as e:
            logger.error(f"保存重定向规则失败: {str(e)}")
            return False
    
    def load_rules(self) -> bool:
        """从文件加载重定向规则
        
        Returns:
            bool: 加载是否成功
        """
        try:
            # 检查配置文件是否存在
            if not self.config_file.exists():
                logger.info(f"重定向规则文件不存在，创建新文件: {self.config_file}")
                # 初始化为空规则集
                self.rules = {}
                self.save_rules()
                return True
            
            # 读取配置文件
            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_content = f.read().strip()
                
            # 处理空文件情况
            if not file_content:
                logger.warning(f"重定向规则文件为空: {self.config_file}")
                self.rules = {}
                return True
                
            # 解析JSON内容
            rules_data = json.loads(file_content)
            
            # 检查是否为有效的字典
            if not isinstance(rules_data, dict):
                logger.error(f"规则文件格式错误，应为JSON对象: {self.config_file}")
                return False
            
            # 加载规则
            self.rules = {}
            for name, rule_dict in rules_data.items():
                try:
                    # 将规则名称添加到参数中
                    rule_params = {"name": name, **rule_dict}
                    self.rules[name] = RedirectRule(**rule_params)
                except Exception as rule_error:
                    logger.warning(f"规则 '{name}' 格式错误，已跳过: {str(rule_error)}")
            
            logger.info(f"重定向规则加载成功，共 {len(self.rules)} 条规则")
            return True
            
        except json.JSONDecodeError as je:
            logger.error(f"解析规则文件JSON失败: {str(je)}")
            return False
        except Exception as e:
            logger.error(f"加载重定向规则失败: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取重定向管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        enabled_rules = sum(1 for rule in self.rules.values() if rule.enabled)
        disabled_rules = len(self.rules) - enabled_rules
        
        return {
            "total_rules": len(self.rules),
            "enabled_rules": enabled_rules,
            "disabled_rules": disabled_rules,
            "config_file": str(self.config_file),
            "last_loaded": time.time()
        }


# 全局重定向管理器实例
redirect_manager = PageRedirectManager()