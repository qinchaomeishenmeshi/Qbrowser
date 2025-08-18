"""调度器客户端单元测试

测试 SchedulerClient 类的核心功能，包括任务管理、触发器创建等。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import json
import asyncio
from datetime import datetime, timedelta

from worker.scheduler_client import SchedulerClient, TaskConfig, TaskResult
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class TestTaskConfig:
    """任务配置测试类"""
    
    def test_task_config_creation(self):
        """测试任务配置创建"""
        config = TaskConfig(
            task_id="test_task",
            name="测试任务",
            trigger_type="cron",
            cron_expression="0 9 * * *",
            enabled=True
        )
        
        assert config.task_id == "test_task"
        assert config.name == "测试任务"
        assert config.trigger_type == "cron"
        assert config.cron_expression == "0 9 * * *"
        assert config.enabled is True
    
    def test_task_config_to_dict(self):
        """测试任务配置转换为字典"""
        config = TaskConfig(
            task_id="test_task",
            name="测试任务",
            trigger_type="interval",
            interval_seconds=3600
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['task_id'] == "test_task"
        assert config_dict['name'] == "测试任务"
        assert config_dict['trigger_type'] == "interval"
        assert config_dict['interval_seconds'] == 3600
    
    def test_task_config_from_dict(self):
        """测试从字典创建任务配置"""
        data = {
            "task_id": "test_task",
            "name": "测试任务",
            "trigger_type": "cron",
            "cron_expression": "0 */2 * * *",
            "enabled": False
        }
        
        config = TaskConfig.from_dict(data)
        
        assert config.task_id == "test_task"
        assert config.name == "测试任务"
        assert config.trigger_type == "cron"
        assert config.cron_expression == "0 */2 * * *"
        assert config.enabled is False


class TestTaskResult:
    """任务结果测试类"""
    
    def test_task_result_creation(self):
        """测试任务结果创建"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=10)
        
        result = TaskResult(
            task_id="test_task",
            execution_id="exec_123",
            start_time=start_time,
            end_time=end_time,
            status="success",
            result_data={"processed": 100}
        )
        
        assert result.task_id == "test_task"
        assert result.execution_id == "exec_123"
        assert result.status == "success"
        assert result.result_data["processed"] == 100
        assert result.duration == 10.0
    
    def test_task_result_to_dict(self):
        """测试任务结果转换为字典"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=5)
        
        result = TaskResult(
            task_id="test_task",
            execution_id="exec_123",
            start_time=start_time,
            end_time=end_time,
            status="failed",
            error_message="执行失败"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['task_id'] == "test_task"
        assert result_dict['status'] == "failed"
        assert result_dict['error_message'] == "执行失败"
        assert result_dict['duration'] == 5.0


class TestSchedulerClient:
    """调度器客户端测试类"""
    
    @pytest.fixture
    def mock_scheduler(self):
        """模拟调度器"""
        scheduler = Mock(spec=AsyncIOScheduler)
        scheduler.start = AsyncMock()
        scheduler.shutdown = AsyncMock()
        scheduler.add_job = Mock()
        scheduler.remove_job = Mock()
        scheduler.get_jobs = Mock(return_value=[])
        scheduler.get_job = Mock(return_value=None)
        scheduler.modify_job = Mock()
        scheduler.pause_job = Mock()
        scheduler.resume_job = Mock()
        return scheduler
    
    @pytest.fixture
    def scheduler_client(self, mock_scheduler, temp_dir):
        """创建调度器客户端实例"""
        with patch('worker.scheduler_client.AsyncIOScheduler', return_value=mock_scheduler):
            client = SchedulerClient(data_dir=str(temp_dir))
            client.scheduler = mock_scheduler
            return client
    
    def test_init(self, scheduler_client, temp_dir):
        """测试初始化"""
        assert scheduler_client.data_dir == str(temp_dir)
        assert scheduler_client.scheduler is not None
        assert isinstance(scheduler_client.tasks, dict)
        assert isinstance(scheduler_client.task_results, list)
    
    @pytest.mark.asyncio
    async def test_start_scheduler(self, scheduler_client, mock_scheduler):
        """测试启动调度器"""
        await scheduler_client.start()
        
        mock_scheduler.start.assert_called_once()
        assert scheduler_client.running is True
    
    @pytest.mark.asyncio
    async def test_stop_scheduler(self, scheduler_client, mock_scheduler):
        """测试停止调度器"""
        scheduler_client.running = True
        
        await scheduler_client.stop()
        
        mock_scheduler.shutdown.assert_called_once_with(wait=True)
        assert scheduler_client.running is False
    
    def test_add_cron_task(self, scheduler_client, mock_scheduler):
        """测试添加 cron 任务"""
        task_config = TaskConfig(
            task_id="cron_task",
            name="定时任务",
            trigger_type="cron",
            cron_expression="0 9 * * *",
            enabled=True
        )
        
        task_id = scheduler_client.add_task(task_config)
        
        assert task_id == "cron_task"
        assert "cron_task" in scheduler_client.tasks
        mock_scheduler.add_job.assert_called_once()
    
    def test_add_interval_task(self, scheduler_client, mock_scheduler):
        """测试添加间隔任务"""
        task_config = TaskConfig(
            task_id="interval_task",
            name="间隔任务",
            trigger_type="interval",
            interval_seconds=3600,
            enabled=True
        )
        
        task_id = scheduler_client.add_task(task_config)
        
        assert task_id == "interval_task"
        assert "interval_task" in scheduler_client.tasks
        mock_scheduler.add_job.assert_called_once()
    
    def test_add_task_invalid_trigger(self, scheduler_client):
        """测试添加无效触发器类型的任务"""
        task_config = TaskConfig(
            task_id="invalid_task",
            name="无效任务",
            trigger_type="invalid",
            enabled=True
        )
        
        with pytest.raises(ValueError, match="不支持的触发器类型"):
            scheduler_client.add_task(task_config)
    
    def test_remove_task(self, scheduler_client, mock_scheduler):
        """测试移除任务"""
        # 先添加任务
        task_config = TaskConfig(
            task_id="test_task",
            name="测试任务",
            trigger_type="cron",
            cron_expression="0 9 * * *"
        )
        scheduler_client.add_task(task_config)
        
        # 移除任务
        result = scheduler_client.remove_task("test_task")
        
        assert result is True
        assert "test_task" not in scheduler_client.tasks
        mock_scheduler.remove_job.assert_called_with("test_task")
    
    def test_remove_nonexistent_task(self, scheduler_client):
        """测试移除不存在的任务"""
        result = scheduler_client.remove_task("nonexistent_task")
        
        assert result is False
    
    def test_get_task(self, scheduler_client):
        """测试获取任务"""
        task_config = TaskConfig(
            task_id="test_task",
            name="测试任务",
            trigger_type="cron",
            cron_expression="0 9 * * *"
        )
        scheduler_client.add_task(task_config)
        
        retrieved_task = scheduler_client.get_task("test_task")
        
        assert retrieved_task is not None
        assert retrieved_task.task_id == "test_task"
        assert retrieved_task.name == "测试任务"
    
    def test_get_nonexistent_task(self, scheduler_client):
        """测试获取不存在的任务"""
        task = scheduler_client.get_task("nonexistent_task")
        
        assert task is None
    
    def test_get_all_tasks(self, scheduler_client):
        """测试获取所有任务"""
        # 添加多个任务
        task1 = TaskConfig(task_id="task1", name="任务1", trigger_type="cron", cron_expression="0 9 * * *")
        task2 = TaskConfig(task_id="task2", name="任务2", trigger_type="interval", interval_seconds=3600)
        
        scheduler_client.add_task(task1)
        scheduler_client.add_task(task2)
        
        all_tasks = scheduler_client.get_all_tasks()
        
        assert len(all_tasks) == 2
        task_ids = [task.task_id for task in all_tasks]
        assert "task1" in task_ids
        assert "task2" in task_ids
    
    def test_update_task(self, scheduler_client, mock_scheduler):
        """测试更新任务"""
        # 先添加任务
        original_config = TaskConfig(
            task_id="test_task",
            name="原始任务",
            trigger_type="cron",
            cron_expression="0 9 * * *"
        )
        scheduler_client.add_task(original_config)
        
        # 更新任务
        updated_config = TaskConfig(
            task_id="test_task",
            name="更新任务",
            trigger_type="cron",
            cron_expression="0 10 * * *"
        )
        
        result = scheduler_client.update_task("test_task", updated_config)
        
        assert result is True
        updated_task = scheduler_client.get_task("test_task")
        assert updated_task.name == "更新任务"
        assert updated_task.cron_expression == "0 10 * * *"
    
    def test_pause_task(self, scheduler_client, mock_scheduler):
        """测试暂停任务"""
        # 先添加任务
        task_config = TaskConfig(
            task_id="test_task",
            name="测试任务",
            trigger_type="cron",
            cron_expression="0 9 * * *"
        )
        scheduler_client.add_task(task_config)
        
        result = scheduler_client.pause_task("test_task")
        
        assert result is True
        mock_scheduler.pause_job.assert_called_with("test_task")
    
    def test_resume_task(self, scheduler_client, mock_scheduler):
        """测试恢复任务"""
        # 先添加任务
        task_config = TaskConfig(
            task_id="test_task",
            name="测试任务",
            trigger_type="cron",
            cron_expression="0 9 * * *"
        )
        scheduler_client.add_task(task_config)
        
        result = scheduler_client.resume_task("test_task")
        
        assert result is True
        mock_scheduler.resume_job.assert_called_with("test_task")
    
    def test_create_cron_trigger(self, scheduler_client):
        """测试创建 cron 触发器"""
        trigger = scheduler_client._create_cron_trigger("0 9 * * *")
        
        assert isinstance(trigger, CronTrigger)
    
    def test_create_interval_trigger(self, scheduler_client):
        """测试创建间隔触发器"""
        trigger = scheduler_client._create_interval_trigger(3600)
        
        assert isinstance(trigger, IntervalTrigger)
    
    def test_save_tasks(self, scheduler_client, temp_dir):
        """测试保存任务配置"""
        # 添加任务
        task_config = TaskConfig(
            task_id="test_task",
            name="测试任务",
            trigger_type="cron",
            cron_expression="0 9 * * *"
        )
        scheduler_client.add_task(task_config)
        
        scheduler_client.save_tasks()
        
        # 验证文件存在
        tasks_file = Path(temp_dir) / "tasks.json"
        assert tasks_file.exists()
        
        # 验证文件内容
        with open(tasks_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert "test_task" in saved_data
        assert saved_data["test_task"]["name"] == "测试任务"
    
    def test_load_tasks(self, scheduler_client, temp_dir):
        """测试加载任务配置"""
        # 创建测试数据文件
        tasks_data = {
            "test_task": {
                "task_id": "test_task",
                "name": "测试任务",
                "trigger_type": "cron",
                "cron_expression": "0 9 * * *",
                "enabled": True
            }
        }
        
        tasks_file = Path(temp_dir) / "tasks.json"
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f)
        
        scheduler_client.load_tasks()
        
        assert "test_task" in scheduler_client.tasks
        loaded_task = scheduler_client.get_task("test_task")
        assert loaded_task.name == "测试任务"
    
    @pytest.mark.asyncio
    async def test_execute_task(self, scheduler_client, async_mock):
        """测试执行任务"""
        # 模拟任务函数
        mock_task_func = async_mock(return_value={"status": "success"})
        
        task_config = TaskConfig(
            task_id="test_task",
            name="测试任务",
            trigger_type="cron",
            cron_expression="0 9 * * *"
        )
        
        result = await scheduler_client._execute_task(task_config, mock_task_func)
        
        assert result.task_id == "test_task"
        assert result.status == "success"
        assert mock_task_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_task_with_error(self, scheduler_client, async_mock):
        """测试执行任务时出现错误"""
        # 模拟任务函数抛出异常
        mock_task_func = async_mock(side_effect=Exception("任务执行失败"))
        
        task_config = TaskConfig(
            task_id="test_task",
            name="测试任务",
            trigger_type="cron",
            cron_expression="0 9 * * *"
        )
        
        result = await scheduler_client._execute_task(task_config, mock_task_func)
        
        assert result.task_id == "test_task"
        assert result.status == "failed"
        assert "任务执行失败" in result.error_message
    
    def test_get_task_results(self, scheduler_client):
        """测试获取任务结果"""
        # 添加一些测试结果
        result1 = TaskResult(
            task_id="task1",
            execution_id="exec1",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="success"
        )
        result2 = TaskResult(
            task_id="task2",
            execution_id="exec2",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="failed"
        )
        
        scheduler_client.task_results = [result1, result2]
        
        # 获取所有结果
        all_results = scheduler_client.get_task_results()
        assert len(all_results) == 2
        
        # 获取特定任务的结果
        task1_results = scheduler_client.get_task_results(task_id="task1")
        assert len(task1_results) == 1
        assert task1_results[0].task_id == "task1"
        
        # 获取限定数量的结果
        limited_results = scheduler_client.get_task_results(limit=1)
        assert len(limited_results) == 1