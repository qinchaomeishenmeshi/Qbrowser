#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖验证脚本
快速检查当前环境的依赖状态和兼容性
"""

import sys
import importlib
from typing import List, Tuple, Dict


def check_python_version() -> Tuple[bool, str]:
    """检查Python版本"""
    version = sys.version_info
    current = f"{version.major}.{version.minor}.{version.micro}"
    
    if version < (3, 8):
        return False, f"Python版本过低: {current} (需要 >= 3.8)"
    elif version >= (3, 13):
        return True, f"Python版本: {current} (较新版本，可能存在兼容性问题)"
    else:
        return True, f"Python版本: {current} ✅"


def check_core_dependencies() -> List[Tuple[str, bool, str]]:
    """检查核心依赖"""
    dependencies = [
        ('PyQt6', 'PyQt6'),
        ('PyQt6.QtCore', 'PyQt6.QtCore'),
        ('PyQt6.QtWidgets', 'PyQt6.QtWidgets'),
        ('PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineWidgets'),
        ('qasync', 'qasync'),
        ('psutil', 'psutil'),
        ('loguru', 'loguru'),
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('aiohttp', 'aiohttp'),
        ('requests', 'requests'),
        ('DrissionPage', 'DrissionPage'),
    ]
    
    results = []
    for name, module_name in dependencies:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', '未知版本')
            results.append((name, True, f"{version} ✅"))
        except ImportError as e:
            results.append((name, False, f"导入失败: {str(e)} ❌"))
        except Exception as e:
            results.append((name, False, f"检查失败: {str(e)} ⚠️"))
    
    return results


def check_optional_dependencies() -> List[Tuple[str, bool, str]]:
    """检查可选依赖"""
    optional_deps = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('pillow', 'PIL'),
        ('pytest', 'pytest'),
        ('mypy', 'mypy'),
        ('black', 'black'),
    ]
    
    results = []
    for name, module_name in optional_deps:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', '未知版本')
            results.append((name, True, f"{version} ✅"))
        except ImportError:
            results.append((name, False, "未安装 (可选) ⚪"))
        except Exception as e:
            results.append((name, False, f"检查失败: {str(e)} ⚠️"))
    
    return results


def check_version_compatibility() -> List[str]:
    """检查版本兼容性问题"""
    issues = []
    
    try:
        import psutil
        if hasattr(psutil, '__version__'):
            version = psutil.__version__
            if version.startswith('7.'):
                issues.append(f"⚠️ psutil {version} 是最新版本，如遇问题可降级到 5.9.x-6.0.x")
    except ImportError:
        pass
    
    try:
        import PyQt6.QtCore
        version = PyQt6.QtCore.PYQT_VERSION_STR
        if version.startswith('6.9.'):
            issues.append(f"⚠️ PyQt6 {version} 在某些系统上可能存在问题，如遇问题可降级到 6.7.x")
    except (ImportError, AttributeError):
        pass
    
    # 检查Python版本是否过高
    if sys.version_info >= (3, 12):
        issues.append("💡 当前Python版本较新，如需更好兼容性可考虑使用 Python 3.8-3.11")
    
    return issues


def get_system_info() -> Dict[str, str]:
    """获取系统信息"""
    import platform
    
    return {
        '操作系统': platform.system(),
        '系统版本': platform.release(),
        '架构': platform.machine(),
        'Python实现': platform.python_implementation(),
        'Python编译器': platform.python_compiler(),
    }


def main():
    """主函数"""
    print("🔍 QW-Browser 依赖验证\n")
    
    # 系统信息
    print("📋 系统信息:")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"  {key}: {value}")
    print()
    
    # Python版本检查
    print("🐍 Python版本检查:")
    py_ok, py_msg = check_python_version()
    print(f"  {py_msg}")
    print()
    
    # 核心依赖检查
    print("📦 核心依赖检查:")
    core_deps = check_core_dependencies()
    core_failed = []
    for name, success, message in core_deps:
        print(f"  {name:25} {message}")
        if not success:
            core_failed.append(name)
    print()
    
    # 可选依赖检查
    print("🎯 可选依赖检查:")
    optional_deps = check_optional_dependencies()
    for name, success, message in optional_deps:
        print(f"  {name:25} {message}")
    print()
    
    # 版本兼容性检查
    print("⚡ 版本兼容性检查:")
    compatibility_issues = check_version_compatibility()
    if compatibility_issues:
        for issue in compatibility_issues:
            print(f"  {issue}")
    else:
        print("  未发现明显的兼容性问题 ✅")
    print()
    
    # 总结
    print("📊 检查总结:")
    if not py_ok:
        print("  ❌ Python版本不符合要求")
    elif core_failed:
        print(f"  ❌ 核心依赖缺失: {', '.join(core_failed)}")
        print("  建议运行: uv sync")
    else:
        print("  ✅ 核心依赖检查通过")
        print("  💡 可以尝试运行: python app.py")
    
    if compatibility_issues:
        print(f"  ⚠️  发现 {len(compatibility_issues)} 个潜在兼容性问题")
        print("  📖 详细信息请查看: dependency_analysis_report.md")
    
    print("\n🔧 如需优化依赖配置:")
    print("  1. 查看分析报告: cat dependency_analysis_report.md")
    print("  2. 使用优化配置: cp pyproject_optimized.toml pyproject.toml")
    print("  3. 重新安装依赖: uv sync")


if __name__ == "__main__":
    main()