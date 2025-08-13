#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API服务器启动脚本
用于启动Chrome配置管理的Web界面和API服务
"""

import uvicorn
from api.api_server import app

def start_server(host: str = "127.0.0.1", port: int = 8000, debug: bool = True):
    """
    启动API服务器
    
    Args:
        host: 服务器主机地址，默认为本地地址
        port: 服务器端口，默认为8000
        debug: 是否启用调试模式，默认为True
    """
    print(f"[INFO] 启动API服务器...")
    print(f"[INFO] 服务地址: http://{host}:{port}")
    print(f"[INFO] Chrome配置页面: http://{host}:{port}/chrome/config")
    print(f"[INFO] API文档: http://{host}:{port}/docs")
    print("\n按 Ctrl+C 停止服务器")
    
    try:
        if debug:
            # 开发模式使用字符串导入以支持reload
            uvicorn.run(
                "api.api_server:app",
                host=host,
                port=port,
                reload=True,
                log_level="info"
            )
        else:
            # 生产模式直接使用app对象
            uvicorn.run(
                app,
                host=host,
                port=port,
                reload=False,
                log_level="warning"
            )
    except KeyboardInterrupt:
        print("\n[INFO] 服务器已停止")
    except Exception as e:
        print(f"[ERROR] 服务器启动失败: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="启动Chrome配置API服务器")
    parser.add_argument("--host", default="127.0.0.1", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--no-debug", action="store_true", help="禁用调试模式")
    
    args = parser.parse_args()
    
    start_server(
        host=args.host,
        port=args.port,
        debug=not args.no_debug
    )