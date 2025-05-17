import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from DrissionPage._base.chromium import Chromium
from DrissionPage._configs.chromium_options import ChromiumOptions

from conf import BASE_DIR
from utils.common_logger import get_logger

logger = get_logger(__name__)


def get_absolute_extension_path(relative_path: str) -> Path:
    # 以项目根目录为基准
    extension_path = Path(BASE_DIR) / relative_path
    return extension_path.resolve(strict=True)


@dataclass
class BrowserConfig:
    extension_path: str = get_absolute_extension_path("extensions/live_room")
    block_videos_extension_path: str = get_absolute_extension_path(
        "extensions/block_videos"
    )
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

    def get_user_blank_html_path(self):
        """
        为每个user_id生成专属的本地空白页，带user_id标识
        """
        static_dir = Path(BASE_DIR) / "static"
        static_dir.mkdir(exist_ok=True)
        template_path = static_dir / "blank.html"
        user_blank_path = static_dir / f"blank_{self.user_id}.html"
        # 如果模板不存在，自动生成一个简单模板
        if not template_path.exists():
            template_path.write_text(
                """<!DOCTYPE html>\n<html lang='zh-CN'>\n<head>\n<meta charset='UTF-8'>\n<title>【USER_ID】</title>\n<style>body{background:#fff;}#user-id-tag{position:fixed;top:10px;left:10px;background:#333;color:#fff;padding:8px 16px;border-radius:8px;font-size:16px;z-index:9999;}</style>\n</head>\n<body><div id='user-id-tag'>Browser ID: 【USER_ID】</div></body>\n</html>\n""",
                encoding="utf-8",
            )
        html = template_path.read_text(encoding="utf-8").replace(
            "【USER_ID】", self.user_id
        )
        user_blank_path.write_text(html, encoding="utf-8")
        return user_blank_path.as_uri()

    def initialize(self) -> bool:
        try:
            # 配置并启动 Chromium（持久化用户数据）
            co = (
                ChromiumOptions()
                .set_local_port(self.port)
                .set_user_data_path(str(self.user_data_dir))
                .set_argument("--disable-features=MediaSource")
            )
            co.add_extension(self.config.extension_path)
            co.add_extension(self.config.block_videos_extension_path)
            # 如需加载扩展，可用 co.set_args([...])
            co.set_argument("--start-maximized")
            self.browser = Chromium(co)
            logger.info(f"Browser started for user: {self.user_id}")

            urls = json.loads(self.last_urls_file.read_text() or "[]")
            print("urls:", urls)
            tabs = self.browser.get_tabs()
            print("tabs:", tabs)
            for url in urls:
                # 判断url是否已经被打开
                if url in [tab.url for tab in tabs]:
                    continue
                tab = self.browser.new_tab(url=url)
                # 注入用户标签
                tab.run_js(
                    f"""
                                                                                    const d = document.createElement('div');
                                                                                    d.innerText = 'Browser ID: {self.user_id}';
                                                                                    Object.assign(d.style, {{
                                                                                      position:'fixed',top:'10px',left:'10px',
                                                                                      background:'rgba(0,0,0,0.6)',color:'white',
                                                                                      padding:'5px 10px',zIndex:999999,
                                                                                      borderRadius:'8px',fontSize:'14px'
                                                                                    }});
                                                                                    document.body.appendChild(d);
                                                                                """
                )

            # 打开自定义本地空白页
            blank_url = self.get_user_blank_html_path()
            self.browser.new_tab(url=blank_url)
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
                    if (
                            url
                            and not url.startswith("chrome://")
                            and url != "about:blank"
                            and "/qw-browser/static" not in url
                            and url not in seen
                    ):
                        urls.append(url)
                        seen.add(url)
                        logger.debug(f"[Tab {i}] Saved URL: {url}")  # 可选调试输出

                if urls:
                    self.last_urls_file.write_text(
                        json.dumps(urls, ensure_ascii=False, indent=2)
                    )
                    logger.info(f"✅ Saved {len(urls)} unique URLs.")
                else:
                    logger.info("ℹ️ No URLs to save.")

                self.browser.quit()

            # 清理 user_blank_path 文件
            static_dir = Path(BASE_DIR) / "static"
            user_blank_path = static_dir / f"blank_{self.user_id}.html"
            if user_blank_path.exists():
                try:
                    user_blank_path.unlink()
                    logger.info(f"已删除本地空白页缓存: {user_blank_path}")
                except Exception as e:
                    logger.warning(f"删除本地空白页缓存失败: {e}")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}", exc_info=True)

    @property
    def is_running(self) -> bool:
        return self.browser is not None

    @property
    def uptime(self) -> Optional[float]:
        return time.time() - self.browser.start_time if self.browser else None
