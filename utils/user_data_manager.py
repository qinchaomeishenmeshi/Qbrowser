import asyncio
from pathlib import Path
from typing import List, Optional, Any
from utils.common_logger import get_logger
from utils.database_manager import db_manager

logger = get_logger(__name__)


class UserDataManager:
    """用户数据管理器

    负责管理用户配置信息的持久化，现已迁移至 SQLite。
    """

    def __init__(self):
        # 兼容性：保留目录引用，但不作为核心存储
        self.user_data_dir = self._get_user_data_directory()

    def _get_user_data_directory(self) -> Path:
        """获取项目数据目录路径"""
        import sys

        if getattr(sys, "frozen", False):
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).parent.parent

        user_data_dir = base_path / "user_data"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        return user_data_dir

    async def load_user_ids(self) -> List[str]:
        """从数据库加载用户ID列表"""
        return await db_manager.get_value("user_ids", [])

    async def save_user_ids(self, user_ids: List[str]) -> bool:
        """保存用户ID列表到数据库"""
        try:
            # 简单去重和过滤
            cleaned_ids = sorted(
                list(set([uid.strip() for uid in user_ids if uid.strip()]))
            )
            await db_manager.set_value("user_ids", cleaned_ids)
            logger.info(f"成功保存 {len(cleaned_ids)} 个用户ID到数据库")
            return True
        except Exception as e:
            logger.error(f"保存用户ID失败: {e}")
            return False

    async def save_user_ids_from_text(self, text: str) -> bool:
        """从文本内容保存用户ID列表"""
        if not text:
            return await self.save_user_ids([])
        user_ids = [line.strip() for line in text.split("\n") if line.strip()]
        return await self.save_user_ids(user_ids)

    async def load_json_config(self, filename: str, default: Any = None) -> Any:
        """从 SQLite kv_storage 加载配置"""
        return await db_manager.get_value(f"config_{filename}", default)

    async def save_json_config(self, filename: str, data: Any) -> bool:
        """保存配置到 SQLite kv_storage"""
        try:
            await db_manager.set_value(f"config_{filename}", data)
            logger.debug(f"成功保存配置文件到数据库: {filename}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件 {filename} 失败: {e}")
            return False


# 全局单例
_user_data_manager = UserDataManager()


def get_user_data_manager() -> UserDataManager:
    return _user_data_manager
