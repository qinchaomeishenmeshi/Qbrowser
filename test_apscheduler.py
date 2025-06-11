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
    print(f"[ERROR] APScheduler import failed: {e}")
    print("Please run: uv add apscheduler")
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
                self.test_results.append(f"[FAIL] Job execution failed: {event.exception}")
            else:
                self.job_executed_count += 1
                self.test_results.append(f"[OK] Job executed successfully (#{self.job_executed_count})")
    
    def test_job(self, job_name: str = "test"):
        """
        测试任务函数
        """
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"  [EXEC] Running test job '{job_name}' at {current_time}")
        return f"Task {job_name} completed at {current_time}"
    
    def test_scheduler_creation(self) -> bool:
        """
        测试调度器创建
        """
        try:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_listener(self.job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
            print("[OK] Scheduler created successfully")
            return True
        except Exception as e:
            print(f"[FAIL] Scheduler creation failed: {e}")
            return False
    
    def test_scheduler_start_stop(self) -> bool:
        """
        测试调度器启动和停止
        """
        try:
            self.scheduler.start()
            print("[OK] Scheduler started successfully")
            
            # 等待一小段时间确保启动完成
            time.sleep(0.1)
            
            if self.scheduler.running:
                print("[OK] Scheduler running status normal")
            else:
                print("[FAIL] Scheduler not running properly")
                return False
            
            return True
        except Exception as e:
            print(f"[FAIL] Scheduler start failed: {e}")
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
            
            print("[OK] Interval job added successfully")
            print(f"  [INFO] Job ID: {job.id}")
            print(f"  [INFO] Next run time: {job.next_run_time}")
            
            # 等待任务执行几次
            time.sleep(2.5)
            
            # 移除任务
            self.scheduler.remove_job("test_interval_job")
            print("[OK] Interval job removed successfully")
            
            return True
        except Exception as e:
            print(f"[FAIL] Interval job test failed: {e}")
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
            
            print("[OK] Date job added successfully")
            print(f"  [INFO] Job ID: {job.id}")
            print(f"  [INFO] Run time: {job.next_run_time}")
            
            # 等待任务执行
            time.sleep(1.5)
            
            return True
        except Exception as e:
            print(f"[FAIL] Date job test failed: {e}")
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
            
            print("[OK] Cron job added successfully")
            print(f"  [INFO] Job ID: {job.id}")
            print(f"  [INFO] Next run time: {job.next_run_time}")
            
            # 立即移除任务（不等待执行）
            self.scheduler.remove_job("test_cron_job")
            print("[OK] Cron job removed successfully")
            
            return True
        except Exception as e:
            print(f"[FAIL] Cron job test failed: {e}")
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
            print(f"[OK] Current job count: {len(jobs)}")
            
            # 获取特定任务
            job = self.scheduler.get_job("test_management_job")
            if job:
                print(f"[OK] Job query successful: {job.id}")
            else:
                print("[FAIL] Job query failed")
                return False
            
            # 暂停任务
            self.scheduler.pause_job("test_management_job")
            print("[OK] Job paused successfully")
            
            # 恢复任务
            self.scheduler.resume_job("test_management_job")
            print("[OK] Job resumed successfully")
            
            # 移除任务
            self.scheduler.remove_job("test_management_job")
            print("[OK] Job removed successfully")
            
            return True
        except Exception as e:
            print(f"[FAIL] Job management test failed: {e}")
            return False
    
    def cleanup(self):
        """
        清理资源
        """
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                print("[OK] Scheduler shutdown successfully")
        except Exception as e:
            print(f"[WARN] Warning during scheduler shutdown: {e}")
    
    def run_all_tests(self) -> bool:
        """
        运行所有测试
        """
        print("[INFO] Starting APScheduler functionality tests...\n")
        
        tests = [
            ("Scheduler Creation", self.test_scheduler_creation),
            ("Scheduler Start/Stop", self.test_scheduler_start_stop),
            ("Interval Job", self.test_interval_job),
            ("Date Job", self.test_date_job),
            ("Cron Job", self.test_cron_job),
            ("Job Management", self.test_job_management),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n[TEST] {test_name}")
            try:
                if test_func():
                    passed += 1
                    print(f"[PASS] {test_name} test passed")
                else:
                    print(f"[FAIL] {test_name} test failed")
            except Exception as e:
                print(f"[ERROR] {test_name} test exception: {e}")
        
        # 显示任务执行结果
        if self.test_results:
            print("\n[RESULTS] Job execution records:")
            for result in self.test_results[-5:]:  # 显示最后5条记录
                print(f"  {result}")
        
        print(f"\n[SUMMARY] Test results: {passed}/{total} passed")
        print(f"[SUMMARY] Job execution count: {self.job_executed_count}")
        
        return passed == total


def main():
    """
    主测试函数
    """
    tester = APSchedulerTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n[SUCCESS] All APScheduler tests passed!")
            return 0
        else:
            print("\n[FAIL] Some APScheduler tests failed")
            return 1
    
    except KeyboardInterrupt:
        print("\n[WARN] Tests interrupted by user")
        return 1
    
    except Exception as e:
        print(f"\n[ERROR] Exception occurred during testing: {e}")
        return 1
    
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())