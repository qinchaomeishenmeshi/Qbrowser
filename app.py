import asyncio
import logging
import threading
import time
from asyncio import Lock, run
from contextlib import asynccontextmanager
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


@dataclass
class BrowserConfig:
    """浏览器配置数据类"""
    viewport_width: int = 1280
    viewport_height: int = 720
    base_url: str = "https://eos.douyin.com"
    extension_path: str = "live_room"
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
        self.cleanup_lock = Lock()  # 为清理资源操作加锁

    async def initialize(self) -> bool:
        """初始化浏览器上下文和页面"""
        try:
            self.user_data_dir.mkdir(parents=True, exist_ok=True)
            self._playwright = await async_playwright().start()

            context_args = {
                "user_data_dir": str(self.user_data_dir),
                "headless": False,
                "channel": "chrome",
                "args": [
                    f"--disable-extensions-except={self.config.extension_path}",
                    f"--load-extension={self.config.extension_path}",
                    "--disable-blink-features=AutomationControlled",
                ],
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height
                },
                "permissions": ["geolocation"],
                "ignore_https_errors": True
            }

            self.context = await self._playwright.chromium.launch_persistent_context(**context_args)
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()

            self.page.set_default_timeout(30000)
            await self._setup_page_handlers()

            await self.page.goto(self.config.base_url, wait_until="networkidle")
            self._startup_time = asyncio.get_running_loop().time()

            logger.info(f"浏览器已启动，用户: {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {str(e)}", exc_info=True)
            await self.cleanup()
            return False

    async def _setup_page_handlers(self):
        """设置页面事件处理器"""
        if not self.page:
            return

        async def handle_dialog(dialog):
            await dialog.dismiss()

        async def handle_error(error):
            logger.error(f"页面错误 {self.user_id}: {error}")

        self.page.on("dialog", handle_dialog)
        self.page.on("pageerror", handle_error)

    @asynccontextmanager
    async def error_boundary(self):
        """错误边界处理器"""
        try:
            yield
        except Exception as e:
            logger.error(f"操作失败 {self.user_id}: {str(e)}", exc_info=True)
            await self.cleanup()
            raise

    async def cleanup(self):
        """清理资源"""
        try:
            print("清理资源", self._playwright)

            if self._playwright:
                try:
                    await self._playwright.stop()
                    self._playwright = None
                    logger.info(f"已停止 playwright 浏览器: {self.user_id}")
                except Exception as e:
                    logger.warning(f"Playwright 浏览器已停止或不存在，无法再次停止: {str(e)}")
            else:
                logger.info(f"没有playwright浏览器需要停止: {self.user_id}")

        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}", exc_info=True)
            raise

    @property
    def is_running(self) -> bool:
        """优化后的浏览器状态检测（线程安全/版本兼容/异常防护）"""
        try:
            return bool(self.context.pages[0])
        except Exception:
            return False

    @property
    def uptime(self) -> Optional[float]:
        """获取运行时间（秒），修改为同步方式"""
        if self._startup_time and self.is_running:
            # 如果没有异步事件循环，使用时间戳计算
            return time.time() - self._startup_time
        return None


class BrowserPool:
    def __init__(self):
        self.browser_managers: Dict[str, BrowserManager] = {}
        self._local = threading.local()

    @property
    def lock(self):
        if not hasattr(self._local, 'lock'):
            self._local.lock = asyncio.Lock()
        return self._local.lock

    async def initialize_user(self, user_id: str) -> bool:
        """安全地初始化用户浏览器（修复死锁问题）"""
        async with self.lock:
            try:
                # 直接清理而不嵌套获取锁
                if manager := self.browser_managers.pop(user_id, None):
                    await manager.cleanup()

                # 创建新浏览器
                manager = BrowserManager(user_id)
                success = await manager.initialize()
                if success:
                    self.browser_managers[user_id] = manager
                return success
            except Exception as e:
                logger.error(f"初始化用户 {user_id} 失败: {str(e)}", exc_info=True)
                return False

    async def cleanup_user(self, user_id: str):
        """清理用户浏览器（无需锁保护，由调用方保证）"""
        print(self.browser_managers)
        if manager := self.browser_managers.pop(user_id, None):
            await manager.cleanup()  # 确保关闭页面和浏览器

    async def cleanup_all(self):
        """清理所有浏览器（由锁保护）"""
        async with self.lock:
            for user_id in list(self.browser_managers.keys()):
                await self.cleanup_user(user_id)  # 直接调用无需锁

    def get_instance_status(self) -> List[Dict]:
        """获取浏览器状态（线程安全读取）"""
        return [
            {
                "user_id": user_id,
                "running": manager.is_running,
                "uptime": manager.uptime
            }
            for user_id, manager in self.browser_managers.copy().items()
        ]


browser_pool = BrowserPool()


async def shutdown_hook():
    """关闭钩子"""
    await browser_pool.cleanup_all()


def run_async(coro):
    """异步执行器"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route('/api/status', methods=['GET'])
def get_status():
    """API端点：获取状态"""
    return jsonify({"instances": browser_pool.get_instance_status()})


@app.route('/api/start', methods=['POST'])
def start_instance():
    """API端点：启动浏览器"""
    user_id = request.json.get('user_id')
    print(f"Starting instance for user: {user_id}")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    success = run_async(browser_pool.initialize_user(user_id))
    return jsonify({"success": success})


@app.route('/api/stop', methods=['POST'])
def stop_instance():
    """API端点：停止浏览器"""
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    # 异步执行清理任务
    run(browser_pool.cleanup_user(user_id))
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
                        ※ 状态每30秒自动刷新，切换标签页时暂停刷新
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

                    // 自动刷新状态（页面可见时每30秒刷新）
                    setInterval(() => {
                        if (document.visibilityState === 'visible') {
                            fetch('/api/status')
                                .then(response => response.json())
                                .then(data => {
                                    const currentIds = new Set(
                                        Array.from(document.querySelectorAll('.instance-item'))
                                            .map(el => el.querySelector('strong').textContent.trim())
                                    );
                                    const newIds = new Set(data.instances.map(i => i.user_id));

                                    if (currentIds.size !== newIds.size || 
                                        ![...currentIds].every(id => newIds.has(id))) {
                                        location.reload();
                                    }
                                });
                        }
                    }, 30000);
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
