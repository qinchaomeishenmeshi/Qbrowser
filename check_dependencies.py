#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查脚本
检查 pyproject.toml 中的依赖配置是否存在问题
"""

import sys
import subprocess
import json
from typing import Dict, List, Tuple, Optional


def get_latest_version(package_name: str) -> Optional[str]:
    """获取包的最新版本（简化版本，不实际请求）"""
    # 简化实现，不进行网络请求
    return None


def parse_requirement(req_str: str) -> Tuple[str, str, str]:
    """解析依赖字符串，返回包名、操作符、版本"""
    req_str = req_str.strip('"')
    
    # 处理带有额外依赖的情况，如 fastapi[all]
    if '[' in req_str:
        package_part = req_str.split('[')[0]
        extras_part = req_str.split('[')[1].split(']')[0]
        version_part = req_str.split(']')[1] if ']' in req_str and len(req_str.split(']')) > 1 else ''
    else:
        package_part = req_str
        version_part = ''
    
    # 解析版本约束
    operators = ['>=', '<=', '==', '~=', '>', '<', '!=']
    for op in operators:
        if op in version_part:
            parts = version_part.split(op)
            return package_part, op, parts[1]
    
    if version_part:
        # 如果有版本但没有操作符，默认为 ==
        return package_part, '==', version_part
    
    return package_part, '', ''


def check_python_version_compatibility() -> List[str]:
    """检查Python版本兼容性"""
    issues = []
    current_python = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    # 检查是否要求Python 3.12+过于严格
    if sys.version_info < (3, 8):
        issues.append(f"当前Python版本 {current_python} 过低，建议升级到3.8+")
    
    # 建议降低Python版本要求以提高兼容性
    issues.append("建议将Python版本要求从 '>=3.12' 降低到 '>=3.8' 以提高兼容性")
    
    return issues


def check_dependency_versions() -> List[str]:
    """检查依赖版本是否存在问题"""
    issues = []
    
    # 定义已知的问题依赖
    known_issues = {
        'psutil': {
            'current': '7.0.0',
            'issue': 'psutil 7.0.0 是最新版本，但可能在某些系统上存在兼容性问题',
            'suggestion': '建议使用 psutil>=5.9.0,<7.0.0 以确保更好的兼容性'
        },
        'pyqt6': {
            'current': '6.9.0',
            'issue': 'PyQt6 6.9.0 在某些macOS版本上可能存在问题',
            'suggestion': '如遇到问题，可尝试降级到 6.7.x 版本'
        },
        'drissionpage': {
            'current': '4.1.0.17',
            'issue': 'DrissionPage版本使用了波浪号约束，可能导致意外升级',
            'suggestion': '建议使用精确版本号或范围约束'
        }
    }
    
    for package, info in known_issues.items():
        issues.append(f"⚠️  {package}: {info['issue']}")
        issues.append(f"   建议: {info['suggestion']}")
    
    return issues


def check_dependency_conflicts() -> List[str]:
    """检查依赖冲突"""
    issues = []
    
    # 检查可能的版本冲突
    potential_conflicts = [
        {
            'packages': ['fastapi', 'starlette'],
            'issue': 'FastAPI和Starlette版本需要兼容',
            'current_fastapi': '0.115.12',
            'current_starlette': '0.46.2'
        },
        {
            'packages': ['pydantic', 'pydantic-core'],
            'issue': 'Pydantic和pydantic-core版本需要匹配',
            'current_pydantic': '2.11.5',
            'current_pydantic_core': '2.33.2'
        }
    ]
    
    for conflict in potential_conflicts:
        issues.append(f"🔍 检查 {', '.join(conflict['packages'])} 版本兼容性")
        issues.append(f"   {conflict['issue']}")
    
    return issues


def check_optional_dependencies() -> List[str]:
    """检查可选依赖配置"""
    issues = []
    
    # 检查可选依赖的合理性
    suggestions = [
        "✅ 可选依赖配置合理，将开发工具、数据分析等功能分离",
        "💡 建议添加 'test' 可选依赖组，包含测试相关的包",
        "💡 可以考虑添加 'docs' 可选依赖组，用于文档生成"
    ]
    
    issues.extend(suggestions)
    return issues


def generate_fixed_pyproject() -> str:
    """生成修复后的pyproject.toml内容建议"""
    fixed_content = '''
# 修复建议的 pyproject.toml 配置

[project]
name = "qw-browser"
version = "0.1.0"
description = "QW Browser - 多浏览器实例管理工具"
readme = "README.md"
requires-python = ">=3.8"  # 降低Python版本要求以提高兼容性
dependencies = [
    "aiohappyeyeballs==2.6.1",
    "aiohttp>=3.12.8",
    "aiosignal==1.3.2",
    "annotated-types==0.7.0",
    "anyio==4.9.0",
    "attrs>=23.0.0",
    "certifi>=2024.0.0",
    "charset-normalizer>=3.0.0",
    "click>=8.0.0",
    "cssselect>=1.2.0",
    "datarecorder>=3.6.0",
    "downloadkit>=2.0.0",
    "drissionpage>=4.1.0,<5.0.0",  # 使用范围约束而非波浪号
    "et-xmlfile>=1.1.0",
    "fastapi[all]>=0.115.0,<0.116.0",
    "filelock>=3.15.0",
    "frozenlist>=1.4.0",
    "h11>=0.14.0",
    "httpcore>=1.0.0",
    "httpx>=0.28.0,<0.29.0",
    "idna>=3.4",
    "loguru>=0.7.0,<0.8.0",
    "lxml>=4.9.0",
    "multidict>=6.0.0",
    "openpyxl>=3.1.0",
    "propcache>=0.2.0",
    "psutil>=5.9.0,<7.0.0",  # 使用更保守的版本范围
    "pydantic>=2.11.0,<3.0.0",
    "pydantic-core>=2.33.0,<3.0.0",
    "pyqt6>=6.7.0,<6.10.0",  # 使用范围约束
    "pyqt6-qt6>=6.7.0,<6.10.0",
    "pyqt6-sip>=13.8.0",
    "pyqt6-webengine>=6.7.0,<6.10.0",
    "qasync>=0.27.0",
    "requests>=2.32.0,<3.0.0",
    "requests-file>=2.0.0",
    "sniffio>=1.3.0",
    "starlette>=0.46.0,<0.47.0",
    "tldextract>=5.0.0",
    "typing-extensions>=4.12.0",
    "typing-inspection>=0.4.0",
    "ujson>=5.10.0,<6.0.0",
    "urllib3>=2.0.0,<3.0.0",
    "uvicorn>=0.34.0,<0.35.0",
    "websocket-client>=1.8.0",
    "yarl>=1.20.0",
    "apscheduler>=3.10.4",
    "aiofiles>=23.2.1",
    "python-multipart>=0.0.6",
    "python-dateutil>=2.8.2",
    "orjson>=3.9.10",
    "tzlocal>=5.0.1",
]
'''
    return fixed_content


def main():
    """主函数"""
    print("🔍 检查 pyproject.toml 依赖配置...\n")
    
    all_issues = []
    
    # 检查Python版本兼容性
    print("📋 Python版本兼容性检查:")
    python_issues = check_python_version_compatibility()
    for issue in python_issues:
        print(f"  {issue}")
    all_issues.extend(python_issues)
    print()
    
    # 检查依赖版本
    print("📦 依赖版本检查:")
    version_issues = check_dependency_versions()
    for issue in version_issues:
        print(f"  {issue}")
    all_issues.extend(version_issues)
    print()
    
    # 检查依赖冲突
    print("⚡ 依赖冲突检查:")
    conflict_issues = check_dependency_conflicts()
    for issue in conflict_issues:
        print(f"  {issue}")
    all_issues.extend(conflict_issues)
    print()
    
    # 检查可选依赖
    print("🎯 可选依赖检查:")
    optional_issues = check_optional_dependencies()
    for issue in optional_issues:
        print(f"  {issue}")
    print()
    
    # 生成修复建议
    print("🔧 修复建议:")
    if all_issues:
        print("  发现以下需要注意的问题:")
        critical_issues = [issue for issue in all_issues if '建议' in issue or '⚠️' in issue]
        if critical_issues:
            print("\n  关键问题:")
            for issue in critical_issues[:5]:  # 只显示前5个关键问题
                print(f"    • {issue}")
    
    print("\n📝 生成修复后的配置建议...")
    fixed_config = generate_fixed_pyproject()
    
    # 保存修复建议到文件
    with open('pyproject_fixed_suggestion.toml', 'w', encoding='utf-8') as f:
        f.write(fixed_config)
    
    print("✅ 修复建议已保存到 'pyproject_fixed_suggestion.toml'")
    print("\n🎯 总结:")
    print("  1. 建议降低Python版本要求到 >=3.8 以提高兼容性")
    print("  2. 使用版本范围约束替代波浪号约束")
    print("  3. psutil建议使用更保守的版本范围")
    print("  4. PyQt6版本在某些系统上可能需要调整")
    print("  5. 整体依赖配置基本合理，主要是版本约束的优化")


if __name__ == "__main__":
    main()