import re
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Callable
from playwright.async_api import Page, Request, Response
from utils.common_logger import get_logger

logger = get_logger(__name__)


class PlaywrightNetworkListener:
    """
    Playwright 网络监听器
    利用 Playwright 原生 API 实现请求和响应捕获
    """

    def __init__(self, page: Page):
        self.page = page
        self.is_listening = False
        self.captured_packets: List[Dict[str, Any]] = []
        self.url_patterns: List[str] = []
        self.callback: Optional[Callable] = None
        self._handlers = []

    def start_listening(
        self,
        url_patterns: Optional[Union[str, List[str]]] = None,
        callback: Optional[Callable] = None,
    ):
        """启动监听"""
        if self.is_listening:
            self.stop_listening()

        self.url_patterns = []
        if url_patterns:
            self.url_patterns = (
                [url_patterns] if isinstance(url_patterns, str) else url_patterns
            )

        self.callback = callback
        self.captured_packets = []
        self.is_listening = True

        # 注册事件处理器
        self.page.on("request", self._handle_request)
        self.page.on("response", self._handle_response)

        logger.info(
            f"Playwright Network Listener started. Filters: {self.url_patterns}"
        )

    def stop_listening(self):
        """停止监听"""
        if self.is_listening:
            self.page.remove_listener("request", self._handle_request)
            self.page.remove_listener("response", self._handle_response)
            self.is_listening = False
            logger.info("Playwright Network Listener stopped.")

    async def _handle_request(self, request: Request):
        """处理请求事件 (内部使用)"""
        # Playwright request handler usually just for logging or specific interception
        # Data capture happens mostly on response to pair them, or we can capture request data here
        pass

    async def _handle_response(self, response: Response):
        """处理响应事件"""
        if not self.is_listening:
            return

        url = response.url
        if not self._match_url(url):
            return

        try:
            # 捕获数据
            req = response.request
            packet = {
                "url": url,
                "method": req.method,
                "status": response.status,
                "request_headers": await req.all_headers(),
                "response_headers": await response.all_headers(),
                "timestamp": datetime.now().isoformat(),
                "resource_type": req.resource_type,
            }

            # 尝试获取 Post Data (Request Body)
            if req.post_data:
                try:
                    packet["request_data"] = json.loads(req.post_data)
                except:
                    packet["request_data"] = req.post_data

            # 尝试获取 Response Body
            # 注意: 大文件或流式响应可能会导致性能问题或异常
            try:
                # 只有文本类型的才尝试获取 text/json
                content_type = packet["response_headers"].get("content-type", "")
                if "application/json" in content_type or "text/" in content_type:
                    text = await response.text()
                    try:
                        packet["response_data"] = json.loads(text)
                    except:
                        packet["response_data"] = text
            except Exception as e:
                # 某些响应可能早已关闭或不可读
                packet["response_error"] = str(e)

            self.captured_packets.append(packet)

            if self.callback:
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(packet)
                else:
                    self.callback(packet)

        except Exception as e:
            logger.error(f"Error capturing packet {url}: {e}")

    def _match_url(self, url: str) -> bool:
        """检查 URL 是否匹配过滤规则"""
        if not self.url_patterns:
            return True

        for pattern in self.url_patterns:
            if pattern in url or re.search(pattern, url):
                return True
        return False

    async def wait_for_packet(
        self, url_pattern: str, timeout: int = 10000
    ) -> Optional[Dict[str, Any]]:
        """等待特定请求包"""
        future = asyncio.get_event_loop().create_future()

        async def _wait_handler(response: Response):
            if self._match_custom(response.url, url_pattern):
                # 捕获完数据后解析
                # 这里简单复用 _handle_response 的逻辑比较复杂，因为需要 future set_result
                # 简化处理：直接等待 response
                if not future.done():
                    future.set_result(response)

        def _match_custom(url, pattern):
            return pattern in url or re.search(pattern, url)

        self.page.on("response", _wait_handler)

        try:
            response = await asyncio.wait_for(future, timeout=timeout / 1000)
            # 解析该 response
            req = response.request
            packet = {
                "url": response.url,
                "headers": await response.all_headers(),  # 兼容旧代码 key
                "request_headers": await req.all_headers(),
                "status": response.status,
            }
            return packet
        except asyncio.TimeoutError:
            return None
        finally:
            self.page.remove_listener("response", _wait_handler)

    def get_captured_packets(self) -> List[Dict[str, Any]]:
        return self.captured_packets
