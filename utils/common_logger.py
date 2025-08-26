import sys
import os
from typing import Optional, Set, Dict
from loguru import logger
import threading
from time import time

# 导入资源路径函数
try:
    from conf import resource_path
except ImportError:
    # 如果导入失败，使用默认的相对路径
    def resource_path(relative_path: str) -> str:
        """
        获取资源文件的绝对路径。

        参数:
            relative_path: 相对路径
        返回:
            资源文件的绝对路径
        """
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

# 日志配置
LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}"
)
LOG_LEVEL = "INFO"
# 日志文件名带日期，每天一个文件
LOG_FILE = os.path.join(resource_path("logs"), "app_{time:YYYY-MM-DD}.log")

# 确保日志目录存在
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# 防止重复添加sink
_added_sinks: Set[str] = set()

# ========== 控制台日志去重 ==========
# 通过环境变量控制开关与窗口时长（秒）
_enable_dedupe: bool = os.getenv("LOG_ENABLE_DEDUP", "true").lower() == "true"
_dedupe_window_sec: float = float(os.getenv("LOG_DEDUP_WINDOW_SEC", "3"))


class MessageDeduper:
    """
    日志消息去重过滤器（仅用于控制台sink）。

    设计目标：
    - 抑制在短时间窗口内完全一样的日志消息，减少刷屏。
    - 默认按【级别+消息文本】作为去重键（忽略模块名），
      这样来自不同模块但文本相同的重复提示也会被抑制。

    参数：
    - window_sec: 时间窗口，单位秒
    """

    def __init__(self, window_sec: float = 3.0) -> None:
        self.window_sec = max(0.0, window_sec)
        self._last_seen: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _make_key(self, record: dict) -> str:
        level = record.get("level").name if record.get("level") else ""
        message = record.get("message", "")
        return f"{level}|{message}"

    def __call__(self, record: dict) -> bool:
        """作为loguru过滤器调用。返回True放行，False抑制。"""
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


# 单例去重器（仅用于控制台输出）
_console_deduper = MessageDeduper(_dedupe_window_sec)


def get_logger(name: Optional[str] = None, log_to_file: bool = True):
    """
    获取一个loguru logger，支持控制台和文件输出。

    函数说明（中文注释）：
    - 该函数统一初始化日志输出，包括控制台与文件两种sink。
    - 控制台输出默认开启“短时间去重”功能，减少重复日志刷屏；文件输出保留完整日志以便追溯。
    - 通过 name 参数为日志绑定模块名，便于定位日志来源。

    参数:
        name: logger名称，建议传入 __name__
        log_to_file: 是否写入文件
    返回:
        logger 实例（loguru 的 logger，带有 patch 的 name）
    """
    global _added_sinks

    # 只添加一次控制台sink
    if "console" not in _added_sinks:
        logger.add(
            sink=sys.stderr,
            level=LOG_LEVEL,
            format=LOG_FORMAT,
            filter=_console_deduper,  # 控制台开启去重，减少重复日志
            enqueue=True,
            diagnose=True,
        )
        _added_sinks.add("console")

    # 只添加一次文件sink
    if log_to_file and "file" not in _added_sinks:
        logger.add(
            LOG_FILE,
            level=LOG_LEVEL,
            format=LOG_FORMAT,
            rotation="00:00",       # 每天0点新文件
            retention="3 days",     # 最多保留3天
            encoding="utf-8",
            enqueue=True,
            diagnose=True,
        )
        _added_sinks.add("file")

    # 用 bind 给每条日志加上模块名
    if name:
        return logger.bind(name=name)
    return logger
