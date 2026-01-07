import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from service.browser_service import browser_service
from utils.database_manager import db_manager


async def verify_proxy_config():
    user_id = "test_proxy_verifier_001"
    mock_proxy = {
        "server": "http://127.0.0.1:8888",
        "username": "user",
        "password": "pass",
    }

    print(f"--- Starting Proxy Config Verification for {user_id} ---")

    # 1. Cleaning up previous data
    print("[1] Cleaning up...")
    if hasattr(browser_service, "delete_browser"):
        await browser_service.delete_browser(user_id)

    # 2. Create Browser with Custom Proxy Config
    print("[2] Creating Browser with Proxy Config...")
    # Simulate API call by passing config_override
    manager = await browser_service.create_browser(
        user_id, config_override={"proxy": mock_proxy}
    )

    if not manager:
        print("❌ Failed to create browser")
        return

    # 3. Check DB for Config
    print("[3] Checking Database for Config...")
    config = await db_manager.get_browser_config(user_id)
    print(f"    Saved Config: {config}")

    if not config:
        print("❌ Config not saved")
        return

    # 4. Verify Proxy is Present and Merged
    saved_proxy = config.get("proxy")
    saved_ua = config.get("user_agent")

    if saved_proxy == mock_proxy:
        print("✅ Proxy Config Match!")
    else:
        print(
            f"❌ Proxy Mismatch!\n   Expected: {mock_proxy}\n   Got:      {saved_proxy}"
        )

    if saved_ua:
        print(f"✅ Auto-generated fingerprint present (UA: {saved_ua[:20]}...)")
    else:
        print("❌ Auto-generated fingerprint MISSING!")

    # 5. Cleanup
    print("[5] Cleaning up...")
    await browser_service.delete_browser(user_id)

    if saved_proxy == mock_proxy and saved_ua:
        print("\n🎉 SUCCESS: Proxy configuration persistence verified!")
    else:
        print("\n⚠️ FAILED: Verification failed.")

    print("--- Verification Finished ---")


if __name__ == "__main__":
    asyncio.run(verify_proxy_config())
