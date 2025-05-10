import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Union

from DrissionPage import Chromium, ChromiumOptions
from DrissionPage.errors import ElementNotFoundError

from app import PORTS_FILE

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(BASE_PATH)
# ——— 日志配置 ———
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

COUPON_MANAGER_URL = (
    "https://buyin.jinritemai.com/dashboard/marketing/coupon-manager"
    "?pre_universal_page_params_id=&universal_page_params_id="
    "8d19445a-fe2f-4e76-a3cb-5571dcc66afe"
)
BUTTON_TEXT = "新建达人券"


class BrowserOperator:
    """
    独立的操作类：
    - 读取端口映射
    - 连接浏览器实例
    - 打开目标页面并点击指定按钮
    """

    def __init__(self, ports_file: Union[str, Path] = Path(BASE_PATH) / PORTS_FILE):
        self.ports_file = Path(__file__).parent / ports_file
        self.mapping: Optional[Dict[str, int]] = None
        self.browsers: Dict[str, Chromium] = {}

    def load_ports(self) -> Optional[Dict[str, int]]:
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

    def attach_browsers(self):
        if not self.mapping and not self.load_ports():
            raise RuntimeError("No ports mapping available.")
        for user_id, port in self.mapping.items():
            co = ChromiumOptions().set_local_port(port)
            browser = Chromium(co)
            self.browsers[user_id] = browser
            logger.info(f"Attached to browser {user_id} on port {port}")

    def get_tab(self, user_id: str):
        browser = self.browsers.get(user_id)
        if not browser:
            raise RuntimeError(f"Browser for {user_id} not attached.")
        return browser.get_tab(browser.tabs_count - 1)

    def find(self, user_id: str, locator: Union[str, tuple], mode: str = 'single', timeout: float = 5, ele=None,
             next_el=None, prev_el=None):
        tab = self.get_tab(user_id)
        try:
            if mode == 'single':
                if ele:
                    return ele.ele(locator, timeout=timeout)
                if next_el:
                    return tab.ele(locator, timeout=timeout).next()
                if prev_el:
                    return tab.ele(locator, timeout=timeout).prev()
                return tab.ele(locator, timeout=timeout)
            else:
                if ele:
                    return ele.eles(locator, timeout=timeout)
                return tab.eles(locator, timeout=timeout)
        except ElementNotFoundError:
            logger.warning(f"Element not found: {locator} in {user_id}")
            return None if mode == 'single' else []

    def click(self, user_id: str, locator: Union[str, tuple], ele=None, parent=False, child=False, by_js=None):
        el = self.find(user_id, mode="single", locator=locator, ele=ele)
        if el:
            if parent:
                el = el.parent().click()

            if child:
                el = el.child().click()

            el.hover()
            el.click(by_js=by_js)
            logger.info(f"Clicked {locator} in {user_id}")
        else:
            logger.error(f"Cannot click, element not found: {locator} in {user_id}")

    def type(self, user_id: str, locator: Union[str, tuple], text: str, clear: bool = True):
        el = self.find(user_id, locator)
        if el:
            if clear:
                el.clear()
            el.focus()
            el.input(text)
            logger.info(f"Typed '{text}' into {locator} in {user_id}")
        else:
            logger.error(f"Cannot type, element not found: {locator} in {user_id}")

    def set_date_range(self, user_id: str, start: str, end: str):
        """
        稳定填写日期范围：先填写开始，再填写结束
        """
        self.type(user_id, "css=input#apply_time_by_range", start)
        self.type(user_id, "xpath=(//input[@placeholder='结束日期'])[1]", end)
        self.click(user_id, "xpath=//body")
        logger.info(f"Set date range {start} - {end} for {user_id}")

    def open_url(self, user_id: str, url: str):
        browser = self.browsers.get(user_id)
        if not browser:
            logger.error(f"Browser for {user_id} not attached.")
            return None
        tab = browser.new_tab(url=url)
        tab.wait(5)
        return tab

    def attach_and_click_new_coupon(self):
        self.attach_browsers()
        for user_id in self.browsers:
            tab = self.open_url(user_id, COUPON_MANAGER_URL)
            marketing_ele = self.find(user_id, "#marketing")
            self.click(user_id, "xpath=//button[contains(@class,'auxo-btn') and .//span[text()='新建达人券']]",
                       ele=marketing_ele)

            form_ele = self.find(user_id, "css=form.auxo-form.auxo-form-horizontal")
            radio_locator = (
                "xpath=//div[contains(@class,'index-RadioCardContainer') "
                "and .//div[contains(@class,'index-title') and text()='直播间推广']]"
            )
            self.click(user_id, radio_locator)
            self.type(user_id, "#coupon_name", "测试券")
            self.click(user_id, "text:活动提交后一定时间内可领取")
            # apply_time_after_submit
            self.click(user_id, "#apply_time_after_submit", ele=form_ele, parent=True)
            rc_virtual_list = self.find(user_id,
                                        "div.rc-virtual-list div.rc-virtual-list-holder div "
                                        "div.rc-virtual-list-holder-inner"
                                        )
            self.click(user_id, locator='@label=3小时', ele=rc_virtual_list)
            # self.click(user_id, "text:固定开始和结束时间")
            # self.set_date_range(user_id, '2025/05/09 14:44:37', '2025/05/16 20:00:00')
            type_text = "text:全部用户可领"
            # type_text = "text:粉丝可领取"
            self.click(user_id, type_text, parent=True, ele=form_ele)
            tab.wait(2)
            type_text = "text:商品满减券"
            # type_text = "text:商品直减券"
            self.click(user_id, type_text, parent=True, ele=form_ele)
            tab.wait(2)
            if type_text == "text:商品直减券":
                self.type(user_id, "#credit", "10")
            else:
                self.type(user_id, "#threshold", "10")
                self.type(user_id, "#credit", "2")

            self.type(user_id, "#total_amount", "1")
            # self.click(user_id, "text:活动提交后一定时间内可使用", ele=form_ele)

            self.click(user_id, "text:活动结束后一定时间内可使用", ele=form_ele, parent=True)
            self.click(user_id, "#use_time_after_finish", ele=form_ele, parent=True)
            use_time_after_finish_list = self.find(user_id,
                                                   'div#use_time_after_finish_list+div>div.rc-virtual-list-holder>div>div.rc-virtual-list-holder-inner')

            self.click(user_id, locator='@label=3小时', ele=use_time_after_finish_list, by_js=False)
            # self.click(user_id, "text:立即提交", ele=form_ele)

            # self.click(user_id, "text:固定开始和结束时间", ele=form_ele)
            # self.click(user_id, "text:选择商品", ele=form_ele)

    def attach_get_cookies(self):
        self.attach_browsers()
        for user_id in self.browsers:
            tab = self.open_url(user_id, COUPON_MANAGER_URL)
            cookies = tab.cookies()
            print(cookies)


def main():
    operator = BrowserOperator()
    operator.attach_get_cookies()


if __name__ == "__main__":
    main()
