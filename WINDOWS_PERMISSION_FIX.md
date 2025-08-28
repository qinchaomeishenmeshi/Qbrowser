# Windows系统权限问题修复指南

## 问题描述

在Windows系统上运行qw-browser时，可能遇到以下错误：

```
[ERROR] 应用程序已在运行，请勿重复启动！
[INFO] 如需重新启动，请先关闭现有实例
2025-08-28 11:23:33.682 | ERROR | __main__:check_single_instance:87 - 检查单例时发生错误: [Errno 13] Permission denied
```

## 问题根本原因

1. **权限不足**：Windows系统在临时目录创建锁文件时权限不足
2. **杀毒软件拦截**：实时防护可能阻止文件操作
3. **锁文件残留**：程序异常退出后锁文件未被正确清理

## 解决方案

### 方案一：立即解决（推荐）

#### 1. 使用自动清理脚本
```bash
# 方法A：运行批处理文件（简单）
双击运行: cleanup_lock.bat

# 方法B：运行Python脚本（详细）
python cleanup_lock.py
```

#### 2. 手动清理锁文件
```batch
# 在命令提示符中执行
del "%TEMP%\\qw_browser_app.lock"
del "%USERPROFILE%\\qw_browser_app.lock"
del "qw_browser_app.lock"
```

### 方案二：以管理员身份运行

1. 右键点击 PowerShell 或命令提示符
2. 选择"以管理员身份运行"
3. 导航到项目目录
4. 运行 `python app.py`

### 方案三：配置杀毒软件

将项目目录添加到杀毒软件的信任列表中，避免文件操作被拦截。

## 代码层面的改进

本次修复对 `app.py` 进行了以下改进：

### 1. 改进单例检查机制

```python
def check_single_instance():
    """检查是否已有应用程序实例在运行
    
    Windows兼容性改进：
    - 使用多个候选目录存放锁文件
    - 改进权限错误处理
    - 提供自动恢复机制
    """
    # 候选锁文件目录列表（按优先级排序）
    candidate_dirs = [
        tempfile.gettempdir(),  # 系统临时目录
        os.path.expanduser("~"),  # 用户家目录
        os.getcwd(),  # 当前工作目录
        "."  # 项目根目录
    ]
    
    # 逐个尝试候选目录，直到成功创建锁文件
    # ...
```

### 2. 添加锁文件清理功能

```python
def cleanup_lock_files():
    """清理可能残留的锁文件
    
    Windows系统专用：用于清理因权限问题或异常退出导致的残留锁文件
    """
    # 检查进程是否还在运行
    # 安全删除残留锁文件
    # ...
```

### 3. 改进启动流程

```python
def main():
    # Windows系统先尝试清理可能的残留锁文件
    if sys.platform == "win32":
        try:
            cleanup_lock_files()
        except Exception as e:
            logger.debug(f"清理锁文件时出错: {e}")
    
    # 检查是否已有实例在运行
    if not check_single_instance():
        # 提供更详细的错误信息和解决方案
        # ...
```

## 测试验证

修复后的程序具有以下特性：

1. **多目录尝试**：如果临时目录没有权限，会自动尝试用户目录、当前目录等
2. **权限检测**：在创建锁文件前先测试目录的写权限
3. **智能清理**：启动时自动检测并清理无效的锁文件
4. **详细提示**：遇到问题时提供具体的解决方案

## 使用建议

1. **首次运行**：建议先运行清理脚本，确保没有残留锁文件
2. **开发环境**：可以将项目目录添加到杀毒软件信任列表
3. **生产环境**：建议以管理员权限运行程序

## 文件说明

- `cleanup_lock.py` - Python清理脚本，提供详细的清理报告
- `cleanup_lock.bat` - Windows批处理脚本，简单快速清理
- `WINDOWS_PERMISSION_FIX.md` - 本文档，详细的修复说明

## 相关文件修改

- `app.py` - 主要修改文件，改进了单例检查和错误处理
- `cleanup_lock.py` - 新增清理工具
- `cleanup_lock.bat` - 新增Windows批处理清理工具

通过这些改进，Windows用户应该能够正常运行qw-browser程序，不再遇到权限相关的启动问题。