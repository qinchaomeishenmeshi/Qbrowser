#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
网络监听功能示例

本示例展示如何使用QW-Browser的网络监听功能来捕获和分析网络请求。
可以指定特定URL进行监听，或者全量监听所有网络请求。
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# 导入浏览器管理器
from browser.browser_manager import BrowserManager


def monitor_specific_url():
    """监听特定URL的示例"""
    # 创建浏览器管理器实例
    browser_manager = BrowserManager(user_id="test_user")
    
    try:
        # 初始化浏览器
        if not browser_manager.initialize():
            print("❌ 浏览器初始化失败")
            return
            
        print("✅ 浏览器初始化成功")
        
        # 创建网络监听器
        network_listener = browser_manager.create_network_listener()
        if not network_listener:
            print("❌ 网络监听器创建失败")
            return
            
        print("✅ 网络监听器创建成功")
        
        # 开始监听特定URL (例如监听API请求)
        target_url = "api.example.com/data"
        if not browser_manager.start_network_listening(target_url):
            print(f"❌ 开始监听URL {target_url} 失败")
            return
            
        print(f"✅ 开始监听URL: {target_url}")
        
        # 打开网页
        tab = browser_manager.browser.get_tab()
        tab.get("https://example.com")
        print("✅ 已打开网页")
        
        # 等待一段时间，让网络请求发生
        print("等待网络请求中...")
        time.sleep(5)
        
        # 获取捕获的数据包
        packets = browser_manager.get_captured_packets()
        print(f"✅ 捕获到 {len(packets)} 个数据包")
        
        # 打印数据包信息
        for i, packet in enumerate(packets[:3], 1):  # 只打印前3个
            print(f"\n数据包 #{i}:")
            print(f"URL: {packet.get('url', 'N/A')}")
            print(f"方法: {packet.get('method', 'N/A')}")
            print(f"状态码: {packet.get('status_code', 'N/A')}")
            
        # 如果有更多数据包，提示有更多
        if len(packets) > 3:
            print(f"...还有 {len(packets) - 3} 个数据包未显示")
            
        # 停止监听
        browser_manager.stop_network_listening()
        print("✅ 已停止网络监听")
        
    finally:
        # 清理资源
        browser_manager.cleanup()
        print("✅ 已清理浏览器资源")


def monitor_all_requests():
    """监听所有网络请求的示例"""
    # 创建浏览器管理器实例
    browser_manager = BrowserManager(user_id="test_user")
    
    try:
        # 初始化浏览器
        if not browser_manager.initialize():
            print("❌ 浏览器初始化失败")
            return
            
        print("✅ 浏览器初始化成功")
        
        # 创建网络监听器
        network_listener = browser_manager.create_network_listener()
        if not network_listener:
            print("❌ 网络监听器创建失败")
            return
            
        print("✅ 网络监听器创建成功")
        
        # 开始监听所有请求 (不指定URL)
        if not browser_manager.start_network_listening():
            print("❌ 开始全量监听失败")
            return
            
        print("✅ 开始全量监听网络请求")
        
        # 打开网页
        tab = browser_manager.browser.get_tab()
        tab.get("https://example.com")
        print("✅ 已打开网页")
        
        # 等待一段时间，让网络请求发生
        print("等待网络请求中...")
        time.sleep(5)
        
        # 获取捕获的数据包
        packets = browser_manager.get_captured_packets()
        print(f"✅ 捕获到 {len(packets)} 个数据包")
        
        # 按类型统计数据包
        content_types = {}
        for packet in packets:
            content_type = packet.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
            
        print("\n数据包类型统计:")
        for content_type, count in content_types.items():
            print(f"{content_type}: {count} 个")
            
        # 导出数据包到文件
        if packets:
            output_file = Path("captured_packets.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(packets, f, ensure_ascii=False, indent=2)
            print(f"✅ 已将数据包导出到 {output_file.absolute()}")
            
        # 停止监听
        browser_manager.stop_network_listening()
        print("✅ 已停止网络监听")
        
    finally:
        # 清理资源
        browser_manager.cleanup()
        print("✅ 已清理浏览器资源")


def monitor_with_regex_pattern():
    """使用正则表达式模式监听网络请求的示例"""
    # 创建浏览器管理器实例
    browser_manager = BrowserManager(user_id="test_user")
    
    try:
        # 初始化浏览器
        if not browser_manager.initialize():
            print("❌ 浏览器初始化失败")
            return
            
        print("✅ 浏览器初始化成功")
        
        # 创建网络监听器
        network_listener = browser_manager.create_network_listener()
        if not network_listener:
            print("❌ 网络监听器创建失败")
            return
            
        print("✅ 网络监听器创建成功")
        
        # 使用正则表达式模式监听多个URL
        # 例如: 监听所有图片请求和API请求
        url_patterns = [
            r".*\.(jpg|jpeg|png|gif|webp)$",  # 所有图片
            r"api\..*\.com/.*"              # 所有API请求
        ]
        
        if not browser_manager.start_network_listening(url_patterns):
            print("❌ 开始监听失败")
            return
            
        print(f"✅ 开始监听URL模式: {url_patterns}")
        
        # 打开网页
        tab = browser_manager.browser.get_tab()
        tab.get("https://example.com")
        print("✅ 已打开网页")
        
        # 等待一段时间，让网络请求发生
        print("等待网络请求中...")
        time.sleep(5)
        
        # 获取捕获的数据包
        packets = browser_manager.get_captured_packets()
        print(f"✅ 捕获到 {len(packets)} 个数据包")
        
        # 分类显示数据包
        image_packets = [p for p in packets if any(ext in p.get('url', '') 
                                               for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]
        api_packets = [p for p in packets if 'api.' in p.get('url', '')]
        
        print(f"\n图片请求: {len(image_packets)} 个")
        print(f"API请求: {len(api_packets)} 个")
        
        # 停止监听
        browser_manager.stop_network_listening()
        print("✅ 已停止网络监听")
        
    finally:
        # 清理资源
        browser_manager.cleanup()
        print("✅ 已清理浏览器资源")


if __name__ == "__main__":
    print("=== 网络监听功能示例 ===")
    print("1. 监听特定URL")
    print("2. 监听所有请求")
    print("3. 使用正则表达式模式监听")
    
    choice = input("请选择示例 (1-3): ")
    
    if choice == "1":
        monitor_specific_url()
    elif choice == "2":
        monitor_all_requests()
    elif choice == "3":
        monitor_with_regex_pattern()
    else:
        print("无效的选择")