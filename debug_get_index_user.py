#!/usr/bin/env python3
import sys
import asyncio
import json
from pathlib import Path

# 添加项目路径
sys.path.append('/Users/cherishxn/工作项目/2024/短视频生产系统/qw-browser')

from worker.eos_client import LivingClient
from utils.common_logger import get_logger

logger = get_logger(__name__)

async def debug_get_index_user():
    """调试get_index_user方法"""
    user_id = 'test001'
    
    print(f"=== 调试 LivingClient.get_index_user 方法 ===")
    
    # 创建LivingClient实例
    client = LivingClient()
    
    print(f"\n1. 获取cookies")
    cookies = await client._get_cookies_for_user(user_id)
    print(f"   cookies类型: {type(cookies)}")
    print(f"   cookies数量: {len(cookies) if cookies else 0}")
    print(f"   eos_s_token存在: {'eos_s_token' in cookies if cookies else False}")
    if cookies and 'eos_s_token' in cookies:
        print(f"   eos_s_token值: {cookies['eos_s_token'][:50]}...")
    
    print(f"\n2. 获取headers")
    headers = await client._get_headers_for_user(user_id)
    print(f"   headers类型: {type(headers)}")
    print(f"   headers数量: {len(headers) if headers else 0}")
    if headers:
        print(f"   headers keys: {list(headers.keys())}")
    
    print(f"\n3. 请求URL")
    print(f"   URL: {client.get_user_url}")
    
    print(f"\n4. 调用get_index_user")
    try:
        result = await client.get_index_user(user_id)
        print(f"   请求结果: {result}")
        
        # 检查响应
        if isinstance(result, dict):
            if 'code' in result:
                print(f"   响应code: {result['code']}")
            if 'msg' in result:
                print(f"   响应msg: {result['msg']}")
            if 'message' in result:
                print(f"   响应message: {result['message']}")
                
    except Exception as e:
        print(f"   请求异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(debug_get_index_user())