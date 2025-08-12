import codecs
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from DrissionPage._base.chromium import Chromium
from DrissionPage._configs.chromium_options import ChromiumOptions

from conf import BASE_DIR, resource_path
from utils.common_logger import get_logger

logger = get_logger(__name__)


def get_absolute_extension_path(relative_path: str) -> str:
    # 兼容打包exe后的情况，使用resource_path确保路径正确
    try:
        # 首先尝试使用resource_path（兼容打包后的情况）
        extension_path = Path(resource_path(relative_path))
        if extension_path.exists():
            return str(extension_path.resolve())
    except Exception as e:
        logger.debug(f"resource_path方式失败: {e}")
    
    # 回退到BASE_DIR方式
    extension_path = Path(BASE_DIR) / relative_path
    return str(extension_path.resolve())


@dataclass
class BrowserConfig:
    def __post_init__(self):
        # 在实例化时动态计算路径，避免类定义时的路径问题
        self.live_room_extension_path = get_absolute_extension_path("extensions/live_room")
        self.block_videos_extension_path = get_absolute_extension_path("extensions/block_videos")
    
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

    def get_user_blank_html_path(self) -> str:
        """
        为每个 user_id 生成专属的本地空白页，带 user_id 标识。
        - 模板和生成的 html 都放在 BASE_DIR/static 下，避免 PyInstaller 路径混乱。
        - 返回生成的本地 html 文件的 file:// URI 路径。
        """
        static_dir = Path(resource_path("static"))
        static_dir.mkdir(parents=True, exist_ok=True)

        template_path = static_dir / "blank.html"
        default_template = (
            "<!DOCTYPE html>\n"
            "<html lang='zh-CN'>\n"
            "<head>\n"
            "<meta charset='UTF-8'>\n"
            "<title>【USER_ID】</title>\n"
            "<style>body{background:#fff;}#user-id-tag{position:fixed;top:10px;left:10px;background:#333;color:#fff;padding:8px 16px;border-radius:8px;font-size:16px;z-index:9999;}</style>\n"
            "</head>\n"
            "<body><div id='user-id-tag'>Browser ID: 【USER_ID】</div></body>\n"
            "</html>\n"
        )

        # 如果模板不存在，写入默认模板
        if not template_path.exists():
            try:
                template_path.write_text(default_template, encoding="utf-8")
            except Exception as e:
                logger.error(f"写入默认模板失败: {e}")
                template_content = default_template
            else:
                template_content = default_template
        else:
            try:
                template_content = template_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"读取模板失败: {e}")
                template_content = default_template

        html = template_content.replace("【USER_ID】", self.user_id)
        user_blank_path = static_dir / f"blank_{self.user_id}.html"
        try:
            if not user_blank_path.exists() or user_blank_path.read_text(encoding="utf-8") != html:
                user_blank_path.write_text(html, encoding="utf-8")
        except Exception as e:
            logger.error(f"写入用户专属空白页失败: {e}")

        return user_blank_path.as_uri()

    def initialize(self) -> bool:
        try:
            # 检查插件路径是否存在
            valid_extensions = []
            
            if Path(self.config.live_room_extension_path).exists():
                valid_extensions.append(self.config.live_room_extension_path)
                logger.info(f"[OK] Live Room 插件路径有效: {self.config.live_room_extension_path}")
            else:
                logger.warning(f"[WARNING] Live Room 插件路径不存在: {self.config.live_room_extension_path}")
            
            if Path(self.config.block_videos_extension_path).exists():
                valid_extensions.append(self.config.block_videos_extension_path)
                logger.info(f"[OK] Block Videos 插件路径有效: {self.config.block_videos_extension_path}")
            else:
                logger.warning(f"[WARNING] Block Videos 插件路径不存在: {self.config.block_videos_extension_path}")
            
            # 配置并启动 Chromium（持久化用户数据）
            co = (
                ChromiumOptions()
                .set_local_port(self.port)
                .set_user_data_path(str(self.user_data_dir))
                .set_argument("--enable-extensions")
                .set_argument("--window-size", "1910,1070")
            )
            
            # 使用 add_extension() 方法加载插件（DrissionPage 推荐方式）
            if valid_extensions:
                for extension_path in valid_extensions:
                    logger.info(f"正在添加插件: {extension_path}")
                    co.add_extension(extension_path)
                logger.info(f"[OK] 已使用 add_extension() 方法加载插件: {len(valid_extensions)}个")
            else:
                logger.warning("[WARNING] 没有有效的插件可以加载")
            
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
                        and not url.startswith("file://")
                        and url not in seen
                    ):
                        urls.append(url)
                        seen.add(url)
                        logger.debug(f"[Tab {i}] Saved URL: {url}")  # 可选调试输出

                if urls:
                    self.last_urls_file.write_text(
                        json.dumps(urls, ensure_ascii=False, indent=2)
                    )
                    logger.info(f"[OK] Saved {len(urls)} unique URLs.")
                else:
                    logger.info("ℹ️ No URLs to save.")

                self.browser.quit()

            # 清理 user_blank_path 文件
            static_dir = Path(resource_path("static"))
            user_blank_path = static_dir / f"blank_{self.user_id}.html"
            if user_blank_path.exists():
                try:
                    user_blank_path.unlink()
                    logger.info(f"已删除本地空白页缓存: {user_blank_path}")
                except Exception as e:
                    logger.warning(f"删除本地空白页缓存失败: {e}")
        except Exception as e:
            logger.error(f"[ERROR] Cleanup error: {e}", exc_info=True)

    @property
    def is_running(self) -> bool:
        return self.browser is not None

    def close(self):
        if self.browser:
            self.browser.quit()
            logger.info(f"Browser closed for user: {self.user_id}")

    @property
    def uptime(self) -> Optional[float]:
        return time.time() - self.browser.start_time if self.browser else None
