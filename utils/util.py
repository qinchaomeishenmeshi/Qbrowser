import os
import time
from datetime import datetime, timedelta, timezone

import httpx
import ujson as json
from utils.common_logger import get_logger

logger = get_logger(__name__)


def str_to_path(str: str):
    """
    把字符串转为Windows合法文件名
    """
    # 非法字符
    lst = ['\r', '\n', '\\', '/', ':', '*', '?', '"', '<', '>', '|']
    # lst.extend([' ', '^'])
    # 字符处理方式1
    for key in lst:
        str = str.replace(key, '_')
    # 字符处理方式2
    # str = str.translate(None, ''.join(lst))
    # 文件名+路径长度最大255，汉字*2，取80
    if len(str) > 80:
        str = str[:80]
    return str.strip()


def quit(str: str = ''):
    """
    直接退出程序
    """
    if str:
        logger.error(str)
    exit()


def url_redirect(url):
    r = httpx.head(url, follow_redirects=False)
    u = r.headers.get('Location', url)
    return u


def save_json(filename: str, data):
    path = os.path.dirname(filename)
    if path:
        os.makedirs(path, exist_ok=True)

    with open(f'{filename}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def to_timestamp(dt_str: str) -> int:
    """Convert datetime string to UNIX timestamp in seconds."""
    try:
        dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(f"时间格式错误，需为 'YYYY-MM-DD HH:MM:SS'，收到: {dt_str}")
    return int(time.mktime(dt_obj.timetuple()))


def get_last_7_days():
    """
    获取近7天的开始日期和结束日期
    
    Returns:
        dict: 包含以下字段：
            - begin_date: 开始日期时间戳（秒）
            - end_date: 结束日期时间戳（秒）
            - begin_date_format: 开始日期格式化字符串 (ISO 8601)
            - end_date_format: 结束日期格式化字符串 (ISO 8601)
    """
    # 获取当前时区
    tz = timezone(timedelta(hours=8))  # 北京时间 UTC+8
    
    # 获取当前日期
    now = datetime.now(tz)
    
    # 计算结束时间（今天的23:59:59）
    end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # 计算开始时间（7天前的00:00:00）
    begin_time = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    return {
        # 时间戳（秒）
        "begin_date": int(begin_time.timestamp()),
        "end_date": int(end_time.timestamp()),
        
        # ISO 8601格式的时间字符串
        "begin_date_format": begin_time.isoformat(),
        "end_date_format": end_time.isoformat()
    }


def get_date_range(days: int = 7, include_today: bool = True):
    """
    获取指定天数的日期范围
    
    Args:
        days: 要获取的天数，默认7天
        include_today: 是否包含今天，默认True
        
    Returns:
        dict: 包含以下字段：
            - begin_date: 开始日期时间戳（秒）
            - end_date: 结束日期时间戳（秒）
            - begin_date_format: 开始日期格式化字符串 (ISO 8601)
            - end_date_format: 结束日期格式化字符串 (ISO 8601)
    """
    # 获取当前时区
    tz = timezone(timedelta(hours=8))  # 北京时间 UTC+8
    
    # 获取当前日期
    now = datetime.now(tz)
    
    # 根据是否包含今天来设置结束时间
    if include_today:
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        end_time = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)
    
    # 计算开始时间
    begin_time = (now - timedelta(days=days-1 if include_today else days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    
    return {
        # 时间戳（秒）
        "begin_date": int(begin_time.timestamp()),
        "end_date": int(end_time.timestamp()),
        
        # ISO 8601格式的时间字符串
        "begin_date_format": begin_time.isoformat(),
        "end_date_format": end_time.isoformat()
    }
