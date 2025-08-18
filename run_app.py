"""应用程序备用启动入口

此文件作为app.py的备用启动入口，统一调用app.py的main函数。
这样确保了启动逻辑的一致性，避免重复实现和潜在的冲突。

推荐使用: python app.py
备用方式: python run_app.py
"""

from app import main

if __name__ == "__main__":
    # 统一调用app.py的main函数，确保启动逻辑一致
    main()