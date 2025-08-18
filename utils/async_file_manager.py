import asyncio
import json
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class AsyncFileManager:
    """
    异步文件管理器
    
    提供高性能的异步文件I/O操作，包括：
    - 异步JSON文件读写
    - 文件锁机制
    - 批量文件操作
    - 目录管理
    - 错误处理和重试
    """
    
    def __init__(self, base_path: Path, encoding: str = 'utf-8'):
        """
        初始化异步文件管理器
        
        Args:
            base_path: 基础路径
            encoding: 文件编码
        """
        self.base_path = Path(base_path)
        self.encoding = encoding
        self._file_locks: Dict[str, asyncio.Lock] = {}
        self._lock_manager_lock = asyncio.Lock()
    
    async def _get_file_lock(self, file_path: Path) -> asyncio.Lock:
        """
        获取文件级别的异步锁
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件对应的异步锁
        """
        file_key = str(file_path.resolve())
        
        async with self._lock_manager_lock:
            if file_key not in self._file_locks:
                self._file_locks[file_key] = asyncio.Lock()
            return self._file_locks[file_key]
    
    @asynccontextmanager
    async def _file_lock_context(self, file_path: Path):
        """
        文件锁上下文管理器
        
        Args:
            file_path: 文件路径
        """
        lock = await self._get_file_lock(file_path)
        async with lock:
            yield
    
    async def ensure_directory(self, directory: Path) -> None:
        """
        异步确保目录存在
        
        Args:
            directory: 目录路径
        """
        try:
            await aiofiles.os.makedirs(directory, exist_ok=True)
        except Exception as e:
            logger.error(f"创建目录失败 {directory}: {e}")
            raise
    
    async def file_exists(self, file_path: Path) -> bool:
        """
        异步检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否存在
        """
        try:
            await aiofiles.os.stat(file_path)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"检查文件存在性失败 {file_path}: {e}")
            return False
    
    async def get_file_size(self, file_path: Path) -> int:
        """
        异步获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        try:
            stat_result = await aiofiles.os.stat(file_path)
            return stat_result.st_size
        except Exception as e:
            logger.error(f"获取文件大小失败 {file_path}: {e}")
            return 0
    
    async def get_file_mtime(self, file_path: Path) -> Optional[datetime]:
        """
        异步获取文件修改时间
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件修改时间
        """
        try:
            stat_result = await aiofiles.os.stat(file_path)
            return datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc)
        except Exception as e:
            logger.error(f"获取文件修改时间失败 {file_path}: {e}")
            return None
    
    async def read_text_file(self, file_path: Path) -> Optional[str]:
        """
        异步读取文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容字符串，失败时返回None
        """
        async with self._file_lock_context(file_path):
            try:
                async with aiofiles.open(file_path, 'r', encoding=self.encoding) as f:
                    content = await f.read()
                    logger.debug(f"成功读取文件: {file_path}")
                    return content
            except FileNotFoundError:
                logger.debug(f"文件不存在: {file_path}")
                return None
            except Exception as e:
                logger.error(f"读取文件失败 {file_path}: {e}")
                return None
    
    async def write_text_file(self, file_path: Path, content: str, create_dirs: bool = True) -> bool:
        """
        异步写入文本文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            create_dirs: 是否自动创建目录
            
        Returns:
            操作是否成功
        """
        async with self._file_lock_context(file_path):
            try:
                if create_dirs:
                    await self.ensure_directory(file_path.parent)
                
                async with aiofiles.open(file_path, 'w', encoding=self.encoding) as f:
                    await f.write(content)
                    await f.flush()  # 确保数据写入磁盘
                    
                logger.debug(f"成功写入文件: {file_path}")
                return True
            except Exception as e:
                logger.error(f"写入文件失败 {file_path}: {e}")
                return False
    
    async def read_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        异步读取JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            JSON数据字典，失败时返回None
        """
        content = await self.read_text_file(file_path)
        if content is None:
            return None
        
        try:
            data = json.loads(content)
            logger.debug(f"成功解析JSON文件: {file_path}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败 {file_path}: {e}")
            return None
    
    async def write_json_file(
        self, 
        file_path: Path, 
        data: Dict[str, Any], 
        create_dirs: bool = True,
        indent: int = 2
    ) -> bool:
        """
        异步写入JSON文件
        
        Args:
            file_path: 文件路径
            data: 要写入的数据
            create_dirs: 是否自动创建目录
            indent: JSON缩进
            
        Returns:
            操作是否成功
        """
        try:
            content = json.dumps(data, ensure_ascii=False, indent=indent)
            return await self.write_text_file(file_path, content, create_dirs)
        except Exception as e:
            logger.error(f"JSON序列化失败 {file_path}: {e}")
            return False
    
    async def append_to_file(self, file_path: Path, content: str, create_dirs: bool = True) -> bool:
        """
        异步追加内容到文件
        
        Args:
            file_path: 文件路径
            content: 要追加的内容
            create_dirs: 是否自动创建目录
            
        Returns:
            操作是否成功
        """
        async with self._file_lock_context(file_path):
            try:
                if create_dirs:
                    await self.ensure_directory(file_path.parent)
                
                async with aiofiles.open(file_path, 'a', encoding=self.encoding) as f:
                    await f.write(content)
                    await f.flush()
                    
                logger.debug(f"成功追加到文件: {file_path}")
                return True
            except Exception as e:
                logger.error(f"追加文件失败 {file_path}: {e}")
                return False
    
    async def delete_file(self, file_path: Path) -> bool:
        """
        异步删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            操作是否成功
        """
        async with self._file_lock_context(file_path):
            try:
                await aiofiles.os.remove(file_path)
                logger.debug(f"成功删除文件: {file_path}")
                return True
            except FileNotFoundError:
                logger.debug(f"文件不存在，无需删除: {file_path}")
                return True
            except Exception as e:
                logger.error(f"删除文件失败 {file_path}: {e}")
                return False
    
    async def copy_file(self, src_path: Path, dst_path: Path, create_dirs: bool = True) -> bool:
        """
        异步复制文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            create_dirs: 是否自动创建目录
            
        Returns:
            操作是否成功
        """
        try:
            content = await self.read_text_file(src_path)
            if content is None:
                return False
            
            return await self.write_text_file(dst_path, content, create_dirs)
        except Exception as e:
            logger.error(f"复制文件失败 {src_path} -> {dst_path}: {e}")
            return False
    
    async def move_file(self, src_path: Path, dst_path: Path, create_dirs: bool = True) -> bool:
        """
        异步移动文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            create_dirs: 是否自动创建目录
            
        Returns:
            操作是否成功
        """
        try:
            if create_dirs:
                await self.ensure_directory(dst_path.parent)
            
            # 使用系统级移动操作
            await aiofiles.os.rename(src_path, dst_path)
            logger.debug(f"成功移动文件: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            logger.error(f"移动文件失败 {src_path} -> {dst_path}: {e}")
            # 尝试复制后删除的方式
            if await self.copy_file(src_path, dst_path, create_dirs):
                return await self.delete_file(src_path)
            return False
    
    async def list_files(
        self, 
        directory: Path, 
        pattern: str = "*", 
        recursive: bool = False
    ) -> List[Path]:
        """
        异步列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件名模式
            recursive: 是否递归搜索
            
        Returns:
            文件路径列表
        """
        try:
            if not await self.file_exists(directory):
                return []
            
            files = []
            if recursive:
                files = list(directory.rglob(pattern))
            else:
                files = list(directory.glob(pattern))
            
            # 过滤出文件（排除目录）
            result = []
            for file_path in files:
                if await self.file_exists(file_path) and file_path.is_file():
                    result.append(file_path)
            
            return result
        except Exception as e:
            logger.error(f"列出文件失败 {directory}: {e}")
            return []
    
    async def batch_read_json_files(self, file_paths: List[Path]) -> Dict[Path, Optional[Dict[str, Any]]]:
        """
        批量异步读取JSON文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件路径到数据的映射字典
        """
        async def read_single_file(file_path: Path) -> tuple[Path, Optional[Dict[str, Any]]]:
            data = await self.read_json_file(file_path)
            return file_path, data
        
        tasks = [read_single_file(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        result_dict = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批量读取文件时出错: {result}")
                continue
            
            file_path, data = result
            result_dict[file_path] = data
        
        return result_dict
    
    async def batch_write_json_files(
        self, 
        file_data_map: Dict[Path, Dict[str, Any]], 
        create_dirs: bool = True
    ) -> Dict[Path, bool]:
        """
        批量异步写入JSON文件
        
        Args:
            file_data_map: 文件路径到数据的映射
            create_dirs: 是否自动创建目录
            
        Returns:
            文件路径到操作结果的映射
        """
        async def write_single_file(file_path: Path, data: Dict[str, Any]) -> tuple[Path, bool]:
            success = await self.write_json_file(file_path, data, create_dirs)
            return file_path, success
        
        tasks = [
            write_single_file(path, data) 
            for path, data in file_data_map.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        result_dict = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批量写入文件时出错: {result}")
                continue
            
            file_path, success = result
            result_dict[file_path] = success
        
        return result_dict
    
    async def batch_delete_files(self, file_paths: List[Path]) -> Dict[Path, bool]:
        """
        批量异步删除文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件路径到操作结果的映射
        """
        async def delete_single_file(file_path: Path) -> tuple[Path, bool]:
            success = await self.delete_file(file_path)
            return file_path, success
        
        tasks = [delete_single_file(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        result_dict = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批量删除文件时出错: {result}")
                continue
            
            file_path, success = result
            result_dict[file_path] = success
        
        return result_dict
    
    async def cleanup_old_files(
        self, 
        directory: Path, 
        max_age_days: int = 30, 
        pattern: str = "*.json"
    ) -> int:
        """
        异步清理旧文件
        
        Args:
            directory: 目录路径
            max_age_days: 最大文件年龄（天）
            pattern: 文件名模式
            
        Returns:
            删除的文件数量
        """
        try:
            files = await self.list_files(directory, pattern, recursive=True)
            current_time = datetime.now(timezone.utc)
            old_files = []
            
            for file_path in files:
                mtime = await self.get_file_mtime(file_path)
                if mtime and (current_time - mtime).days > max_age_days:
                    old_files.append(file_path)
            
            if old_files:
                delete_results = await self.batch_delete_files(old_files)
                deleted_count = sum(1 for success in delete_results.values() if success)
                logger.info(f"清理了 {deleted_count} 个旧文件")
                return deleted_count
            
            return 0
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
            return 0
    
    async def get_directory_size(self, directory: Path) -> int:
        """
        异步计算目录大小
        
        Args:
            directory: 目录路径
            
        Returns:
            目录总大小（字节）
        """
        try:
            files = await self.list_files(directory, "*", recursive=True)
            total_size = 0
            
            for file_path in files:
                size = await self.get_file_size(file_path)
                total_size += size
            
            return total_size
        except Exception as e:
            logger.error(f"计算目录大小失败 {directory}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取文件管理器统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'base_path': str(self.base_path),
            'encoding': self.encoding,
            'active_file_locks': len(self._file_locks),
            'lock_manager_status': 'active'
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # 清理资源
        async with self._lock_manager_lock:
            self._file_locks.clear()


# 创建全局异步文件管理器实例
async_file_manager = AsyncFileManager(Path.cwd())