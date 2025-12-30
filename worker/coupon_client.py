import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union

import requests

from browser.playwright_operator import (
    playwright_operator as browser_operator,
    PlaywrightOperator as BrowserOperator,
)
from conf import PORTS_FILE
from utils.common_logger import get_logger
from utils.common_response import PublicResponse

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger = get_logger(__name__)

# 常量定义
DEFAULT_VISIBILITY = 2
MAX_RETRY_COUNT = 1
RETRY_DELAY = 1  # 秒


class CouponClient:
    """
    从 ports_file 中读取已保存的 cookies，并封装优惠券创建请求
    """

    def __init__(self, ports_file: Union[str, Path] = Path(BASE_PATH) / PORTS_FILE):
        self.ports_file = Path(__file__).parent / ports_file
        self.ab_url = (
            "http://113.57.110.35:13276/DouyinLiveWebFetcher/api/get_sign_buyin"
        )
        self.check_login_url = "https://buyin-sso.jinritemai.com/aff/check_login/"
        self.create_url = (
            "https://buyin.jinritemai.com/api/buyin/marketing/anchor_coupon/create"
        )
        self.basic_url = "https://buyin.jinritemai.com/api/anchor/livepc/basic_list"
        self.promotion_url = "https://buyin.jinritemai.com/api/buyin/marketing/anchor_coupon/promotion_list"

    @staticmethod
    async def _get_cookies_for_user(user_id: str) -> Dict[str, str]:
        """
        从 mapping 中提取指定 user_id 的 cookies 列表，并转换为 requests 可用的 dict
        确保包含所有必要的认证和会话 cookies
        """
        cookies_list = await browser_operator.get_user_cookies(user_id)

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
                c["name"]: c["value"]
                for c in cookies_list
                if isinstance(c, dict) and "name" in c and "value" in c
            }
        else:
            logger.error(
                f"用户 {user_id} 的 cookies 格式不支持，类型: {type(cookies_list)}"
            )
            return cookies_dict
        return cookies_dict

    @staticmethod
    async def _get_headers_for_user(user_id: str) -> Dict[str, Any]:
        """
        从 mapping 中提取指定 user_id 的 headers 字段作为请求头，
        并仅保留 default_headers 中定义的键，优先使用保存的值，缺失则用默认值。
        """
        # 默认 headers
        default_headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json",
            "origin": "https://buyin.jinritemai.com",
            "priority": "u=1, i",
            "referer": "https://buyin.jinritemai.com/dashboard/marketing/coupon-manager?pre_universal_page_params_id=&universal_page_params_id=8d19445a-fe2f-4e76-a3cb-5571dcc66afe",
            "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "x-secsdk-csrf-token": "000100000001fce811655e8cb3ac1bcfeff9e29b8cb6d8df2bd6272d1e5a601aa1ddb74da05f183dcc6360bd0127",
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

    async def get_sign_buyin(self, user_id: str):
        """获取直播商品签名"""
        try:
            cookies = await self._get_cookies_for_user(user_id)
            headers = await self._get_headers_for_user(user_id)
            params = {
                "source_type": "force",
                "User-Agent": headers.get("user-agent", ""),
            }

            logger.info(f"发送请求：{self.ab_url} params={params}")
            resp = requests.post(
                self.ab_url, params=params, cookies=cookies, headers=headers
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"获取直播商品签名失败: {e}")
            return {"code": -1, "msg": f"获取签名失败: {str(e)}"}

    async def check_login(self, user_id: str):
        """检查登录状态"""
        return await self.get_basic_list(user_id)

    async def create_coupon(
        self,
        user_id: str,
        coupon_data: Dict[str, Any],
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        发送创建达人券请求，返回接口 JSON
        """
        for retry in range(MAX_RETRY_COUNT):
            try:
                cookies = await self._get_cookies_for_user(user_id)
                headers = await self._get_headers_for_user(user_id)
                # 默认 params
                ts = int(time.time() * 1000)
                params = {
                    "_bid": "mcenter_buyin",
                    "_": str(ts),
                    "verifyFp": cookies.get("s_v_web_id", ""),
                    "fp": cookies.get("s_v_web_id", ""),
                }
                # 合并额外 params
                if extra_params:
                    params.update(extra_params)

                logger.info(
                    f"发送请求： {self.create_url} params={params} coupon_data={coupon_data}"
                )
                resp = requests.post(
                    self.create_url,
                    params=params,
                    cookies=cookies,
                    headers=headers,
                    json=coupon_data,
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"创建达人券失败(重试 {retry + 1}/{MAX_RETRY_COUNT}): {e}")
                if retry < MAX_RETRY_COUNT - 1:
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    return {"code": -1, "msg": f"创建达人券失败: {str(e)}"}

    async def get_basic_list(self, user_id: str):
        """获取直播商品列表"""
        try:
            cookies = await self._get_cookies_for_user(user_id)
            headers = await self._get_headers_for_user(user_id)
            params = {
                "source_type": "force",
                "verifyFp": cookies.get("s_v_web_id", ""),
                "fp": cookies.get("s_v_web_id", ""),
            }

            logger.info(f"发送请求：{self.basic_url} params={params}")
            resp = requests.get(
                self.basic_url, params=params, cookies=cookies, headers=headers
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"获取直播商品列表失败: {e}")
            return {"code": -1, "msg": f"获取直播商品列表失败: {str(e)}"}

    async def get_promotion_list(self, user_id: str):
        """获取推广列表"""
        try:
            cookies = await self._get_cookies_for_user(user_id)
            headers = await self._get_headers_for_user(user_id)
            ts = int(time.time() * 1000)
            params = {
                "_bid": "mcenter_buyin",
                "_": str(ts),
                "promotion_name_or_id": "",
                "page": "1",
                "size": "10",
                "search_type": "1",
                "verifyFp": cookies.get("s_v_web_id", ""),
                "fp": cookies.get("s_v_web_id", ""),
            }

            logger.info(f"发送请求：{self.promotion_url} params={params}")
            resp = requests.get(
                self.promotion_url, params=params, cookies=cookies, headers=headers
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"获取推广列表失败: {e}")
            return {"code": -1, "msg": f"获取推广列表失败: {str(e)}"}


def to_timestamp(dt_str: str) -> int:
    """将字符串时间转为时间戳（秒）"""
    try:
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(dt_obj.timetuple()))
    except ValueError as e:
        logger.error(f"时间格式转换错误: {e}")
        return 0


def format_data(data, goods_id_list="", live_promotion_ids=None):
    """格式化优惠券数据，将前端字段转换为API所需格式"""
    live_promotion_ids = live_promotion_ids or []

    # 转换时间字符串为时间戳
    start_apply_time = data.get("startApplyTime", "")
    end_apply_time = data.get("endApplyTime", "")
    start_use_time = data.get("startUseTime", "")
    end_use_time = data.get("endUseTime", "")

    return {
        "coupon_name": data.get("couponName", ""),
        "max_apply_times": data.get("maxApplyTimes", ""),
        "type": data.get("type", ""),
        "threshold": data.get("threshold", ""),
        "credit": data.get("credit", ""),
        "total_amount": data.get("totalAmount", ""),
        "anchor_coupon_scene": data.get("anchorCouponScene", ""),
        "start_apply_time": start_apply_time,
        "end_apply_time": end_apply_time,
        "start_use_time": start_use_time,
        "end_use_time": end_use_time,
        "goods_id_list": goods_id_list,
        "live_promotion_ids": live_promotion_ids,
        "kol_user_tag": data.get("kolUserTag", 0),
        "visibility": DEFAULT_VISIBILITY,
    }


def process_products(data, basic_list) -> Dict[str, Any]:
    """处理商品列表，根据条件筛选商品"""
    # 1. 读取并转换参数
    try:
        goods_id_type = int(data.get("goodsIdType", 1))
    except ValueError:
        goods_id_type = 1

    goods_id_list_str = data.get("goodsIdList", "")
    goods_id_list = [gid.strip() for gid in goods_id_list_str.split(",") if gid.strip()]

    # 2. 初始化输出列表
    goods_id_list_out = []
    live_promotion_ids = []

    # 3. 抽取过滤判断函数
    def keep_product(pid: str) -> bool:
        if goods_id_type == 1:  # 不过滤
            return True
        if goods_id_type == 2:  # 仅包含指定商品
            return pid in goods_id_list
        if goods_id_type == 3:  # 排除指定商品
            return pid not in goods_id_list
        return False  # 非法类型一律丢弃

    # 4. 遍历 basic_list，收集符合条件的商品
    for product in basic_list:
        pid = product.get("product_id", "")
        prom_id = product.get("promotion_id", "")

        if not keep_product(pid):
            continue

        # 收集
        goods_id_list_out.append(pid)
        live_promotion_ids.append(prom_id)

    # 拼成字符串
    goods_id_list_str_out = ",".join(goods_id_list_out)

    # 返回结果
    return {
        "goodsIdList": goods_id_list_str_out,
        "promotionIds": live_promotion_ids,
    }


async def anchor_coupon_create_main(data) -> PublicResponse:
    """批量创建达人券入口 (串行执行)"""
    logger.info(f"批量创建达人券入口: {data}")

    # 分割用户ID列表
    device_no_list = data.get("deviceNoList", "").split(",")
    print("准备抓取cookies")
    await BrowserOperator().attach_get_cookies(user_ids=device_no_list)
    print("抓取cookies完成")

    client = CouponClient()
    response_json_data = []

    # 串行执行每个用户的任务，避免并发请求触发风控
    for user_id in device_no_list:
        logger.info(f"开始处理用户 {user_id} 的优惠券创建请求")
        result = await process_user_coupon(client, user_id, data)
        response_json_data.append(result)
        # 每个用户处理完成后等待一段时间，降低API调用频率
        await asyncio.sleep(1.5)  # 设置1.5秒的间隔，可根据实际情况调整

    logger.info(f"批量创建达人券结果: {response_json_data}")
    return PublicResponse.success(data=response_json_data, message="操作成功")


async def process_user_coupon(client, user_id, data):
    """处理单个用户的优惠券创建流程"""

    # 获取商品列表
    result = await client.get_basic_list(user_id)
    code = int(result.get("code", -1))
    if code != 0:
        return {**result, "user_id": user_id}

    # 处理商品列表
    basic_list = result.get("data", {}).get("basic_list", [])
    logger.info(f"用户 {user_id} 商品列表数量: {len(basic_list)}")

    # 根据配置过滤商品
    process_products_resp = process_products(
        {
            "goodsIdType": data.get("goodsIdType", "1"),
            "goodsIdList": data.get("goodsIdList", ""),
        },
        basic_list=basic_list,
    )

    # 格式化优惠券数据
    coupon_data = format_data(
        data,
        goods_id_list=process_products_resp["goodsIdList"],
        live_promotion_ids=process_products_resp["promotionIds"],
    )
    logger.info(f"优惠券数据: {coupon_data}")
    # 创建优惠券
    result = await client.create_coupon(user_id, coupon_data)
    return {**result, "user_id": user_id}


# 示例使用
if __name__ == "__main__":
    sample_data = {
        "id": "1921119979076325378",
        "status": "0",
        "createBy": "1897092900773171202",
        "createTime": "2025-05-10 16:27:50",
        "couponName": "固定时间可用",
        "maxApplyTimes": "1",
        "type": "53",
        "credit": "1",
        "totalAmount": "50",
        "threshold": "10",
        "anchorCouponScene": "0",
        "startApplyTime": "2025-05-13 16:27:08",
        "endApplyTime": "2025-05-13 17:27:13",
        "startUseTime": "2025-05-14 16:27:33",
        "endUseTime": "2025-05-14 20:27:42",
        "kolUserTag": "0",
        "applyTimeType": "2",
        "applyTime": "",
        "useTimeType": "3",
        "useTime": "",
        "goodsIdType": "1",
        "goodsIdList": "3740185954082750838,3734249967804612830,3736891222183247936,3731302879173148771",
        "deviceNoList": "wh001,wh002,wh003",
    }

    asyncio.run(anchor_coupon_create_main(sample_data))
