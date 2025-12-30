import asyncio
import time
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from loguru import logger
from playwright.async_api import Page, BrowserContext

from conf import BASE_DIR, resource_path
from utils.common_logger import get_logger
from utils.cookies_manager import CookiesManager
from utils.page_redirect_manager import redirect_manager
from utils.playwright_network_listener import PlaywrightNetworkListener

# Import PlaywrightManager for type hinting only (avoid runtime circular dependency if possible)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from browser.playwright_manager import PlaywrightManager

logger = get_logger(__name__)

# 配置不同站点的URL和API监听路径
SITE_CONFIGS = {
    "baiying": {
        "name": "百应",
        "login_url": "https://buyin.jinritemai.com/mpa/account/login",
        "target_url": "https://buyin.jinritemai.com/dashboard/marketing/coupon-manager",
        "api_paths": ["/selection/common/btm_mapping"],
        "required_cookies": ["MSESSIONID", "passport_csrf_token"],
        "required_headers": ["x-secsdk-csrf-token", "user-agent"],
    },
    "screen": {
        "name": "百应大屏",
        "login_url": "",
        "target_url": "https://compass.jinritemai.com/screen/live/talent",
        "api_paths": ["/config_center/common/config"],
        "required_cookies": ["COMPASS_LUOPAN_DT", "LUOPAN_DT"],
        "required_headers": ["referer", "user-agent"],
    },
    "eos": {
        "name": "EOS抖音",
        "login_url": "",
        "target_url": "https://eos.douyin.com/livesite/live/history?tab=diagnosis",
        "api_paths": ["/life/api/live_screen/v4/replay/anchor_info"],
        "required_cookies": ["eos_s_token"],
        "required_headers": ["referer", "user-agent", "x-secsdk-csrf-token"],
    },
}


