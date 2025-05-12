import json
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from DrissionPage._base.chromium import Chromium
from DrissionPage._configs.chromium_options import ChromiumOptions

from log.logger import logger


def get_absolute_extension_path(relative_path: str) -> str:
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent
    extension_path = base_dir / relative_path
    absolute_path = extension_path.resolve(strict=True)
    if platform.system() == 'Windows':
        win_path = str(absolute_path)
        if any(c in win_path for c in (' ', '&', '^')):
            win_path = f'"{win_path}"'
        try:
            from ctypes import windll, create_unicode_buffer
            buffer = create_unicode_buffer(256)
            if windll.kernel32.GetShortPathNameW(win_path, buffer, 256):
                win_path = buffer.value
        except Exception:
            pass
        return win_path
    return str(absolute_path)


@dataclass
class BrowserConfig:
    extension_path: str = get_absolute_extension_path("extensions/live_room")
    data_dir_base: Path = Path("browser_data") / "douyin"


class BrowserManager:
    def __init__(self, user_id: str, port=9111):
        self.user_id = user_id
        self.port = port
        self.config = BrowserConfig()
        self.user_data_dir = self.config.data_dir_base / user_id
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.last_urls_file = self.user_data_dir / "last_urls.json"
        if not self.last_urls_file.exists():
            self.last_urls_file.touch()
        self.browser: Optional[Chromium] = None

    def initialize(self) -> bool:
        try:
            # 配置并启动 Chromium（持久化用户数据）
            co = ChromiumOptions().set_local_port(self.port).set_user_data_path(str(self.user_data_dir))
            co.add_extension(self.config.extension_path)
            # 如需加载扩展，可用 co.set_args([...])
            co.set_argument('--start-maximized')
            self.browser = Chromium(co)
            logger.info(f"Browser started for user: {self.user_id}")

            urls = json.loads(self.last_urls_file.read_text() or "[]")
            print('urls:', urls)
            for url in urls:
                tab = self.browser.new_tab(url=url)
                # 注入用户标签
                tab.run_js(f"""
                                                                                    const d = document.createElement('div');
                                                                                    d.innerText = 'Browser ID: {self.user_id}';
                                                                                    Object.assign(d.style, {{
                                                                                      position:'fixed',top:'10px',left:'10px',
                                                                                      background:'rgba(0,0,0,0.6)',color:'white',
                                                                                      padding:'5px 10px',zIndex:999999,
                                                                                      borderRadius:'8px',fontSize:'14px'
                                                                                    }});
                                                                                    document.body.appendChild(d);
                                                                                """)

            tab = self.browser.new_tab(url="about:blank")
            tab.run_js(f"""document.title='{self.user_id}'""")

            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            self.cleanup()
            return False

    def cleanup(self):
        try:
            if self.browser:
                urls = []
                seen = set()  # 用于去重
                for i in range(self.browser.tabs_count):
                    tab = self.browser.get_tab(i)
                    url = tab.url
                    if url and url != 'about:blank' and url not in seen:
                        urls.append(url)
                        seen.add(url)
                        logger.debug(f"[Tab {i}] Saved URL: {url}")  # 可选调试输出

                if urls:
                    self.last_urls_file.write_text(json.dumps(urls, ensure_ascii=False, indent=2))
                    logger.info(f"✅ Saved {len(urls)} unique URLs.")
                else:
                    logger.info("ℹ️ No URLs to save.")

                self.browser.quit()
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}", exc_info=True)

    @property
    def is_running(self) -> bool:
        return self.browser is not None

    @property
    def uptime(self) -> Optional[float]:
        return time.time() - self.browser.start_time if self.browser else None
