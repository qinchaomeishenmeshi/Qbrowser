import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Union

from conf import PORTS_FILE
from service.browser_service import browser_service

# ——— 日志配置 ———
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BAIYING_LOGIN_PAGE_URL = "https://buyin.jinritemai.com/mpa/account/login"
COUPON_MANAGER_URL = "https://buyin.jinritemai.com/dashboard/marketing/coupon-manager?pre_universal_page_params_id=&universal_page_params_id=8d19445a-fe2f-4e76-a3cb-5571dcc66afe"

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
            logger.error(f"Listening for {self.api_uri} timed out: {e}")
        finally:
            self.tab.listen.stop()

    def get_request_headers(self) -> Optional[dict]:
        if self.packet:
            return dict(self.packet.request.headers)
        return None


class BrowserOperator:
    """
    只负责操作，所有实例管理交给 browser_service。
    端口映射只做兼容展示。
    """

    def __init__(self, ports_file: Union[str, Path] = Path(BASE_PATH) / PORTS_FILE):
        self.ports_file = Path(__file__).parent / ports_file
        self.mapping: Optional[Dict[str, Union[int, dict]]] = None

    def load_ports(self) -> Optional[Dict[str, Union[int, dict]]]:
        if self.ports_file.exists():
            try:
                self.mapping = json.loads(self.ports_file.read_text(encoding="utf-8"))
                logger.info(f"Loaded ports mapping: {self.mapping}")
                return self.mapping
            except Exception as e:
                logger.error(f"Failed to load ports mapping: {e}")
        else:
            logger.warning(f"Ports file not found: {self.ports_file}")
        return None

    def save_ports(self):
        # 只保存 cookies/headers 相关信息，不再保存端口分配
        if not self.mapping:
            return
        try:
            self.ports_file.write_text(
                json.dumps(self.mapping, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logger.info(
                f"Saved updated ports mapping with cookies to {self.ports_file}"
            )
        except Exception as e:
            logger.error(f"Failed to save ports mapping: {e}")

    @staticmethod
    def fetch_cookies_and_headers(
            browser, user_id: str, url: str, api_uri: str
    ) -> dict:
        tab = browser.get_tab(browser.tabs_count - 1, url=url)
        listener = RequestListener(tab, api_uri)
        tab.get(url)
        packet = listener.listen_for()
        headers = listener.get_request_headers()
        cookies = tab.cookies()
        return {"cookies": cookies, "headers": headers}

    async def attach_get_cookies(self, user_ids=None):
        self.load_ports()
        if user_ids is None:
            user_ids = list(self.mapping.keys())
        try:
            for user_id in user_ids:
                print(f"处理 user_id: {user_id}")
                manager = await browser_service.get_or_create_browser(user_id)
                if not manager:
                    print(f"manager is None for {user_id}")
                    continue
                if not manager.is_running:
                    print(f"manager not running for {user_id}")
                    continue
                print(f"manager is running for {user_id}")
                browser = manager.browser
                target_url = COUPON_MANAGER_URL
                api_uri = "/selection/common/btm_mapping"
                try:
                    print(f"即将抓取 {user_id} 的 cookies/headers")
                    result = self.fetch_cookies_and_headers(
                        browser, user_id, target_url, api_uri
                    )
                except Exception as e:
                    print(f"fetch_cookies_and_headers error for {user_id}: {e}")
                    logger.error(f"Error fetching for {user_id}: {e}")
                    continue

                entry = self.mapping.get(user_id)
                if isinstance(entry, dict):
                    entry.update(result)
                else:
                    self.mapping[user_id] = {"port": entry, **result}
                logger.info(f"Updated mapping for {user_id} with cookies and headers")

            self.save_ports()
        except Exception as e:
            logger.error(f"Error attaching cookies {e}")


def main():
    operator = BrowserOperator()
    operator.attach_get_cookies("wh001,wh002")


if __name__ == "__main__":
    main()
