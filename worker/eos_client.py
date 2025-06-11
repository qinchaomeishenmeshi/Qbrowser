import asyncio
import json
from typing import Dict, Any

from datetime import datetime, timedelta
import aiohttp

from browser.browser_operator import browser_operator, BrowserOperator, SITE_CONFIGS
from utils.common_logger import get_logger
from utils.common_response import PublicResponse


logger = get_logger(__name__)

# 常量定义
DEFAULT_VISIBILITY = 2
MAX_RETRY_COUNT = 1
RETRY_DELAY = 1  # 秒


def format_data(data, user_name="", buyin_account_id=""):
    """格式化直播复盘数据，将前端字段转换为API所需格式"""
    data_result = data.get("data", [])
    formatted_result = []
    
    if data_result and len(data_result) > 0:
        for item in data_result:
            # 按照JS代码的字段映射格式化数据
            formatted_item = {
                "eosLiveId": item.get("room_id", ""),  # 直播间ID
                "roomTitle": item.get("room_title", ""),  # 直播名称
                "liveStartTime": item.get("live_start_time", ""),  # 直播开始时间
                "liveEndTime": item.get("live_end_time", ""),  # 直播结束时间
                "liveDurationTime": item.get("live_duration_time", 0),  # 直播时长
                "orderMoney": item.get("order_money", 0),  # 成交金额
                "orderCnt": item.get("order_cnt", 0),  # 成交订单数
                "watchUv": item.get("watch_uv", 0),  # 累计观看人数
                "dyAccountNo": buyin_account_id,  # 抖音账号
                "dyRoomName": user_name  # 直播间名称
            }
            formatted_result.append(formatted_item)
   
    return {
        "dyAccountNo": buyin_account_id,
        "dyRoomName": user_name,
        "dataResult": formatted_result,
    }


def format_punish_data(data, user_name="", buyin_account_id=""):
    """格式化违规记录数据，将前端字段转换为API所需格式"""
    data_result = data.get("data", [])
    formatted_result = []
    
    if data_result and len(data_result) > 0:
        for item in data_result:
            # 按照JS代码的字段映射格式化数据
            formatted_item = {
                "violationReason": item.get("violation_reason", ""),  # 违规原因
                "violationTime": item.get("time", ""),  # 违规时间
                "punishmentType": item.get("punish_result", ""),  # 处罚类型
                "dyAccountNo": buyin_account_id,  # 抖音账号
                "name": user_name  # 直播间名称
            }
            formatted_result.append(formatted_item)
   
    return {
        "dyAccountNo": buyin_account_id,
        "dyRoomName": user_name,
        "dataResult": formatted_result,
    }


