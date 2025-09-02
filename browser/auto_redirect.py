#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动重定向模块
在浏览器启动时自动应用重定向规则
"""

import time
from typing import Any, Optional

from utils.common_logger import get_logger
from utils.page_redirect_manager import redirect_manager

# 获取logger
logger = get_logger(__name__)


class AutoRedirect:
    """自动重定向类"""
    
    @staticmethod
    def setup_tab_listener(tab: Any) -> bool:
        """设置标签页URL变化监听器
        
        Args:
            tab: 浏览器标签页对象
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 创建一个简单的重定向监听脚本
            redirect_script = """
            // 重定向监听脚本
            function setupRedirectObserver() {
                console.log('[AutoRedirect] 设置URL变化监听器...');
                
                // 监听URL变化
                let lastUrl = location.href;
                new MutationObserver(() => {
                    const url = location.href;
                    if (url !== lastUrl) {
                        lastUrl = url;
                        console.log('[AutoRedirect] URL changed to', url);
                        checkAndRedirect(url);
                    }
                }).observe(document, {subtree: true, childList: true});
                
                // 初始检查
                checkAndRedirect(location.href);
            }
            
            // 检查并重定向
            function checkAndRedirect(url) {
                // 检查Google
                if (url.includes('google')) {
                    console.log('[AutoRedirect] 检测到Google URL，重定向到百度...');
                    location.href = 'https://www.baidu.com';
                    return;
                }
                
                // 检查YouTube
                if (url.includes('youtube')) {
                    console.log('[AutoRedirect] 检测到YouTube URL，重定向到哔哩哔哩...');
                    location.href = 'https://www.bilibili.com';
                    return;
                }
            }
            
            // 页面加载完成后设置监听器
            if (document.readyState === 'complete') {
                setupRedirectObserver();
            } else {
                window.addEventListener('load', setupRedirectObserver);
            }
            
            // 立即执行初始检查
            checkAndRedirect(location.href);
            """
            
            # 注入脚本到浏览器
            tab.run_js(redirect_script)
            logger.info("✅ 自动重定向脚本注入成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 自动重定向脚本注入失败: {e}")
            return False
    
    @staticmethod
    def apply_rules_to_tab(tab: Any) -> bool:
        """应用所有启用的重定向规则到标签页
        
        Args:
            tab: 浏览器标签页对象
            
        Returns:
            bool: 是否成功应用规则
        """
        try:
            current_url = tab.url
            if not current_url:
                logger.warning("无法获取当前URL")
                return False
            
            # 检查每个规则
            for rule in redirect_manager.list_rules():
                if rule.enabled and rule.source_pattern in current_url:
                    logger.info(f"应用重定向规则: {rule.name}")
                    return redirect_manager.redirect_page(tab, rule.target_url, 1.0)
            
            logger.info(f"没有找到匹配URL的规则: {current_url}")
            return False
            
        except Exception as e:
            logger.error(f"应用重定向规则失败: {e}")
            return False
    
    @staticmethod
    def setup_browser(browser: Any) -> bool:
        """为浏览器设置自动重定向
        
        Args:
            browser: 浏览器实例
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 获取所有标签页
            tabs = browser.get_tabs()
            
            success_count = 0
            for tab in tabs:
                try:
                    # 设置标签页监听器
                    if AutoRedirect.setup_tab_listener(tab):
                        success_count += 1
                        
                    # 应用当前规则
                    AutoRedirect.apply_rules_to_tab(tab)
                    
                except Exception as e:
                    logger.error(f"设置标签页自动重定向失败: {e}")
            
            logger.info(f"已为 {success_count}/{len(tabs)} 个标签页设置自动重定向")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"设置浏览器自动重定向失败: {e}")
            return False


# 创建一个全局实例
auto_redirect = AutoRedirect()