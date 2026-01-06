import sys
import os
from typing import Optional, Set, Dict
from loguru import logger
import threading
from time import time

# 导入资源路径函数
try:
    from conf import resource_path, LOG_DIR
except ImportError:
    # Fallback for standalone script usage
    def resource_path(relative_path: str) -> str:
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


# 日志配置
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {extra[name]}:{function}:{line} - {message}"
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(LOG_DIR, "app_{time:YYYY-MM-DD}.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

_added_sinks: Set[str] = set()

# 控制台日志去重
_enable_dedupe: bool = os.getenv("LOG_ENABLE_DEDUP", "true").lower() == "true"
_dedupe_window_sec: float = float(os.getenv("LOG_DEDUP_WINDOW_SEC", "3"))


class MessageDeduper:
    def __init__(self, window_sec: float = 3.0) -> None:
        self.window_sec = max(0.0, window_sec)
        self._last_seen: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _make_key(self, record: dict) -> str:
        level = record.get("level").name if record.get("level") else ""
        message = record.get("message", "")
        return f"{level}|{message}"

    def __call__(self, record: dict) -> bool:
        if not _enable_dedupe or self.window_sec <= 0:
            return True
        key = self._make_key(record)
        now = time()
        with self._lock:
            last = self._last_seen.get(key)
            if last is not None and (now - last) < self.window_sec:
                return False
            self._last_seen[key] = now
        return True


_console_deduper = MessageDeduper(_dedupe_window_sec)


def get_logger(name: Optional[str] = None, log_to_file: bool = True):
    """
    获取一个 loguru logger，支持控制台和文件输出。
    控制台日志短时间去重，文件日志完整保留。
    """
    global _added_sinks

    # 移除默认 sink，避免重复打印
    if not _added_sinks:
        logger.remove()

    # 控制台 sink
    if "console" not in _added_sinks:
        logger.add(
            sys.stderr,
            level=LOG_LEVEL,
            format=LOG_FORMAT,
            filter=_console_deduper,
            enqueue=False,  # 禁用 enqueue 避免信号量问题
            diagnose=False,
        )
        _added_sinks.add("console")

    # 文件 sink
    if log_to_file and "file" not in _added_sinks:
        logger.add(
            LOG_FILE,
            level=LOG_LEVEL,
            format=LOG_FORMAT,
            rotation="00:00",
            retention="3 days",
            encoding="utf-8",
            enqueue=False,  # 禁用 enqueue 避免信号量问题
            diagnose=False,
        )
        _added_sinks.add("file")

    # 强制 name，避免有的日志没对齐
    return logger.bind(name=name or "root")
