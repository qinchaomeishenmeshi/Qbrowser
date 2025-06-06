import asyncio
import json
from typing import Dict, Any

import aiohttp

from browser.browser_operator import browser_operator, BrowserOperator
from utils.common_logger import get_logger
from utils.common_response import PublicResponse
from utils.util import get_date_range
from utils.get_ab import get_douyin_tokens_async

logger = get_logger(__name__)

# 常量定义
DEFAULT_VISIBILITY = 2
MAX_RETRY_COUNT = 1
RETRY_DELAY = 1  # 秒


def format_data(data, user_name="", buyin_account_id=""):
    """格式化直播间明细数据，将前端字段转换为API所需格式"""
    # 将user_name 和buyin_account_id  放进data.get("data_result", [])的每个item中。
    data_result = data.get("data_result", [])
    if data_result and len(data_result) > 0:
        for item in data_result:
            item["buyinAccountId"] = buyin_account_id
            item["dyAccountName"] = user_name

    return {
        "buyinAccountId": buyin_account_id,
        "dyAccountName": user_name,
        "dataResult": data_result,
    }


class LivingClient:
    def __init__(self, ):
        self.get_user_url = "https://buyin.jinritemai.com/index/getUser"
        self.history_live_url = "https://buyin.jinritemai.com/compass_api/content_live/author/live_detail/history_live"
        self.core_data_url = "https://compass.jinritemai.com/compass_api/author/live/live_screen/core_data"

    @staticmethod
    async def _get_cookies_for_user(user_id: str,site_key='baiying') -> Dict[str, str]:
        """
        从 mapping 中提取指定 user_id 的 cookies 列表，并转换为 requests 可用的 dict
        确保包含所有必要的认证和会话 cookies
        """
        cookies_list = await browser_operator.get_user_cookies(user_id,site_key)
        # DrissionPage cookies 格式为 dict 列表，包含 name 和 value
        cookies_dict = {
            c["name"]: c["value"] for c in cookies_list if "name" in c and "value" in c
        }
        
        # 确保包含关键的认证和会话 cookies（参考 core_data.py 中的成功配置）
        required_cookies = [
            'passport_csrf_token', 'passport_csrf_token_default', 'is_staff_user',
            's_v_web_id', 'ttwid', 'uid_tt', 'uid_tt_ss', 'sid_tt', 'sessionid', 
            'sessionid_ss', 'odin_tt', 'BUYIN_SASID', 'ucas_c0_compass', 
            'ucas_c0_ss_compass', 'sid_guard', 'sid_ucp_v1', 'ssid_ucp_v1',
            'LUOPAN_DT', 'COMPASS_LUOPAN_DT', 'Hm_lvt_b6520b076191ab4b36812da4c90f7a5e',
            'Hm_lpvt_b6520b076191ab4b36812da4c90f7a5e', 'HMACCOUNT', 'csrf_session_id'
        ]
        
        # 记录缺失的关键 cookies
        missing_cookies = [cookie for cookie in required_cookies if cookie not in cookies_dict]
        if missing_cookies:
            logger.warning(f"用户 {user_id} 缺失关键 cookies: {missing_cookies}")
            logger.info(f"当前可用 cookies: {list(cookies_dict.keys())}")
        
        return cookies_dict

    @staticmethod
    async def _get_headers_for_user(user_id: str,site_key='baiying') -> Dict[str, Any]:
        """
        从 mapping 中提取指定 user_id 的 headers 字段作为请求头，
        并仅保留 default_headers 中定义的键，优先使用保存的值，缺失则用默认值。
        参考 core_data.py 中成功的 headers 配置
        """
        # 默认 headers（参考 core_data.py 中的成功配置）
        default_headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "priority": "u=1, i",
            "referer": "https://buyin.jinritemai.com/dashboard/compass-home/live-list?pre_universal_page_params_id=&universal_page_params_id=31994513-4957-4b8c-8091-3f0988367d33",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',  
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36", 
        }

        saved_headers = await browser_operator.get_user_headers(user_id,site_key)
        if saved_headers is None:
            logger.warning(f"用户 {user_id} 未找到保存的 headers，使用默认配置")
            return default_headers
        
        # 只保留 default_headers 中的 key，并优先使用 saved_headers 中的值
        filtered_headers = {
            key: saved_headers.get(key, default_value)
            for key, default_value in default_headers.items()
        }
        
        # 记录关键 headers 的状态
        logger.info(f"用户 {user_id} headers 配置完成，User-Agent: {filtered_headers.get('user-agent', 'N/A')}")

        return filtered_headers

    async def get_index_user(self, user_id: str):
        """获取直播间用户信息"""
        try:
            cookies = await self._get_cookies_for_user(user_id)
            headers = await self._get_headers_for_user(user_id)

            params = {
                "verifyFp": cookies.get("s_v_web_id", ""),
                "fp": cookies.get("s_v_web_id", ""),
            }

            logger.info(f"发送请求：{self.get_user_url} params={params}")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.get_user_url, params=params, cookies=cookies, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as e:
            logger.error(f"获取直播间用户信息失败: {e}")
            return {"code": -1, "msg": f"获取直播间用户信息失败: {str(e)}"}

    async def get_history_live_list(self, user_id: str):
        """获取直播商品列表"""
        try:
            cookies = await self._get_cookies_for_user(user_id)
            headers = await self._get_headers_for_user(user_id)
            # 获取近7天的日期范围
            # 21 - 7天 / 23 - 30天 / 24 - 90天 / 4 - 自然月
            result = get_date_range(days=7, include_today=True)
            date_type = '21'
            params = {
                "is_asc": "false",
                "page_no": '1',
                "page_size": "10",
                "date_type": date_type,
                "begin_date": result['begin_date'],
                "begin_date_format": result['begin_date_format'],
                "index_selected": "",
            }

            logger.info(f"发送请求：{self.history_live_url} params={params}")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.history_live_url, params=params, cookies=cookies, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as e:
            logger.error(f"获取直播商品列表失败: {e}")
            return {"code": -1, "msg": f"获取直播商品列表失败: {str(e)}"}

    async def get_core_data(self, user_id: str, room_id: str):
        """获取直播间详情数据"""
        try:
            # 再获取直播间详情数据 - 使用 screen 站点的 cookies（包含 LUOPAN_DT）
            cookies = await self._get_cookies_for_user(user_id, 'screen')
            headers = await self._get_headers_for_user(user_id, 'screen')
            a_bogus, ms_token = await get_douyin_tokens_async()
            headers['referer'] = f'https://compass.jinritemai.com/screen/live/talent?live_room_id={room_id}'
            
            # 检查关键认证 cookies 是否存在
            critical_cookies = ['COMPASS_LUOPAN_DT', 'LUOPAN_DT']
            missing_critical = [cookie for cookie in critical_cookies if not cookies.get(cookie)]
            if missing_critical:
                logger.error(f"用户 {user_id} 缺失关键认证 cookies: {missing_critical}")
                logger.error(f"这可能导致请求失败，请检查浏览器登录状态")

            params = {
                'room_id': room_id,
                'index_selected': 'gpm,pay_ucnt,pay_combo_cnt,watch_pay_ucnt_ratio,product_click_pay_ucnt_ratio,online_user_cnt,live_show_watch_cnt_ratio,avg_watch_duration,watch_interact_ucnt_ratio,follow_anchor_ucnt',
                # '_lid': cookies.get('_lid', '174900436'),  # 添加_lid参数，从cookies获取或使用默认值
                'verifyFp': cookies.get('s_v_web_id', ''),
                'fp': cookies.get('s_v_web_id', ''),
                'msToken': ms_token, 
                'a_bogus': a_bogus,
            }

            logger.info(f"用户 {user_id} 请求 room_id: {room_id}")
            logger.info(f"关键 cookies 状态: COMPASS_LUOPAN_DT={cookies.get('COMPASS_LUOPAN_DT')}, LUOPAN_DT={cookies.get('LUOPAN_DT')}")
            logger.info(f"请求参数: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.core_data_url, params=params, cookies=cookies, headers=headers
                ) as resp:
                    logger.info(f"响应状态码: {resp.status}")
                    if resp.status != 200:
                        response_text = await resp.text()
                        logger.error(f"请求失败，响应内容: {response_text}")
                    resp.raise_for_status()
                    result = await resp.json()
                    logger.info(f"请求成功，响应数据结构: {type(result)} - {list(result.keys()) if isinstance(result, dict) else 'non-dict'}")
                    return result
        except Exception as e:
            logger.error(f"获取直播间详情数据失败: {e}")
            return {"code": -1, "msg": f"获取直播间详情数据失败: {str(e)}"}


