import asyncio
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from conf import BASE_DIR
from service.browser_service import browser_service
from utils.common_logger import get_logger
from utils.cookies_manager import CookiesManager

logger = get_logger(__name__)

# 配置不同站点的URL和API监听路径
SITE_CONFIGS = {
    "baiying": {
        "name": "百应",
        "login_url": "https://buyin.jinritemai.com/mpa/account/login",
        "target_url": "https://buyin.jinritemai.com/dashboard/marketing/coupon-manager",
        "api_paths": ["/selection/common/btm_mapping"],
        "required_cookies": ["MSESSIONID", "passport_csrf_token"],
        "required_headers": ["x-secsdk-csrf-token", "user-agent"]
    }, 
    "screen": {
        "name": "百应大屏",
        "login_url": "",
        "target_url": "https://compass.jinritemai.com/screen/live/talent",
        "api_paths": ["/config_center/common/config"],
        "required_cookies": ["COMPASS_LUOPAN_DT", "LUOPAN_DT"],
        "required_headers": ["referer", "user-agent"]
    }, 
    "eos": {
        "name": "EOS抖音",
        "login_url": "",
        "target_url": "https://eos.douyin.com/livesite/live/history?tab=diagnosis",
        "api_paths": ["/life/api/live_screen/v4/replay/anchor_info"],
        "required_cookies": ["eos_s_token"],
        "required_headers": ["referer", "user-agent","x-secsdk-csrf-token"]
    },
    # 可以添加其他站点的配置
}


class RequestListener:
    """
    封装 DrissionPage 请求监听逻辑：
    - 启动监听特定的 api_uri
    - 执行页面加载并等待
    - 停止监听并返回请求头和数据包
    """

    def __init__(self, tab, api_uri: str, timeout: int = 5):
        self.tab = tab
        self.api_uri = api_uri
        self.timeout = timeout
        self.packet = None

    def listen_for(self):
        self.tab.listen.start(self.api_uri)
        try:
            self.packet = self.tab.listen.wait(timeout=self.timeout)
            return self.packet
        except Exception as e:
            logger.error(f"监听 {self.api_uri} 超时: {e}")
        finally:
            self.tab.listen.stop()

    def get_request_headers(self) -> Optional[dict]:
        if self.packet:
            return dict(self.packet.request.headers)
        return None


