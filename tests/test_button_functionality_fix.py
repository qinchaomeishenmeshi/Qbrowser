"""
测试按钮功能修复
验证ModernApp中的start_browsers和stop_browsers方法已经从占位符实现恢复为正常功能
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
import sys

@pytest.fixture
def qapp():
    """创建QApplication实例"""
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield app

@pytest.fixture  
def modern_app_mock(qapp):
    """创建ModernApp的模拟实例"""
    with patch('ui.modern_app.browser_service') as mock_service, \
         patch('ui.modern_app.scheduler_client') as mock_scheduler:
        
        from ui.modern_app import ModernApp
        
        # 模拟必要的服务
        mock_service.save_cache = MagicMock()
        mock_service.start_browsers = AsyncMock(return_value=[
            {'user_id': 'test001', 'status': 'started', 'port': 9000},
            {'user_id': 'test002', 'status': 'started', 'port': 9001}
        ])
        mock_service.stop_all_browsers = AsyncMock()
        mock_scheduler.update_all_task_configs = AsyncMock()
        
        # 创建应用实例
        app = ModernApp()
        
        # 模拟UI组件
        app.text_edit = MagicMock()
        app.text_edit.toPlainText.return_value = "test001\ntest002"
        app.start_btn = MagicMock()
        app.stop_btn = MagicMock()
        app.progress = MagicMock()
        app.log_signal = MagicMock()
        
        yield app

class TestButtonFunctionalityFix:
    """测试按钮功能修复"""
    
    @pytest.mark.asyncio
    async def test_start_browsers_implementation(self, modern_app_mock):
        """测试启动浏览器功能已正确实现"""
        app = modern_app_mock
        
        # 执行启动浏览器方法
        await app.start_browsers()
        
        # 验证方法调用
        app.browser_service.save_cache.assert_called_once()
        app.browser_service.start_browsers.assert_called_once_with(['test001', 'test002'])
        app.scheduler_client.update_all_task_configs.assert_called_once()
        
        # 验证UI状态更新
        app.start_btn.setEnabled.assert_called()
        app.stop_btn.setEnabled.assert_called()
        app.progress.setMaximum.assert_called_with(2)
        app.progress.setValue.assert_called()
        
        # 验证日志更新
        assert app.log_signal.log_updated.emit.call_count > 0
        
        # 确保不是占位符实现
        log_calls = [call[0][0] for call in app.log_signal.log_updated.emit.call_args_list]
        assert "启动浏览器功能待实现" not in log_calls
        assert any("启动浏览器操作已完成" in msg for msg in log_calls)
    
    @pytest.mark.asyncio 
    async def test_stop_browsers_implementation(self, modern_app_mock):
        """测试停止浏览器功能已正确实现"""
        app = modern_app_mock
        
        # 执行停止浏览器方法
        await app.stop_browsers()
        
        # 验证方法调用
        app.browser_service.stop_all_browsers.assert_called_once()
        
        # 验证UI状态更新
        app.start_btn.setEnabled.assert_called()
        app.stop_btn.setEnabled.assert_called()
        app.progress.setValue.assert_called_with(0)
        
        # 验证日志更新
        assert app.log_signal.log_updated.emit.call_count > 0
        
        # 确保不是占位符实现
        log_calls = [call[0][0] for call in app.log_signal.log_updated.emit.call_args_list]
        assert "停止浏览器功能待实现" not in log_calls
        assert any("正在关闭所有浏览器" in msg for msg in log_calls)
        assert any("所有浏览器已关闭" in msg for msg in log_calls)
    
    def test_no_placeholder_messages(self, modern_app_mock):
        """测试确保不再有占位符消息"""
        app = modern_app_mock
        
        # 检查start_browsers方法源码
        import inspect
        start_source = inspect.getsource(app.start_browsers)
        assert "启动浏览器功能待实现" not in start_source
        
        # 检查stop_browsers方法源码
        stop_source = inspect.getsource(app.stop_browsers)
        assert "停止浏览器功能待实现" not in stop_source
        
        # 确保包含实际业务逻辑
        assert "browser_service.start_browsers" in start_source
        assert "browser_service.stop_all_browsers" in stop_source
    
    @pytest.mark.asyncio
    async def test_error_handling(self, modern_app_mock):
        """测试错误处理功能"""
        app = modern_app_mock
        
        # 模拟启动浏览器时出错
        app.browser_service.start_browsers.side_effect = Exception("测试错误")
        
        # 执行启动浏览器
        await app.start_browsers()
        
        # 验证错误处理
        log_calls = [call[0][0] for call in app.log_signal.log_updated.emit.call_args_list]
        assert any("启动浏览器时发生错误" in msg for msg in log_calls)
        
        # 验证UI状态恢复
        app.start_btn.setEnabled.assert_called_with(True)
        app.stop_btn.setEnabled.assert_called_with(True)

if __name__ == "__main__":
    pytest.main([__file__])