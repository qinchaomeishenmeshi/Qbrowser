#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动重定向设置脚本
为浏览器添加自动重定向功能
"""

import sys
import time
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.page_redirect_manager import PageRedirectManager, RedirectRule
from service.browser_service import BrowserService
from utils.common_logger import get_logger

# 获取logger
logger = get_logger(__name__)


class AutoRedirectSetup:
    """自动重定向设置类"""
    
    def __init__(self):
        self.redirect_manager = PageRedirectManager()
        self.browser_service = BrowserService()
    
    def setup_redirect_rules(self):
        """设置重定向规则"""
        print("\n===== 设置重定向规则 =====")
        
        # 检查现有规则
        existing_rules = self.redirect_manager.list_rules()
        print(f"当前已有 {len(existing_rules)} 条规则")
        
        # 检查Google规则
        has_google_rule = False
        for rule in existing_rules:
            if rule.name == "google_to_baidu":
                has_google_rule = True
                print(f"发现Google规则: {rule.name}")
                print(f"  - 源模式: {rule.source_pattern}")
                print(f"  - 目标URL: {rule.target_url}")
                print(f"  - 启用状态: {rule.enabled}")
                
                # 更新规则以确保正确匹配
                if rule.source_pattern != "google":
                    print("  - 更新规则源模式为 'google'")
                    rule.source_pattern = "google"
                    self.redirect_manager.update_rule(rule.name, rule)
                
                # 确保规则已启用
                if not rule.enabled:
                    print("  - 启用规则")
                    rule.enabled = True
                    self.redirect_manager.update_rule(rule.name, rule)
        
        # 如果没有Google规则，创建一个
        if not has_google_rule:
            print("未发现Google规则，创建新规则")
            rule = RedirectRule(
                name="google_to_baidu",
                source_pattern="google",  # 使用更简单的模式以确保匹配
                target_url="https://www.baidu.com",
                enabled=True
            )
            self.redirect_manager.add_rule(rule)
            print("✅ 已创建Google到百度的重定向规则")
        
        # 保存规则
        self.redirect_manager.save_rules()
        print("✅ 规则已保存")
    
    async def setup_browser_redirect_hook(self):
        """设置浏览器重定向钩子"""
        print("\n===== 设置浏览器重定向钩子 =====")
        
        # 获取浏览器实例
        user_id = "auto_redirect_user"
        try:
            browser_manager, tab = await self.browser_service.get_or_create_browser(user_id)
            
            if not tab:
                print("❌ 无法获取浏览器标签页")
                return False
            
            print("✅ 成功获取浏览器标签页")
            
            # 创建一个简单的重定向监听脚本
            redirect_script = """
            // 重定向监听脚本
            function setupRedirectObserver() {
                console.log('设置URL变化监听器...');
                
                // 监听URL变化
                let lastUrl = location.href;
                new MutationObserver(() => {
                    const url = location.href;
                    if (url !== lastUrl) {
                        lastUrl = url;
                        console.log('URL changed to', url);
                        
                        // 检查是否需要重定向
                        if (url.includes('google')) {
                            console.log('检测到Google URL，重定向到百度...');
                            location.href = 'https://www.baidu.com';
                        }
                    }
                }).observe(document, {subtree: true, childList: true});
                
                // 初始检查
                if (location.href.includes('google')) {
                    console.log('初始页面是Google，重定向到百度...');
                    location.href = 'https://www.baidu.com';
                }
            }
            
            // 页面加载完成后设置监听器
            if (document.readyState === 'complete') {
                setupRedirectObserver();
            } else {
                window.addEventListener('load', setupRedirectObserver);
            }
            
            // 立即执行初始检查
            if (location.href.includes('google')) {
                console.log('页面是Google，立即重定向到百度...');
                location.href = 'https://www.baidu.com';
            }
            """
            
            # 注入脚本到浏览器
            print("注入重定向监听脚本到浏览器...")
            try:
                # 导航到一个空白页面
                tab.get("about:blank")
                time.sleep(1)
                
                # 注入脚本
                tab.run_js(redirect_script)
                print("✅ 脚本注入成功")
                
                # 测试重定向
                print("\n测试重定向功能...")
                tab.get("https://www.google.com/")
                time.sleep(5)
                
                current_url = tab.url
                print(f"当前URL: {current_url}")
                
                if "baidu.com" in current_url:
                    print("✅ 重定向成功！")
                    return True
                else:
                    print("❌ 重定向失败")
                    return False
                
            except Exception as e:
                print(f"❌ 脚本注入失败: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 设置浏览器重定向钩子失败: {e}")
            return False


async def main():
    """主函数"""
    print("🚀 开始设置自动重定向功能")
    
    try:
        setup = AutoRedirectSetup()
        
        # 设置重定向规则
        setup.setup_redirect_rules()
        
        # 设置浏览器重定向钩子
        result = await setup.setup_browser_redirect_hook()
        
        if result:
            print("\n✅ 自动重定向功能设置成功！")
            print("现在，当你访问Google时，将自动重定向到百度。")
        else:
            print("\n❌ 自动重定向功能设置失败")
            print("请检查日志以获取更多信息。")
            
    except Exception as e:
        print(f"\n❌ 设置过程中出现错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))