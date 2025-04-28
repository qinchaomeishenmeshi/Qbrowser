import asyncio
import json
import logging
import os
import platform
import sys
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from playwright.async_api import async_playwright, BrowserContext, Page, Playwright

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CACHE_FILE = "user_ids_cache.json"


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
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
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
        self.last_urls_file = self.user_data_dir / "last_urls.json"

    async def inject_user_tag(self, page: Page):
        await page.evaluate(f"""
            (() => {{
                const div = document.createElement('div');
                div.innerText = 'Browser ID: {self.user_id}';
                div.style.position = 'fixed';
                div.style.top = '10px';
                div.style.left = '10px';
                div.style.background = 'rgba(0,0,0,0.6)';
                div.style.color = 'white';
                div.style.padding = '5px 10px';
                div.style.zIndex = '999999';
                div.style.borderRadius = '8px';
                div.style.fontSize = '14px';
                div.style.pointerEvents = 'none';
                document.body.appendChild(div);
            }})()
        """)

    async def initialize(self) -> bool:
        try:
            lock_file = self.user_data_dir / "SingletonLock"
            retry_count = 0
            while lock_file.exists():
                if retry_count >= 5:
                    logger.error(f"User data dir {self.user_data_dir} is occupied, aborting.")
                    return False
                logger.warning(f"User data dir {self.user_data_dir} is occupied, waiting...")
                await asyncio.sleep(2)
                retry_count += 1

            self._playwright = await async_playwright().start()
            logger.info(f"Extension path: {self.config.extension_path}")

            self.context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=False,
                channel="chrome",
                no_viewport=True,
                args=[
                    f"--disable-extensions-except={self.config.extension_path}",
                    f"--load-extension={self.config.extension_path}",
                ],
            )

            blank_page = None
            for page in self.context.pages:
                if page.url == "about:blank" and blank_page is None:
                    blank_page = page
                else:
                    await page.close()
            if not blank_page:
                blank_page = await self.context.new_page()
            self.page = blank_page
            await self.page.evaluate(f"document.title = '{self.user_id}'")

            if self.last_urls_file.exists():
                try:
                    with open(self.last_urls_file, 'r', encoding='utf-8') as f:
                        urls = json.load(f)
                    if isinstance(urls, list) and urls:
                        for url in urls:
                            page = await self.context.new_page()
                            await page.goto(url)
                            await self.inject_user_tag(page)
                        logger.info(f"Restored {len(urls)} pages.")
                except Exception as e:
                    logger.warning(f"Failed to restore URLs: {str(e)}")

            self._startup_time = time.time()
            logger.info(f"Browser started for user: {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}", exc_info=True)
            await self.cleanup()
            return False

    async def cleanup(self):
        try:
            if self.context:
                urls = [page.url for page in self.context.pages if
                        page.url and not page.url.startswith('chrome://') and page.url != 'about:blank']
                if urls:
                    self.user_data_dir.mkdir(parents=True, exist_ok=True)
                    with open(self.last_urls_file, 'w', encoding='utf-8') as f:
                        json.dump(urls, f, ensure_ascii=False, indent=2)
                    logger.info(f"Saved {len(urls)} open page URLs.")

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
            logger.error(f"Cleanup error: {str(e)}", exc_info=True)
        finally:
            await asyncio.sleep(2)
            self.page = None
            self.context = None
            self._playwright = None

    @property
    def is_running(self) -> bool:
        return bool(self.context)

    @property
    def uptime(self) -> Optional[float]:
        if self._startup_time and self.is_running:
            return time.time() - self._startup_time
        return None


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Browser Manager")
        self.browser_managers = []

        self.text = tk.Text(root, height=8)
        self.text.pack(fill=tk.X, padx=10, pady=5)

        frame = tk.Frame(root)
        frame.pack(fill=tk.X, padx=10, pady=5)

        self.start_button = tk.Button(frame, text="启动浏览器", width=15, command=self.start_browsers)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(frame, text="一键关闭", width=15, command=self.stop_browsers)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.load_button = tk.Button(frame, text="加载 user_ids.txt", width=20, command=self.load_user_ids)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = tk.Button(frame, text="清除缓存", width=15, command=self.clear_cache)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.progress = ttk.Progressbar(root, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        self.log = scrolledtext.ScrolledText(root, height=15, state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.load_cache()

    def log_message(self, message):
        self.log.configure(state='normal')
        self.log.insert(tk.END, message + '\n')
        self.log.configure(state='disabled')
        self.log.yview(tk.END)

    def load_user_ids(self):
        path = filedialog.askopenfilename(title="Select user_ids.txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.text.delete('1.0', tk.END)
            self.text.insert(tk.END, content)
            self.save_cache()

    def start_browsers(self):
        user_ids = [line.strip() for line in self.text.get('1.0', tk.END).splitlines() if line.strip()]
        if not user_ids:
            messagebox.showerror("Error", "Please enter at least one user_id.")
            return

        if len(user_ids) != len(set(user_ids)):
            messagebox.showerror("Error", "Duplicate user_ids are not allowed.")
            return

        self.save_cache()

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        asyncio.create_task(self.launch(user_ids))

    async def launch(self, user_ids):
        self.log_message("Starting browsers...")
        self.browser_managers = [BrowserManager(user_id) for user_id in user_ids]

        self.progress['maximum'] = len(user_ids)
        self.progress['value'] = 0

        for idx, manager in enumerate(self.browser_managers, start=1):
            try:
                result = await manager.initialize()
                if result:
                    self.log_message(f"[{idx}/{len(user_ids)}] Browser for {manager.user_id} started successfully.")
                else:
                    self.log_message(f"[{idx}/{len(user_ids)}] Browser for {manager.user_id} failed to start.")
            except Exception as e:
                self.log_message(f"[{idx}/{len(user_ids)}] Error starting {manager.user_id}: {e}")

            self.progress['value'] = idx
            self.root.update_idletasks()

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.log_message("All browsers started.")

    def stop_browsers(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        asyncio.create_task(self.shutdown())

    async def shutdown(self):
        self.log_message("Stopping all browsers...")
        await asyncio.gather(*(manager.cleanup() for manager in self.browser_managers if manager.is_running))
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.progress['value'] = 0
        self.log_message("All browsers closed.")

    def save_cache(self):
        user_ids = [line.strip() for line in self.text.get('1.0', tk.END).splitlines() if line.strip()]
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_ids, f, ensure_ascii=False, indent=2)

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                try:
                    user_ids = json.load(f)
                    if isinstance(user_ids, list):
                        self.text.delete('1.0', tk.END)
                        self.text.insert(tk.END, '\n'.join(user_ids))
                except Exception:
                    pass

    def clear_cache(self):
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        self.text.delete('1.0', tk.END)
        self.log_message("Cache cleared.")


def main():
    root = tk.Tk()
    app = App(root)
    asyncio.run(async_main(root, app))


async def async_main(root, app):
    while True:
        root.update()
        await asyncio.sleep(0.01)


if __name__ == "__main__":
    main()
