#!/usr/bin/env python3
import sys
import asyncio
import json
from pathlib import Path

# 添加项目路径
sys.path.append('/Users/cherishxn/工作项目/2024/短视频生产系统/qw-browser')

from browser.browser_operator import browser_operator, SITE_CONFIGS
from utils.common_logger import get_logger

logger = get_logger(__name__)

async def debug_eos_client_cookies():
    """模拟eos_client中的_get_cookies_for_user方法"""
    user_id = 'test001'
    site_key = 'eos'
    
    print(f"=== 模拟 eos_client._get_cookies_for_user 方法 ===")
    
    # 模拟 _get_cookies_for_user 方法的逻辑
    print(f"\n1. 调用 browser_operator.get_user_cookies({user_id}, {site_key})")
    cookies_list = await browser_operator.get_user_cookies(user_id, site_key)
    print(f"   返回类型: {type(cookies_list)}")
    print(f"   返回值是否为None: {cookies_list is None}")
    
    # 处理不同的 cookies 数据格式
    cookies_dict = {}
    if cookies_list is None:
        print(f"\n2. cookies_list 为 None，返回空字典")
        logger.warning(f"用户 {user_id} 的 cookies 为空")
        return cookies_dict
        
    if isinstance(cookies_list, dict):
        print(f"\n2. cookies_list 是字典格式，直接使用")
        cookies_dict = cookies_list
        print(f"   字典中的cookies数量: {len(cookies_dict)}")
    elif isinstance(cookies_list, list):
        print(f"\n2. cookies_list 是列表格式，转换为字典")
        cookies_dict = {
            c["name"]: c["value"] for c in cookies_list 
            if isinstance(c, dict) and "name" in c and "value" in c
        }
        print(f"   转换后的cookies数量: {len(cookies_dict)}")
    else:
        print(f"\n2. cookies_list 格式不支持，类型: {type(cookies_list)}")
        logger.error(f"用户 {user_id} 的 cookies 格式不支持，类型: {type(cookies_list)}")
        return cookies_dict
    
    # 检查关键cookies
    print(f"\n3. 检查关键cookies")
    required_cookies = SITE_CONFIGS[site_key]['required_cookies']
    print(f"   必需的cookies: {required_cookies}")
    print(f"   当前cookies中的keys: {list(cookies_dict.keys())[:10]}...")  # 只显示前10个
    
    missing_cookies = [cookie for cookie in required_cookies if cookie not in cookies_dict]
    if missing_cookies:
        print(f"\n4. 发现缺失的关键cookies: {missing_cookies}")
        logger.warning(f"用户 {user_id} 缺失关键 cookies: {missing_cookies}")
        logger.info(f"当前可用 cookies: {list(cookies_dict.keys())}")
    else:
        print(f"\n4. 所有关键cookies都存在")
        for cookie in required_cookies:
            print(f"   {cookie}: {cookies_dict[cookie][:50]}...")
    
    return cookies_dict

if __name__ == '__main__':
    asyncio.run(debug_eos_client_cookies())