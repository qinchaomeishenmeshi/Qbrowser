#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qt兼容性工具模块

解决不同Qt版本之间的API差异问题，特别是ApplicationAttribute属性的兼容性。
在Windows系统打包exe后运行时，某些Qt属性可能不存在，导致AttributeError。

作者: AI Assistant
创建时间: 2024
"""

import os
import sys
from typing import List, Tuple
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def safe_set_qt_attribute(attribute_name: str, description: str = "") -> bool:
    """
    安全地设置Qt应用程序属性
    
    Args:
        attribute_name: Qt.ApplicationAttribute的属性名称（不包含前缀）
        description: 属性描述，用于日志输出
    
    Returns:
        bool: 是否成功设置属性
    """
    try:
        if hasattr(Qt.ApplicationAttribute, attribute_name):
            attribute = getattr(Qt.ApplicationAttribute, attribute_name)
            QApplication.setAttribute(attribute)
            if description:
                print(f"[OK] 已设置Qt属性: {attribute_name} - {description}")
            return True
        else:
            print(f"[WARNING] Qt属性不存在: {attribute_name} - 跳过设置")
            return False
    except Exception as e:
        print(f"[ERROR] 设置Qt属性失败: {attribute_name} - {e}")
        return False


def setup_qt_attributes_for_windows() -> List[Tuple[str, bool]]:
    """
    为Windows系统设置Qt属性，解决显示器接口问题
    
    Returns:
        List[Tuple[str, bool]]: 每个属性的设置结果 (属性名, 是否成功)
    """
    results = []
    
    # 必需的基础属性
    results.append((
        "AA_ShareOpenGLContexts",
        safe_set_qt_attribute("AA_ShareOpenGLContexts", "共享OpenGL上下文")
    ))
    
    # Windows特定的可选属性
    if sys.platform == "win32":
        print("[INFO] 检测到Windows系统，应用Windows特定的Qt属性...")
        
        results.append((
            "AA_DisableWindowContextHelpButton",
            safe_set_qt_attribute("AA_DisableWindowContextHelpButton", "禁用窗口上下文帮助按钮")
        ))
        
        results.append((
            "AA_UseDesktopOpenGL",
            safe_set_qt_attribute("AA_UseDesktopOpenGL", "使用桌面OpenGL")
        ))
        
        # 设置Windows环境变量
        setup_windows_environment_variables()
    
    return results


def setup_windows_environment_variables() -> None:
    """
    设置Windows系统的环境变量，解决显示器接口问题
    """
    env_vars = {
        'QT_QPA_PLATFORM_PLUGIN_PATH': '',
        'QT_OPENGL': 'desktop',
        'QT_DEVICE_PIXEL_RATIO': 'auto'
    }
    
    print("[INFO] 设置Windows环境变量...")
    for key, value in env_vars.items():
        os.environ.setdefault(key, value)
        print(f"[OK] 环境变量: {key} = {value}")


def initialize_qt_compatibility() -> bool:
    """
    初始化Qt兼容性设置
    
    这个函数应该在创建QApplication之前调用
    
    Returns:
        bool: 是否成功初始化所有必需的属性
    """
    print("[INFO] 初始化Qt兼容性设置...")
    
    results = setup_qt_attributes_for_windows()
    
    # 检查关键属性是否设置成功
    critical_attributes = ["AA_ShareOpenGLContexts"]
    success = True
    
    for attr_name, result in results:
        if attr_name in critical_attributes and not result:
            print(f"[ERROR] 关键Qt属性设置失败: {attr_name}")
            success = False
    
    if success:
        print("[OK] Qt兼容性设置完成")
    else:
        print("[WARNING] Qt兼容性设置部分失败，程序可能无法正常运行")
    
    return success


def get_qt_version_info() -> dict:
    """
    获取Qt版本信息，用于调试
    
    Returns:
        dict: Qt版本相关信息
    """
    from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
    
    return {
        "qt_version": QT_VERSION_STR,
        "pyqt_version": PYQT_VERSION_STR,
        "platform": sys.platform,
        "python_version": sys.version
    }


if __name__ == "__main__":
    # 测试模块功能
    print("Qt兼容性工具测试")
    print("=" * 50)
    
    # 显示版本信息
    version_info = get_qt_version_info()
    for key, value in version_info.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 50)
    
    # 测试兼容性设置
    initialize_qt_compatibility()