import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Union

from DrissionPage import Chromium, ChromiumOptions

from conf import PORTS_FILE

# ——— 日志配置 ———
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BAIYING_LOGIN_PAGE_URL = 'https://buyin.jinritemai.com/mpa/account/login'
COUPON_MANAGER_URL = (
    "https://buyin.jinritemai.com/dashboard/marketing/coupon-manager?pre_universal_page_params_id=&universal_page_params_id=8d19445a-fe2f-4e76-a3cb-5571dcc66afe"
)

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
    独立的操作类：
    - 读取端口映射
    - 连接浏览器实例
    - 打开目标页面并点击指定按钮
    - 获取 Cookie 并写回 ports_file
    """

    def __init__(
            self,
            ports_file: Union[str, Path] = Path(BASE_PATH) / PORTS_FILE
    ):
        self.ports_file = Path(__file__).parent / ports_file
        self.mapping: Optional[Dict[str, Union[int, dict]]] = None
        self.browsers: Dict[str, Chromium] = {}

    def load_ports(self) -> Optional[Dict[str, Union[int, dict]]]:
        if self.ports_file.exists():
            try:
                self.mapping = json.loads(
                    self.ports_file.read_text(encoding='utf-8')
                )
                logger.info(f"Loaded ports mapping: {self.mapping}")
                return self.mapping
            except Exception as e:
                logger.error(f"Failed to load ports mapping: {e}")
        else:
            logger.warning(f"Ports file not found: {self.ports_file}")
        return None

    def save_ports(self):
        if not self.mapping:
            return
        try:
            self.ports_file.write_text(
                json.dumps(self.mapping, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            logger.info(f"Saved updated ports mapping with cookies to {self.ports_file}")
        except Exception as e:
            logger.error(f"Failed to save ports mapping: {e}")

    def attach_browsers(self):
        if not self.mapping and not self.load_ports():
            raise RuntimeError("No ports mapping available.")
        for user_id, info in self.mapping.items():
            port = info['port'] if isinstance(info, dict) and 'port' in info else info
            co = ChromiumOptions().set_local_port(port)
            browser = Chromium(co)
            self.browsers[user_id] = browser
            logger.info(f"Attached to browser {user_id} on port {port}")

    def get_tab(self, user_id: str, url: str = ""):
        browser = self.browsers.get(user_id)
        if not browser:
            raise RuntimeError(f"Browser for {user_id} not attached.")
        return browser.get_tab(browser.tabs_count - 1, url=url)

    def open_url(self, user_id: str, url: str):
        browser = self.browsers.get(user_id)
        if not browser:
            logger.error(f"Browser for {user_id} not attached.")
            return None
        tab = browser.new_tab(url=url)
        tab.wait(5)
        return tab

    def fetch_cookies_and_headers(self, user_id: str, url: str, api_uri: str) -> dict:
        tab = self.get_tab(user_id, url)
        listener = RequestListener(tab, api_uri)
        tab.get(url)
        packet = listener.listen_for()
        headers = listener.get_request_headers()
        cookies = tab.cookies()
        return {"cookies": cookies, "headers": headers}

    def attach_get_cookies(self, eos: bool = False):
        self.attach_browsers()
        for user_id in list(self.browsers.keys()):
            target_url = COUPON_MANAGER_URL
            api_uri = '/selection/common/btm_mapping'
            if eos:
                target_url = (
                    'https://eos.douyin.com/livesite/live/history?tab=diagnosis'
                )
                api_uri = '/life/api/live_screen/v4/replay/goods_list'
            try:
                result = self.fetch_cookies_and_headers(
                    user_id, target_url, api_uri
                )
            except Exception as e:
                logger.error(f"Error fetching for {user_id}: {e}")
                continue

            entry = self.mapping.get(user_id)
            if isinstance(entry, dict):
                entry.update(result)
            else:
                self.mapping[user_id] = {"port": entry, **result}
            logger.info(f"Updated mapping for {user_id} with cookies and headers")

        self.save_ports()


def main():
    operator = BrowserOperator()
    operator.attach_get_cookies()


if __name__ == "__main__":
    main()
