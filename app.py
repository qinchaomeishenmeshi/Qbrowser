import asyncio
import logging
import platform
import threading
import time
from asyncio import Semaphore
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, List

from flask import Flask, request, render_template_string, jsonify
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from werkzeug.middleware.proxy_fix import ProxyFix

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


def get_absolute_extension_path(relative_path: str) -> str:
    """跨平台安全的绝对路径获取"""
    base_dir = Path(__file__).parent

    # 构建完整路径对象
    extension_path = base_dir / relative_path

    # 转换为绝对路径并解析符号链接
    absolute_path = extension_path.resolve(strict=True)

    # Windows特殊处理
    if platform.system() == 'Windows':
        # 转换为Windows原生路径格式
        win_path = str(absolute_path)

        # 处理空格和特殊字符
        if any(c in win_path for c in (' ', '&', '^')):
            win_path = f'"{win_path}"'

        # 可选：转换为短路径格式（8.3格式）
        try:
            from ctypes import windll, create_unicode_buffer
            buffer = create_unicode_buffer(256)
            if windll.kernel32.GetShortPathNameW(win_path, buffer, 256):
                win_path = buffer.value
        except Exception:
            pass

        return win_path

    # 非Windows系统处理
    return str(absolute_path)


@dataclass
class BrowserConfig:
    """浏览器配置数据类"""
    viewport_width: int = 1280
    viewport_height: int = 720
    base_url: str = "https://eos.douyin.com"
    extension_path = get_absolute_extension_path("extensions/live_room")

    data_dir_base: Path = Path("browser_data") / "douyin"


class BrowserManager:
    def __init__(self, user_id: str, config: Optional[BrowserConfig] = None):
        self.user_id = user_id
        self.config = config or BrowserConfig()
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.user_data_dir = self.config.data_dir_base / user_id
        self._playwright: Optional[Playwright] = None
        self._startup_time = None

    async def initialize(self) -> bool:
        """初始化浏览器上下文和页面"""
        try:
            # 新增：检查目录是否可用
            lock_file = self.user_data_dir / "SingletonLock"
            retry_count = 0
            while lock_file.exists():
                if retry_count >= 5:  # 最多重试5次
                    logger.error(f"用户目录 {self.user_data_dir} 被占用，放弃启动")
                    return False
                logger.warning(f"检测到目录 {self.user_data_dir} 被占用，等待释放...")
                await asyncio.sleep(2)
                retry_count += 1

            self._playwright = await async_playwright().start()
            print(f"扩展路径: {self.config.extension_path}")
            # context_args = {
            #     "user_data_dir": str(self.user_data_dir),
            #     "headless": False,
            #     "channel": "chrome",
            #     "args": [
            #         f"--disable-extensions-except={self.config.extension_path}",
            #         f"--load-extension={self.config.extension_path}",
            #     ],
            #     "viewport": {
            #         "width": self.config.viewport_width,
            #         "height": self.config.viewport_height
            #     },
            #     "permissions": ["geolocation"],
            # }

            self.context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=False,
                channel="chrome",
                args=[
                    f"--disable-extensions-except={self.config.extension_path}",
                    f"--load-extension={self.config.extension_path}",
                ], )
            # 增加一个空页作为浏览器标识
            empty_page = self.context.pages[0] if self.context.pages[0] else await self.context.new_page()
            # 设置浏览器标题为 user_id
            await empty_page.evaluate(f"document.title = '浏览器ID: {self.user_id}'")
            # 新打开一个页面
            self.page = await self.context.new_page()
            await self.page.goto(self.config.base_url)
            self._startup_time = asyncio.get_running_loop().time()

            logger.info(f"浏览器已启动，用户: {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {str(e)}", exc_info=True)
            await self.cleanup()
            return False

    async def cleanup(self):
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}", exc_info=True)
        finally:
            # 强制等待浏览器进程退出（避免残留）
            await asyncio.sleep(2)
            self.page = None
            self.context = None
            self._playwright = None

    @property
    def is_running(self) -> bool:
        """优化后的浏览器状态检测（线程安全/版本兼容/异常防护）"""
        try:
            return bool(self.context)
        except Exception:
            return False

    @property
    def uptime(self) -> Optional[float]:
        """获取运行时间（秒），修改为同步方式"""
        if self._startup_time and self.is_running:
            return time.time() - self._startup_time
        return None


class BrowserPool:
    def __init__(self, max_concurrent_instances: int = 10, idle_timeout: int = 3600):
        self.browser_managers: Dict[str, BrowserManager] = {}
        self.idle_timeout = idle_timeout
        self._local = threading.local()
        self._semaphore = Semaphore(max_concurrent_instances)  # 限制最大并发实例数

    async def cleanup_old_instances(self):
        """定期清理闲置实例（可配合定时任务调用）"""
        now = time.time()
        for user_id, manager in list(self.browser_managers.items()):
            if manager.uptime and now - (manager.uptime or 0) > self.idle_timeout:
                await self.cleanup_user(user_id)

    async def initialize_user(self, user_id: str) -> bool:
        """初始化用户浏览器，使用信号量限制并发"""
        async with self._semaphore:
            try:
                if manager := self.browser_managers.pop(user_id, None):
                    await manager.cleanup()

                manager = BrowserManager(user_id)
                success = await manager.initialize()
                if success:
                    self.browser_managers[user_id] = manager
                return success
            except Exception as e:
                logger.error(f"初始化用户 {user_id} 失败: {str(e)}", exc_info=True)
                return False

    async def cleanup_user(self, user_id: str):
        manager = self.browser_managers.pop(user_id, None)
        if manager:
            await manager.cleanup()
            del manager  # 显式删除引用

    async def cleanup_all(self):
        """清理所有浏览器"""
        for user_id in list(self.browser_managers.keys()):
            await self.cleanup_user(user_id)

    def get_instance_status(self) -> List[Dict]:
        """获取浏览器状态"""
        return [
            {
                "user_id": user_id,
                "running": manager.is_running,
                "uptime": manager.uptime
            }
            for user_id, manager in self.browser_managers.copy().items()
        ]


