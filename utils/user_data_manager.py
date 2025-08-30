# user_data_manager.py
# 用户数据管理器 - 统一管理用户配置文件的读写操作

import os
import json
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any
from utils.common_logger import get_logger

logger = get_logger(__name__)

class UserDataManager:
    """用户数据管理器
    
    负责管理用户配置文件的读写操作，确保：
    1. 本地开发和打包exe都能正确读取数据
    2. 数据文件独立于版本控制
    3. 支持实时保存和自动备份
    4. 线程安全的文件操作
    """
    
    def __init__(self):
        self._lock = threading.RLock()  # 线程安全锁
        self.user_data_dir = self._get_user_data_directory()
        self._ensure_user_data_directory()
        # 执行数据迁移（仅在首次运行时）
        self._migrate_legacy_data()
        
    def _get_user_data_directory(self) -> Path:
        """获取用户数据目录路径
        
        优先级：
        1. 打包exe：exe所在目录/user_data
        2. 开发环境：项目根目录/user_data
        3. 备选方案：用户主目录/.qw-browser
        
        Returns:
            Path: 用户数据目录路径
        """
        import sys
        
        if getattr(sys, 'frozen', False):
            # 打包后的exe环境
            base_path = Path(sys.executable).parent
        else:
            # 开发环境
            base_path = Path(__file__).parent.parent
            
        user_data_dir = base_path / 'user_data'
        
        # 如果无法在程序目录创建，则使用用户主目录
        try:
            user_data_dir.mkdir(parents=True, exist_ok=True)
            # 测试写入权限
            test_file = user_data_dir / '.test_write'
            test_file.write_text('test')
            test_file.unlink()
            return user_data_dir
        except (PermissionError, OSError) as e:
            logger.warning(f"无法在程序目录创建用户数据目录: {e}")
            # 使用用户主目录作为备选方案
            fallback_dir = Path.home() / '.qw-browser'
            fallback_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"使用备选用户数据目录: {fallback_dir}")
            return fallback_dir
    
    def _ensure_user_data_directory(self) -> None:
        """确保用户数据目录存在"""
        try:
            self.user_data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"用户数据目录: {self.user_data_dir}")
        except Exception as e:
            logger.error(f"创建用户数据目录失败: {e}")
            raise
    
    def get_user_ids_file_path(self) -> Path:
        """获取用户ID文件路径
        
        Returns:
            Path: user_ids.txt文件的完整路径
        """
        return self.user_data_dir / 'user_ids.txt'
    
    def load_user_ids(self) -> List[str]:
        """加载用户ID列表
        
        Returns:
            List[str]: 用户ID列表，如果文件不存在或为空则返回空列表
        """
        with self._lock:
            try:
                file_path = self.get_user_ids_file_path()
                if not file_path.exists():
                    logger.info(f"用户ID文件不存在: {file_path}")
                    return []
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    user_ids = [line.strip() for line in lines if line.strip()]
                    logger.info(f"成功加载 {len(user_ids)} 个用户ID")
                    return user_ids
                    
            except Exception as e:
                logger.error(f"加载用户ID失败: {e}")
                return []
    
    def save_user_ids(self, user_ids: List[str]) -> bool:
        """保存用户ID列表
        
        Args:
            user_ids: 用户ID列表
            
        Returns:
            bool: 保存是否成功
        """
        with self._lock:
            try:
                # 数据清理：去除空行和重复项，保持顺序
                cleaned_ids = []
                seen = set()
                for user_id in user_ids:
                    user_id = user_id.strip()
                    if user_id and user_id not in seen:
                        cleaned_ids.append(user_id)
                        seen.add(user_id)
                
                file_path = self.get_user_ids_file_path()
                
                # 创建备份
                if file_path.exists():
                    backup_path = file_path.with_suffix('.txt.bak')
                    file_path.rename(backup_path)
                    logger.debug(f"创建备份文件: {backup_path}")
                
                # 保存新数据
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(cleaned_ids))
                    if cleaned_ids:  # 如果有数据，在末尾添加换行符
                        f.write('\n')
                
                logger.info(f"成功保存 {len(cleaned_ids)} 个用户ID到 {file_path}")
                return True
                
            except Exception as e:
                logger.error(f"保存用户ID失败: {e}")
                # 尝试恢复备份
                try:
                    backup_path = file_path.with_suffix('.txt.bak')
                    if backup_path.exists():
                        backup_path.rename(file_path)
                        logger.info("已恢复备份文件")
                except Exception as restore_e:
                    logger.error(f"恢复备份失败: {restore_e}")
                return False
    
    def save_user_ids_from_text(self, text: str) -> bool:
        """从文本内容保存用户ID列表
        
        Args:
            text: 包含用户ID的文本内容（每行一个ID）
            
        Returns:
            bool: 保存是否成功
        """
        if not text:
            return self.save_user_ids([])
        
        user_ids = [line.strip() for line in text.split('\n') if line.strip()]
        return self.save_user_ids(user_ids)
    
    def get_config_file_path(self, filename: str) -> Path:
        """获取配置文件路径
        
        Args:
            filename: 配置文件名
            
        Returns:
            Path: 配置文件的完整路径
        """
        return self.user_data_dir / filename
    
    def load_json_config(self, filename: str, default: Any = None) -> Any:
        """加载JSON配置文件
        
        Args:
            filename: 配置文件名
            default: 默认值
            
        Returns:
            Any: 配置数据，如果加载失败则返回默认值
        """
        with self._lock:
            try:
                file_path = self.get_config_file_path(filename)
                if not file_path.exists():
                    return default
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f"成功加载配置文件: {filename}")
                    return data
                    
            except Exception as e:
                logger.error(f"加载配置文件 {filename} 失败: {e}")
                return default
    
    def save_json_config(self, filename: str, data: Any) -> bool:
        """保存JSON配置文件
        
        Args:
            filename: 配置文件名
            data: 要保存的数据
            
        Returns:
            bool: 保存是否成功
        """
        with self._lock:
            try:
                file_path = self.get_config_file_path(filename)
                
                # 创建备份
                if file_path.exists():
                    backup_path = file_path.with_suffix(f'{file_path.suffix}.bak')
                    file_path.rename(backup_path)
                
                # 保存新数据
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.debug(f"成功保存配置文件: {filename}")
                return True
                
            except Exception as e:
                logger.error(f"保存配置文件 {filename} 失败: {e}")
                return False
    
    def get_user_data_directory(self) -> Path:
        """获取用户数据目录路径（只读）
        
        Returns:
            Path: 用户数据目录路径
        """
        return self.user_data_dir
    
    def cleanup_old_backups(self, max_backups: int = 5) -> None:
        """清理旧的备份文件
        
        Args:
            max_backups: 保留的最大备份数量
        """
        try:
            backup_files = list(self.user_data_dir.glob('*.bak'))
            if len(backup_files) > max_backups:
                # 按修改时间排序，删除最旧的备份
                backup_files.sort(key=lambda x: x.stat().st_mtime)
                for old_backup in backup_files[:-max_backups]:
                    old_backup.unlink()
                    logger.debug(f"删除旧备份文件: {old_backup}")
        except Exception as e:
            logger.warning(f"清理备份文件失败: {e}")
    
    def _migrate_legacy_data(self) -> None:
        """迁移老版本的用户数据文件
        
        检查项目根目录是否存在老版本的数据文件，如果存在则迁移到新的user_data目录
        迁移完成后创建标记文件，避免重复迁移
        """
        # 检查是否已经迁移过
        migration_marker = self.user_data_dir / '.migration_completed'
        if migration_marker.exists():
            return
            
        # 获取项目根目录（老版本数据存储位置）
        import sys
        if getattr(sys, 'frozen', False):
            # 打包环境：exe所在目录
            legacy_base_dir = Path(sys.executable).parent
        else:
            # 开发环境：项目根目录
            legacy_base_dir = Path(__file__).parent.parent
            
        # 定义需要迁移的文件列表
        files_to_migrate = [
            'user_ids.txt',
            'chrome_config.json',
            'app_config.json',
            'user_cache.json'
        ]
        
        migrated_files = []
        
        with self._lock:
            try:
                for filename in files_to_migrate:
                    legacy_file = legacy_base_dir / filename
                    if legacy_file.exists() and legacy_file.is_file():
                        # 目标文件路径
                        target_file = self.user_data_dir / filename
                        
                        # 如果目标文件不存在，则迁移
                        if not target_file.exists():
                            # 复制文件内容
                            target_file.write_bytes(legacy_file.read_bytes())
                            migrated_files.append(filename)
                            logger.info(f"迁移用户数据文件: {filename}")
                            
                            # 创建备份（重命名原文件）
                            backup_file = legacy_base_dir / f"{filename}.legacy_backup"
                            if not backup_file.exists():
                                legacy_file.rename(backup_file)
                                logger.info(f"原文件已备份为: {backup_file.name}")
                        else:
                            logger.info(f"目标文件已存在，跳过迁移: {filename}")
                
                # 创建迁移完成标记文件
                migration_marker.write_text(
                    f"Migration completed at: {threading.current_thread().name}\n"
                    f"Migrated files: {', '.join(migrated_files) if migrated_files else 'None'}\n"
                )
                
                if migrated_files:
                    logger.info(f"数据迁移完成，共迁移 {len(migrated_files)} 个文件: {', '.join(migrated_files)}")
                else:
                    logger.info("未发现需要迁移的老版本数据文件")
                    
            except Exception as e:
                logger.error(f"数据迁移过程中发生错误: {e}")
                # 即使迁移失败，也创建标记文件避免重复尝试
                try:
                    migration_marker.write_text(f"Migration failed at: {threading.current_thread().name}\nError: {str(e)}\n")
                except:
                    pass


# 全局单例实例
_user_data_manager = None
_manager_lock = threading.Lock()

def get_user_data_manager() -> UserDataManager:
    """获取用户数据管理器单例实例
    
    Returns:
        UserDataManager: 用户数据管理器实例
    """
    global _user_data_manager
    if _user_data_manager is None:
        with _manager_lock:
            if _user_data_manager is None:
                _user_data_manager = UserDataManager()
    return _user_data_manager