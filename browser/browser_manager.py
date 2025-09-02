import codecs
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

from DrissionPage._base.chromium import Chromium
from DrissionPage._configs.chromium_options import ChromiumOptions

from conf import BASE_DIR, resource_path
from conf.browser_config import chrome_path_manager
from utils.common_logger import get_logger

logger = get_logger(__name__)


def get_absolute_extension_path(relative_path: str) -> str:
    """获取插件的绝对路径
    
    Args:
        relative_path: 相对路径
        
    Returns:
        插件的绝对路径字符串
    """
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
    """浏览器管理器类
    
    负责单个浏览器实例的生命周期管理，包括初始化、配置、启动和清理。
    """
    
    def __init__(self, user_id: str, port: int = 9111) -> None:
        """初始化浏览器管理器
        
        Args:
            user_id: 用户ID
            port: 浏览器调试端口，默认9111
        """
        self.user_id = user_id
        self.port = port
        self.config = BrowserConfig()
        self.user_data_dir = self.config.data_dir_base / user_id
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.last_urls_file = self.user_data_dir / "last_urls.json"
        if not self.last_urls_file.exists():
            self.last_urls_file.touch()
        self.browser: Optional[Chromium] = None

    def inject_user_tag_to_tab(self, tab) -> bool:
        """为指定标签页注入用户标签
        
        Args:
            tab: 要注入用户标签的标签页对象
            
        Returns:
            注入成功返回True，失败返回False
        """
        try:
            tab.run_js(
                 f"""
                 (function() {{
                     function injectUserTag() {{
                         // 检查是否已经存在用户标签，避免重复注入
                         const existingTag = document.querySelector('[data-user-tag="{self.user_id}"]');
                         if (existingTag) {{
                             return;
                         }}
                         
                         const d = document.createElement('div');
                         d.innerText = 'Browser ID: {self.user_id}';
                         d.setAttribute('data-user-tag', '{self.user_id}');
                         Object.assign(d.style, {{
                             position: 'fixed',
                             top: '10px',
                             left: '10px',
                             background: 'rgba(0,0,0,0.6)',
                             color: 'white',
                             padding: '5px 10px',
                             zIndex: 999999,
                             borderRadius: '8px',
                             fontSize: '14px'
                         }});
                         
                         // 使用更可靠的方法添加元素
                         function appendElement() {{
                             if (document.body) {{
                                 document.body.appendChild(d);
                             }} else if (document.documentElement) {{
                                 document.documentElement.appendChild(d);
                             }} else {{
                                 // 最后的备选方案，延迟执行
                                 setTimeout(appendElement, 100);
                             }}
                         }}
                         
                         // 立即尝试添加，如果失败则延迟重试
                         try {{
                             appendElement();
                         }} catch (e) {{
                             setTimeout(appendElement, 500);
                         }}
                     }}
                     
                     // 如果页面还在加载，等待加载完成后注入
                     if (document.readyState === 'loading') {{
                         document.addEventListener('DOMContentLoaded', function() {{
                             setTimeout(injectUserTag, 100);
                         }});
                     }} else {{
                         // 页面已加载完成，延迟执行注入函数
                         setTimeout(injectUserTag, 100);
                     }}
                 }})();
                 """
            )
            return True
        except Exception as js_error:
            logger.warning(f"注入用户标签失败: {js_error}")
            return False
    
    def create_tab_with_user_tag(self, url: str = None):
        """创建新标签页并自动注入用户标签
        
        Args:
            url: 要打开的URL，如果为None则打开空白页
            
        Returns:
            创建的标签页对象
        """
        if not self.browser:
            raise RuntimeError("浏览器实例不存在")
            
        tab = self.browser.new_tab(url=url)
        
        # 等待页面开始加载
        time.sleep(0.5)
        
        # 注入用户标签
        self.inject_user_tag_to_tab(tab)
        
        return tab

    def get_user_blank_html_path(self) -> str:
        """为每个用户生成专属的本地空白页
        
        为每个 user_id 生成专属的本地空白页，带 user_id 标识。
        模板和生成的 html 都放在 BASE_DIR/static 下，避免 PyInstaller 路径混乱。
        
        Returns:
            生成的本地 html 文件的 file:// URI 路径
            
        Raises:
            Exception: 文件读写操作失败时抛出异常
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
        """初始化浏览器实例
        
        配置并启动Chromium浏览器，加载插件，恢复上次打开的标签页。
        
        Returns:
            初始化成功返回True，失败返回False
            
        Raises:
            Exception: 浏览器初始化过程中发生的任何异常
        """
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
            co = ChromiumOptions()
            
            # 设置自定义Chrome路径（如果配置了的话）
            chrome_path = chrome_path_manager.get_chrome_path()
            if chrome_path:
                logger.info(f"使用Chrome路径: {chrome_path}")
                co.set_browser_path(chrome_path)
            else:
                logger.warning("未找到Chrome路径，将使用系统默认")
            
            # 设置其他配置
            co.set_local_port(self.port)
            co.set_user_data_path(str(self.user_data_dir))
            co.set_argument("--window-size", "1910,1070")
            
            # 启用扩展相关参数
            co.set_argument("--enable-extensions")
            co.set_argument("--no-default-browser-check")
            # 注意：不要使用 --disable-extensions-except，它会导致扩展加载失败
            # co.set_argument("--disable-extensions-except")
            # co.set_argument("--allowlisted-extension-id=*")
            
            # 移除可能导致扩展加载问题的参数
            # co.set_argument("--enable-automation")
            # co.set_argument("--disable-blink-features=AutomationControlled")
            
            # 使用--load-extension参数加载插件（更可靠的方式）
            if valid_extensions:
                extension_paths = ",".join(valid_extensions)
                co.set_argument(f"--load-extension={extension_paths}")
                logger.info(f"[OK] 使用--load-extension加载插件: {len(valid_extensions)}个")
                logger.info(f"[OK] 扩展路径: {extension_paths}")
            else:
                logger.warning("[WARNING] 没有有效的插件可以加载")
            
            # DrissionPage 4.1.x 兼容性改进

            
            try:

            
                self.browser = Chromium(co)

            
                # 等待浏览器完全启动

            
                time.sleep(1)

            
                # 验证浏览器是否正常运行

            
                if not self.browser or not hasattr(self.browser, 'tabs_count'):

            
                    raise Exception("浏览器启动失败或状态异常")

            
                logger.info(f"浏览器启动成功，当前标签页数量: {self.browser.tabs_count}")

            
            except Exception as e:

            
                logger.error(f"浏览器启动失败: {e}")

            
                if hasattr(self, 'browser') and self.browser:

            
                    try:

            
                        self.browser.quit()

            
                    except:

            
                        pass

            
                raise
            logger.info(f"Browser started for user: {self.user_id}")

            urls = json.loads(self.last_urls_file.read_text() or "[]")
            print("urls:", urls)
            tabs = self.browser.get_tabs()
            print("tabs:", tabs)
            for url in urls:
                # 判断url是否已经被打开
                if url in [tab.url for tab in tabs]:
                    continue
                try:
                    tab = self.browser.new_tab(url=url)
                    # 等待页面完全加载
                    time.sleep(2)
                    # 检查页面连接状态
                    if hasattr(tab, 'url') and tab.url:
                        # 使用新的注入方法
                        self.inject_user_tag_to_tab(tab)
                    else:
                        logger.warning(f"页面连接异常，跳过标签注入: {url}")
                except Exception as e:
                    logger.warning(f"打开页面失败: {url}, 错误: {e}")
                    continue

            # 打开自定义本地空白页
            try:
                blank_url = self.get_user_blank_html_path()
                blank_tab = self.browser.new_tab(url=blank_url)
                time.sleep(1)  # 等待空白页加载
                logger.info(f"成功打开自定义空白页: {blank_url}")
            except Exception as e:
                logger.warning(f"打开自定义空白页失败: {e}")
            
            # 设置自动重定向
            try:
                # 导入自动重定向模块
                from browser.auto_redirect import auto_redirect
                
                # 为浏览器设置自动重定向
                if auto_redirect.setup_browser(self.browser):
                    logger.info(f"✅ 成功为用户 {self.user_id} 设置自动重定向")
                else:
                    logger.warning(f"⚠️ 为用户 {self.user_id} 设置自动重定向失败")
            except Exception as e:
                logger.error(f"❌ 设置自动重定向时出错: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            self.cleanup()
            return False

    def cleanup(self) -> None:
        """清理浏览器实例和相关资源
        
        保存当前打开的标签页URL，关闭浏览器，清理临时文件。
        
        Raises:
            Exception: 清理过程中发生的任何异常
        """
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
                    # 重写last_urls_file为空
                    self.last_urls_file.write_text("[]")
                    logger.info("[INFO] No URLs to save.")

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
        """检查浏览器是否正在运行
        
        Returns:
            浏览器实例存在且运行中返回True，否则返回False
        """
        return self.browser is not None

    def close(self) -> None:
        """关闭浏览器实例
        
        直接关闭浏览器，不保存状态。
        """
        if self.browser:
            self.browser.quit()
            logger.info(f"Browser closed for user: {self.user_id}")

    @property
    def uptime(self) -> Optional[float]:
        """获取浏览器运行时间
        
        Returns:
            浏览器运行时间（秒），如果浏览器未运行则返回None
        """
        return time.time() - self.browser.start_time if self.browser else None