browser_pool = BrowserPool()


@app.route('/api/status', methods=['GET'])
def get_status():
    """API端点：获取状态"""
    return jsonify({"instances": browser_pool.get_instance_status()})


@app.route('/api/start', methods=['POST'])
def start_instance():
    """API端点：启动浏览器"""
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    success = asyncio.run(browser_pool.initialize_user(user_id))
    return jsonify({"success": success})


@app.route('/api/stop', methods=['POST'])
def stop_instance():
    """API端点：停止浏览器"""
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    asyncio.run(browser_pool.cleanup_user(user_id))
    return jsonify({"success": True})


@app.route('/')
def index():
    """Web界面"""
    instances = browser_pool.get_instance_status()
    return render_template_string('''
        <!DOCTYPE html>
        <html>
            <head>
                <title>Browser Manager</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    .container { 
                        max-width: 800px; 
                        margin: 20px auto; 
                        padding: 20px;
                        font-family: system-ui, -apple-system, sans-serif;
                    }
                    .instance-list { margin-top: 20px; }
                    .instance-item { 
                        display: flex; 
                        justify-content: space-between;
                        align-items: center;
                        padding: 15px;
                        border-bottom: 1px solid #eee;
                        background: #f9f9f9;
                        border-radius: 4px;
                        margin-bottom: 10px;
                    }
                    .instance-info {
                        display: flex;
                        flex-direction: column;
                        gap: 5px;
                    }
                    .status-badge {
                        padding: 3px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                    }
                    .status-running { background: #e6ffe6; color: #006600; }
                    .status-stopped { background: #ffe6e6; color: #660000; }
                    button {
                        padding: 8px 16px;
                        border-radius: 4px;
                        border: none;
                        cursor: pointer;
                        transition: opacity 0.2s;
                    }
                    button:disabled { opacity: 0.5; cursor: not-allowed; }
                    .btn-start { background: #4CAF50; color: white; }
                    .btn-stop { background: #f44336; color: white; }
                    .input-group {
                        display: flex;
                        gap: 10px;
                        margin-bottom: 20px;
                    }
                    input[type="text"] {
                        flex: 1;
                        padding: 8px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }
                    .refresh-notice {
                        color: #666;
                        font-size: 0.9em;
                        margin-top: 10px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>浏览器管理器</h1>

                    <!-- 启动表单 -->
                    <div class="input-group">
                        <input type="text" id="userIds" 
                               placeholder="输入用户ID（逗号分隔）" 
                               required>
                        <button onclick="startInstances()" class="btn-start">
                            启动新浏览器
                        </button>
                    </div>

                    <!-- 浏览器列表 -->
                    <div class="instance-list">
                        <h3>运行中的浏览器（{{ instances|length }}）</h3>
                        {% if instances %}
                            {% for instance in instances %}
                                <div class="instance-item">
                                    <div class="instance-info">
                                        <div>
                                            <strong>用户ID:</strong> {{ instance.user_id }}
                                            <span class="status-badge {{ 'status-running' if instance.running else 'status-stopped' }}">
                                                {{ "运行中" if instance.running else "已停止" }}
                                            </span>
                                        </div>
                                    </div>

                                </div>
                            {% endfor %}
                        {% else %}
                            <p>当前没有运行中的浏览器</p>
                        {% endif %}
                    </div>
                    <div class="refresh-notice">
                        ※ 页面加载时自动获取最新状态
                    </div>
                </div>

                <script>
                    async function startInstances() {
                        const input = document.getElementById('userIds');
                        const userIds = input.value.split(',').map(id => id.trim()).filter(Boolean);

                        for (const userId of userIds) {
                            try {
                                const response = await fetch('/api/start', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({user_id: userId})
                                });
                                if (!response.ok) throw new Error('启动失败');
                            } catch (error) {
                                console.error(`启动浏览器失败: ${userId}`, error);
                            }
                        }
                        location.reload();
                    }

                    async function stopInstance(userId) {
                        try {
                            const response = await fetch('/api/stop', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({user_id: userId})
                            });
                            if (!response.ok) throw new Error('停止失败');
                            location.reload();
                        } catch (error) {
                            console.error(`停止浏览器失败: ${userId}`, error);
                        }
                    }
                </script>
            </body>
        </html>
    ''', instances=instances)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python app.py <port>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        app.run(port=port, threaded=True)
    except ValueError:
        print("端口号必须是整数")
        sys.exit(1)
