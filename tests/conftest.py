"""测试配置和夹具

提供测试所需的通用配置、夹具和工具函数。
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import asyncio
from typing import Generator, Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录用于测试"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_browser_config(temp_dir: Path) -> Dict[str, Any]:
    """模拟浏览器配置"""
    return {
        "user_id": "test_user_123",
        "data_dir": str(temp_dir / "browser_data"),
        "extensions_dir": str(temp_dir / "extensions"),
        "port": 9999,
        "headless": True
    }


@pytest.fixture
def mock_scheduler_config() -> Dict[str, Any]:
    """模拟调度器配置"""
    return {
        "host": "127.0.0.1",
        "port": 8001,
        "max_workers": 2,
        "timezone": "Asia/Shanghai"
    }


@pytest.fixture
def mock_api_config() -> Dict[str, Any]:
    """模拟 API 配置"""
    return {
        "host": "127.0.0.1",
        "port": 6002,
        "debug": True,
        "cors_origins": ["*"]
    }


@pytest.fixture
def mock_logger():
    """模拟日志记录器"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_browser_instance():
    """模拟浏览器实例"""
    browser = Mock()
    browser.is_running = Mock(return_value=True)
    browser.start = Mock(return_value=True)
    browser.stop = Mock(return_value=True)
    browser.get_port = Mock(return_value=9999)
    browser.get_user_id = Mock(return_value="test_user_123")
    return browser


@pytest.fixture
def mock_scheduler_client():
    """模拟调度器客户端"""
    client = Mock()
    client.start = Mock()
    client.stop = Mock()
    client.add_task = Mock(return_value="task_123")
    client.remove_task = Mock(return_value=True)
    client.get_tasks = Mock(return_value=[])
    return client


@pytest.fixture
def sample_task_config() -> Dict[str, Any]:
    """示例任务配置"""
    return {
        "task_id": "test_task_123",
        "name": "测试任务",
        "trigger_type": "cron",
        "cron_expression": "0 */1 * * *",
        "enabled": True,
        "max_instances": 1
    }


@pytest.fixture
def sample_user_ids() -> list[str]:
    """示例用户ID列表"""
    return ["user_001", "user_002", "user_003"]


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """设置测试环境变量"""
    # 设置测试模式
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    # 禁用实际的浏览器启动
    monkeypatch.setenv("DISABLE_BROWSER_LAUNCH", "true")
    
    # 使用测试数据库
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def mock_file_operations():
    """模拟文件操作"""
    with patch('builtins.open'), \
         patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('shutil.rmtree'):
        yield


class AsyncMock:
    """异步模拟类"""
    
    def __init__(self, return_value=None, side_effect=None):
        self.return_value = return_value
        self.side_effect = side_effect
        self.call_count = 0
        self.call_args_list = []
    
    async def __call__(self, *args, **kwargs):
        self.call_count += 1
        self.call_args_list.append((args, kwargs))
        
        if self.side_effect:
            if isinstance(self.side_effect, Exception):
                raise self.side_effect
            return self.side_effect(*args, **kwargs)
        
        return self.return_value


@pytest.fixture
def async_mock():
    """异步模拟夹具"""
    return AsyncMock


# 测试数据
TEST_USER_IDS = [
    "1234567890123456",
    "2345678901234567",
    "3456789012345678"
]

TEST_BROWSER_CONFIGS = [
    {
        "user_id": "1234567890123456",
        "port": 9111,
        "headless": False
    },
    {
        "user_id": "2345678901234567", 
        "port": 9112,
        "headless": True
    }
]

TEST_TASK_CONFIGS = [
    {
        "task_id": "daily_task",
        "name": "每日任务",
        "trigger_type": "cron",
        "cron_expression": "0 9 * * *"
    },
    {
        "task_id": "hourly_task",
        "name": "每小时任务",
        "trigger_type": "interval",
        "interval_seconds": 3600
    }
]