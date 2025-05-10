from typing import Any, Dict


def PublicResponse(status: str, message: str, data: Any = None) -> Dict[str, Any]:
    """
    返回统一格式的 API 响应

    :param status: 响应状态，例如 'success' 或 'error'
    :param message: 可读性良好的状态描述信息
    :param data: 返回的数据对象，默认为 None
    :return: 标准化的字典格式响应
    """
    return dict({
        "status": status,
        "message": message,
        "data": data
    })
