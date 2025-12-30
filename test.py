import os
from playwright.sync_api import sync_playwright

# 获取项目的根目录和扩展路径
current_dir = os.path.dirname(os.path.abspath(__file__))
extension_path = os.path.join(current_dir, "extensions", "live_room")

with sync_playwright() as p:
    # 注意：Playwright 加载扩展有以下限制：
    # 1. 必须使用 launch_persistent_context
    # 2. 必须设置 headless=False (有头模式)
    # 3. 扩展路径必须是解压后的文件夹，不能是 .crx 文件

    print(f"正在启动浏览器并加载扩展: {extension_path}")

    browser = p.chromium.launch_persistent_context(
        user_data_dir="",  # 使用临时目录，避免污染本地数据
        headless=False,
        args=[
            f"--disable-extensions-except={extension_path}",
            f"--load-extension={extension_path}",
        ],
    )

    try:
        # launch_persistent_context 默认会打开一个空标签页
        page = browser.pages[0] if browser.pages else browser.new_page()

        # 导航到百度进行测试
        print("正在导航到百度...")
        page.goto("https://www.baidu.com", wait_until="networkidle")

        print("✅ 成功打开浏览器，进入百度，并加载了扩展。")

        # 停留一会方便观察（可选）
        # page.wait_for_timeout(5000)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        # 关闭浏览器
        browser.close()
        print("浏览器已关闭。")
