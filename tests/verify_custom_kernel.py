import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from service.browser_service import browser_service

# Common macOS Chrome paths
CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


async def verify_custom_kernel():
    user_id = "test_custom_kernel_001"

    # Find a valid kernel path
    executable_path = None
    for p in CHROME_PATHS:
        if os.path.exists(p):
            executable_path = p
            break

    if not executable_path:
        print(
            "⚠️ No system Chrome found to test custom kernel behavior. Skipping native launch test."
        )
        # We can still test trying to use a non-existent path and see if it falls back correctly
        executable_path = "/path/to/non/existent/chrome"
        expect_fallback = True
    else:
        print(f"✅ Found System Chrome at: {executable_path}")
        expect_fallback = False

    print(f"--- Starting Custom Kernel Verification for {user_id} ---")

    # 1. Cleanup
    print("[1] Cleaning up...")
    if hasattr(browser_service, "delete_browser"):
        await browser_service.delete_browser(user_id)

    # 2. Create Browser with Custom Kernel Config
    print(f"[2] Creating Browser with executable_path='{executable_path}'...")
    manager = await browser_service.create_browser(
        user_id, config_override={"executable_path": executable_path}
    )

    # 3. Start Browser
    print("[3] Starting Browser...")
    manager = await browser_service.get_or_create_browser(user_id)

    # Wait for page
    for i in range(10):
        if manager.page:
            break
        await asyncio.sleep(0.5)

    if not manager.page:
        print("❌ Browser failed to launch!")
        await browser_service.delete_browser(user_id)
        return

    # 4. Check Browser Version via internal user agent or chrome://version?
    # Actually checking navigator.userAgent is enough to see it running.
    # If we used system Chrome, the build might be different than Playwright's bundled one.
    page = manager.page
    ua = await page.evaluate("navigator.userAgent")
    print(f"    Runtime UA: {ua}")

    # If we used a fake path, check logs/behavior (manual check of logs usually)
    # But here we just verify it launched successfully.

    print("✅ Browser launched successfully!")

    # 5. Cleanup
    print("[5] Cleaning up...")
    await browser_service.stop_browser(user_id)
    await browser_service.delete_browser(user_id)
    print("--- Verification Finished ---")


if __name__ == "__main__":
    asyncio.run(verify_custom_kernel())
