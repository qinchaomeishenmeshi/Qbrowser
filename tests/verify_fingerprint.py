import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
print(f"DEBUG: sys.path: {sys.path}")

import service.browser_service

print(f"DEBUG: module name: {service.browser_service.__name__}")
print(f"DEBUG: module file: {service.browser_service.__file__}")
print(f"DEBUG: module dir: {dir(service.browser_service)}")

from service.browser_service import browser_service
from utils.database_manager import db_manager


async def verify_fingerprint():
    user_id = "test_fp_verifier_003"

    print(f"--- Starting Fingerprint Verification for {user_id} ---")
    print(f"DEBUG: browser_service type: {type(browser_service)}")
    print(f"DEBUG: browser_service dir: {dir(browser_service)}")

    # 1. Cleaning up previous data
    print("[1] Cleaning up...")
    if hasattr(browser_service, "delete_browser"):
        await browser_service.delete_browser(user_id)
    else:
        print("❌ CRITICAL: browser_service.delete_browser missing!")
        return

    # 2. Create Browser (Should generate fingerprint)
    print("[2] Creating Browser...")
    manager = await browser_service.create_browser(user_id)
    if not manager:
        print("❌ Failed to create browser")
        return

    # 3. Check DB for Config
    print("[3] Checking Database for Config...")
    config = await db_manager.get_browser_config(user_id)
    print(f"    Saved Config: {config}")
    if not config or not config.get("user_agent"):
        print("❌ Config not saved or empty UA")
        return

    db_ua = config["user_agent"]
    db_viewport = config["viewport"]

    # 4. Start Browser
    print("[4] Starting Browser...")
    # launching...
    res = await browser_service.start_browsers([user_id])

    # 5. Check actual browser fingerprint
    print("[5] Verifying Runtime Fingerprint...")
    manager = await browser_service.get_or_create_browser(user_id)

    # Wait for page to be ready
    for i in range(10):
        if manager.page:
            break
        print(f"    Waiting for page... {i+1}/10")
        await asyncio.sleep(0.5)

    page = manager.page

    if not page:
        print("❌ Page not available")
        await browser_service.stop_browser(user_id)
        return

    runtime_ua = await page.evaluate("navigator.userAgent")
    runtime_viewport = await page.evaluate(
        "({width: window.innerWidth, height: window.innerHeight})"
    )

    print(f"    Runtime UA: {runtime_ua}")
    print(f"    Runtime Viewport: {runtime_viewport}")

    # Verification
    ua_match = runtime_ua == db_ua
    vp_match = (
        runtime_viewport["width"] == db_viewport["width"]
        and runtime_viewport["height"] == db_viewport["height"]
    )

    if ua_match:
        print("✅ User-Agent Match!")
    else:
        print(
            f"❌ User-Agent Mismatch!\n   Expected: {db_ua}\n   Got:      {runtime_ua}"
        )

    if vp_match:
        print("✅ Viewport Match!")
    else:
        print(
            f"❌ Viewport Mismatch!\n   Expected: {db_viewport}\n   Got:      {runtime_viewport}"
        )

    # 6. Stop and Cleanup
    print("[6] Stopping and Cleaning up...")
    await browser_service.stop_browser(user_id)
    await browser_service.delete_browser(user_id)

    if ua_match and vp_match:
        print("\n🎉 SUCCESS: Fingerprint persistence verified!")
    else:
        print("\n⚠️ FAILED: Fingerprint mismatch detected.")

    print("--- Verification Finished ---")


if __name__ == "__main__":
    asyncio.run(verify_fingerprint())
