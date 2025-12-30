# chrome_config_api.py
# Chrome浏览器路径配置API接口

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from conf.browser_config import chrome_path_manager
from utils.common_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chrome-config", tags=["Chrome配置"])


class ChromePathRequest(BaseModel):
    """设置Chrome路径的请求模型"""

    path: Optional[str] = None


class ChromePathResponse(BaseModel):
    """Chrome路径响应模型"""

    success: bool
    message: str
    data: Optional[dict] = None


def _handle_chrome_operation_error(operation: str, error: Exception) -> None:
    """处理Chrome操作异常的通用函数"""
    logger.error(f"{operation}失败: {error}")
    raise HTTPException(status_code=500, detail=str(error))


def _create_chrome_response(
    success: bool, message: str, data: Optional[dict] = None
) -> ChromePathResponse:
    """创建Chrome配置响应的工厂函数"""
    return ChromePathResponse(success=success, message=message, data=data)


async def _clear_chrome_path_operation() -> ChromePathResponse:
    """清除Chrome路径的核心操作"""
    success = await chrome_path_manager.set_chrome_path(None)
    if success:
        return _create_chrome_response(
            success=True, message="已清除自定义Chrome路径，将使用系统默认路径"
        )
    else:
        return _create_chrome_response(success=False, message="清除Chrome路径失败")


@router.get("/current", response_model=ChromePathResponse, summary="获取当前Chrome配置")
async def get_current_chrome_config():
    """获取当前Chrome配置信息"""
    try:
        config = await chrome_path_manager.get_current_config()
        return _create_chrome_response(
            success=True, message="获取Chrome配置成功", data=config
        )
    except Exception as e:
        _handle_chrome_operation_error("获取Chrome配置", e)


@router.get("/detect", response_model=ChromePathResponse, summary="检测Chrome浏览器")
async def detect_chrome_browsers():
    """自动检测系统中可用的Chrome浏览器"""
    try:
        available_paths = chrome_path_manager.auto_detect_chrome()
        return _create_chrome_response(
            success=True,
            message=f"检测到 {len(available_paths)} 个可用的Chrome浏览器",
            data={"available_paths": available_paths},
        )
    except Exception as e:
        _handle_chrome_operation_error("检测Chrome浏览器", e)


@router.post("/set-path", response_model=ChromePathResponse, summary="设置Chrome路径")
async def set_chrome_path(request: ChromePathRequest):
    """设置自定义Chrome路径"""
    try:
        # 如果路径为空或None，则清除自定义路径
        if not request.path or not request.path.strip():
            return await _clear_chrome_path_operation()

        # 设置自定义路径
        cleaned_path = request.path.strip()
        success = await chrome_path_manager.set_chrome_path(cleaned_path)

        if success:
            return _create_chrome_response(
                success=True, message=f"Chrome路径设置成功: {cleaned_path}"
            )
        else:
            return _create_chrome_response(
                success=False,
                message=f"Chrome路径设置失败，请检查路径是否正确: {cleaned_path}",
            )
    except Exception as e:
        _handle_chrome_operation_error("设置Chrome路径", e)


@router.delete(
    "/clear-path", response_model=ChromePathResponse, summary="清除Chrome路径"
)
async def clear_chrome_path():
    """清除自定义Chrome路径，恢复使用系统默认路径"""
    try:
        return await _clear_chrome_path_operation()
    except Exception as e:
        _handle_chrome_operation_error("清除Chrome路径", e)
