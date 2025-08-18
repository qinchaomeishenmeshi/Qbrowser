import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any

from utils.common_logger import get_logger

logger = get_logger(__name__)


class CookiesManager:
    """
    Cookies管理器，负责用户cookies和headers的存储、检索和生命周期管理。
    
    支持多站点cookies管理，提供缓存机制和过期检查功能。
    所有操作都是线程安全的，使用异步锁保护并发访问。
    """
    
    def __init__(self, storage_dir: Path) -> None:
        """
        初始化Cookies管理器。
        
        Args:
            storage_dir: cookies存储目录路径
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_cookie_file(self, user_id: str, site_key: str = None) -> Path:
        """
        获取用户cookie文件路径
        
        Args:
            user_id: 用户ID
            site_key: 站点标识，用于存储不同站点的cookies
        
        Returns:
            文件路径
        """
        if site_key:
            return self.storage_dir / f"{user_id}_{site_key}_cookies.json"
        return self.storage_dir / f"{user_id}_cookies.json"

    def _get_cache_key(self, user_id: str, site_key: str = None) -> str:
        """
        获取缓存键
        """
        if site_key:
            return f"{user_id}_{site_key}"
        return user_id

    async def save_cookies(
        self, 
        user_id: str, 
        cookies: dict, 
        headers: Optional[dict] = None,
        expires_in_days: int = 7,
        site_key: str = None
    ) -> None:
        """
        保存用户的cookies和headers信息
        
        Args:
            user_id: 用户ID
            cookies: cookies数据
            headers: 请求头数据
            expires_in_days: cookie过期天数
            site_key: 站点标识，用于存储不同站点的cookies
        """
        async with self._lock:
            now = datetime.now()
            data = {
                'cookies': cookies,
                'headers': headers or {},
                'updated_at': now.isoformat(),
                'expires_at': (now + timedelta(days=expires_in_days)).isoformat(),
                'site_key': site_key
            }
            
            cache_key = self._get_cache_key(user_id, site_key)
            self._cache[cache_key] = data
            
            try:
                cookie_file = self._get_cookie_file(user_id, site_key)
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                site_info = f"[{site_key}]" if site_key else ""
                logger.info(f"已保存用户 {user_id} {site_info} 的 cookies 信息")
            except Exception as e:
                logger.error(f"保存用户 {user_id} 的 cookies 失败: {e}")
                raise

    async def get_cookies(self, user_id: str, site_key: str = None) -> Optional[Dict]:
        """
        获取用户的cookies信息
        
        如果cookies不存在或已过期，返回None
        
        Args:
            user_id: 用户ID
            site_key: 站点标识
        """
        cache_key = self._get_cache_key(user_id, site_key)
        
        if cache_key not in self._cache:
            await self._load_cookies(user_id, site_key)
        
        data = self._cache.get(cache_key)
        if not data:
            return None

        if self._is_expired(data):
            site_info = f"[{site_key}]" if site_key else ""
            logger.info(f"用户 {user_id} {site_info} 的 cookies 已过期")
            return None

        return data.get('cookies')

    async def get_headers(self, user_id: str, site_key: str = None) -> Optional[Dict]:
        """
        获取用户的headers信息
        
        Args:
            user_id: 用户ID
            site_key: 站点标识
        """
        cache_key = self._get_cache_key(user_id, site_key)
        
        if cache_key not in self._cache:
            await self._load_cookies(user_id, site_key)
        
        data = self._cache.get(cache_key)
        if not data:
            return None

        if self._is_expired(data):
            site_info = f"[{site_key}]" if site_key else ""
            logger.info(f"用户 {user_id} {site_info} 的 headers 已过期")
            return None

        return data.get('headers')

    async def _load_cookies(self, user_id: str, site_key: str = None) -> None:
        """
        从文件加载用户的cookies信息
        
        Args:
            user_id: 用户ID
            site_key: 站点标识
        """
        async with self._lock:
            cookie_file = self._get_cookie_file(user_id, site_key)
            if not cookie_file.exists():
                return
            
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                cache_key = self._get_cache_key(user_id, site_key)
                self._cache[cache_key] = data
                
                site_info = f"[{site_key}]" if site_key else ""
                logger.info(f"已加载用户 {user_id} {site_info} 的 cookies 信息")
            except Exception as e:
                logger.error(f"加载用户 {user_id} 的 cookies 失败: {e}")

    def _is_expired(self, data: Dict) -> bool:
        """
        检查cookies是否过期
        """
        try:
            expires_at = datetime.fromisoformat(data['expires_at'])
            return datetime.now() > expires_at
        except (KeyError, ValueError) as e:
            logger.error(f"检查 cookies 过期时间出错: {e}")
            return True

    async def remove_cookies(self, user_id: str, site_key: str = None) -> None:
        """
        删除用户的cookies信息
        
        Args:
            user_id: 用户ID
            site_key: 站点标识，如果为None则删除所有站点
        """
        async with self._lock:
            if site_key is None:
                # 删除所有站点的cookies
                for file in self.storage_dir.glob(f"{user_id}_*_cookies.json"):
                    try:
                        file.unlink()
                    except Exception as e:
                        logger.error(f"删除用户 {user_id} 的 cookies 文件失败: {e}")
                
                # 同时删除没有站点标识的默认cookies
                default_file = self._get_cookie_file(user_id)
                if default_file.exists():
                    try:
                        default_file.unlink()
                    except Exception as e:
                        logger.error(f"删除用户 {user_id} 的默认 cookies 文件失败: {e}")
                
                # 清除缓存
                keys_to_remove = []
                for key in self._cache:
                    if key.startswith(f"{user_id}_") or key == user_id:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    self._cache.pop(key, None)
                
                logger.info(f"已删除用户 {user_id} 的所有 cookies 信息")
            else:
                # 只删除特定站点的cookies
                cookie_file = self._get_cookie_file(user_id, site_key)
                if cookie_file.exists():
                    try:
                        cookie_file.unlink()
                        logger.info(f"已删除用户 {user_id} [{site_key}] 的 cookies 文件")
                    except Exception as e:
                        logger.error(f"删除用户 {user_id} [{site_key}] 的 cookies 文件失败: {e}")
                
                # 清除缓存
                cache_key = self._get_cache_key(user_id, site_key)
                self._cache.pop(cache_key, None)

    async def clear_all(self) -> None:
        """
        清除所有用户的cookies信息
        """
        async with self._lock:
            try:
                for file in self.storage_dir.glob("*_cookies.json"):
                    file.unlink()
                self._cache.clear()
                logger.info("已清除所有用户的 cookies 信息")
            except Exception as e:
                logger.error(f"清除所有 cookies 失败: {e}")

    async def get_all_valid_users(self, site_key: str = None) -> Dict[str, Dict]:
        """
        获取所有有效的用户cookies信息
        
        Args:
            site_key: 站点标识，如果指定则只获取特定站点的用户
        """
        result = {}
        
        if site_key:
            # 只获取特定站点的用户
            pattern = f"*_{site_key}_cookies.json"
        else:
            # 获取所有用户
            pattern = "*_cookies.json"
            
        for file in self.storage_dir.glob(pattern):
            # 从文件名中提取用户ID和站点信息
            parts = file.stem.split('_')
            
            if site_key:
                # 特定站点模式: {user_id}_{site_key}_cookies.json
                if len(parts) >= 2 and parts[-1] == "cookies":
                    user_id = parts[0]
                    actual_site_key = parts[1] if len(parts) > 2 else None
                    
                    if actual_site_key == site_key:
                        cookies = await self.get_cookies(user_id, site_key)
                        if cookies:
                            cache_key = self._get_cache_key(user_id, site_key)
                            result[user_id] = self._cache[cache_key]
            else:
                # 所有用户模式
                if parts[-1] == "cookies":
                    user_id = parts[0]
                    actual_site_key = parts[1] if len(parts) > 2 else None
                    
                    cookies = await self.get_cookies(user_id, actual_site_key)
                    if cookies:
                        cache_key = self._get_cache_key(user_id, actual_site_key)
                        result[user_id] = result.get(user_id, {})
                        result[user_id][actual_site_key or "default"] = self._cache[cache_key]
                    
        return result