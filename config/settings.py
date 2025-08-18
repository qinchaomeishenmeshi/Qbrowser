"""应用配置管理模块

统一管理应用的所有配置项，支持环境变量覆盖和配置验证。
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import json
from loguru import logger


@dataclass
class NetworkConfig:
    """网络配置"""
    host: str = "127.0.0.1"
    api_port: int = 6001
    scheduler_port: int = 8000
    browser_start_port: int = 9111
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    
    def __post_init__(self):
        """配置后处理，支持环境变量覆盖"""
        self.host = os.getenv("APP_HOST", self.host)
        self.api_port = int(os.getenv("API_PORT", self.api_port))
        self.scheduler_port = int(os.getenv("SCHEDULER_PORT", self.scheduler_port))
        self.browser_start_port = int(os.getenv("BROWSER_START_PORT", self.browser_start_port))
        
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            self.cors_origins = cors_env.split(",")


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = False
    disable_web_security: bool = True
    disable_features: List[str] = field(default_factory=lambda: [
        "VizDisplayCompositor",
        "TranslateUI"
    ])
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    window_size: tuple = (1920, 1080)
    timeout: int = 30
    max_instances: int = 10
    
    def __post_init__(self):
        """配置后处理"""
        self.headless = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
        self.timeout = int(os.getenv("BROWSER_TIMEOUT", self.timeout))
        self.max_instances = int(os.getenv("BROWSER_MAX_INSTANCES", self.max_instances))
        
        if os.getenv("BROWSER_USER_AGENT"):
            self.user_agent = os.getenv("BROWSER_USER_AGENT")


@dataclass
class SchedulerConfig:
    """调度器配置"""
    timezone: str = "Asia/Shanghai"
    max_workers: int = 4
    job_defaults: Dict[str, Any] = field(default_factory=lambda: {
        "coalesce": False,
        "max_instances": 1,
        "misfire_grace_time": 30
    })
    executors: Dict[str, Any] = field(default_factory=lambda: {
        "default": {
            "type": "threadpool",
            "max_workers": 4
        }
    })
    
    def __post_init__(self):
        """配置后处理"""
        self.timezone = os.getenv("SCHEDULER_TIMEZONE", self.timezone)
        self.max_workers = int(os.getenv("SCHEDULER_MAX_WORKERS", self.max_workers))


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    rotation: str = "10 MB"
    retention: str = "7 days"
    compression: str = "zip"
    
    def __post_init__(self):
        """配置后处理"""
        self.level = os.getenv("LOG_LEVEL", self.level).upper()
        self.rotation = os.getenv("LOG_ROTATION", self.rotation)
        self.retention = os.getenv("LOG_RETENTION", self.retention)


@dataclass
class PathConfig:
    """路径配置"""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    cache_dir: Path = field(init=False)
    extensions_dir: Path = field(init=False)
    templates_dir: Path = field(init=False)
    static_dir: Path = field(init=False)
    
    def __post_init__(self):
        """初始化路径配置"""
        # 支持环境变量覆盖项目根目录
        if os.getenv("PROJECT_ROOT"):
            self.project_root = Path(os.getenv("PROJECT_ROOT"))
        
        # 设置各种目录路径
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        self.cache_dir = self.project_root / "cache"
        self.extensions_dir = self.project_root / "extensions"
        self.templates_dir = self.project_root / "templates"
        self.static_dir = self.project_root / "frontend" / "src"
        
        # 支持环境变量覆盖特定目录
        if os.getenv("DATA_DIR"):
            self.data_dir = Path(os.getenv("DATA_DIR"))
        if os.getenv("LOGS_DIR"):
            self.logs_dir = Path(os.getenv("LOGS_DIR"))
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_dir,
            self.logs_dir,
            self.cache_dir
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"无法创建目录 {directory}: {e}")


@dataclass
class SecurityConfig:
    """安全配置"""
    api_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    jwt_expire_hours: int = 24
    rate_limit_per_minute: int = 60
    allowed_hosts: List[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])
    
    def __post_init__(self):
        """配置后处理"""
        self.api_key = os.getenv("API_KEY")
        self.jwt_secret = os.getenv("JWT_SECRET")
        self.jwt_expire_hours = int(os.getenv("JWT_EXPIRE_HOURS", self.jwt_expire_hours))
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", self.rate_limit_per_minute))
        
        allowed_hosts_env = os.getenv("ALLOWED_HOSTS")
        if allowed_hosts_env:
            self.allowed_hosts = allowed_hosts_env.split(",")


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///data/app.db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    
    def __post_init__(self):
        """配置后处理"""
        self.url = os.getenv("DATABASE_URL", self.url)
        self.pool_size = int(os.getenv("DB_POOL_SIZE", self.pool_size))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", self.max_overflow))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", self.pool_timeout))


class AppSettings:
    """应用设置管理器"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """初始化应用设置
        
        Args:
            config_file: 可选的配置文件路径
        """
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 初始化各个配置模块
        self.network = NetworkConfig()
        self.browser = BrowserConfig()
        self.scheduler = SchedulerConfig()
        self.logging = LoggingConfig()
        self.paths = PathConfig()
        self.security = SecurityConfig()
        self.database = DatabaseConfig()
        
        # 如果指定了配置文件，从文件加载配置
        if self.config_file and self.config_file.exists():
            self._load_from_file()
        
        # 设置环境标识
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.testing = os.getenv("TESTING", "false").lower() == "true"
    
    def _load_from_file(self):
        """从配置文件加载设置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新各个配置模块
            if "network" in config_data:
                self._update_config(self.network, config_data["network"])
            if "browser" in config_data:
                self._update_config(self.browser, config_data["browser"])
            if "scheduler" in config_data:
                self._update_config(self.scheduler, config_data["scheduler"])
            if "logging" in config_data:
                self._update_config(self.logging, config_data["logging"])
            if "security" in config_data:
                self._update_config(self.security, config_data["security"])
            if "database" in config_data:
                self._update_config(self.database, config_data["database"])
                
            logger.info(f"已从配置文件加载设置: {self.config_file}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    
    def _update_config(self, config_obj, config_data: Dict[str, Any]):
        """更新配置对象"""
        for key, value in config_data.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
    
    def save_to_file(self, file_path: Optional[Path] = None):
        """保存配置到文件
        
        Args:
            file_path: 保存路径，默认使用初始化时的配置文件路径
        """
        save_path = file_path or self.config_file
        if not save_path:
            raise ValueError("未指定配置文件路径")
        
        config_data = {
            "network": self._config_to_dict(self.network),
            "browser": self._config_to_dict(self.browser),
            "scheduler": self._config_to_dict(self.scheduler),
            "logging": self._config_to_dict(self.logging),
            "security": self._config_to_dict(self.security),
            "database": self._config_to_dict(self.database)
        }
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {save_path}")
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise
    
    def _config_to_dict(self, config_obj) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        result = {}
        for key, value in config_obj.__dict__.items():
            if isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
        return result
    
    def validate(self) -> List[str]:
        """验证配置
        
        Returns:
            验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证端口范围
        if not (1024 <= self.network.api_port <= 65535):
            errors.append(f"API 端口超出有效范围: {self.network.api_port}")
        
        if not (1024 <= self.network.scheduler_port <= 65535):
            errors.append(f"调度器端口超出有效范围: {self.network.scheduler_port}")
        
        if not (1024 <= self.network.browser_start_port <= 65535):
            errors.append(f"浏览器起始端口超出有效范围: {self.network.browser_start_port}")
        
        # 验证浏览器配置
        if self.browser.max_instances <= 0:
            errors.append("浏览器最大实例数必须大于 0")
        
        if self.browser.timeout <= 0:
            errors.append("浏览器超时时间必须大于 0")
        
        # 验证调度器配置
        if self.scheduler.max_workers <= 0:
            errors.append("调度器最大工作线程数必须大于 0")
        
        # 验证路径
        if not self.paths.project_root.exists():
            errors.append(f"项目根目录不存在: {self.paths.project_root}")
        
        return errors
    
    def get_api_url(self) -> str:
        """获取 API 服务 URL"""
        return f"http://{self.network.host}:{self.network.api_port}"
    
    def get_scheduler_url(self) -> str:
        """获取调度器服务 URL"""
        return f"http://{self.network.host}:{self.network.scheduler_port}"
    
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.environment.lower() == "development"
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"AppSettings(environment={self.environment}, debug={self.debug})"


# 全局设置实例
settings = AppSettings()


def get_settings() -> AppSettings:
    """获取应用设置实例"""
    return settings


def reload_settings(config_file: Optional[Path] = None) -> AppSettings:
    """重新加载设置
    
    Args:
        config_file: 可选的配置文件路径
    
    Returns:
        新的设置实例
    """
    global settings
    settings = AppSettings(config_file)
    return settings