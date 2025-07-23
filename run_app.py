import sys
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
import asyncio

from app import App, USE_MODERN_UI

# 提前导入 ModernApp，以解决 QtWebEngineWidgets 的初始化问题
if USE_MODERN_UI:
    from ui.modern_app import ModernApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    if USE_MODERN_UI:
        main_window = ModernApp()
    else:
        main_window = App()

    main_window.show()

    with loop:
        loop.run_forever()