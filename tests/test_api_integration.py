"""API 服务集成测试

测试 FastAPI 应用的各个端点和业务逻辑集成。
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from pathlib import Path

# 导入 API 应用
from api.api_server import app
from service.browser_service import browser_service
from worker.scheduler_client import SchedulerClient


class TestAPIIntegration:
    """API 集成测试类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def mock_browser_service(self):
        """模拟浏览器服务"""
        with patch("api.api_server.browser_service") as mock_service:
            mock_service.start_browsers = AsyncMock(
                return_value={
                    "started": ["user1", "user2"],
                    "already_running": [],
                    "failed": [],
                }
            )
            mock_service.stop_all_browsers = AsyncMock(
                return_value={"stopped": 2, "failed": 0}
            )
            mock_service.get_browser_status = Mock(
                return_value={"running": True, "port": 9111, "user_id": "user1"}
            )
            mock_service.get_all_browser_status = Mock(
                return_value=[
                    {"user_id": "user1", "running": True, "port": 9111},
                    {"user_id": "user2", "running": False, "port": None},
                ]
            )
            yield mock_service

    @pytest.fixture
    def mock_scheduler_client(self):
        """模拟调度器客户端"""
        with patch("api.api_server.scheduler_client") as mock_client:
            mock_client.get_all_tasks = Mock(return_value=[])
            mock_client.add_task = Mock(return_value="task_123")
            mock_client.remove_task = Mock(return_value=True)
            mock_client.get_task = Mock(return_value=None)
            mock_client.pause_task = Mock(return_value=True)
            mock_client.resume_task = Mock(return_value=True)
            yield mock_client

    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_system_status(self, client, mock_browser_service, mock_scheduler_client):
        """测试系统状态端点"""
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "browser_service" in data
        assert "scheduler" in data
        assert "api_server" in data

    def test_browser_status(self, client, mock_browser_service):
        """测试浏览器状态端点"""
        response = client.get("/browser/status")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_browser_service.get_all_browser_status.assert_called_once()

    def test_start_browsers_success(
        self, client, mock_browser_service, sample_user_ids
    ):
        """测试成功启动浏览器"""
        request_data = {"user_ids": sample_user_ids[:2]}

        response = client.post("/browser/start", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "started" in data["data"]
        mock_browser_service.start_browsers.assert_called_once_with(sample_user_ids[:2])

    def test_start_browsers_invalid_data(self, client):
        """测试启动浏览器时传入无效数据"""
        request_data = {"invalid_field": ["user1"]}

        response = client.post("/browser/start", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_stop_all_browsers(self, client, mock_browser_service):
        """测试停止所有浏览器"""
        response = client.post("/browser/stop_all")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_browser_service.stop_all_browsers.assert_called_once()

    def test_get_browser_info(self, client, mock_browser_service):
        """测试获取单个浏览器信息"""
        user_id = "user1"

        response = client.get(f"/browser/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        mock_browser_service.get_browser_status.assert_called_once_with(user_id)

    def test_restart_browser(self, client, mock_browser_service):
        """测试重启浏览器"""
        user_id = "user1"
        mock_browser_service.restart_browser = AsyncMock(return_value=True)

        response = client.post(f"/browser/{user_id}/restart")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_browser_service.restart_browser.assert_called_once_with(user_id)

    def test_clear_cache(self, client, mock_browser_service):
        """测试清理缓存"""
        mock_browser_service.clear_cache = Mock(return_value=True)

        response = client.post("/browser/clear_cache")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_browser_service.clear_cache.assert_called_once()

    def test_get_extensions_status(self, client):
        """测试获取扩展状态"""
        with patch("api.api_server.get_extensions_status") as mock_get_status:
            mock_get_status.return_value = {
                "live_room": {"enabled": True, "version": "1.0.0"},
            }

            response = client.get("/extensions/status")

            assert response.status_code == 200
            data = response.json()
            assert "live_room" in data

    def test_get_user_extensions(self, client):
        """测试获取用户扩展"""
        user_id = "user1"

        with patch("api.api_server.get_user_extensions") as mock_get_extensions:
            mock_get_extensions.return_value = [
                {"name": "live_room", "enabled": True},
                {"name": "block_videos", "enabled": False},
            ]

            response = client.get(f"/extensions/{user_id}")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            mock_get_extensions.assert_called_once_with(user_id)

    def test_scheduler_tasks_list(self, client, mock_scheduler_client):
        """测试获取调度器任务列表"""
        response = client.get("/scheduler/tasks")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_scheduler_client.get_all_tasks.assert_called_once()

    def test_add_scheduler_task(
        self, client, mock_scheduler_client, sample_task_config
    ):
        """测试添加调度器任务"""
        response = client.post("/scheduler/tasks", json=sample_task_config)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data
        mock_scheduler_client.add_task.assert_called_once()

    def test_get_scheduler_task(self, client, mock_scheduler_client):
        """测试获取单个调度器任务"""
        task_id = "test_task_123"

        response = client.get(f"/scheduler/tasks/{task_id}")

        assert response.status_code == 200
        mock_scheduler_client.get_task.assert_called_once_with(task_id)

    def test_delete_scheduler_task(self, client, mock_scheduler_client):
        """测试删除调度器任务"""
        task_id = "test_task_123"

        response = client.delete(f"/scheduler/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_scheduler_client.remove_task.assert_called_once_with(task_id)

    def test_pause_scheduler_task(self, client, mock_scheduler_client):
        """测试暂停调度器任务"""
        task_id = "test_task_123"

        response = client.post(f"/scheduler/tasks/{task_id}/pause")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_scheduler_client.pause_task.assert_called_once_with(task_id)

    def test_resume_scheduler_task(self, client, mock_scheduler_client):
        """测试恢复调度器任务"""
        task_id = "test_task_123"

        response = client.post(f"/scheduler/tasks/{task_id}/resume")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_scheduler_client.resume_task.assert_called_once_with(task_id)

    def test_get_logs(self, client):
        """测试获取系统日志"""
        with patch("api.api_server.get_recent_logs") as mock_get_logs:
            mock_get_logs.return_value = [
                {
                    "timestamp": "2024-01-01 10:00:00",
                    "level": "INFO",
                    "message": "系统启动",
                },
                {
                    "timestamp": "2024-01-01 10:01:00",
                    "level": "ERROR",
                    "message": "连接失败",
                },
            ]

            response = client.get("/logs")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2

    def test_get_logs_with_params(self, client):
        """测试带参数获取系统日志"""
        with patch("api.api_server.get_recent_logs") as mock_get_logs:
            mock_get_logs.return_value = []

            response = client.get("/logs?level=ERROR&limit=50")

            assert response.status_code == 200
            mock_get_logs.assert_called_once_with(level="ERROR", limit=50)

    def test_ui_settings_get(self, client):
        """测试获取 UI 设置"""
        with patch("api.api_server.load_ui_settings") as mock_load_settings:
            mock_load_settings.return_value = {
                "theme": "dark",
                "language": "zh-CN",
                "auto_start": True,
            }

            response = client.get("/ui/settings")

            assert response.status_code == 200
            data = response.json()
            assert data["theme"] == "dark"
            assert data["language"] == "zh-CN"

    def test_ui_settings_update(self, client):
        """测试更新 UI 设置"""
        settings_data = {"theme": "light", "language": "en-US", "auto_start": False}

        with patch("api.api_server.save_ui_settings") as mock_save_settings:
            mock_save_settings.return_value = True

            response = client.post("/ui/settings", json=settings_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            mock_save_settings.assert_called_once_with(settings_data)

    def test_error_handling(self, client, mock_browser_service):
        """测试错误处理"""
        # 模拟服务异常
        mock_browser_service.start_browsers.side_effect = Exception("服务异常")

        request_data = {"user_ids": ["user1"]}
        response = client.post("/browser/start", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_cors_headers(self, client):
        """测试 CORS 头部"""
        response = client.options("/health")

        # 检查 CORS 相关头部
        assert "access-control-allow-origin" in response.headers

    def test_static_files(self, client):
        """测试静态文件服务"""
        # 测试静态文件路由是否正确配置
        # 注意：这里只测试路由配置，不测试实际文件内容
        response = client.get("/static/nonexistent.css")

        # 应该返回 404 而不是路由错误
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_websocket_connection(self, client):
        """测试 WebSocket 连接（如果有的话）"""
        # 如果 API 服务器支持 WebSocket，可以在这里测试
        # 目前跳过此测试
        pytest.skip("WebSocket 功能尚未实现")

    def test_batch_operations(self, client, mock_browser_service):
        """测试批量操作"""
        # 测试批量启动多个浏览器
        user_ids = ["user1", "user2", "user3", "user4", "user5"]
        request_data = {"user_ids": user_ids}

        response = client.post("/browser/start", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_browser_service.start_browsers.assert_called_once_with(user_ids)

    def test_input_validation(self, client):
        """测试输入验证"""
        # 测试无效的用户ID格式
        invalid_data = {"user_ids": [""]}  # 空字符串

        response = client.post("/browser/start", json=invalid_data)

        # 应该返回验证错误
        assert response.status_code in [400, 422]

    def test_rate_limiting(self, client):
        """测试速率限制（如果实现了的话）"""
        # 如果 API 实现了速率限制，可以在这里测试
        # 目前跳过此测试
        pytest.skip("速率限制功能尚未实现")
