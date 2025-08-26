import asyncio
import json
import time
from typing import Dict, Any, Optional, Tuple

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


def format_data(data: Dict[str, Any], user_name: str = "", buyin_account_id: str = "") -> Dict[str, Any]:
    """格式化直播间明细数据，将前端字段转换为API所需格式

    参数:
        data: 接口返回的原始数据字典
        user_name: 抖音账号名称
        buyin_account_id: 账号ID
    返回:
        组装后的规范数据结构，便于后端入库
    """
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
    """直播业务客户端

    - 负责调用 buyin/screen 站点相关接口
    - 内置 get_index_user 结果的内存级 TTL 缓存，避免重复请求
    - 提供登录态校验方法，未登录时可早返回，减少无效请求
    """

    def __init__(self,) -> None:
        self.get_user_url = "https://buyin.jinritemai.com/index/getUser"
        self.history_live_url = "https://buyin.jinritemai.com/compass_api/content_live/author/live_detail/history_live"
        self.core_data_url = "https://compass.jinritemai.com/compass_api/author/live/live_screen/core_data"
        # 新增：用户信息结果缓存（避免重复请求 get_index_user）
        # 结构：{ user_id: {"ts": 时间戳, "data": 响应数据} }
        self._user_info_cache: Dict[str, Dict[str, Any]] = {}
        # 缓存TTL（秒），同一用户在TTL内重复请求直接命中缓存
        self._user_info_cache_ttl: int = 300

    def _get_cached_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存中的用户信息（命中且未过期则返回，否则返回None）"""
        cache_item = self._user_info_cache.get(user_id)
        if not cache_item:
            return None
        ts = cache_item.get("ts", 0)
        if time.time() - ts > self._user_info_cache_ttl:
            self._user_info_cache.pop(user_id, None)
            return None
        return cache_item.get("data")

    def _set_cached_user_info(self, user_id: str, data: Dict[str, Any]) -> None:
        """写入用户信息到缓存"""
        self._user_info_cache[user_id] = {"ts": time.time(), "data": data}

    @staticmethod
    async def _get_cookies_for_user(user_id: str, site_key: str = 'baiying') -> Dict[str, str]:
        """根据 user_id 从浏览器存储中提取指定站点的 cookies

        - 支持 list/dict 两种格式的容错
        - 记录缺失关键 cookies 的情况便于排查
        """
        cookies_list = await browser_operator.get_user_cookies(user_id, site_key)

        cookies_dict: Dict[str, str] = {}
        if cookies_list is None:
            logger.warning(f"用户 {user_id} 的 cookies 为空")
            return cookies_dict

        if isinstance(cookies_list, dict):
            cookies_dict = cookies_list
        elif isinstance(cookies_list, list):
            cookies_dict = {
                c["name"]: c["value"] for c in cookies_list
                if isinstance(c, dict) and "name" in c and "value" in c
            }
        else:
            logger.error(f"用户 {user_id} 的 cookies 格式不支持，类型: {type(cookies_list)}")
            return cookies_dict

        # 关键 cookies 提示（与项目其他模块对齐，非强制）
        required_cookies = [
            'passport_csrf_token', 'passport_csrf_token_default', 'is_staff_user',
            's_v_web_id', 'ttwid', 'uid_tt', 'uid_tt_ss', 'sid_tt', 'sessionid',
            'sessionid_ss', 'odin_tt', 'BUYIN_SASID', 'ucas_c0_compass',
            'ucas_c0_ss_compass', 'sid_guard', 'sid_ucp_v1', 'ssid_ucp_v1',
            'LUOPAN_DT', 'COMPASS_LUOPAN_DT', 'Hm_lvt_b6520b076191ab4b36812da4c90f7a5e',
            'Hm_lpvt_b6520b076191ab4b36812da4c90f7a5e', 'HMACCOUNT', 'csrf_session_id'
        ]
        missing_cookies = [cookie for cookie in required_cookies if cookie not in cookies_dict]
        if missing_cookies:
            logger.warning(f"用户 {user_id} 缺失关键 cookies: {missing_cookies}")
            logger.info(f"当前可用 cookies: {list(cookies_dict.keys())}")

        return cookies_dict

    @staticmethod
    async def _get_headers_for_user(user_id: str, site_key: str = 'baiying') -> Dict[str, Any]:
        """获取 headers 配置，优先使用保存内容，不存在时使用默认值

        只保留默认头里定义的键，降低异常概率
        """
        default_headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "priority": "u=1, i",
            "referer": "https://buyin.jinritemai.com/dashboard/compass-home/live-list",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        }

        saved_headers = await browser_operator.get_user_headers(user_id, site_key)
        if saved_headers is None:
            logger.warning(f"用户 {user_id} 未找到保存的 headers，使用默认配置")
            return default_headers

        filtered_headers = {
            key: saved_headers.get(key, default_value)
            for key, default_value in default_headers.items()
        }
        logger.info(f"用户 {user_id} headers 配置完成，User-Agent: {filtered_headers.get('user-agent', 'N/A')}")
        return filtered_headers

    async def get_index_user(self, user_id: str) -> Dict[str, Any]:
        """获取直播间用户信息（带TTL缓存，避免重复请求）"""
        cached = self._get_cached_user_info(user_id)
        if cached is not None:
            logger.debug(f"get_index_user 命中缓存: user_id={user_id}")
            return cached
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
                    data = await resp.json()
                    if isinstance(data, dict):
                        self._set_cached_user_info(user_id, data)
                    return data
        except Exception as e:
            logger.error(f"获取直播间用户信息失败: {e}")
            return {"code": -1, "msg": f"获取直播间用户信息失败: {str(e)}"}

    @staticmethod
    def _has_required_cookies(cookies: Dict[str, str], required: Optional[list] = None) -> bool:
        """校验 cookies 是否包含要求的关键字段"""
        required_set = set(required or [])
        return all(name in cookies and cookies.get(name) for name in required_set)

    async def check_login(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """登录态校验（buyin站点）

        - 先做关键 cookie 的存在性检查
        - 再通过 get_index_user 进行轻量级探测（命中缓存不会重复请求）
        返回 (是否登录, 用户信息字典)
        """
        cookies = await self._get_cookies_for_user(user_id, 'baiying')
        required = [
            'passport_csrf_token', 'sessionid', 'sessionid_ss', 'sid_tt', 'uid_tt', 'uid_tt_ss', 's_v_web_id'
        ]
        if not cookies or not self._has_required_cookies(cookies, required):
            logger.error(f"用户 {user_id} 未登录或关键cookies缺失（buyin站点），停止后续请求。现有keys={list(cookies.keys()) if cookies else []}")
            return False, {}
        try:
            probe = await self.get_index_user(user_id)
            code = int(probe.get('code', -1))
            buyin_account_id = probe.get('data', {}).get('buyin_account_id', '')
            if code != 0 or not buyin_account_id:
                logger.error(f"用户 {user_id} 登录校验失败：code={code}, buyin_account_id={buyin_account_id}")
                return False, probe if isinstance(probe, dict) else {}
            return True, probe if isinstance(probe, dict) else {}
        except Exception as e:
            logger.error(f"用户 {user_id} 登录校验异常（buyin站点）: {e}")
            return False, {}

    async def check_screen_login(self, user_id: str) -> bool:
        """大屏(screen)站点登录态校验：只做关键cookie存在性检查，缺失则早返回。"""
        cookies = await self._get_cookies_for_user(user_id, 'screen')
        critical = ['COMPASS_LUOPAN_DT', 'LUOPAN_DT']
        if not cookies or not self._has_required_cookies(cookies, critical):
            logger.error(f"用户 {user_id} 缺失screen站点关键cookies: {critical}，请先在浏览器登录大屏站点")
            return False
        return True

    async def get_history_live_list(self, user_id: str) -> Dict[str, Any]:
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

    async def get_core_data(self, user_id: str, room_id: str) -> Dict[str, Any]:
        """获取直播间详情数据（大屏screen接口）"""
        try:
            # 使用 screen 站点的 cookies（包含 LUOPAN_DT）
            cookies = await self._get_cookies_for_user(user_id, 'screen')
            headers = await self._get_headers_for_user(user_id, 'screen')
            a_bogus, ms_token = await get_douyin_tokens_async()
            headers['referer'] = f'https://compass.jinritemai.com/screen/live/talent?live_room_id={room_id}'

            critical_cookies = ['COMPASS_LUOPAN_DT', 'LUOPAN_DT']
            missing_critical = [cookie for cookie in critical_cookies if not cookies.get(cookie)]
            if missing_critical:
                logger.error(f"用户 {user_id} 缺失关键认证 cookies: {missing_critical}")
                logger.error(f"这可能导致请求失败，请检查浏览器登录状态")

            params = {
                'room_id': room_id,
                'index_selected': 'gpm,pay_ucnt,pay_combo_cnt,watch_pay_ucnt_ratio,product_click_pay_ucnt_ratio,online_user_cnt,live_show_watch_cnt_ratio,avg_watch_duration,watch_interact_ucnt_ratio,follow_anchor_ucnt',
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


async def save_history_list_fn(data: list) -> bool:
    """保存直播间明细数据到后端系统

    参数:
        data: 直播间明细数据（多个用户的结果）
    返回:
        保存是否成功
    """
    from utils.api_client import default_api_client

    try:
        # 修改data数据结构，将所有dataResult的内容合并到一个大数组中
        flattened_data = []
        for item in data:
            data_result = item.get("dataResult", [])
            flattened_data.extend(data_result)
        data_to_save = flattened_data
        logger.info(f"保存的数据内容: {data_to_save}")
        if not data_to_save:
            logger.warning("没有数据需要保存")
            return False
        result = await default_api_client.sync_live_replay_data(data_to_save)
        if result.get("code") in (0, 200):
            logger.info("直播间明细数据保存成功")
            return True
        logger.error(f"直播间明细数据保存失败: {result.get('msg', '未知错误')}")
        return False
    except Exception as e:
        logger.error(f"保存直播间明细数据时发生异常: {e}", exc_info=True)
        return False


async def save_core_data_fn(live_id: str, core_data: dict, other_data: str) -> bool:
    """保存直播间大屏数据到后端系统"""
    from utils.api_client import default_api_client
    try:
        post_data = {
            "live_id": live_id,
            "core_data": core_data,
            "other_data": other_data
        }
        logger.info(f"保存直播间大屏数据: live_id={live_id}")
        logger.debug(f"保存的数据内容: {post_data}")

        result = await default_api_client.sync_live_core_data(post_data)
        if result.get("code") in (0, 200):
            logger.info(f"直播间大屏数据保存成功: live_id={live_id}")
            return True
        logger.error(f"直播间大屏数据保存失败: {result.get('msg', '未知错误')}")
        return False
    except Exception as e:
        logger.error(f"保存直播间大屏数据时发生异常: {e}", exc_info=True)
        return False


async def get_core_data_for_live_rooms(response_json_data: list) -> None:
    """在保存直播间明细数据成功后，获取每个直播间的大屏明细数据"""
    logger.info("开始获取直播间大屏明细数据")

    for user_data in response_json_data:
        user_id = user_data.get("user_id")
        data_result = user_data.get("dataResult", [])
        if not user_id or not data_result:
            logger.warning(f"用户 {user_id} 数据不完整，跳过大屏明细获取")
            continue

        for live_data in data_result:
            room_id = live_data.get("operation", {}).get("live_id")
            if not room_id:
                logger.warning(f"用户 {user_id} 的直播间数据缺少 room_id，跳过")
                continue

            try:
                logger.info(f"获取用户 {user_id} 直播间 {room_id} 的大屏明细数据")
                core_data_request = {
                    "userId": user_id,
                    "roomId": room_id
                }
                core_data_response = await get_core_data_main(core_data_request)
                logger.info(f"get_core_data_main 响应数据: {core_data_response}")
                if core_data_response.get('status') == 'success':
                    logger.info(f"成功获取用户 {user_id} 直播间 {room_id} 的大屏明细数据")
                    response_data = core_data_response.get('data', {}).get('data', {})
                    if response_data and isinstance(response_data, dict):
                        core_data = response_data.get('core_data', {})
                        other_data = json.dumps(response_data, ensure_ascii=False)
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


async def get_history_live_main(data: Dict[str, Any]) -> PublicResponse:
    """批量直播间明细入口 (串行执行)

    - 串行处理以降低风控风险
    - 每个用户先做登录校验，未登录则早返回空数据占位
    - 透传用户信息给后续步骤，避免重复请求 get_index_user
    """
    logger.info(f"批量直播间明细入口: {data}")

    device_no_list = data.get("deviceNoList", "").split(",")
    print("准备抓取cookies")
    await BrowserOperator().attach_get_cookies(user_ids=device_no_list)
    print("抓取cookies完成")

    client = LivingClient()
    response_json_data: list = []

    for user_id in device_no_list:
        logger.info(f"开始处理用户 {user_id} 的直播间明细创建请求")
        is_logged_in, user_info = await client.check_login(user_id)
        if not is_logged_in:
            logger.error(f"用户 {user_id} 未登录或会话失效，本次明细抓取跳过网络请求。")
            empty_payload = format_data({}, user_name="", buyin_account_id="")
            response_json_data.append({**empty_payload, "user_id": user_id, "message": "未登录或会话失效"})
            await asyncio.sleep(0.5)
            continue
        result = await process_user_history_live(client, user_id, user_info=user_info)
        print(f"处理结果[{user_id}] ：", result)
        response_json_data.append(result)
        await asyncio.sleep(1.5)  # 降低API调用频率

    logger.info(f"批量直播间明细结果: {response_json_data}")
    save_success = await save_history_list_fn(response_json_data)

    if save_success:
        await get_core_data_for_live_rooms(response_json_data)

    return PublicResponse.success(data=response_json_data, message="操作成功")


async def process_user_history_live(client: LivingClient, user_id: str, user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """处理单个用户的直播间明细创建流程

    参数:
        client: LivingClient 实例
        user_id: 用户ID
        user_info: 可选，已获取的用户信息；提供则不再调用 get_index_user
    返回:
        该用户的明细数据（包含 user_id）
    """
    # 优先复用传入的用户信息，若无则查询；内部带缓存
    result = user_info if isinstance(user_info, dict) else await client.get_index_user(user_id)
    code = int(result.get("code", -1))

    print("获取直播间用户信息结果: ", result)
    user_name = result.get("data", {}).get("user_name", "")
    buyin_account_id = result.get("data", {}).get("buyin_account_id", "")
    if code != 0 or buyin_account_id == "":
        data_formatted = format_data(result.get("data", {}), user_name, buyin_account_id)
        return {**data_formatted, "user_id": user_id}

    history_live_result = await client.get_history_live_list(user_id)
    format_data_result = format_data(history_live_result.get("data", {}), user_name, buyin_account_id)
    logger.info(f"处理后的直播间明细数据==format_data: {format_data_result}")
    return {**format_data_result, "user_id": user_id}


async def get_core_data_main(data: Dict[str, Any]) -> PublicResponse:
    """直播间大屏明细入口"""
    logger.info(f"直播间大屏明细入口: {data}")

    print("准备抓取cookies")
    await BrowserOperator().attach_get_cookies(user_ids=[data.get("userId")], site_key="screen")
    print("抓取cookies完成")

    client = LivingClient()
    is_screen_ok = await client.check_screen_login(data.get("userId"))
    if not is_screen_ok:
        return PublicResponse.error(message="未登录或缺失大屏站点关键Cookies，请先在浏览器登录")

    await asyncio.sleep(2)  # 设置2秒的间隔

    response_json_data = await client.get_core_data(data.get("userId"), data.get("roomId"))

    logger.info(f"直播间大屏明细结果: {response_json_data}")
    return PublicResponse.success(data=response_json_data, message="操作成功")


# 示例使用
if __name__ == "__main__":
    sample_data = {
        "deviceNoList": "test003,test004",
    }

    asyncio.run(get_history_live_main(sample_data))
