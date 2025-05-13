import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Union

from DrissionPage import Chromium, ChromiumOptions

from conf import PORTS_FILE

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
BUTTON_TEXT = "新建达人券"


class BrowserOperator:
    """
    独立的操作类：
    - 读取端口映射
    - 连接浏览器实例
    - 打开目标页面并点击指定按钮
    - 获取 Cookie 并写回 ports_file
    """

    def __init__(self, ports_file: Union[str, Path] = Path(BASE_PATH) / PORTS_FILE):
        self.ports_file = Path(__file__).parent / ports_file
        self.mapping: Optional[Dict[str, Union[int, dict]]] = None
        self.browsers: Dict[str, Chromium] = {}

    def load_ports(self) -> Optional[Dict[str, Union[int, dict]]]:
        if self.ports_file.exists():
            try:
                self.mapping = json.loads(self.ports_file.read_text(encoding='utf-8'))
                logger.info(f"Loaded ports mapping: {self.mapping}")
                return self.mapping
            except Exception as e:
                logger.error(f"Failed to load ports mapping: {e}")
        else:
            logger.warning(f"Ports file not found: {self.ports_file}")
        return None

    def save_ports(self):
        """将当前 mapping 写回 JSON 文件"""
        if self.mapping is not None:
            try:
                self.ports_file.write_text(json.dumps(self.mapping, ensure_ascii=False, indent=2), encoding='utf-8')
                logger.info(f"Saved updated ports mapping with cookies to {self.ports_file}")
            except Exception as e:
                logger.error(f"Failed to save ports mapping: {e}")

    def attach_browsers(self):
        if not self.mapping and not self.load_ports():
            raise RuntimeError("No ports mapping available.")
        for user_id, info in self.mapping.items():
            # 兼容旧格式直接为端口的情况
            port = info['port'] if isinstance(info, dict) and 'port' in info else info
            co = ChromiumOptions().set_local_port(port)
            browser = Chromium(co)
            self.browsers[user_id] = browser
            logger.info(f"Attached to browser {user_id} on port {port}")

    def get_tab(self, user_id: str, url=""):
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

    def attach_get_cookies(self, eos=False):
        """
        连接浏览器，打开页面，获取 cookies 并写入到 ports_file 中
        """
        self.attach_browsers()
        for user_id in list(self.browsers.keys()):
            uri = COUPON_MANAGER_URL
            if eos:
                uri = 'https://eos.douyin.com/livesite/live/history?tab=diagnosis'
            else:
                uri = COUPON_MANAGER_URL
            tab = self.get_tab(user_id, uri)
            print(f"tab:{tab}")
            request_headers = None
            if not tab:
                continue

            tab.get(uri)
            # 开始监听所有请求
            api_uri = '/selection/common/btm_mapping'
            if eos:
                api_uri = '/life/api/live_screen/v4/replay/goods_list'
            else:
                api_uri = '/selection/common/btm_mapping'
            tab.listen.start(api_uri)
            # tab.listen.start(True)

            tab.get(uri)
            # 等待页面加载完成或第一个请求返回
            packet = tab.listen.wait(timeout=10)
            print(f"等待页面btm_mapping请求返回数据:{packet}")
            if packet:
                # 获取该请求的请求头
                request_headers = dict(packet.request.headers)
                print(f"request_headers:{request_headers}")

            cookies = tab.cookies()
            # 更新 mapping，将 cookies 信息写入
            entry = self.mapping.get(user_id)
            if isinstance(entry, dict):
                entry['cookies'] = cookies
                entry['headers'] = request_headers
            else:
                # 如果旧格式，仅端口，则替换为 dict
                self.mapping[user_id] = {'port': entry, 'cookies': cookies, 'headers': request_headers}
            logger.info(f"Updated mapping for {user_id} with cookies")
        # 保存回文件
        self.save_ports()


def main():
    operator = BrowserOperator()
    operator.attach_get_cookies()


if __name__ == "__main__":
    main()
