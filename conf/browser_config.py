# browser_config.py
# Chrome浏览器路径配置管理

import os
import json
from pathlib import Path
from typing import Optional
from conf import writable_path, resource_path
from utils.common_logger import get_logger

logger = get_logger(__name__)

# 默认Chrome路径配置（按操作系统）
DEFAULT_CHROME_PATHS = {
    'darwin': [  # macOS
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
    ],
    'win32': [  # Windows
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        r'C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
    ],
    'linux': [  # Linux
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/snap/bin/chromium',
        '/usr/bin/microsoft-edge',
        '/usr/bin/brave-browser'
    ]
}

class ChromePathManager:
    """Chrome浏览器路径管理器"""
    
    def __init__(self):
        self.config_file = Path(writable_path("chrome_config.json"))
        self._custom_path = None
        self._load_config()
    
    def _load_config(self) -> None:
        """从配置文件加载Chrome路径配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self._custom_path = config.get('chrome_path')
                    logger.info(f"已加载Chrome路径配置: {self._custom_path}")
        except Exception as e:
            logger.warning(f"加载Chrome路径配置失败: {e}")
            self._custom_path = None
    
    def _save_config(self) -> None:
        """保存Chrome路径配置到文件"""
        try:
            config = {'chrome_path': self._custom_path}
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"Chrome路径配置已保存: {self._custom_path}")
        except Exception as e:
            logger.error(f"保存Chrome路径配置失败: {e}")
    
    def set_chrome_path(self, path: str) -> bool:
        """设置自定义Chrome路径
        
        Args:
            path: Chrome可执行文件的完整路径
            
        Returns:
            bool: 设置是否成功
        """
        if not path:
            self._custom_path = None
            self._save_config()
            logger.info("已清除自定义Chrome路径，将使用系统默认路径")
            return True
            
        path_obj = Path(path)
        if not path_obj.exists():
            logger.error(f"Chrome路径不存在: {path}")
            return False
            
        if not path_obj.is_file():
            logger.error(f"Chrome路径不是文件: {path}")
            return False
            
        self._custom_path = str(path_obj.resolve())
        self._save_config()
        logger.info(f"Chrome路径设置成功: {self._custom_path}")
        return True
    
    def get_chrome_path(self) -> Optional[str]:
        """获取Chrome浏览器路径
        
        Returns:
            str: Chrome可执行文件路径，如果未找到返回None
        """
        # 1. 优先使用自定义路径
        if self._custom_path and Path(self._custom_path).exists():
            logger.info(f"使用自定义Chrome路径: {self._custom_path}")
            return self._custom_path
        
        # 2. 尝试系统默认路径
        platform = os.name if os.name != 'posix' else 'darwin' if 'darwin' in os.sys.platform else 'linux'
        if platform == 'nt':
            platform = 'win32'
        
        default_paths = DEFAULT_CHROME_PATHS.get(platform, [])
        
        for path_template in default_paths:
            # 处理Windows路径中的{username}占位符
            if '{username}' in path_template:
                username = os.getenv('USERNAME') or os.getenv('USER', '')
                path = path_template.format(username=username)
            else:
                path = path_template
            
            if Path(path).exists():
                logger.info(f"找到系统Chrome路径: {path}")
                return path
        
        logger.warning("未找到可用的Chrome浏览器路径")
        return None
    
    def get_current_config(self) -> dict:
        """获取当前配置信息
        
        Returns:
            dict: 包含当前配置的字典
        """
        return {
            'custom_path': self._custom_path,
            'effective_path': self.get_chrome_path(),
            'config_file': str(self.config_file),
            'platform': os.sys.platform
        }
    
    def auto_detect_chrome(self) -> list:
        """自动检测系统中可用的Chrome浏览器
        
        Returns:
            list: 可用的Chrome路径列表
        """
        available_paths = []
        
        platform = os.name if os.name != 'posix' else 'darwin' if 'darwin' in os.sys.platform else 'linux'
        if platform == 'nt':
            platform = 'win32'
        
        default_paths = DEFAULT_CHROME_PATHS.get(platform, [])
        
        for path_template in default_paths:
            # 处理Windows路径中的{username}占位符
            if '{username}' in path_template:
                username = os.getenv('USERNAME') or os.getenv('USER', '')
                path = path_template.format(username=username)
            else:
                path = path_template
            
            if Path(path).exists():
                available_paths.append(path)
        
        logger.info(f"检测到 {len(available_paths)} 个可用的Chrome浏览器")
        return available_paths

# 全局实例
chrome_path_manager = ChromePathManager()