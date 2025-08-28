#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锁文件清理工具

专门用于解决Windows系统下的权限问题和锁文件残留问题。
当遇到"Permission denied"或"应用程序已在运行"错误时，可以运行此脚本。

使用方法:
    python cleanup_lock.py

功能:
    1. 自动检测并清理残留的锁文件
    2. 验证进程是否仍在运行
    3. 提供详细的清理报告
"""

import os
import sys
import tempfile
import psutil
from pathlib import Path


def find_lock_files():
    """查找所有可能的锁文件位置"""
    candidate_dirs = [
        tempfile.gettempdir(),  # 系统临时目录
        os.path.expanduser("~"),  # 用户家目录
        os.getcwd(),  # 当前工作目录
        str(Path(__file__).parent),  # 项目根目录
    ]
    
    lock_files = []
    
    for lock_dir in candidate_dirs:
        if not os.path.exists(lock_dir):
            continue
            
        lock_file_path = os.path.join(lock_dir, "qw_browser_app.lock")
        
        if os.path.exists(lock_file_path):
            lock_files.append(lock_file_path)
    
    return lock_files


def is_process_running(pid):
    """检查指定PID的进程是否仍在运行"""
    try:
        return psutil.pid_exists(pid)
    except Exception:
        # 如果psutil不可用，使用系统方法
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def cleanup_lock_file(lock_file_path):
    """清理单个锁文件"""
    result = {
        'path': lock_file_path,
        'cleaned': False,
        'reason': '',
        'pid': None
    }
    
    try:
        # 尝试读取文件内容
        with open(lock_file_path, 'r') as f:
            content = f.read().strip()
        
        if content.isdigit():
            pid = int(content)
            result['pid'] = pid
            
            # 检查进程是否仍在运行
            if is_process_running(pid):
                result['reason'] = f'进程 {pid} 仍在运行，不清理锁文件'
                return result
            else:
                result['reason'] = f'进程 {pid} 已停止，可以安全清理'
        else:
            result['reason'] = '锁文件内容无效'
        
        # 尝试删除锁文件
        os.remove(lock_file_path)
        result['cleaned'] = True
        result['reason'] += '，锁文件已成功删除'
        
    except PermissionError:
        result['reason'] = '权限不足，无法删除锁文件'
    except FileNotFoundError:
        result['reason'] = '锁文件已不存在'
        result['cleaned'] = True
    except Exception as e:
        result['reason'] = f'删除失败: {e}'
    
    return result


def main():
    """主函数"""
    print("=" * 60)
    print("QW-Browser 锁文件清理工具")
    print("=" * 60)
    print()
    
    # 查找锁文件
    print("🔍 正在查找锁文件...")
    lock_files = find_lock_files()
    
    if not lock_files:
        print("✅ 没有发现锁文件，无需清理")
        return
    
    print(f"📁 发现 {len(lock_files)} 个锁文件:")
    for lock_file in lock_files:
        print(f"   - {lock_file}")
    print()
    
    # 清理锁文件
    print("🧹 开始清理...")
    cleaned_count = 0
    
    for lock_file in lock_files:
        print(f"\n处理: {lock_file}")
        result = cleanup_lock_file(lock_file)
        
        if result['cleaned']:
            print(f"  ✅ {result['reason']}")
            cleaned_count += 1
        else:
            print(f"  ❌ {result['reason']}")
            
            # 提供手动清理建议
            if 'Permission' in result['reason'] or '权限' in result['reason']:
                print(f"  💡 手动清理方法:")
                if sys.platform == "win32":
                    print(f"     以管理员身份运行: del \"{lock_file}\"")
                else:
                    print(f"     运行: rm \"{lock_file}\"")
    
    print()
    print("=" * 60)
    print("清理结果总结:")
    print(f"  总共发现: {len(lock_files)} 个锁文件")
    print(f"  成功清理: {cleaned_count} 个")
    print(f"  清理失败: {len(lock_files) - cleaned_count} 个")
    
    if cleaned_count > 0:
        print("\n✅ 清理完成！现在可以尝试重新启动应用程序")
    elif len(lock_files) > cleaned_count:
        print("\n⚠️  部分文件清理失败，建议:")
        if sys.platform == "win32":
            print("   1. 以管理员身份运行此脚本")
            print("   2. 关闭杀毒软件实时防护")
            print("   3. 检查是否有其他程序实例仍在运行")
        else:
            print("   1. 检查文件权限")
            print("   2. 使用 sudo 运行此脚本")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消操作")
    except Exception as e:
        print(f"\n\n❌ 清理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按任意键退出...")