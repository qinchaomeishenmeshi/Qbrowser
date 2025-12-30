import asyncio
from pathlib import Path
from typing import Dict, Optional, Any

from utils.common_logger import get_logger
from utils.database_manager import db_manager

logger = get_logger(__name__)


class CookiesManager:
    """
    Cookies管理器，负责用户cookies和headers的存储、检索和生命周期管理。

    使用 SQLite 数据库持久化，支持多站点管理，内置过期检查。
    """

    def __init__(self, storage_dir: Path) -> None:
        """
        初始化Cookies管理器。

        Args:
            storage_dir: cookies存储目录路径（保留用于迁移参考）
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, user_id: str, site_key: str = None) -> str:
        """获取缓存键"""
        return f"{user_id}_{site_key or 'default'}"

    async def save_cookies(
        self,
        user_id: str,
        cookies: dict,
        headers: Optional[dict] = None,
        expires_in_days: int = 3,
        site_key: str = None,
    ) -> None:
        """保存用户的cookies和headers信息"""
        try:
            await db_manager.save_cookies(
                user_id, site_key, cookies, headers, expires_in_days
            )

            # 同时更新内存缓存（可选，SQLite 已经很快）
            cache_key = self._get_cache_key(user_id, site_key)
            self._cache[cache_key] = {
                "cookies": cookies,
                "headers": headers or {},
                "site_key": site_key,
            }

            site_info = f"[{site_key}]" if site_key else ""
            logger.info(f"已通过数据库保存用户 {user_id} {site_info} 的 cookies 信息")
        except Exception as e:
            logger.error(f"保存用户 {user_id} 的 cookies 失败: {e}")
            raise

    async def get_cookies(self, user_id: str, site_key: str = None) -> Optional[Dict]:
        """获取用户的cookies信息"""
        data = await db_manager.get_cookies_and_headers(user_id, site_key)
        if data:
            return data.get("cookies")
        return None

    async def get_headers(self, user_id: str, site_key: str = None) -> Optional[Dict]:
        """获取用户的headers信息"""
        data = await db_manager.get_cookies_and_headers(user_id, site_key)
        if data:
            return data.get("headers")
        return None

    async def remove_cookies(self, user_id: str, site_key: str = None) -> None:
        """删除用户的cookies信息"""
        try:
            await db_manager.delete_cookies(user_id, site_key)

            # 清理缓存
            if site_key is None:
                keys_to_remove = [k for k in self._cache if k.startswith(f"{user_id}_")]
                for k in keys_to_remove:
                    self._cache.pop(k, None)
            else:
                self._cache.pop(self._get_cache_key(user_id, site_key), None)

            logger.info(f"已从数据库删除用户 {user_id} 的 cookies 信息")
        except Exception as e:
            logger.error(f"删除用户 {user_id} 的 cookies 失败: {e}")

    async def clear_all(self) -> None:
        """清除所有用户的cookies信息"""
        try:
            db = await db_manager.get_db()
            await db.execute("DELETE FROM browser_cookies")
            await db.commit()
            self._cache.clear()
            logger.info("已清除数据库中所有用户的 cookies 信息")
        except Exception as e:
            logger.error(f"清除所有 cookies 失败: {e}")

    async def get_all_valid_users(self, site_key: str = None) -> Dict[str, Dict]:
        """获取所有有效的用户cookies信息"""
        try:
            rows = await db_manager.get_all_valid_cookies(site_key)
            result = {}
            for row in rows:
                u_id = row["user_id"]
                s_key = row["site_key"] or "default"

                if site_key:
                    result[u_id] = row
                else:
                    if u_id not in result:
                        result[u_id] = {}
                    result[u_id][s_key] = row
            return result
        except Exception as e:
            logger.error(f"获取有效用户列表失败: {e}")
            return {}
