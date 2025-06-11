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

async def debug_cookies():
    """调试cookie获取问题"""
    user_id = 'test001'
    site_key = 'eos'
    
    print(f"=== 调试用户 {user_id} 的 {site_key} 站点 cookies ===")
    
    # 1. 检查配置
    print(f"\n1. 站点配置:")
    config = SITE_CONFIGS.get(site_key, {})
    print(f"   required_cookies: {config.get('required_cookies', [])}")
    
    # 2. 直接读取cookie文件
    print(f"\n2. 直接读取cookie文件:")
    cookie_file = Path('/Users/cherishxn/工作项目/2024/短视频生产系统/qw-browser/data/cookies/test001_eos_cookies.json')
    if cookie_file.exists():
        with open(cookie_file, 'r') as f:
            file_data = json.load(f)
        file_cookies = file_data.get('cookies', {})
        print(f"   文件中的cookies数量: {len(file_cookies)}")
        print(f"   eos_s_token存在: {'eos_s_token' in file_cookies}")
        if 'eos_s_token' in file_cookies:
            print(f"   eos_s_token值: {file_cookies['eos_s_token'][:50]}...")
    else:
        print(f"   Cookie文件不存在: {cookie_file}")
    
    # 3. 通过browser_operator获取
    print(f"\n3. 通过browser_operator获取:")
    try:
        cookies = await browser_operator.get_user_cookies(user_id, site_key)
        print(f"   返回类型: {type(cookies)}")
        print(f"   返回内容: {cookies}")
        if isinstance(cookies, dict):
            print(f"   cookies数量: {len(cookies)}")
            print(f"   eos_s_token存在: {'eos_s_token' in cookies}")
            if 'eos_s_token' in cookies:
                print(f"   eos_s_token值: {cookies['eos_s_token'][:50]}...")
    except Exception as e:
        print(f"   获取失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 检查缓存
    print(f"\n4. 检查cookies_manager缓存:")
    cache_key = browser_operator.cookies_manager._get_cache_key(user_id, site_key)
    print(f"   缓存key: {cache_key}")
    print(f"   缓存中存在: {cache_key in browser_operator.cookies_manager._cache}")
    if cache_key in browser_operator.cookies_manager._cache:
        cache_data = browser_operator.cookies_manager._cache[cache_key]
        cache_cookies = cache_data.get('cookies', {})
        print(f"   缓存中cookies数量: {len(cache_cookies)}")
        print(f"   缓存中eos_s_token存在: {'eos_s_token' in cache_cookies}")

if __name__ == '__main__':
    asyncio.run(debug_cookies())