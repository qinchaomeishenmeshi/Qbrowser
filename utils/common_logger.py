# 公共的logger配置

import os
from typing import Optional

from loguru import logger

LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}"
LOG_LEVEL = "INFO"
# 日志文件名带日期，每天一个文件
LOG_FILE = os.path.join(os.path.dirname(__file__), '../logs/app_{time:YYYY-MM-DD}.log')

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# 防止重复添加sink
_added_sinks = set()


def get_logger(name: Optional[str] = None, log_to_file: bool = True):
    """
    获取一个loguru logger，支持控制台和文件输出。
    :param name: logger名称，建议传入__name__
    :param log_to_file: 是否写入文件
    :return: logger实例（loguru的logger，带有patch的name）
    """
    global _added_sinks
    # 只添加一次sink
    if "console" not in _added_sinks:
        logger.remove()  # 移除默认sink
        logger.add(
            sink=lambda msg: print(msg, end=""),
            level=LOG_LEVEL,
            format=LOG_FORMAT,
            enqueue=True,
        )
        _added_sinks.add("console")
    if log_to_file and "file" not in _added_sinks:
        logger.add(
            LOG_FILE,
            level=LOG_LEVEL,
            format=LOG_FORMAT,
            rotation="00:00",  # 每天0点新文件
            retention="3 days",  # 最多保留3天
            encoding="utf-8",
            enqueue=True,
        )
        _added_sinks.add("file")
    # 用patch给每条日志加上模块名
    if name:
        return logger.bind(name=name)
    return logger