class PlaywrightOperator:
    """
    Playwright 版浏览器操作类
    作为 BrowserOperator 的直接替代品
    """

    def __init__(self):
        self.cookies_manager = CookiesManager(Path(resource_path("data/cookies")))

    async def get_or_create_page(
        self, manager: "PlaywrightManager", url_substr: str
    ) -> Optional[Page]:
        """获取匹配的页面或创建新页面"""
        context = manager.context
        if not context:
            logger.error("Browser context not initialized")
            return None

        # 尝试复用现有页面
        for page in context.pages:
            if url_substr in page.url:
                logger.info(f"Reusing page: {page.url}")
                try:
                    await page.bring_to_front()
                    return page
                except Exception as e:
                    logger.warning(f"Failed to bring page to front: {e}")
                    # Continue to start fresh or try next

        # 创建新页面
        logger.info("Creating new page")
        try:
            page = await context.new_page()
            return page
        except Exception as e:
            logger.error(f"Failed to create new page: {e}")
            return None

    async def fetch_cookies_and_headers(
        self,
        manager: "PlaywrightManager",
        user_id: str,
        url: str,
        api_paths: List[str],
        max_retries: int = 2,
        site_key: str = "",
    ) -> Dict[str, Any]:
        """
        获取指定页面的cookies和headers
        """
        results = {"cookies": {}, "headers": {}, "api_results": {}}

        # 1. 检查缓存
        cached_cookies = await self.cookies_manager.get_cookies(user_id, site_key)
        cached_headers = await self.cookies_manager.get_headers(user_id, site_key)

        if cached_cookies and cached_headers:
            logger.debug(f"用户 {user_id} 从缓存获取 {site_key} 的 cookies 和 headers")
            results["cookies"] = cached_cookies
            results["headers"] = cached_headers
            return results

        # 2. 获取页面
        page = await self.get_or_create_page(manager, url)
        if not page:
            logger.error(f"无法获取用户 {user_id} 的页面")
            return results

        # 3. 登录检查
        if site_key == "eos":
            if "eos.douyin.com/livesite/login" in page.url:
                raise Exception("EOS未登录，操作失败")
        if site_key == "baiying":
            if "/login?" in page.url or "www.douyinec.com" in page.url:
                raise Exception("百应未登录，操作失败")

        # 4. 设置网络监听
        listener = PlaywrightNetworkListener(page)
        listener.start_listening(api_paths)

        try:
            # 5. 导航到目标 URL (如果当前不在)
            logger.info(f"Navigating to {url} for user {user_id}")
            if url not in page.url:
                await page.goto(url, wait_until="domcontentloaded")
            else:
                await page.reload(wait_until="domcontentloaded")

            # 等待额外时间确保各种脚本加载
            await asyncio.sleep(3)

            # 手动获取 Cookies
            all_cookies = await manager.context.cookies()
            cookies_dict = {c["name"]: c["value"] for c in all_cookies}
            results["cookies"] = cookies_dict

            # 等待并提前刷新一次以确保触发请求
            # Some requests only fire on fresh load or interaction
            # If nothing captured yet, maybe scroll or wait

            max_wait_time = 5  # seconds
            start_time = time.time()

            captured_any = False
            while time.time() - start_time < max_wait_time:
                packets = listener.get_captured_packets()
                if packets:
                    # Check if we have what we need
                    # For simplest logic, just see if we caught anything relevant
                    for path in api_paths:
                        for p_url in packets:
                            if path in p_url:
                                captured_any = True
                    if captured_any:
                        break
                await asyncio.sleep(0.5)

            # 7. 提取 Headers
            captured = listener.get_captured_packets()
            for packet in captured:
                c_url = packet.get("url", "")
                for path in api_paths:
                    if path in c_url:
                        results["headers"][path] = packet.get("request_headers", {})
                        results["api_results"][path] = {"status": "success"}

        except Exception as e:
            logger.error(f"获取Cookies和Headers失败: {e}", exc_info=True)
        finally:
            listener.stop_listening()

        return results

    def filter_data(
        self,
        data: Dict[str, Any],
        required_cookies: List[str] = None,
        required_headers: List[str] = None,
    ) -> Dict[str, Any]:
        """过滤和整理数据 (兼容 BrowserOperator)"""
        result = {"cookies": {}, "headers": {}}

        # 收集全量cookies
        result["cookies"] = data.get("cookies", {})

        # 收集全量headers (来自所有API路径)
        all_headers = {}
        for headers_dict in data.get("headers", {}).values():
            all_headers.update(headers_dict)

        result["headers"] = all_headers
        return result

    async def collect_site_cookies(
        self, user_id: str, site_key: str = "baiying", custom_config: Dict = None
    ) -> bool:
        """收集特定站点的cookies"""
        config = custom_config or SITE_CONFIGS.get(site_key)
        if not config:
            logger.error(f"站点 {site_key} 的配置不存在")
            return False

        try:
            from service.browser_service import browser_service

            manager = await browser_service.get_or_create_browser(user_id)
            if not manager or not manager.is_running:
                logger.error(f"用户 {user_id} 的浏览器实例创建或运行失败")
                return False

            raw_data = await self.fetch_cookies_and_headers(
                manager,
                user_id,
                config["target_url"],
                config["api_paths"],
                site_key=site_key,
            )

            filtered_data = self.filter_data(raw_data)

            await self.cookies_manager.save_cookies(
                user_id,
                filtered_data["cookies"],
                filtered_data["headers"],
                site_key=site_key,
            )

            logger.info(f"已保存用户 {user_id} 的 {site_key} 站点数据")
            return True

        except Exception as e:
            logger.error(f"收集用户 {user_id} 的 {site_key} 站点数据失败: {e}")
            return False

    async def attach_get_cookies(self, user_ids: List[str], site_key: str = "baiying"):
        """批量获取并保存用户的cookies信息"""

        async def process_user(user_id):
            try:
                success = await self.collect_site_cookies(user_id, site_key)
                return {"user_id": user_id, "success": success}
            except Exception as e:
                logger.error(f"Error processing user {user_id}: {e}")
                return {"user_id": user_id, "success": False}

        tasks = [process_user(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks)
        return results

    async def get_user_cookies(
        self, user_id: str, site_key: str = "baiying"
    ) -> Optional[Dict]:
        """获取用户的cookies信息"""
        return await self.cookies_manager.get_cookies(user_id, site_key)

    async def get_user_headers(
        self, user_id: str, site_key: str = "baiying"
    ) -> Optional[Dict]:
        """获取用户的headers信息"""
        return await self.cookies_manager.get_headers(user_id, site_key)

    async def clear_user_data(self, user_id: str, site_key: str = None):
        """清除用户的cookies信息"""
        await self.cookies_manager.remove_cookies(user_id, site_key)

    async def clear_all_data(self):
        """清除所有用户的cookies信息"""
        await self.cookies_manager.clear_all()

    async def check_and_refresh_cookies(
        self, user_id: str, site_key: str = "baiying"
    ) -> bool:
        """检查并在需要时刷新cookies"""
        cookies = await self.cookies_manager.get_cookies(user_id, site_key)
        if not cookies:
            return await self.collect_site_cookies(user_id, site_key)
        return True

    async def redirect_user_page(
        self, user_id: str, target_url: str, wait_time: float = 1.0
    ) -> bool:
        """重定向用户页面到指定URL"""
        try:
            from service.browser_service import browser_service

            manager = await browser_service.get_or_create_browser(user_id)
            if not manager or not manager.is_running:
                logger.error(f"User {user_id} browser not running")
                return False

            page = await self.get_or_create_page(manager, target_url)
            if not page:
                return False

            logger.info(f"Redirecting user {user_id} to {target_url}")
            await page.goto(target_url)
            await asyncio.sleep(wait_time)
            return True
        except Exception as e:
            logger.error(f"Redirect failed for {user_id}: {e}")
            return False

    async def batch_redirect_users(
        self, user_redirects: List[Dict[str, str]], wait_time: float = 1.0
    ) -> Dict[str, bool]:
        """批量重定向"""
        results = {}
        for item in user_redirects:
            user_id = item.get("user_id")
            url = item.get("target_url")
            if user_id and url:
                # Use a small delay or concurrency constraint if needed
                res = await self.redirect_user_page(user_id, url, wait_time)
                results[user_id] = res
        return results

    async def redirect_to_site(
        self, user_id: str, site_key: str, wait_time: float = 1.0
    ) -> bool:
        """重定向到站点"""
        config = SITE_CONFIGS.get(site_key)
        if not config:
            logger.error(f"Unknown site key: {site_key}")
            return False
        return await self.redirect_user_page(user_id, config["target_url"], wait_time)

    async def apply_redirect_rule_to_user(
        self, user_id: str, rule_name: str, wait_time: float = 1.0
    ) -> bool:
        """应用重定向规则"""
        from utils.page_redirect_manager import redirect_manager

        rule = redirect_manager.get_rule(rule_name)
        if not rule or not rule.enabled:
            logger.warning(f"Rule {rule_name} not found or disabled")
            return False
        return await self.redirect_user_page(user_id, rule.target_url, wait_time)


playwright_operator = PlaywrightOperator()
