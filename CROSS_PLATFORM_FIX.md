# 跨平台兼容性修复 - 更新日志

## 修复时间
2025-08-28

## 问题描述
项目中使用了 `fcntl` 模块实现单例启动机制，但该模块仅在Unix/Linux系统上可用，导致Windows用户在执行 `uv sync` 后无法正常运行应用程序。

## 错误表现
- Windows用户运行 `python app.py` 时出现 `ImportError: No module named 'fcntl'` 错误
- macOS/Linux用户正常使用，Windows用户无法启动应用

## 技术根因
`fcntl` 是Unix系统特有的文件控制模块，Windows系统不提供此模块，导致直接导入失败。

## 修复方案

### 1. 依赖替换
- **替换前**: 使用 `import fcntl` 和 `fcntl.flock()` 实现文件锁
- **替换后**: 使用 `from filelock import FileLock, Timeout` 实现跨平台文件锁

### 2. 代码修改

#### 2.1 导入部分修改
```python
# 修改前
import fcntl

# 修改后  
from filelock import FileLock, Timeout
```

#### 2.2 全局变量修改
```python
# 修改前
_app_lock_file = None

# 修改后
_app_lock = None
```

#### 2.3 单例检查函数重写
```python
# 修改前 - 使用fcntl.flock
def check_single_instance():
    global _app_lock_file
    try:
        lock_file_path = os.path.join(tempfile.gettempdir(), "qw_browser_app.lock")
        _app_lock_file = open(lock_file_path, "w")
        fcntl.flock(_app_lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # ...
    except (IOError, OSError) as e:
        # 复杂的错误处理逻辑

# 修改后 - 使用FileLock
def check_single_instance():
    global _app_lock
    try:
        lock_file_path = os.path.join(tempfile.gettempdir(), "qw_browser_app.lock")
        _app_lock = FileLock(lock_file_path)
        _app_lock.acquire(timeout=0)
        # ...
    except Timeout:
        # 简洁的超时处理
```

#### 2.4 锁释放函数简化
```python
# 修改前
def release_single_instance():
    global _app_lock_file
    if _app_lock_file:
        try:
            fcntl.flock(_app_lock_file.fileno(), fcntl.LOCK_UN)
            _app_lock_file.close()

# 修改后
def release_single_instance():
    global _app_lock
    if _app_lock:
        try:
            _app_lock.release()
```

## 修复效果

### 平台兼容性
- ✅ **Windows**: 现在可以正常运行，使用Windows文件锁API
- ✅ **macOS**: 继续正常运行，底层仍使用fcntl.flock
- ✅ **Linux**: 继续正常运行，底层仍使用fcntl.flock

### 功能保持
- ✅ 单例启动机制完全保持
- ✅ 进程ID写入功能保持
- ✅ 锁文件自动清理保持
- ✅ 错误处理更加规范

### 代码改进
- ✅ 代码更简洁，减少了复杂的错误处理逻辑
- ✅ 使用现代化的跨平台库，更易维护
- ✅ 错误信息更清晰，调试更容易

## 技术细节

### filelock库的优势
1. **跨平台**: 自动选择最适合的底层锁机制
2. **简洁API**: 提供简单易用的接口
3. **超时机制**: 内置超时处理，避免死锁
4. **现有依赖**: 项目中已包含此依赖，无需额外安装

### 底层实现
- **Windows**: 使用 `msvcrt.locking()` 或 Windows API
- **Unix/Linux**: 使用 `fcntl.flock()`
- **自动选择**: filelock库会根据平台自动选择最佳实现

## 验证结果
从应用启动日志可以看到：
```
2025-08-28 11:07:11.497 | INFO | __main__:check_single_instance:78 - 应用程序启动成功，进程ID: 90021
```

## 部署说明

### Windows用户
1. 执行 `uv sync` 安装依赖
2. 运行 `python app.py` 正常启动应用
3. 无需额外配置或权限设置

### 现有用户
- macOS/Linux用户无感知升级，应用继续正常运行
- 所有功能保持不变，仅底层实现优化

## 相关文件
- `app.py` - 主要修改文件
- `pyproject.toml` - 依赖配置（已包含filelock）
- `test_cross_platform_fix.py` - 兼容性测试脚本

## 总结
此次修复彻底解决了Windows系统的兼容性问题，使QW-Browser真正成为跨平台应用。使用现代化的filelock库不仅解决了问题，还提升了代码质量和可维护性。