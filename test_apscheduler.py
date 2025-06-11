#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APScheduler 功能测试脚本
用于验证 APScheduler 调度器的基本功能
"""

import sys
import time
import threading
from datetime import datetime, timedelta
from typing import List

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
except ImportError as e:
    print(f"❌ APScheduler 导入失败: {e}")
    print("请运行: uv add apscheduler")
    sys.exit(1)


class APSchedulerTester:
    """
    APScheduler 测试类
    """
    
    def __init__(self):
        self.scheduler = None
        self.test_results = []
        self.job_executed_count = 0
        self.lock = threading.Lock()
    
    def job_listener(self, event):
        """
        任务执行监听器
        """
        with self.lock:
            if event.exception:
                self.test_results.append(f"❌ 任务执行失败: {event.exception}")
            else:
                self.job_executed_count += 1
                self.test_results.append(f"✅ 任务执行成功 (#{self.job_executed_count})")
    
    def test_job(self, job_name: str = "test"):
        """
        测试任务函数
        """
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"  📋 执行测试任务 '{job_name}' at {current_time}")
        return f"Task {job_name} completed at {current_time}"
    
    def test_scheduler_creation(self) -> bool:
        """
        测试调度器创建
        """
        try:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_listener(self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
            print("✅ 调度器创建成功")
            return True
        except Exception as e:
            print(f"❌ 调度器创建失败: {e}")
            return False
    
    def test_scheduler_start_stop(self) -> bool:
        """
        测试调度器启动和停止
        """
        try:
            self.scheduler.start()
            print("✅ 调度器启动成功")
            
            # 等待一小段时间确保启动完成
            time.sleep(0.1)
            
            if self.scheduler.running:
                print("✅ 调度器运行状态正常")
            else:
                print("❌ 调度器未正常运行")
                return False
            
            return True
        except Exception as e:
            print(f"❌ 调度器启动失败: {e}")
            return False
    
    def test_interval_job(self) -> bool:
        """
        测试间隔任务
        """
        try:
            # 添加每秒执行一次的任务
            job = self.scheduler.add_job(
                func=self.test_job,
                trigger=IntervalTrigger(seconds=1),
                args=["interval"],
                id="test_interval_job",
                max_instances=1
            )
            
            print("✅ 间隔任务添加成功")
            print(f"  📅 任务ID: {job.id}")
            print(f"  ⏰ 下次执行时间: {job.next_run_time}")
            
            # 等待任务执行几次
            time.sleep(2.5)
            
            # 移除任务
            self.scheduler.remove_job("test_interval_job")
            print("✅ 间隔任务移除成功")
            
            return True
        except Exception as e:
            print(f"❌ 间隔任务测试失败: {e}")
            return False
    
    def test_date_job(self) -> bool:
        """
        测试定时任务
        """
        try:
            # 添加1秒后执行的任务
            run_time = datetime.now() + timedelta(seconds=1)
            job = self.scheduler.add_job(
                func=self.test_job,
                trigger=DateTrigger(run_date=run_time),
                args=["date"],
                id="test_date_job"
            )
            
            print("✅ 定时任务添加成功")
            print(f"  📅 任务ID: {job.id}")
            print(f"  ⏰ 执行时间: {job.next_run_time}")
            
            # 等待任务执行
            time.sleep(1.5)
            
            return True
        except Exception as e:
            print(f"❌ 定时任务测试失败: {e}")
            return False
    
    def test_cron_job(self) -> bool:
        """
        测试 Cron 任务
        """
        try:
            # 添加每分钟执行的任务（仅用于验证语法）
            job = self.scheduler.add_job(
                func=self.test_job,
                trigger=CronTrigger(minute="*"),
                args=["cron"],
                id="test_cron_job"
            )
            
            print("✅ Cron 任务添加成功")
            print(f"  📅 任务ID: {job.id}")
            print(f"  ⏰ 下次执行时间: {job.next_run_time}")
            
            # 立即移除任务（不等待执行）
            self.scheduler.remove_job("test_cron_job")
            print("✅ Cron 任务移除成功")
            
            return True
        except Exception as e:
            print(f"❌ Cron 任务测试失败: {e}")
            return False
    
    def test_job_management(self) -> bool:
        """
        测试任务管理功能
        """
        try:
            # 添加测试任务
            self.scheduler.add_job(
                func=self.test_job,
                trigger=IntervalTrigger(seconds=10),
                args=["management"],
                id="test_management_job"
            )
            
            # 获取所有任务
            jobs = self.scheduler.get_jobs()
            print(f"✅ 当前任务数量: {len(jobs)}")
            
            # 获取特定任务
            job = self.scheduler.get_job("test_management_job")
            if job:
                print(f"✅ 任务查询成功: {job.id}")
            else:
                print("❌ 任务查询失败")
                return False
            
            # 暂停任务
            self.scheduler.pause_job("test_management_job")
            print("✅ 任务暂停成功")
            
            # 恢复任务
            self.scheduler.resume_job("test_management_job")
            print("✅ 任务恢复成功")
            
            # 移除任务
            self.scheduler.remove_job("test_management_job")
            print("✅ 任务移除成功")
            
            return True
        except Exception as e:
            print(f"❌ 任务管理测试失败: {e}")
            return False
    
    def cleanup(self):
        """
        清理资源
        """
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                print("✅ 调度器关闭成功")
        except Exception as e:
            print(f"⚠️  调度器关闭时出现警告: {e}")
    
    def run_all_tests(self) -> bool:
        """
        运行所有测试
        """
        print("🔍 开始 APScheduler 功能测试...\n")
        
        tests = [
            ("调度器创建", self.test_scheduler_creation),
            ("调度器启动停止", self.test_scheduler_start_stop),
            ("间隔任务", self.test_interval_job),
            ("定时任务", self.test_date_job),
            ("Cron 任务", self.test_cron_job),
            ("任务管理", self.test_job_management),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 测试: {test_name}")
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} 测试通过")
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
        
        # 显示任务执行结果
        if self.test_results:
            print("\n📊 任务执行记录:")
            for result in self.test_results[-5:]:  # 显示最后5条记录
                print(f"  {result}")
        
        print(f"\n📊 测试结果汇总: {passed}/{total} 通过")
        print(f"📊 任务执行次数: {self.job_executed_count}")
        
        return passed == total


def main():
    """
    主测试函数
    """
    tester = APSchedulerTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 APScheduler 测试全部通过!")
            return 0
        else:
            print("\n❌ APScheduler 测试存在失败项")
            return 1
    
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return 1
    
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        return 1
    
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())