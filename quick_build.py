#!/usr/bin/env python3
"""
快速打包脚本 - 简化版本
跳过复杂的环境检查，直接进行核心功能测试和打包
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def quick_check():
    """快速检查核心依赖"""
    print("=== 快速依赖检查 ===")
    
    core_imports = [
        ("PyQt6.QtCore", "PyQt6 核心"),
        ("PyQt6.QtWidgets", "PyQt6 界面"),
        ("PyQt6.QtNetwork", "PyQt6 网络"),
        ("utils.singleton_manager", "单例管理器"),
    ]
    
    failed = False
    for module, desc in core_imports:
        try:
            __import__(module)
            print(f"✅ {desc} - OK")
        except ImportError as e:
            print(f"❌ {desc} - 失败: {e}")
            failed = True
    
    return not failed

def clean_build():
    """清理构建目录"""
    print("\n=== 清理构建目录 ===")
    
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ 已清理 {dir_name}")
            except Exception as e:
                print(f"⚠️  清理 {dir_name} 失败: {e}")

def build_exe():
    """执行打包"""
    print("\n=== 开始打包 ===")
    
    try:
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'app.spec']
        print(f"执行: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            print("✅ 打包成功")
            return True
        else:
            print("❌ 打包失败")
            print("\n=== 错误信息 ===")
            print(result.stderr)
            if result.stdout:
                print("\n=== 输出信息 ===")
                print(result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ 打包异常: {e}")
        return False

def check_result():
    """检查打包结果"""
    print("\n=== 检查打包结果 ===")
    
    exe_path = Path("dist/全网直播浏览器/全网直播浏览器.exe")
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / 1024 / 1024
        print(f"✅ 可执行文件已生成: {exe_path}")
        print(f"📁 文件大小: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ 可执行文件未找到: {exe_path}")
        
        # 检查是否有其他生成的文件
        dist_dir = Path("dist")
        if dist_dir.exists():
            print("\ndist 目录内容:")
            for item in dist_dir.iterdir():
                print(f"  - {item}")
        
        return False

def main():
    """主函数"""
    print("QW-Browser 快速打包工具")
    print("=" * 40)
    
    # 步骤1: 快速检查
    if not quick_check():
        print("\n❌ 核心依赖检查失败")
        print("\n可能的解决方案:")
        print("1. 确保在正确的虚拟环境中")
        print("2. 重新安装 PyQt6: pip install PyQt6")
        print("3. 检查项目文件完整性")
        return False
    
    # 步骤2: 清理
    clean_build()
    
    # 步骤3: 打包
    if not build_exe():
        print("\n❌ 打包失败，请检查上述错误信息")
        return False
    
    # 步骤4: 检查结果
    if not check_result():
        print("\n❌ 打包结果检查失败")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 快速打包完成！")
    print("\n下一步:")
    print("1. 测试运行: dist\\全网直播浏览器\\全网直播浏览器.exe")
    print("2. 如有问题，运行: python build_windows.py 进行详细诊断")
    
    return True

if __name__ == "__main__":
    success = main()
    print("\n按任意键退出...")
    try:
        input()
    except:
        pass
    sys.exit(0 if success else 1)