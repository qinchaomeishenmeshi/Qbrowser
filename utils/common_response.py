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


class PublicResponse:
    """
    统一响应格式类
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> Dict[str, Any]:
        """
        返回成功响应
        
        :param data: 返回的数据
        :param message: 成功消息
        :return: 成功响应字典
        """
        return {
            "status": "success",
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(message: str = "操作失败", data: Any = None) -> Dict[str, Any]:
        """
        返回错误响应
        
        :param message: 错误消息
        :param data: 错误相关数据
        :return: 错误响应字典
        """
        return {
            "status": "error",
            "message": message,
            "data": data
        }
