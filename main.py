#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API服务器启动脚本
用于启动Chrome配置管理的Web界面和API服务
"""

import sys
import os
import traceback
from pathlib import Path

# 尽早设置日志重定向，以便捕获启动/导入错误
# 尽早设置日志重定向，以便捕获启动/导入错误
try:
    # 仅在打包环境下重定向日志，本地开发保留控制台输出
    if getattr(sys, "frozen", False):
        from conf import LOG_DIR

        log_path = Path(LOG_DIR)
        log_path.mkdir(parents=True, exist_ok=True)

        sys.stdout = open(log_path / "stdout.log", "a", buffering=1, encoding="utf-8")
        sys.stderr = open(log_path / "stderr.log", "a", buffering=1, encoding="utf-8")
        print(f"--- Process Started (Frozen): {os.getpid()} ---")
    else:
        print(f"--- Process Started (Local): {os.getpid()} ---")
except Exception as e:
    pass

import uvicorn
from api.api_server import app


def start_server(host: str = "127.0.0.1", port: int = 8000, debug: bool = True):
    print(f"[INFO] 启动API服务器...")
    print(f"[INFO] 服务地址: http://{host}:{port}")

    try:
        # 强制配置 uvicorn 使用我们的日志目录，或者简单地让它输出到 stdout/stderr (已重定向)
        log_config = uvicorn.config.LOGGING_CONFIG.copy()

        # 确保 uvicorn 不会吞掉异常
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info" if debug else "warning",
            # 如果是开发模式，使用 reload=False (打包后不能 reload)
            reload=False,
        )
    except KeyboardInterrupt:
        print("\n[INFO] 服务器已停止")
    except Exception as e:
        print(f"[ERROR] 服务器启动失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    try:
        parser = argparse.ArgumentParser(description="启动Chrome配置API服务器")
        parser.add_argument("--host", default="127.0.0.1", help="服务器主机地址")
        parser.add_argument("--port", type=int, default=8000, help="服务器端口")
        parser.add_argument("--no-debug", action="store_true", help="禁用调试模式")

        args = parser.parse_args()

        start_server(host=args.host, port=args.port, debug=not args.no_debug)
    except Exception as e:
        print(f"Fatal error in main: {e}")
        traceback.print_exc()