class BrowserOperator:
    """
    浏览器操作类：
    - 负责浏览器操作
    - 管理cookies和headers
    - 实例管理交给 browser_service
    """

    def __init__(self):
        self.cookies_manager = CookiesManager(Path(BASE_DIR) / "data" / "cookies")

    def fetch_cookies_and_headers(
            self,
            browser,
            user_id: str,
            url: str,
            api_paths: List[str],
            max_retries: int = 2,
            retry_delay: int = 1
    ) -> Dict[str, Any]:
        """
        获取指定页面的cookies和headers，支持多个API路径监听和重试机制

        Args:
            browser: 浏览器实例
            user_id: 用户ID
            url: 目标URL
            api_paths: 要监听的API路径列表
            max_retries: 最大重试次数
            retry_delay: 重试间隔(秒)

        Returns:
            包含cookies和headers的字典，每个API路径对应一个条目
        """
        results = {
            "cookies": {},
            "headers": {},
            "api_results": {}
        }

        try:
            # 尝试打开最后一个标签页或创建新标签页
            try:
                tab = browser.get_tab(browser.tabs_count - 1)
            except Exception:
                tab = browser.new_tab()

            # 确保页面加载完成
            tab.get(url)
            time.sleep(1)  # 等待页面加载

            # 获取cookies (不依赖于API监听)
            results["cookies"] = tab.cookies()
            logger.info(f"已获取用户 {user_id} 的 cookies，共 {len(results['cookies'])} 项")

            # 监听每个API路径
            for api_path in api_paths:
                for retry in range(max_retries):
                    logger.info(f"尝试监听 {api_path} (第 {retry + 1}/{max_retries} 次)")
                    listener = RequestListener(tab, api_path)

                    # 页面交互 - 可以在这里添加模拟点击等操作
                    # 例如: tab.ele('xpath://button[@id="refresh"]').click()

                    # 刷新页面触发API请求
                    tab.refresh()

                    packet = listener.listen_for()
                    if packet:
                        headers = listener.get_request_headers()
                        if headers:
                            results["headers"][api_path] = headers
                            results["api_results"][api_path] = {
                                "status": "success",
                                "retry": retry
                            }
                            logger.info(f"成功获取 {api_path} 的请求头")
                            break

                    # 如果失败且不是最后一次重试，则等待后再试
                    if retry < max_retries - 1:
                        time.sleep(retry_delay)
                        logger.info(f"监听 {api_path} 失败，准备重试")

            return results

        except Exception as e:
            logger.error(f"获取用户 {user_id} 的 cookies 和 headers 失败: {e}")
            return results

    def filter_data(
            self,
            data: Dict[str, Any],
            required_cookies: List[str] = None,
            required_headers: List[str] = None
    ) -> Dict[str, Any]:
        """
        获取cookies和headers，默认收集全量数据
        """
        result = {
            "cookies": {},
            "headers": {}
        }

        # 收集全量cookies
        result["cookies"] = data.get("cookies", {})

        # 收集全量headers (来自所有API路径)
        all_headers = {}
        for headers_dict in data.get("headers", {}).values():
            all_headers.update(headers_dict)

        result["headers"] = all_headers

        return result

    async def collect_site_cookies(
            self,
            user_id: str,
            site_key: str = "baiying",
            custom_config: Dict = None
    ) -> bool:
        """
        收集特定站点的cookies

        Args:
            user_id: 用户ID
            site_key: 站点配置键名
            custom_config: 自定义配置(覆盖默认)

        Returns:
            操作成功与否
        """
        # 获取站点配置
        config = custom_config or SITE_CONFIGS.get(site_key)
        if not config:
            logger.error(f"站点 {site_key} 的配置不存在")
            return False

        try:
            # 获取或创建浏览器实例
            manager = await browser_service.get_or_create_browser(user_id)
            if not manager or not manager.is_running:
                logger.error(f"用户 {user_id} 的浏览器实例创建或运行失败")
                return False

            # 获取cookies和headers
            raw_data = self.fetch_cookies_and_headers(
                manager.browser,
                user_id,
                config["target_url"],
                config["api_paths"]
            )

            # 获取全量数据
            filtered_data = self.filter_data(raw_data)

            # 保存cookies和headers
            await self.cookies_manager.save_cookies(
                user_id,
                filtered_data["cookies"],
                filtered_data["headers"],
                site_key=site_key  # 添加站点标识
            )

            logger.info(f"已保存用户 {user_id} 的 {site_key} 站点数据")
            return True

        except Exception as e:
            logger.error(f"收集用户 {user_id} 的 {site_key} 站点数据失败: {e}")
            return False

    async def attach_get_cookies(self, user_ids: List[str], site_key: str = "baiying"):
        """
        批量获取并保存用户的cookies信息
        """
        results = []
        try:
            for user_id in user_ids:
                logger.info(f"处理用户 {user_id} 的 {site_key} 站点cookies")
                success = await self.collect_site_cookies(user_id, site_key)
                results.append({"user_id": user_id, "success": success})

                # 稍作延迟，避免并发问题
                await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"批量处理 cookies 时发生错误: {e}")

        return results

    async def get_user_cookies(self, user_id: str, site_key: str = "baiying") -> Optional[Dict]:
        """
        获取用户的cookies信息
        """
        return await self.cookies_manager.get_cookies(user_id, site_key)

    async def get_user_headers(self, user_id: str, site_key: str = "baiying") -> Optional[Dict]:
        """
        获取用户的headers信息
        """
        return await self.cookies_manager.get_headers(user_id, site_key)

    async def clear_user_data(self, user_id: str, site_key: str = None):
        """
        清除用户的cookies信息
        """
        await self.cookies_manager.remove_cookies(user_id, site_key)

    async def clear_all_data(self):
        """
        清除所有用户的cookies信息
        """
        await self.cookies_manager.clear_all()

    async def check_and_refresh_cookies(self, user_id: str, site_key: str = "baiying") -> bool:
        """
        检查并在需要时刷新cookies
        """
        cookies = await self.cookies_manager.get_cookies(user_id, site_key)
        if not cookies:
            logger.info(f"用户 {user_id} 的 cookies 不存在，尝试收集")
            return await self.collect_site_cookies(user_id, site_key)

        return True


browser_operator = BrowserOperator()
