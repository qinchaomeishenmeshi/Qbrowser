import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union

import requests

from conf import PORTS_FILE
from log.logger import logger
from utils.common_response import PublicResponse

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CouponClient:
    """
    从 ports_file 中读取已保存的 cookies，并封装优惠券创建请求
    """

    def __init__(self, ports_file: Union[str, Path] = Path(BASE_PATH) / PORTS_FILE):
        self.ports_file = Path(__file__).parent / ports_file
        self.mapping = self._load_ports()
        self.ab_url = 'http://113.57.110.35:13276/DouyinLiveWebFetcher/api/get_sign_buyin'
        self.check_login_url = 'https://buyin-sso.jinritemai.com/aff/check_login/'
        self.create_url = 'https://buyin.jinritemai.com/api/buyin/marketing/anchor_coupon/create'
        self.basic_url = 'https://buyin.jinritemai.com/api/anchor/livepc/basic_list'
        self.promotion_url = 'https://buyin.jinritemai.com/api/buyin/marketing/anchor_coupon/promotion_list'

    def _load_ports(self) -> Dict[str, Any]:
        """读取并返回 ports_file 中的映射"""
        if not self.ports_file.exists():
            raise FileNotFoundError(f"Ports file not found: {self.ports_file}")
        text = self.ports_file.read_text(encoding='utf-8')
        return json.loads(text)

    def get_user(self, user_id: str):
        entry = self.mapping.get(user_id)
        if entry is None:
            return None
        return entry

    def _get_cookies_for_user(self, user_id: str) -> Dict[str, str]:
        """
        从 mapping 中提取指定 user_id 的 cookies 列表，并转换为 requests 可用的 dict
        """
        entry = self.get_user(user_id)

        # entry 可能是 {"port": 9222, "cookies": [...]}
        cookies_list = entry.get('cookies') or []
        # DrissionPage cookies 格式为 dict 列表，包含 name 和 value
        cookies_dict = {c['name']: c['value'] for c in cookies_list if 'name' in c and 'value' in c}
        # print(f"Cookies for user {user_id}: {cookies_dict}")
        return cookies_dict

    def _get_headers_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        从 mapping 中提取指定 user_id 的 headers 字段作为请求头，
        并仅保留 default_headers 中定义的键，优先使用保存的值，缺失则用默认值。
        """
        entry = self.mapping.get(user_id)
        if entry is None:
            raise KeyError(f"No entry for user_id {user_id}")

        # 默认 headers
        default_headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://buyin.jinritemai.com',
            'priority': 'u=1, i',
            'referer': 'https://buyin.jinritemai.com/dashboard/marketing/coupon-manager?pre_universal_page_params_id=&universal_page_params_id=8d19445a-fe2f-4e76-a3cb-5571dcc66afe',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'x-secsdk-csrf-token': '000100000001fce811655e8cb3ac1bcfeff9e29b8cb6d8df2bd6272d1e5a601aa1ddb74da05f183dcc6360bd0127',
        }

        saved_headers = entry.get('headers', {})
        if saved_headers is None:
            return {}
        # 只保留 default_headers 中的 key，并优先使用 saved_headers 中的值
        filtered_headers = {
            key: saved_headers.get(key, default_value)
            for key, default_value in default_headers.items()
        }

        return filtered_headers

    def get_sign_buyin(self, user_id: str):
        """获取直播商品"""
        cookies = self._get_cookies_for_user(user_id)
        headers = self._get_headers_for_user(user_id)
        ts = int(time.time() * 1000)
        params = {
            "source_type": "force",
            "User-Agent": headers.get('user-agent', ''),
        }

        print(f"发送请求：{self.ab_url} params={params}")
        resp = requests.post(self.ab_url, params=params, cookies=cookies, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def check_login(self, user_id: str):
        """检查登录状态"""
        return self.get_basic_list(user_id)

    def create_coupon(
            self,
            user_id: str,
            coupon_data: Dict[str, Any],
            extra_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        发送创建达人券请求，返回接口 JSON
        """
        cookies = self._get_cookies_for_user(user_id)

        headers = self._get_headers_for_user(user_id)
        # 默认 params
        ts = int(time.time() * 1000)
        params = {
            '_bid': 'mcenter_buyin',
            '_': str(ts),
            # 's': '1216599',
            'verifyFp': cookies.get('s_v_web_id', ''),
            'fp': cookies.get('s_v_web_id', ''),
        }
        # 合并额外 params
        if extra_params:
            params.update(extra_params)
        logger.info(f"发送请求： {self.create_url}  params {params} headers {headers} coupon_data {coupon_data}")
        resp = requests.post(self.create_url, params=params, cookies=cookies, headers=headers, json=coupon_data)
        resp.raise_for_status()
        return resp.json()

    def get_basic_list(self, user_id: str):
        """获取直播商品"""
        cookies = self._get_cookies_for_user(user_id)
        headers = self._get_headers_for_user(user_id)
        params = {
            'source_type': 'force',
            'verifyFp': cookies.get('s_v_web_id', ''),
            'fp': cookies.get('s_v_web_id', ''),
            # "msToken": "OeDuKb1bB6Od4tYKwdX2SopCTY0HUpDkS_8F_KwQrPSQC4--rS3YZvZB2DwBg9b2C53yOkSipM8ofmQiCBW0YfsfOWGngNELb=c4822d3W5a9dcg7X0_L4FY",
            # 'a_bogus': "mj8M/5LhdDdkgDyg53ALfY3q6Va3YZO50trEMD2f8xvaFy39HMYr9exosBsvUaRjxT/2IeYjy4hbT3ohrQ2y8qwf9W0L/25gsDSkKl12so0j53inCLf/E0iE5hsAtFH8svr4iKi8owICSYyhldAJ5kIlO62-zo0/91D="
        }

        print(f"发送请求：{self.basic_url} params={params}")
        resp = requests.get(self.basic_url, params=params, cookies=cookies, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def get_promotion_list(self, user_id: str):
        """获取直播商品"""
        cookies = self._get_cookies_for_user(user_id)
        headers = self._get_headers_for_user(user_id)
        ts = int(time.time() * 1000)
        params = {
            '_bid': 'mcenter_buyin',
            '_': str(ts),
            's': '244824',
            'promotion_name_or_id': '',
            'page': '1',
            'size': '10',
            'search_type': '1',
            'verifyFp': cookies.get('s_v_web_id', ''),
            'fp': cookies.get('s_v_web_id', ''),
            "a_bogus": "OfmhQVhkDE6igDWX565LfY3q6AF3YD8u0trEMD2f6VV1Cy39HMY59exoXfvv8GEjxT/2IeYjy4hbT3ohrQ2y8qwf9W0L/25gsDSkKl12so0j53inCLf/E0iE5hsAtFH8svr4iKi8owICSYyhldAJ5kIlO62-zo0/96f=",
            "ms_token": "C=PwS33coTeqpBt5y6c4ligMT97UnIGOc-_aYHtl=XlFu38qOo9ZIdNDLa92nmShlDpiS6xrQqky1R6w9aSS-6DguNfZuc8GNf8_2wcxLnMmNmQTCreas3_G"
        }

        print(f"发送请求：{self.promotion_url} params={params}")
        resp = requests.get(self.promotion_url, params=params, cookies=cookies, headers=headers)
        resp.raise_for_status()
        return resp.json()


def get_basic_list_main(user_id=''):
    client = CouponClient()

    data = {
        'coupon_name': '测试0509-server',
        'max_apply_times': 1,
        'type': 53,
        'threshold': '100',
        'credit': '10',
        'total_amount': '5',
        'anchor_coupon_scene': 0,
        'start_apply_time': 1746771086,
        'end_apply_time': 1746792686,
        'start_use_time': 1746771086,
        'end_use_time': 1746792686,
        'goods_id_list': '3740185954082750838',
        'live_promotion_ids': [
            '3741298964599800150',
        ],
        'visibility': 2,
        'kol_user_tag': 0,
    }
    result = client.check_login(user_id)
    # 获取第一页，每页10条记录
    # result = client.get_basic_list(user_id, page=1, size=100)
    print(f"是否登录{result.get('code') == 0}")
    basic_list = result.get('data', {}).get('basic_list', [])
    logger.info(f"basic_list 数据为：{basic_list}")
    return True
    # result = client.create_coupon('wh002', data)
    # print(result)


def format_data(data, goods_id_list='', live_promotion_ids=None):
    live_promotion_ids = live_promotion_ids or []
    return {
        'coupon_name': data.get('couponName', ''),
        'max_apply_times': data.get('maxApplyTimes', ''),
        'type': data.get('type', ''),
        'threshold': data.get('threshold', ''),
        'credit': data.get('credit', ''),
        'total_amount': data.get('totalAmount', ''),
        'anchor_coupon_scene': data.get('anchorCouponScene', ''),
        'start_apply_time': data.get('startApplyTime', ''),
        'end_apply_time': data.get('endApplyTime', ''),
        'start_use_time': data.get('startUseTime', ''),
        'end_use_time': data.get('endUseTime', ''),
        'goods_id_list': goods_id_list,
        'live_promotion_ids': live_promotion_ids,
        'kol_user_tag': data.get('kolUserTag'),
        'visibility': 2,
    }


def process_products(data, basic_list):
    # 1. 读取并转换参数
    try:
        goods_id_type = int(data.get('goodsIdType', 1))
    except ValueError:
        goods_id_type = 1

    goods_id_list_str = data.get('goodsIdList', '')
    goods_id_list = [gid.strip() for gid in goods_id_list_str.split(',') if gid.strip()]

    # 2. 初始化输出列表
    goods_id_list_out = []
    live_promotion_ids = []

    # 3. 抽取过滤判断函数
    def keep_product(pid: str) -> bool:
        if goods_id_type == 1:
            return True
        if goods_id_type == 2:
            return pid in goods_id_list
        if goods_id_type == 3:
            return pid not in goods_id_list
        return False  # 非法类型一律丢弃

    # 4. 遍历 basic_list，收集符合条件的商品
    for p_ind, product in enumerate(basic_list):
        pid = product.get('product_id', '')
        prom_id = product.get('promotion_id', '')

        if not keep_product(pid):
            continue

        # 收集
        goods_id_list_out.append(pid)
        live_promotion_ids.append(prom_id)

    # 6. 拼成字符串（无尾逗号）
    goods_id_list_str_out = ','.join(goods_id_list_out)

    # 7. 返回结果
    return {
        'goodsIdList': goods_id_list_str_out,
        'promotionIds': live_promotion_ids,
    }


# —— 调用示例 ——
# data = {
#     'goodsIdType': '2',
#     'goodsIdList': '3740185954082750838,3736891222183247936,3731302879173148771'
# }
# result = process_products(data, basic_list)
# print(result)


def anchor_coupon_create_main(data) -> PublicResponse:
    """ 批量创建达人券入口 """
    client = CouponClient()
    response_json_data = []
    print(f"批量创建达人券入口{data}")
    device_no_list = data.get('deviceNoList').split(',')
    for user_id in device_no_list:
        entry = client.get_user(user_id)
        if not entry:
            logger.error(f"{user_id} 无有效cookie，请检查账号或节点")
            response_json_data.append({
                "msg": f"无有效cookie，请检查账号或节点",
                "data": None,
                "user_id": user_id
            })
            continue

        result = client.get_basic_list(user_id)
        code = int(result.get('code', -1))
        if code != 0:
            response_json_data.append({**result, 'user_id': user_id})
            continue
        basic_list = result.get('data', {}).get('basic_list', [])
        goods_id_list = ''
        live_promotion_ids = []
        print(f"basic_list 数据为：{basic_list}")
        # 如果data.get('goodsIdType', '1') 为 1 默认不操作 ， 2 指定商品，3 则过滤掉商品

        process_products_resp = process_products({
            "goodsIdType": data.get('goodsIdType', '1'), 'goodsIdList': data.get('goodsIdList', '')
        }, basic_list=basic_list)

        coupon_data = format_data(
            data,
            goods_id_list=process_products_resp['goodsIdList'].rstrip(','),  # 去掉末尾逗号
            live_promotion_ids=process_products_resp['promotionIds'],
        )
        result = client.create_coupon(user_id, coupon_data)
        response_json_data.append({**result, 'user_id': user_id})

    logger.info(f"结果：{response_json_data}")
    # 先获取商品列表
    # 再提交创建达人券接口

    return PublicResponse(status='success', message='操作成功', data=response_json_data)


def test():
    client = CouponClient()
    resp = client.get_promotion_list('wh002')
    print(resp)


# 示例使用
if __name__ == '__main__':
    # test()
    def to_timestamp(dt_str: str) -> int:
        """将字符串时间转为时间戳（秒）"""
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return int(time.mktime(dt_obj.timetuple()))


    anchor_coupon_create_main({
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
        "deviceNoList": "wh001,wh002,wh003"
    })
