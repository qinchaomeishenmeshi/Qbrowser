import aiohttp
import asyncio
import json
from typing import Optional, Tuple


async def get_douyin_tokens_async(
    source_type: str = "force",
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    host: str = "113.57.110.35",
    port: int = 13276,
    timeout: int = 30
) -> Tuple[Optional[str], Optional[str]]:
    """
    异步获取抖音签名数据，返回 (a_bogus, ms_token)
    
    Args:
        source_type (str): 来源类型，默认为 "force"
        user_agent (str): 用户代理字符串
        host (str): 服务器主机地址
        port (int): 服务器端口
        timeout (int): 请求超时时间（秒）
    
    Returns:
        Tuple[Optional[str], Optional[str]]: 返回 (a_bogus, ms_token)，失败时返回 (None, None)
    """
    try:
        # 使用HTTP协议（根据之前测试结果，HTTPS有SSL问题）
        url = f"http://{host}:{port}/DouyinLiveWebFetcher/api/get_sign_buyin"
        
        # 构建请求载荷
        payload = {
            "source_type": source_type,
            "User-Agent": user_agent
        }
        
        # 设置请求头
        headers = {
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Host': f'{host}:{port}',
            'Connection': 'keep-alive'
        }
        
        # 设置超时
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        
        # 发送异步POST请求
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data.get("status_code") == 0:
                        data = response_data.get("data", {})
                        a_bogus = data.get("a_bogus")
                        ms_token = data.get("ms_token")
                        return a_bogus, ms_token
                    
        return None, None
        
    except Exception as e:
        print(f"获取签名失败: {e}")
        return None, None


def get_douyin_sign(
    source_type: str = "force",
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    host: str = "113.57.110.35",
    port: int = 13276,
    timeout: int = 30,
    use_http: bool = False,
    verify_ssl: bool = False
) -> Optional[dict]:
    """
    同步获取抖音签名数据（内部调用异步方法）
    
    Args:
        source_type (str): 来源类型，默认为 "force"
        user_agent (str): 用户代理字符串
        host (str): 服务器主机地址
        port (int): 服务器端口
        timeout (int): 请求超时时间（秒）
        use_http (bool): 是否使用HTTP而非HTTPS
        verify_ssl (bool): 是否验证SSL证书
    
    Returns:
        Optional[dict]: 返回包含签名数据的字典
    """
    try:
        a_bogus, ms_token = asyncio.run(
            get_douyin_tokens_async(source_type, user_agent, host, port, timeout)
        )
        if a_bogus and ms_token:
            return {
                "status_code": 0,
                "data": {
                    "a_bogus": a_bogus,
                    "ms_token": ms_token
                },
                "msg": "操作成功"
            }
        return None
    except Exception as e:
        print(f"同步调用失败: {e}")
        return None


async def get_a_bogus_async(
    source_type: str = "force",
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    host: str = "113.57.110.35",
    port: int = 13276,
    timeout: int = 30
) -> Optional[str]:
    """
    异步获取 a_bogus 签名字符串
    
    Returns:
        Optional[str]: 返回 a_bogus 签名字符串，如果请求失败则返回 None
    """
    a_bogus, _ = await get_douyin_tokens_async(source_type, user_agent, host, port, timeout)
    return a_bogus


async def get_ms_token_async(
    source_type: str = "force",
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    host: str = "113.57.110.35",
    port: int = 13276,
    timeout: int = 30
) -> Optional[str]:
    """
    异步获取 ms_token 字符串
    
    Returns:
        Optional[str]: 返回 ms_token 字符串，如果请求失败则返回 None
    """
    _, ms_token = await get_douyin_tokens_async(source_type, user_agent, host, port, timeout)
    return ms_token


async def get_multiple_signs_async(
    count: int = 1,
    source_type: str = "force",
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    **kwargs
) -> list[Optional[dict]]:
    """
    批量异步获取多个签名数据
    
    Args:
        count (int): 需要获取的签名数量
        source_type (str): 来源类型
        user_agent (str): 用户代理字符串
        **kwargs: 其他传递给 get_douyin_tokens_async 的参数
    
    Returns:
        list[Optional[dict]]: 签名数据列表
    """
    tasks = []
    for _ in range(count):
        task = get_douyin_tokens_async(
            source_type=source_type,
            user_agent=user_agent,
            **kwargs
        )
        tasks.append(task)
    
    # 并发执行所有任务
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理异常结果
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            print(f"批量请求中的异常: {result}")
            processed_results.append(None)
        else:
            a_bogus, ms_token = result
            if a_bogus and ms_token:
                processed_results.append({
                    "status_code": 0,
                    "data": {
                        "a_bogus": a_bogus,
                        "ms_token": ms_token
                    },
                    "msg": "操作成功"
                })
            else:
                processed_results.append(None)
    
    return processed_results


def get_a_bogus(user_agent: str = None) -> Optional[str]:
    """
    同步便捷方法：直接获取 a_bogus 签名字符串
    
    Args:
        user_agent (str): 可选的用户代理字符串
    
    Returns:
        Optional[str]: a_bogus 签名字符串，失败时返回 None
    """
    kwargs = {}
    if user_agent:
        kwargs['user_agent'] = user_agent
        
    result = get_douyin_sign(**kwargs)
    if result and result.get('status_code') == 0:
        return result.get('data', {}).get('a_bogus')
    return None


def get_ms_token(user_agent: str = None) -> Optional[str]:
    """
    同步便捷方法：直接获取 ms_token 字符串
    
    Args:
        user_agent (str): 可选的用户代理字符串
    
    Returns:
        Optional[str]: ms_token 字符串，失败时返回 None
    """
    kwargs = {}
    if user_agent:
        kwargs['user_agent'] = user_agent
        
    result = get_douyin_sign(**kwargs)
    if result and result.get('status_code') == 0:
        return result.get('data', {}).get('ms_token')
    return None


async def test_async_functions():
    """
    测试异步功能
    """
    # print("=== 异步获取 a_bogus 和 ms_token ===")
    # a_bogus = await get_a_bogus_async()
    # ms_token = await get_ms_token_async()
    
    # print(f"a_bogus: {a_bogus}")
    # print(f"ms_token: {ms_token}")
    
    print("\n=== 同时获取a_bogus/ms_token ===")
    a_bogus, ms_token = await get_douyin_tokens_async()
    print(f"a_bogus: {a_bogus}")
    print(f"ms_token: {ms_token}")
    
    # print("\n=== 批量获取测试 ===")
    # import time
    # start_time = time.time()
    # results = await get_multiple_signs_async(count=2)
    # end_time = time.time()
    
    # print(f"批量获取2个签名耗时: {end_time - start_time:.2f}秒")
    # for i, result in enumerate(results, 1):
    #     if result:
    #         data = result.get('data', {})
    #         print(f"签名{i}: a_bogus={data.get('a_bogus')[:20]}..., ms_token={data.get('ms_token')[:20]}...")
    #     else:
    #         print(f"签名{i}: 获取失败")


if __name__ == "__main__":
    import time
    
    print("=== 抖音签名获取工具（简化版） ===")
    asyncio.run(test_async_functions())
    
    # print("\n=== 使用说明 ===")
    # print("1. 异步获取单个字段: await get_a_bogus_async() 或 await get_ms_token_async()")
    # print("2. 异步同时获取: await get_douyin_tokens_async()")
    # print("3. 批量获取: await get_multiple_signs_async(count=N)")