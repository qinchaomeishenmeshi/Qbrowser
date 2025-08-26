import aiohttp
import json
from typing import Dict, Any, Optional
from utils.common_logger import get_logger

logger = get_logger(__name__)


class InternalApiClient:
    """
    内部后端API客户端，用于统一处理内部接口调用
    """

    def __init__(
        self, base_url: str = "http://113.57.110.35:13276/dev-api", timeout: int = 60
    ):
        """
        初始化API客户端

        :param base_url: API基础URL
        :param timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "QW-Browser-Client/1.0",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        发起HTTP请求的通用方法

        :param method: HTTP方法 (GET, POST, PUT, DELETE等)
        :param endpoint: API端点路径
        :param data: 请求体数据
        :param headers: 额外的请求头
        :param params: URL查询参数
        :return: 响应数据字典
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # 合并请求头
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.debug(f"发起{method}请求: {url}")
                logger.debug(f"请求头: {request_headers}")
                logger.debug(f"请求数据: {data}")

                async with session.request(
                    method=method,
                    url=url,
                    json=data if data else None,
                    headers=request_headers,
                    params=params,
                ) as response:
                    response_text = await response.text()
                    logger.debug(f"响应状态码: {response.status}")
                    logger.debug(f"响应内容: {response_text}")

                    # 尝试解析JSON响应
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError:
                        result = {
                            "code": response.status,
                            "msg": f"响应解析失败: {response_text[:200]}...",
                            "data": None,
                        }

                    # 检查HTTP状态码
                    if response.status >= 400:
                        logger.error(f"HTTP错误 {response.status}: {response_text}")
                        return {
                            "code": response.status,
                            "msg": f"HTTP错误: {response.status}",
                            "data": result,
                        }

                    return result

        except aiohttp.ClientTimeout:
            logger.error(f"请求超时: {url}")
            return {"code": -1, "msg": "请求超时", "data": None}
        except aiohttp.ClientError as e:
            logger.error(f"网络请求错误: {e}")
            return {"code": -1, "msg": f"网络请求错误: {str(e)}", "data": None}
        except Exception as e:
            logger.error(f"未知错误: {e}", exc_info=True)
            return {"code": -1, "msg": f"未知错误: {str(e)}", "data": None}

    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发起POST请求

        :param endpoint: API端点路径
        :param data: 请求体数据
        :param headers: 额外的请求头
        :return: 响应数据字典
        """
        return await self._make_request("POST", endpoint, data=data, headers=headers)

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发起GET请求

        :param endpoint: API端点路径
        :param params: URL查询参数
        :param headers: 额外的请求头
        :return: 响应数据字典
        """
        return await self._make_request("GET", endpoint, params=params, headers=headers)

    async def put(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        发起PUT请求

        :param endpoint: API端点路径
        :param data: 请求体数据
        :param headers: 额外的请求头
        :return: 响应数据字典
        """
        return await self._make_request("PUT", endpoint, data=data, headers=headers)

    async def delete(
        self, endpoint: str, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        发起DELETE请求

        :param endpoint: API端点路径
        :param headers: 额外的请求头
        :return: 响应数据字典
        """
        return await self._make_request("DELETE", endpoint, headers=headers)

    async def sync_live_replay_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步直播回放数据到后端

        :param data: 直播回放数据
        :return: 同步结果
        """
        endpoint = "/aiplay/admin/livereplaydata/synmessage"
        return await self.post(endpoint, data)

    async def sync_live_core_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步直播间大屏数据到后端

        :param data: 直播间大屏数据，包含live_id、core_data、other_data等字段
        :return: 同步结果
        """
        endpoint = "/aiplay/admin/livereplaydatadetail/synmessage"
        return await self.post(endpoint, data)

    async def sync_coupon_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步优惠券数据到后端

        :param data: 优惠券数据
        :return: 同步结果
        """
        endpoint = "/aiplay/admin/coupondata/sync"
        return await self.post(endpoint, data)

    async def sync_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步用户数据到后端

        :param data: 用户数据
        :return: 同步结果
        """
        endpoint = "/aiplay/admin/userdata/sync"
        return await self.post(endpoint, data)

    async def sync_live_room_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步eos直播复盘数据到后端

        :param data: 直播回放数据
        :return: 同步结果
        """
        endpoint = "/aiplay/admin/livebroadcastreview/batchSave"
        return await self.post(endpoint, data)

    async def sync_punish_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步eos直播违规数据到后端

        :param data: 直播违规记录数据
        :return: 同步结果
        """
        endpoint = "/aiplay/admin/liveviolationrecordsdeal/save"
        return await self.post(endpoint, data)

    async def sync_live_key_index_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        同步eos直播大屏数据到后端

        :param data: 直播大屏数据
        :return: 同步结果
        """
        endpoint = "/aiplay/admin/livebroadcastreviewdetail/synmessage"
        return await self.post(endpoint, data)


# 创建默认的API客户端实例
default_api_client = InternalApiClient()
