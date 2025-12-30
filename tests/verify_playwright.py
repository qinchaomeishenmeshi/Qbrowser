import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from browser.playwright_manager import PlaywrightManager
from browser.playwright_operator import playwright_operator
from utils.common_logger import get_logger

logger = get_logger("verify_playwright")


async def test_anti_detection(user_id="test_user_001"):
    """Test browser initialization and anti-detection capabilities"""
    logger.info(f"--- Starting Anti-Detection Test for {user_id} ---")

    manager = PlaywrightManager(user_id, headless=False)
    success = await manager.initialize()

    if not success:
        logger.error("Failed to initialize browser")
        return

    try:
        page = manager.page

        # 1. Test Bot Detection Site
        logger.info("Navigating to bot.sannysoft.com...")
        await page.goto("https://bot.sannysoft.com/")
        await asyncio.sleep(5)

        # Screenshot results
        screenshot_path = f"verify_bot_{user_id}.png"
        await page.screenshot(path=screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")

        # Check specific anti-detection indicators via JS
        webdriver = await page.evaluate("navigator.webdriver")
        logger.info(f"navigator.webdriver: {webdriver}")

        if webdriver:
            logger.error("❌ FAILED: navigator.webdriver is true!")
        else:
            logger.info("✅ PASSED: navigator.webdriver is false/undefined")

        # 2. Test User Tag Injection
        # Check if the tag element exists
        tag_exists = await page.evaluate(
            "!!document.querySelector('div[style*=\"Browser ID\"]')"
        )
        if tag_exists:
            logger.info("✅ PASSED: User tag injected successfully")
        else:
            logger.warning("❌ FAILED: User tag not found")

    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        await manager.cleanup()


async def test_network_capture(user_id="test_user_002"):
    """Test network capture capabilities"""
    logger.info(f"--- Starting Network Capture Test for {user_id} ---")

    manager = PlaywrightManager(user_id, headless=False)
    await manager.initialize()

    try:
        # Use httpbin to simulate an API endpoint that returns JSON
        test_url = "https://httpbin.org/get"
        api_path = "/get"  # Match the path component

        logger.info(f"Testing capture on {test_url}")

        # Use existing operator logic
        # Note: fetch_cookies_and_headers assumes we can navigate to the URL
        # For this test we act like httpbin.org is the "site"

        # Manually using operator for test
        context = manager.context
        page = await context.new_page()

        # Start capture
        from utils.playwright_network_listener import PlaywrightNetworkListener

        listener = PlaywrightNetworkListener(page)
        listener.start_listening([api_path])

        # Trigger request
        await page.goto(test_url)

        # Wait for packet
        packet = await listener.wait_for_packet(api_path)

        if packet:
            logger.info("✅ PASSED: Captured network packet")
            logger.info(f"URL: {packet.get('url')}")
            # logger.info(f"Headers: {packet.get('request_headers')}")
        else:
            logger.error("❌ FAILED: Did not capture packet")

    except Exception as e:
        logger.error(f"Network test failed: {e}")
    finally:
        await manager.cleanup()


from unittest.mock import AsyncMock, MagicMock


async def test_operator_functionality(user_id="test_user_003"):
    """Test PlaywrightOperator methods"""
    logger.info(f"--- Starting Operator Functionality Test for {user_id} ---")

    manager = PlaywrightManager(user_id, headless=False)
    success = await manager.initialize()
    if not success:
        logger.error("Failed to initialize manager")
        return

    try:
        # Mock browser_service to return our local manager instance
        # We need to patch where it is IMPORTED in the operator file or used
        # Since usage is inside methods via import, we can try to patch the module 'service.browser_service'
        import sys

        # Create a mock browser service
        mock_service = MagicMock()
        mock_service.get_or_create_browser = AsyncMock(return_value=manager)

        # We need to make sure when 'from service.browser_service import browser_service' runs, it gets our mock
        # But global imports happen at module level.
        # In PlaywrightOperator, browser_service is imported inside methods in some cases, or at top level.
        # Let's check the file content... It imports at top level: 'from service.browser_service import browser_service'
        # So we need to patch 'browser.playwright_operator.browser_service'

        import browser.playwright_operator

        original_service = getattr(browser.playwright_operator, "browser_service", None)
        browser.playwright_operator.browser_service = mock_service

        logger.info("MOCKED browser_service in playwright_operator")

        # 1. Test Redirect
        target_url = "https://example.com"
        logger.info(f"Testing redirect to {target_url}")
        res = await playwright_operator.redirect_user_page(user_id, target_url)

        if res:
            page = manager.context.pages[-1]
            if "example.com" in page.url:
                logger.info("✅ PASSED: Redirect successful")
            else:
                logger.error(f"❌ FAILED: Redirected but URL is {page.url}")
        else:
            logger.error("❌ FAILED: Redirect returned False")

        # 2. Test Fetch Cookies (mocking a site)
        # We use httpbin cookies endpoint
        cookie_url = "https://httpbin.org/cookies/set?test_cookie=valid"
        logger.info("Testing fetch_cookies_and_headers...")

        # We need to simulate 'get_or_create_page' which is used inside fetch
        # It takes 'manager' which we pass in specific method calls or it gets from service
        # In fetch_cookies_and_headers sig: (manager, user_id, url, ...)

        # Note: fetch_cookies_and_headers calls manager.context

        data = await playwright_operator.fetch_cookies_and_headers(
            manager=manager,
            user_id=user_id,
            url=cookie_url,
            api_paths=["/cookies"],
            site_key="custom",  # avoid special login logic
        )

        cookies = data.get("cookies", {})
        if "test_cookie" in cookies and cookies["test_cookie"] == "valid":
            logger.info("✅ PASSED: Cookies fetched successfully")
        else:
            logger.error(f"❌ FAILED: Cookies not found or mismatch: {cookies}")

        # Restore
        if original_service:
            browser.playwright_operator.browser_service = original_service

    except Exception as e:
        logger.error(f"Operator test failed: {e}")
    finally:
        await manager.cleanup()


async def main():
    await test_anti_detection()
    await test_network_capture()
    await test_operator_functionality()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
