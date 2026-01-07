import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from conf.browser_config import chrome_path_manager


async def main():
    print("Testing Chrome Detection...")
    try:
        path = await chrome_path_manager.get_chrome_path()
        print(f"Detected Path: {path}")
        if path and os.path.exists(path):
            print("Path exists.")
        else:
            print("Path does not exist or is None.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