async def save_history_list_fn(data):
    """
    保存直播间明细数据到后端系统
    
    :param data: 直播间明细数据，包含直播回放相关信息
    :return: 保存结果，成功返回True，失败返回False
    """
    from utils.api_client import default_api_client
    
    try:

        # 修改data数据结构，将所有dataResult的内容合并到一个大数组中
        flattened_data = []
        for item in data:
            data_result = item.get("dataResult", [])
            flattened_data.extend(data_result)
        data = flattened_data
        logger.info(f"保存的数据内容: {data}")
        # 调用后端接口同步直播回放数据
        result = await default_api_client.sync_live_replay_data(data)
        
        # 检查响应结果
        if result.get("code") == 0 or result.get("code") == 200:
            logger.info("直播间明细数据保存成功")
            return True
        else:
            logger.error(f"直播间明细数据保存失败: {result.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        logger.error(f"保存直播间明细数据时发生异常: {e}", exc_info=True)
        return False


async def save_core_data_fn(live_id: str, core_data: dict, other_data: str) -> bool:
    """
    保存直播间大屏数据到后端系统
    
    :param live_id: 直播间ID
    :param core_data: 核心数据
    :param other_data: 其他数据（JSON字符串格式）
    :return: 保存结果，成功返回True，失败返回False
    """
    from utils.api_client import default_api_client
    
    try:
        # 构造请求数据，参考JavaScript代码中的postData结构
        post_data = {
            "live_id": live_id,
            "core_data": core_data,
            "other_data": other_data
        }
        
        logger.info(f"保存直播间大屏数据: live_id={live_id}")
        logger.debug(f"保存的数据内容: {post_data}")
        
        # 调用后端接口同步直播间大屏数据
        result = await default_api_client.sync_live_core_data(post_data)
        
        # 检查响应结果
        if result.get("code") == 0 or result.get("code") == 200:
            logger.info(f"直播间大屏数据保存成功: live_id={live_id}")
            return True
        else:
            logger.error(f"直播间大屏数据保存失败: {result.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        logger.error(f"保存直播间大屏数据时发生异常: {e}", exc_info=True)
        return False


async def get_core_data_for_live_rooms(response_json_data):
    """
    在保存直播间明细数据成功后，获取每个直播间的大屏明细数据
    
    :param response_json_data: 直播间明细数据列表
    """
    logger.info("开始获取直播间大屏明细数据")
    
    for user_data in response_json_data:
        user_id = user_data.get("user_id")
        data_result = user_data.get("dataResult", [])
        
        if not user_id or not data_result:
            logger.warning(f"用户 {user_id} 数据不完整，跳过大屏明细获取")
            continue
            
        # 遍历每个直播间数据
        for live_data in data_result:
            room_id = live_data.get("operation",{}).get("live_id")
            if not room_id:
                logger.warning(f"用户 {user_id} 的直播间数据缺少 room_id，跳过")
                continue
                
            try:
                logger.info(f"获取用户 {user_id} 直播间 {room_id} 的大屏明细数据")
                
                # 调用 get_core_data_main 获取大屏明细
                core_data_request = {
                    "userId": user_id,
                    "roomId": room_id
                }
                
                core_data_response = await get_core_data_main(core_data_request)
                logger.info(f"get_core_data_main 响应数据: {core_data_response}")
                if core_data_response.get('status') == 'success':
                    logger.info(f"成功获取用户 {user_id} 直播间 {room_id} 的大屏明细数据")
                    
                    # 提取核心数据并保存到后端
                    response_data = core_data_response.get('data',{}).get('data',{})
                    if response_data and isinstance(response_data, dict):
                        core_data = response_data.get('core_data', {})
                        other_data = json.dumps(response_data, ensure_ascii=False)
                        
                        # 调用保存方法
                        save_success = await save_core_data_fn(room_id, core_data, other_data)
                        if save_success:
                            logger.info(f"直播间 {room_id} 大屏数据保存成功")
                        else:
                            logger.error(f"直播间 {room_id} 大屏数据保存失败")
                    else:
                        logger.warning(f"直播间 {room_id} 返回数据格式异常，无法保存")
                else:
                    logger.error(f"获取用户 {user_id} 直播间 {room_id} 大屏明细数据失败: {core_data_response.message}")
                    
                
                
            except Exception as e:
                logger.error(f"获取用户 {user_id} 直播间 {room_id} 大屏明细数据时发生异常: {e}", exc_info=True)
                continue
    
    logger.info("所有直播间大屏明细数据获取完成")


async def get_history_live_main(data) -> PublicResponse:
    """批量直播间明细入口 (串行执行)"""
    logger.info(f"批量直播间明细入口: {data}")

    # 分割用户ID列表
    device_no_list = data.get("deviceNoList", "").split(",")
    print("准备抓取cookies")
    await BrowserOperator().attach_get_cookies(user_ids=device_no_list)
    print("抓取cookies完成")

    client = LivingClient()
    response_json_data = []

    # 串行执行每个用户的任务，避免并发请求触发风控
    for user_id in device_no_list:
        logger.info(f"开始处理用户 {user_id} 的直播间明细创建请求")
        result = await process_user_history_live(client, user_id)
        print(f"处理结果[{user_id}] ：", result)
        response_json_data.append(result)
        # 每个用户处理完成后等待一段时间，降低API调用频率
        await asyncio.sleep(1.5)  # 设置1.5秒的间隔，可根据实际情况调整

    logger.info(f"批量直播间明细结果: {response_json_data}")
    # 调用api接口传递给后端
    save_success = await save_history_list_fn(response_json_data)
    
    # 如果保存成功，获取每个直播间的大屏明细数据
    if save_success:
        await get_core_data_for_live_rooms(response_json_data)
    
    return PublicResponse.success(data=response_json_data, message="操作成功")


async def process_user_history_live(client, user_id):
    """处理单个用户的直播间明细创建流程"""

    # 获取商品列表
    result = await client.get_index_user(user_id)
    code = int(result.get("code", -1))

    print("获取直播间用户信息结果: ", result)
    user_name = result.get("data", {}).get("user_name", "")
    buyin_account_id = result.get("data", {}).get("buyin_account_id", "")
    if code != 0 or buyin_account_id == "":
        data = format_data(result.get("data", {}), user_name, buyin_account_id)
        return {**data, "user_id": user_id}
    history_live_result = await client.get_history_live_list(user_id)
    # 处理商品列表
    format_data_result = format_data(history_live_result.get("data", {}), user_name, buyin_account_id)
    logger.info(f"处理后的直播间明细数据==format_data: {format_data_result}")
    return {**format_data_result, "user_id": user_id}


async def get_core_data_main(data) -> PublicResponse:
    """直播间大屏明细入口"""
    logger.info(f"直播间大屏明细入口: {data}")

    print("准备抓取cookies")
    await BrowserOperator().attach_get_cookies(user_ids=[data.get("userId")],site_key="screen")
    print("抓取cookies完成")
    # 每个直播间处理完成后等待一段时间，降低API调用频率
    await asyncio.sleep(2)  # 设置2秒的间隔

    client = LivingClient()
    response_json_data = await client.get_core_data(data.get("userId"), data.get("roomId"))

    logger.info(f"直播间大屏明细结果: {response_json_data}")
    return PublicResponse.success(data=response_json_data, message="操作成功")


# 示例使用
if __name__ == "__main__":
    sample_data = {
        "deviceNoList": "test003,test004",
    }

    asyncio.run(get_history_live_main(sample_data))
