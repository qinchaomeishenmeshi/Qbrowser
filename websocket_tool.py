import json
import threading
import time
from typing import Callable, Optional, Any

import websocket


class WebSocketClient:
    def __init__(
            self,
            url: str,
            heartbeat_interval: float = 30.0,
            reconnect_interval: float = 5.0,
    ):
        """
        :param url: WebSocket服务器URL
        :param heartbeat_interval: 心跳检测间隔（秒）
        :param reconnect_interval: 断线后重连间隔（秒）
        """
        self.url = url
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_interval = reconnect_interval

        self.ws: Optional[websocket.WebSocketApp] = None
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        self._on_message: Optional[Callable[[str], None]] = None
        self._on_open: Optional[Callable[[], None]] = None
        self._on_close: Optional[Callable[[], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None

    def on_message(self, func: Callable[[str], None]):
        self._on_message = func
        return func

    def on_open(self, func: Callable[[], None]):
        self._on_open = func
        return func

    def on_close(self, func: Callable[[], None]):
        self._on_close = func
        return func

    def on_error(self, func: Callable[[Exception], None]):
        self._on_error = func
        return func

    def _send_heartbeat(self):
        while not self.stop_event.wait(self.heartbeat_interval):
            try:
                if self.ws and self.ws.sock and self.ws.sock.connected:
                    heartbeat_msg = json.dumps({"type": "heartbeat", "timestamp": time.time()})
                    self.ws.send(heartbeat_msg)
                else:
                    break
            except Exception as e:
                if self._on_error:
                    self._on_error(e)
                break

    def _run(self):
        while not self.stop_event.is_set():
            self.ws = websocket.WebSocketApp(
                self.url,
                on_open=lambda ws: self._handle_open(),
                on_message=lambda ws, msg: self._handle_message(msg),
                on_close=lambda ws, code, msg: self._handle_close(),
                on_error=lambda ws, err: self._handle_error(err),
            )

            # 阻塞运行，直到断开
            self.ws.run_forever()

            # 触发断开回调
            if self._on_close:
                self._on_close()

            # 如果未停止，则等待并重连
            if not self.stop_event.is_set():
                time.sleep(self.reconnect_interval)

    def _handle_open(self):
        # 启动心跳线程
        threading.Thread(target=self._send_heartbeat, daemon=True).start()
        if self._on_open:
            self._on_open()

    def _handle_message(self, message: str):
        if self._on_message:
            self._on_message(message)

    def _handle_close(self):
        # 连接关闭时，将在 run loop 中重连
        pass

    def _handle_error(self, error: Exception):
        if self._on_error:
            self._on_error(error)

    def start(self):
        """启动 WebSocket 客户端"""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """停止 WebSocket 客户端"""
        self.stop_event.set()
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join()

    def send(self, data: Any):
        """发送消息到服务器"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            if isinstance(data, (dict, list)):
                message = json.dumps(data)
            else:
                message = str(data)
            self.ws.send(message)
        else:
            raise ConnectionError("WebSocket 未连接")


# 示例用法
if __name__ == "__main__":
    client = WebSocketClient("wss://example.com/socket")


    @client.on_open
    def handle_open():
        print("连接已打开，发送初始化消息")
        client.send({"type": "init", "payload": "hello"})


    @client.on_message
    def handle_message(msg: str):
        print("收到消息：", msg)
        # 在这里调用原项目的方法
        # result = my_project.process(msg)


    @client.on_close
    def handle_close():
        print("连接已关闭，正在尝试重连...")


    @client.on_error
    def handle_error(e: Exception):
        print("发生错误：", e)


    client.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.stop()
        print("客户端已停止")