class LivingClient:
    def __init__(self, ):
        self.get_user_url = "https://eos.douyin.com/data/life/live/user/info/v1/"
        self.live_room_list_url = "https://eos.douyin.com/life/api/live_screen/v4/replay/live_room_list"
 

    @staticmethod
    async def _get_cookies_for_user(user_id: str,site_key='eos') -> Dict[str, str]:
        """
        从 mapping 中提取指定 user_id 的 cookies 列表，并转换为 requests 可用的 dict
        确保包含所有必要的认证和会话 cookies
        """
        cookies_list = await browser_operator.get_user_cookies(user_id,site_key)
        
        # 处理不同的 cookies 数据格式
        cookies_dict = {}
        if cookies_list is None:
            logger.warning(f"用户 {user_id} 的 cookies 为空")
            return cookies_dict
            
        if isinstance(cookies_list, dict):
            # 如果已经是字典格式，直接使用
            cookies_dict = cookies_list
        elif isinstance(cookies_list, list):
            # DrissionPage cookies 格式为 dict 列表，包含 name 和 value
            cookies_dict = {
                c["name"]: c["value"] for c in cookies_list 
                if isinstance(c, dict) and "name" in c and "value" in c
            }
        else:
            logger.error(f"用户 {user_id} 的 cookies 格式不支持，类型: {type(cookies_list)}")
            return cookies_dict
        
        # 记录缺失的关键 cookies
        missing_cookies = [cookie for cookie in SITE_CONFIGS[site_key]['required_cookies'] if cookie not in cookies_dict]
        if missing_cookies:
            logger.warning(f"用户 {user_id} 缺失关键 cookies: {missing_cookies}")
            logger.info(f"当前可用 cookies: {list(cookies_dict.keys())}")
        
        return cookies_dict

    @staticmethod
    async def _get_headers_for_user(user_id: str,site_key='eos') -> Dict[str, Any]:
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
            "referer": "https://eos.douyin.com/livesite/live/history?tab=diagnosis",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',  
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36", 
            "x-secsdk-csrf-token":""
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
        """EOS获取直播间用户信息"""
        try:
            cookies = await self._get_cookies_for_user(user_id)
            headers = await self._get_headers_for_user(user_id)
            logger.info(f"EOS发送请求：{self.get_user_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.get_user_url,  cookies=cookies, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as e:
            logger.error(f"EOS获取直播间用户信息失败: {e}")
            return {"code": -1, "msg": f"EOS获取直播间用户信息失败: {str(e)}"}

    async def get_live_room_list(self, user_id: str):
        """获取直播复盘列表"""
        try:
            cookies = await self._get_cookies_for_user(user_id)
            headers = await self._get_headers_for_user(user_id)
            # —— 动态计算四个日期 ——
            
            today = datetime.now()
            period_days = 30  # 周期天数
            fmt = lambda d: d.strftime('%Y-%m-%d')
            
            # end_date = 今天
            end_date = fmt(today)
            
            # begin_date = 今天往前推 (period_days - 1) 天
            begin = today - timedelta(days=period_days - 1)
            begin_date = fmt(begin)
            
            # compare_end_date = 统计开始前一天
            compare_end_date = fmt(begin - timedelta(days=1))
            
            # compare_begin_date = 再往前推30天
            compare_begin_date = fmt(begin - timedelta(days=period_days))
            json_data = {
                "begin_date": begin_date,  # 统计时间开始
                "end_date": end_date,  # 统计时间结束
                "compare_begin_date": compare_begin_date,  # 对比时间开始
                "compare_end_date": compare_end_date,  # 对比时间结束
                "user_id": "1258293549605997"  # 固定值
            }

            logger.info(f"发送请求：{self.live_room_list_url} **** json_data={json_data}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.live_room_list_url, json=json_data, cookies=cookies, headers=headers
                ) as resp:
                    logger.info(f"resp={resp}")
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as e:
            logger.error(f"获取直播商品列表失败: {e}")
            return {"code": -1, "msg": f"获取直播商品列表失败: {str(e)}"}

    async def get_replay_punish_list(self, user_id: str):
        """获取直播违规记录列表"""
        try:
            cookies = await self._get_cookies_for_user(user_id)
            headers = await self._get_headers_for_user(user_id)
            
            # —— 动态计算四个日期 ——
            today = datetime.now()
            period_days = 30  # 周期天数
            fmt = lambda d: d.strftime('%Y-%m-%d')
            
            # end_date = 今天
            end_date = fmt(today)
            
            # begin_date = 今天往前推 (period_days - 1) 天
            begin = today - timedelta(days=period_days - 1)
            begin_date = fmt(begin)
            
            # compare_end_date = end_date (与JS逻辑保持一致)
            compare_end_date = end_date
            
            # compare_begin_date = begin_date (与JS逻辑保持一致)
            compare_begin_date = begin_date
            
            json_data = {
                "user_id": "1258293549605997",  # 固定值
                "begin_date": begin_date,
                "end_date": end_date,
                "compare_begin_date": compare_begin_date,
                "compare_end_date": compare_end_date
            }
            
            punish_list_url = "https://eos.douyin.com/life/api/live_screen/v4/replay/punish_list"
            logger.info(f"发送请求：{punish_list_url} **** json_data={json_data}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    punish_list_url, json=json_data, cookies=cookies, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    return await resp.json()
                    
        except Exception as e:
            logger.error(f"获取直播违规记录失败: {e}")
            return {"code": -1, "msg": f"获取直播违规记录失败: {str(e)}", "data": []}


async def save_live_room_list_fn(data):
    """
    保存直播复盘数据到后端系统
    
    :param data: 直播复盘数据，包含直播回放相关信息
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
        result = await default_api_client.sync_live_room_list(data)
        
        # 检查响应结果
        if result.get("code") == 0 or result.get("code") == 200:
            logger.info("eos直播复盘数据保存成功")
            return True
        else:
            logger.error(f"eos直播复盘数据保存失败: {result.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        logger.error(f"保存eos直播复盘数据时发生异常: {e}", exc_info=True)
        return False


async def save_punish_list_fn(data):
    """
    保存违规记录数据到后端系统
    按照前端逐条保存的方式，每次保存单个违规记录
    
    :param data: 违规记录数据，包含违规相关信息
    :return: 保存结果，成功返回True，失败返回False
    """
    from utils.api_client import default_api_client
    
    try:
        # 获取账号信息（模拟前端从localStorage获取的数据）
        # 这里需要从data中提取或者从其他地方获取账号信息
        dy_account_no = None
        dy_room_name = None
        
        # 尝试从data中提取账号信息
        if data and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict) and 'dataResult' in first_item:
                # 如果有dataResult，可能包含账号信息
                pass
        
        # 修改data数据结构，将所有dataResult的内容合并到一个大数组中
        flattened_data = []
        for item in data:
            data_result = item.get("dataResult", [])
            flattened_data.extend(data_result)
        
        logger.info(f"准备保存 {len(flattened_data)} 条违规记录")
        
        # 按照前端方式逐条保存违规记录
        success_count = 0
        failed_count = 0
        
        for violation_item in flattened_data:
            try:
                # 按照前端格式构造单条记录参数
                params = {
                    "violationReason": violation_item.get("violationReason", ""),
                    "violationTime": violation_item.get("violationTime", ""),
                    "punishmentType": violation_item.get("punishmentType", ""),
                    "dyAccountNo": violation_item.get("dyAccountNo"),
                    "name": violation_item.get("name")
                }

                logger.info(f"保存单条违规记录参数: {params}")
                
                # 调用后端接口保存单条记录
                result = await default_api_client.sync_punish_list(params)
                
                # 检查响应结果
                if result.get("code") == 0 or result.get("code") == 200:
                    success_count += 1
                    logger.info(f"违规记录保存成功: {violation_item.get('violation_reason', '')}")
                else:
                    failed_count += 1
                    logger.error(f"违规记录保存失败: {result.get('msg', '未知错误')}, 记录: {violation_item}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"单条违规记录保存异常: {e}, 记录: {violation_item}")
        
        logger.info(f"违规记录保存完成: 成功 {success_count} 条, 失败 {failed_count} 条")
        
        # 如果有成功保存的记录就认为整体成功
        return success_count > 0
            
    except Exception as e:
        logger.error(f"保存eos违规记录数据时发生异常: {e}", exc_info=True)
        return False


async def get_live_room_list_main(data) -> PublicResponse:
    """批量直播复盘入口 (串行执行)"""
    logger.info(f"批量直播复盘入口: {data}")

    # 分割用户ID列表
    device_no_list = data.get("deviceNoList", "").split(",")
    logger.info("准备抓取cookies")
    await BrowserOperator().attach_get_cookies(user_ids=device_no_list, site_key="eos")
    logger.info("抓取cookies完成")

    client = LivingClient()
    response_json_data = []

    # 串行执行每个用户的任务，避免并发请求触发风控
    for user_id in device_no_list:
        logger.info(f"开始处理用户 {user_id} 的直播复盘创建请求")
        result = await process_user_history_live(client, user_id)
        logger.info(f"处理结果[{user_id}] ：", result)
        response_json_data.append(result)
        # 每个用户处理完成后等待一段时间，降低API调用频率
        await asyncio.sleep(1.5)  # 设置1.5秒的间隔，可根据实际情况调整

    logger.info(f"批量直播复盘结果: {response_json_data}")
    # # 调用api接口传递给后端
    save_success = await save_live_room_list_fn(response_json_data)
    logger.info("保存结果：", save_success)
    
    return PublicResponse.success(data=response_json_data, message="操作成功")


async def get_replay_punish_list_main(data) -> PublicResponse:
    """批量违规记录入口 (串行执行)"""
    logger.info(f"批量违规记录入口: {data}")

    # 分割用户ID列表
    device_no_list = data.get("deviceNoList", "").split(",")
    logger.info("准备抓取cookies")
    await BrowserOperator().attach_get_cookies(user_ids=device_no_list, site_key="eos")
    logger.info("抓取cookies完成")

    client = LivingClient()
    response_json_data = []

    # 串行执行每个用户的任务，避免并发请求触发风控
    for user_id in device_no_list:
        logger.info(f"开始处理用户 {user_id} 的违规记录请求")
        result = await process_user_punish_list(client, user_id)
        logger.info(f"处理结果[{user_id}] ：", result)
        response_json_data.append(result)
        # 每个用户处理完成后等待一段时间，降低API调用频率
        await asyncio.sleep(1.5)  # 设置1.5秒的间隔，可根据实际情况调整

    logger.info(f"批量违规记录结果: {response_json_data}")
    # 调用api接口传递给后端
    save_success = await save_punish_list_fn(response_json_data)
    logger.info("保存结果：", save_success)
    
    return PublicResponse.success(data=response_json_data, message="操作成功")


async def process_user_history_live(client, user_id):
    """处理单个用户的直播复盘创建流程"""

    # 获取商品列表
    result = await client.get_index_user(user_id)
    code = int(result.get("status_code", -1))

    logger.info("获取直播间用户信息结果: ", result)
    user_name = result.get("username", "")
    douyin_unique_id = result.get("douyin_unique_id", "")
    logger.info('douyin_unique_id: ',douyin_unique_id)
    if code != 0 or douyin_unique_id == "":
        data = format_data(result, user_name, douyin_unique_id)
        return {**data, "user_id": user_id}
    history_live_result = await client.get_live_room_list(user_id)
    logger.info("获取直播间复盘列表结果: ", history_live_result)
    # 处理商品列表
    format_data_result = format_data(history_live_result, user_name, douyin_unique_id)
    logger.info(f"处理后的直播复盘数据==format_data: {format_data_result}")
    return {**format_data_result, "user_id": user_id}


async def process_user_punish_list(client, user_id):
    """处理单个用户的违规记录获取流程"""

    # 获取用户信息
    result = await client.get_index_user(user_id)
    code = int(result.get("status_code", -1))

    logger.info("获取直播间用户信息结果: ", result)
    user_name = result.get("username", "")
    logger.info('user_name: ',user_name)
    douyin_unique_id = result.get("douyin_unique_id", "")
    logger.info('douyin_unique_id: ',douyin_unique_id)
    
    if code != 0 or douyin_unique_id == "":
        data = format_punish_data({"data": []}, user_name, douyin_unique_id)
        return {**data, "user_id": user_id}
    
    # 获取违规记录列表
    punish_result = await client.get_replay_punish_list(user_id)
    logger.info("获取违规记录列表结果: ", punish_result)
    
    # 处理违规记录列表
    format_data_result = format_punish_data(punish_result, user_name, douyin_unique_id)
    logger.info(f"处理后的违规记录数据==format_punish_data: {format_data_result}")
    return {**format_data_result, "user_id": user_id}




# 示例使用
if __name__ == "__main__":
    sample_data = {
        "deviceNoList": "test003,test004",
    }

    # 测试直播复盘数据获取
    logger.info("=== 测试直播复盘数据获取 ===")
    asyncio.run(get_live_room_list_main(sample_data))
    
    # 测试违规记录数据获取
    logger.info("\n=== 测试违规记录数据获取 ===")
    asyncio.run(get_replay_punish_list_main(sample_data))
