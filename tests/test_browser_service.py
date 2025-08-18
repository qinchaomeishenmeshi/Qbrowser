"""浏览器服务单元测试

测试 BrowserService 类的核心功能，包括浏览器实例管理、端口分配等。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import asyncio

from service.browser_service import BrowserService
from browser.browser_manager import BrowserManager
from utils.port_manager import PortManager
from utils.cookies_manager import CookiesManager


class TestBrowserService:
    """浏览器服务测试类"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """模拟依赖项"""
        with patch('service.browser_service.BrowserManager') as mock_browser_manager, \
             patch('service.browser_service.PortManager') as mock_port_manager, \
             patch('service.browser_service.CookiesManager') as mock_cookies_manager, \
             patch('service.browser_service.browser_store') as mock_browser_store:
            
            # 配置模拟对象
            mock_browser_manager.return_value = Mock()
            mock_port_manager.return_value = Mock()
            mock_cookies_manager.return_value = Mock()
            mock_browser_store.get_all_browsers.return_value = {}
            
            yield {
                'browser_manager': mock_browser_manager.return_value,
                'port_manager': mock_port_manager.return_value,
                'cookies_manager': mock_cookies_manager.return_value,
                'browser_store': mock_browser_store
            }
    
    @pytest.fixture
    def browser_service(self, mock_dependencies):
        """创建浏览器服务实例"""
        return BrowserService()
    
    def test_init(self, browser_service, mock_dependencies):
        """测试初始化"""
        assert browser_service.browser_manager is not None
        assert browser_service.port_manager is not None
        assert browser_service.cookies_manager is not None
        assert isinstance(browser_service.user_ports, dict)
    
    @pytest.mark.asyncio
    async def test_start_browsers_success(self, browser_service, mock_dependencies, sample_user_ids):
        """测试成功启动浏览器"""
        # 配置模拟返回值
        mock_dependencies['browser_manager'].create_browser.return_value = Mock()
        mock_dependencies['port_manager'].get_available_port.return_value = 9999
        
        # 模拟浏览器启动成功
        mock_browser = Mock()
        mock_browser.start.return_value = True
        mock_browser.is_running.return_value = True
        mock_dependencies['browser_manager'].create_browser.return_value = mock_browser
        
        result = await browser_service.start_browsers(sample_user_ids[:2])
        
        assert len(result['started']) == 2
        assert len(result['already_running']) == 0
        assert len(result['failed']) == 0
    
    @pytest.mark.asyncio
    async def test_start_browsers_already_running(self, browser_service, mock_dependencies, sample_user_ids):
        """测试启动已运行的浏览器"""
        # 模拟浏览器已在运行
        mock_dependencies['browser_store'].get_all_browsers.return_value = {
            sample_user_ids[0]: Mock(is_running=Mock(return_value=True))
        }
        
        result = await browser_service.start_browsers([sample_user_ids[0]])
        
        assert len(result['started']) == 0
        assert len(result['already_running']) == 1
        assert len(result['failed']) == 0
    
    @pytest.mark.asyncio
    async def test_start_browsers_failure(self, browser_service, mock_dependencies, sample_user_ids):
        """测试浏览器启动失败"""
        # 配置模拟启动失败
        mock_browser = Mock()
        mock_browser.start.side_effect = Exception("启动失败")
        mock_dependencies['browser_manager'].create_browser.return_value = mock_browser
        mock_dependencies['port_manager'].get_available_port.return_value = 9999
        
        result = await browser_service.start_browsers([sample_user_ids[0]])
        
        assert len(result['started']) == 0
        assert len(result['already_running']) == 0
        assert len(result['failed']) == 1
    
    def test_save_ports(self, browser_service, temp_dir):
        """测试保存端口映射"""
        # 设置测试数据
        browser_service.user_ports = {
            "user1": 9111,
            "user2": 9112
        }
        
        ports_file = temp_dir / "ports.json"
        
        with patch('service.browser_service.PORTS_FILE', str(ports_file)):
            browser_service.save_ports()
            
            # 验证文件内容
            assert ports_file.exists()
            with open(ports_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            assert saved_data == browser_service.user_ports
    
    def test_load_ports(self, browser_service, temp_dir):
        """测试加载端口映射"""
        # 创建测试数据文件
        test_ports = {"user1": 9111, "user2": 9112}
        ports_file = temp_dir / "ports.json"
        
        with open(ports_file, 'w', encoding='utf-8') as f:
            json.dump(test_ports, f)
        
        with patch('service.browser_service.PORTS_FILE', str(ports_file)):
            browser_service.load_ports()
            
            assert browser_service.user_ports == test_ports
    
    def test_load_ports_file_not_exists(self, browser_service, temp_dir):
        """测试加载不存在的端口文件"""
        non_existent_file = temp_dir / "non_existent_ports.json"
        
        with patch('service.browser_service.PORTS_FILE', str(non_existent_file)):
            browser_service.load_ports()
            
            # 应该初始化为空字典
            assert browser_service.user_ports == {}
    
    @pytest.mark.asyncio
    async def test_stop_all_browsers(self, browser_service, mock_dependencies):
        """测试停止所有浏览器"""
        # 模拟运行中的浏览器
        mock_browser1 = Mock()
        mock_browser1.stop.return_value = True
        mock_browser2 = Mock()
        mock_browser2.stop.return_value = True
        
        mock_dependencies['browser_store'].get_all_browsers.return_value = {
            "user1": mock_browser1,
            "user2": mock_browser2
        }
        
        result = await browser_service.stop_all_browsers()
        
        # 验证所有浏览器都被停止
        mock_browser1.stop.assert_called_once()
        mock_browser2.stop.assert_called_once()
        assert result['stopped'] == 2
        assert result['failed'] == 0
    
    @pytest.mark.asyncio
    async def test_stop_all_browsers_with_failure(self, browser_service, mock_dependencies):
        """测试停止浏览器时出现失败"""
        # 模拟一个浏览器停止失败
        mock_browser1 = Mock()
        mock_browser1.stop.side_effect = Exception("停止失败")
        mock_browser2 = Mock()
        mock_browser2.stop.return_value = True
        
        mock_dependencies['browser_store'].get_all_browsers.return_value = {
            "user1": mock_browser1,
            "user2": mock_browser2
        }
        
        result = await browser_service.stop_all_browsers()
        
        assert result['stopped'] == 1
        assert result['failed'] == 1
    
    def test_get_browser_status(self, browser_service, mock_dependencies):
        """测试获取浏览器状态"""
        # 模拟浏览器状态
        mock_browser = Mock()
        mock_browser.is_running.return_value = True
        mock_browser.get_port.return_value = 9111
        
        mock_dependencies['browser_store'].get_browser.return_value = mock_browser
        
        status = browser_service.get_browser_status("user1")
        
        assert status['running'] is True
        assert status['port'] == 9111
    
    def test_get_browser_status_not_found(self, browser_service, mock_dependencies):
        """测试获取不存在浏览器的状态"""
        mock_dependencies['browser_store'].get_browser.return_value = None
        
        status = browser_service.get_browser_status("non_existent_user")
        
        assert status['running'] is False
        assert status['port'] is None
    
    @pytest.mark.asyncio
    async def test_restart_browser(self, browser_service, mock_dependencies):
        """测试重启浏览器"""
        # 模拟现有浏览器
        mock_browser = Mock()
        mock_browser.stop.return_value = True
        mock_browser.start.return_value = True
        
        mock_dependencies['browser_store'].get_browser.return_value = mock_browser
        
        result = await browser_service.restart_browser("user1")
        
        assert result is True
        mock_browser.stop.assert_called_once()
        mock_browser.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restart_browser_not_found(self, browser_service, mock_dependencies):
        """测试重启不存在的浏览器"""
        mock_dependencies['browser_store'].get_browser.return_value = None
        
        result = await browser_service.restart_browser("non_existent_user")
        
        assert result is False
    
    def test_clear_cache(self, browser_service, mock_dependencies):
        """测试清理缓存"""
        mock_dependencies['cookies_manager'].clear_all_cookies.return_value = True
        
        with patch('service.browser_service.shutil.rmtree') as mock_rmtree:
            result = browser_service.clear_cache()
            
            assert result is True
            mock_dependencies['cookies_manager'].clear_all_cookies.assert_called_once()
    
    def test_get_all_browser_status(self, browser_service, mock_dependencies):
        """测试获取所有浏览器状态"""
        # 模拟多个浏览器
        mock_browser1 = Mock()
        mock_browser1.is_running.return_value = True
        mock_browser1.get_port.return_value = 9111
        
        mock_browser2 = Mock()
        mock_browser2.is_running.return_value = False
        mock_browser2.get_port.return_value = None
        
        mock_dependencies['browser_store'].get_all_browsers.return_value = {
            "user1": mock_browser1,
            "user2": mock_browser2
        }
        
        status_list = browser_service.get_all_browser_status()
        
        assert len(status_list) == 2
        assert status_list[0]['user_id'] == "user1"
        assert status_list[0]['running'] is True
        assert status_list[1]['user_id'] == "user2"
        assert status_list[1]['running'] is False