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

@router.get("/current", response_model=ChromePathResponse)
async def get_current_chrome_config():
    """获取当前Chrome配置信息"""
    try:
        config = chrome_path_manager.get_current_config()
        return ChromePathResponse(
            success=True,
            message="获取Chrome配置成功",
            data=config
        )
    except Exception as e:
        logger.error(f"获取Chrome配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detect", response_model=ChromePathResponse)
async def detect_chrome_browsers():
    """自动检测系统中可用的Chrome浏览器"""
    try:
        available_paths = chrome_path_manager.auto_detect_chrome()
        return ChromePathResponse(
            success=True,
            message=f"检测到 {len(available_paths)} 个可用的Chrome浏览器",
            data={"available_paths": available_paths}
        )
    except Exception as e:
        logger.error(f"检测Chrome浏览器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set-path", response_model=ChromePathResponse)
async def set_chrome_path(request: ChromePathRequest):
    """设置自定义Chrome路径"""
    try:
        if request.path is None or request.path.strip() == "":
            # 清除自定义路径
            success = chrome_path_manager.set_chrome_path(None)
            if success:
                return ChromePathResponse(
                    success=True,
                    message="已清除自定义Chrome路径，将使用系统默认路径"
                )
            else:
                return ChromePathResponse(
                    success=False,
                    message="清除Chrome路径失败"
                )
        else:
            # 设置自定义路径
            success = chrome_path_manager.set_chrome_path(request.path.strip())
            if success:
                return ChromePathResponse(
                    success=True,
                    message=f"Chrome路径设置成功: {request.path}"
                )
            else:
                return ChromePathResponse(
                    success=False,
                    message=f"Chrome路径设置失败，请检查路径是否正确: {request.path}"
                )
    except Exception as e:
        logger.error(f"设置Chrome路径失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear-path", response_model=ChromePathResponse)
async def clear_chrome_path():
    """清除自定义Chrome路径"""
    try:
        success = chrome_path_manager.set_chrome_path(None)
        if success:
            return ChromePathResponse(
                success=True,
                message="已清除自定义Chrome路径，将使用系统默认路径"
            )
        else:
            return ChromePathResponse(
                success=False,
                message="清除Chrome路径失败"
            )
    except Exception as e:
        logger.error(f"清除Chrome路径失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))