import asyncio
from typing import Dict, Any

import requests

from browser.browser_operator import browser_operator, BrowserOperator
from utils.common_logger import get_logger
from utils.common_response import PublicResponse
from utils.util import get_date_range

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
    async def _get_cookies_for_user(user_id: str) -> Dict[str, str]:
        """
        从 mapping 中提取指定 user_id 的 cookies 列表，并转换为 requests 可用的 dict
        """
        cookies_list = await browser_operator.get_user_cookies(user_id)
        # DrissionPage cookies 格式为 dict 列表，包含 name 和 value
        cookies_dict = {
            c["name"]: c["value"] for c in cookies_list if "name" in c and "value" in c
        }
        return cookies_dict

    @staticmethod
    async def _get_headers_for_user(user_id: str) -> Dict[str, Any]:
        """
        从 mapping 中提取指定 user_id 的 headers 字段作为请求头，
        并仅保留 default_headers 中定义的键，优先使用保存的值，缺失则用默认值。
        """
        # 默认 headers
        default_headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "priority": "u=1, i",
            "referer": "https://buyin.jinritemai.com/dashboard/compass-home/live-list?pre_universal_page_params_id=&universal_page_params_id=31994513-4957-4b8c-8091-3f0988367d33",
            "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        }

        saved_headers = await browser_operator.get_user_headers(user_id)
        if saved_headers is None:
            return {}
        # 只保留 default_headers 中的 key，并优先使用 saved_headers 中的值
        filtered_headers = {
            key: saved_headers.get(key, default_value)
            for key, default_value in default_headers.items()
        }

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
            resp = requests.get(
                self.get_user_url, params=params, cookies=cookies, headers=headers
            )
            resp.raise_for_status()
            return resp.json()
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
            resp = requests.get(
                self.history_live_url, params=params, cookies=cookies, headers=headers
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"获取直播商品列表失败: {e}")
            return {"code": -1, "msg": f"获取直播商品列表失败: {str(e)}"}

    async def get_core_data(self, user_id: str, room_id: str):
        """获取直播间详情数据"""
        try:
            cookies = await self._get_cookies_for_user(user_id)
            headers = await self._get_headers_for_user(user_id)
            headers['referer'] = f'https://compass.jinritemai.com/screen/live/talent?live_room_id={room_id}'
            params = {
                'room_id': room_id,
                'index_selected': 'gpm,pay_ucnt,pay_combo_cnt,watch_pay_ucnt_ratio,product_click_pay_ucnt_ratio,online_user_cnt,live_show_watch_cnt_ratio,avg_watch_duration,watch_interact_ucnt_ratio,follow_anchor_ucnt',
                "verifyFp": cookies.get("s_v_web_id", ""),
                "fp": cookies.get("s_v_web_id", ""),

            }

            logger.info(f"发送请求：{self.core_data_url} params={params}")
            resp = requests.get(
                self.core_data_url, params=params, cookies=cookies, headers=headers
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"获取直播间详情数据失败: {e}")
            return {"code": -1, "msg": f"获取直播间详情数据失败: {str(e)}"}


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
    return PublicResponse(status="success", message="操作成功", data=response_json_data)


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
    await BrowserOperator().attach_get_cookies(user_ids=[data.get("userId")])
    print("抓取cookies完成")

    client = LivingClient()
    response_json_data = await client.get_core_data(data.get("userId"), data.get("roomId"))

    logger.info(f"直播间大屏明细结果: {response_json_data}")
    return PublicResponse(status="success", message="操作成功", data=response_json_data)


# 示例使用
if __name__ == "__main__":
    sample_data = {
        "deviceNoList": "wh001,wh002,wh003",
    }

    asyncio.run(get_history_live_main(sample_data))
