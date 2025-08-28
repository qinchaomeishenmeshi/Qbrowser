#!/usr/bin/env python3
"""
Windows 平台专用打包脚本
包含环境检查、依赖验证和打包诊断功能
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_environment():
    """检查打包环境"""
    print("=== 环境检查 ===")
    
    # 检查 Python 版本
    python_version = sys.version_info
    print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 版本过低，需要 3.8 或更高版本")
        return False
    else:
        print("✅ Python 版本符合要求")
    
    # 检查必要依赖
    required_packages = [
        ('PyQt6', 'PyQt6'),
        ('qasync', 'qasync'),
        ('loguru', 'loguru'),
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('DrissionPage', 'DrissionPage'),
        ('PyInstaller', 'PyInstaller')
    ]
    
    missing_packages = []
    for display_name, import_name in required_packages:
        try:
            __import__(import_name.replace('-', '_').lower())
            print(f"✅ {display_name} - 已安装")
        except ImportError:
            missing_packages.append(display_name)
            print(f"❌ {display_name} - 未安装")
    
    # 特别检查PyQt6-Qt6（通过检查PyQt6.QtCore是否包含Qt库）
    try:
        from PyQt6 import QtCore
        print(f"✅ PyQt6-Qt6 - 已安装 (Qt版本: {QtCore.qVersion()})")
    except ImportError:
        missing_packages.append('PyQt6-Qt6')
        print(f"❌ PyQt6-Qt6 - 未安装")
    
    if missing_packages:
        print(f"\n缺少以下依赖包: {missing_packages}")
        
        # 提供精确的安装命令
        install_packages = []
        for pkg in missing_packages:
            if pkg == 'PyQt6-Qt6':  # 这个会随 PyQt6 自动安装
                continue
            install_packages.append(pkg)
        
        if install_packages:
            print("\n请运行以下命令安装缺少的依赖:")
            print(f"pip install {' '.join(install_packages)}")
        return False
    
    return True

def check_pyqt6_modules():
    """检查 PyQt6 关键模块"""
    print("\n=== PyQt6 模块检查 ===")
    
    pyqt6_modules = [
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',  # 新增：QLocalServer 需要
    ]
    
    for module in pyqt6_modules:
        try:
            __import__(module)
            print(f"✅ {module} - 可用")
        except ImportError as e:
            print(f"❌ {module} - 不可用: {e}")
            return False
    
    # 特别检查 QLocalServer
    try:
        from PyQt6.QtNetwork import QLocalServer, QLocalSocket
        print("✅ QLocalServer/QLocalSocket - 可用")
    except ImportError as e:
        print(f"❌ QLocalServer/QLocalSocket 导入失败: {e}")
        return False
    
    return True

def check_project_files():
    """检查项目文件完整性"""
    print("\n=== 项目文件检查 ===")
    
    required_files = [
        'app.py',
        'app.spec',
        'utils/singleton_manager.py',  # 新增
        'conf/__init__.py',
        'service/browser_service.py',
        'ui/modern_app.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} - 存在")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} - 缺失")
    
    if missing_files:
        print(f"\n缺少以下关键文件: {missing_files}")
        return False
    
    # 检查扩展目录
    extension_dirs = ['extensions/live_room', 'extensions/block_videos']
    for ext_dir in extension_dirs:
        if os.path.exists(ext_dir):
            print(f"✅ {ext_dir} - 存在")
        else:
            print(f"⚠️  {ext_dir} - 不存在（可选）")
    
    return True

def clean_build_dirs():
    """清理旧的构建目录"""
    print("\n=== 清理构建目录 ===")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ 已清理 {dir_name}")
            except Exception as e:
                print(f"❌ 清理 {dir_name} 失败: {e}")
        else:
            print(f"ℹ️  {dir_name} 不存在")

def test_imports():
    """测试关键模块导入"""
    print("\n=== 关键模块导入测试 ===")
    
    test_modules = [
        ('utils.singleton_manager', 'SingletonManager'),
        ('ui.modern_app', 'ModernApp'),
        ('service.browser_service', 'browser_service'),
        ('api.api_server', 'run_server'),
    ]
    
    for module_name, class_or_func in test_modules:
        try:
            module = __import__(module_name, fromlist=[class_or_func])
            getattr(module, class_or_func)
            print(f"✅ {module_name}.{class_or_func} - 导入成功")
        except Exception as e:
            print(f"❌ {module_name}.{class_or_func} - 导入失败: {e}")
            return False
    
    return True

def build_executable():
    """执行打包"""
    print("\n=== 开始打包 ===")
    
    try:
        # 使用 PyInstaller 打包
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',  # 清理缓存
            '--noconfirm',  # 不询问确认
            'app.spec'
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 打包成功")
            print("\n打包输出:")
            print(result.stdout)
            return True
        else:
            print("❌ 打包失败")
            print("\n错误信息:")
            print(result.stderr)
            print("\n输出信息:")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ 打包过程中发生异常: {e}")
        return False

def test_executable():
    """测试生成的可执行文件"""
    print("\n=== 测试可执行文件 ===")
    
    exe_path = Path("dist/全网直播浏览器/全网直播浏览器.exe")
    
    if not exe_path.exists():
        print(f"❌ 可执行文件不存在: {exe_path}")
        return False
    
    print(f"✅ 可执行文件存在: {exe_path}")
    print(f"文件大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    # 可选：尝试运行（仅做快速测试）
    try:
        print("正在进行快速启动测试...")
        result = subprocess.run(
            [str(exe_path), '--help'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        print("✅ 可执行文件可以启动")
    except subprocess.TimeoutExpired:
        print("⚠️  启动测试超时（这通常是正常的）")
    except Exception as e:
        print(f"⚠️  启动测试失败: {e}")
    
    return True

def main():
    """主函数"""
    print("QW-Browser Windows 打包工具")
    print("=" * 50)
    
    # 检查系统
    if sys.platform != "win32":
        print("❌ 此工具仅适用于 Windows 系统")
        return False
    
    # 步骤1: 环境检查
    if not check_environment():
        print("\n❌ 环境检查失败，请解决上述问题后重试")
        return False
    
    # 步骤2: PyQt6 模块检查
    if not check_pyqt6_modules():
        print("\n❌ PyQt6 模块检查失败，请重新安装 PyQt6")
        return False
    
    # 步骤3: 项目文件检查
    if not check_project_files():
        print("\n❌ 项目文件检查失败，请确保项目完整")
        return False
    
    # 步骤4: 模块导入测试
    if not test_imports():
        print("\n❌ 模块导入测试失败，请检查代码")
        return False
    
    # 步骤5: 清理旧构建
    clean_build_dirs()
    
    # 步骤6: 执行打包
    if not build_executable():
        print("\n❌ 打包失败")
        return False
    
    # 步骤7: 测试可执行文件
    if not test_executable():
        print("\n❌ 可执行文件测试失败")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 打包成功完成！")
    print("可执行文件位置: dist/全网直播浏览器/全网直播浏览器.exe")
    print("\n建议测试:")
    print("1. 双击运行可执行文件")
    print("2. 检查所有功能是否正常")
    print("3. 测试单例检查功能")
    
    return True

if __name__ == "__main__":
    success = main()
    print("\n按任意键退出...")
    try:
        input()
    except:
        pass
    sys.exit(0 if success else 1)