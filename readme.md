# QW-Browser 浏览器管理工具

## 项目简介
QW-Browser 是一个强大的多浏览器实例管理工具，提供图形化界面，支持多浏览器实例的统一管理、控制和监控。

## 功能特点
- 📱 多浏览器实例管理
- 🖥️ 友好的图形用户界面
- 📊 实时日志监控
- 🔄 内网穿透支持（基于frp）
- 🛠️ RESTful API接口
- 💾 用户配置持久化
- 🌐 跨平台支持（Windows/macOS/Linux）
- 🔐 统一的Cookies管理
- 🔒 单例启动机制，防止重复运行

## 系统要求
- Python 3.8+ (推荐 3.9-3.12)
- 操作系统: Windows 10+, macOS 10.15+, Linux (Ubuntu 20.04+)
- PyQt6 (包含QtWebEngineWidgets模块，用于现代UI)

## 依赖配置

### 📦 核心依赖版本说明

- **Python版本**: 建议使用 Python 3.8-3.12，当前配置要求 >=3.12 (可能过于严格)
- **PyQt6**: 使用 6.9.0 版本，在某些系统上可能需要降级到 6.7.x
- **psutil**: 当前使用 7.0.0，如遇问题可降级到 5.9.x-6.0.x 范围
- **DrissionPage**: 使用波浪号约束 ~=4.1.0.17，建议改为范围约束

### ⚠️ 已知依赖问题

1. **Python版本要求过高**: `requires-python = ">=3.12"` 可能限制用户使用
2. **psutil 7.0.0**: 最新版本在某些系统上可能不稳定
3. **PyQt6版本**: 6.9.0 在部分macOS版本上存在兼容性问题
4. **版本约束不一致**: 混合使用了 `==`, `~=`, `>=` 等约束方式

### 🔧 依赖优化建议

如需优化依赖配置，可参考以下文件：
- `dependency_analysis_report.md` - 详细的依赖分析报告
- `pyproject_optimized.toml` - 优化后的配置文件
- `check_dependencies.py` - 依赖检查脚本

### 📋 可选依赖组

```bash
# 安装完整版本（包含所有功能）
uv sync --extra full

# 仅安装数据分析功能
uv sync --extra data-analysis

# 仅安装开发工具
uv sync --extra dev

# 仅安装测试工具
uv sync --extra test
```

## 启动方式

### 推荐启动方式
```bash
# 主启动入口（推荐）
python app.py
```

### 备用启动方式
```bash
# 备用启动入口（统一调用app.py的main函数）
python run_app.py
```

### 单例启动机制
- 应用程序采用单例启动机制，防止重复运行
- 如果检测到已有实例在运行，新启动的实例会自动退出
- 锁文件位置：系统临时目录下的 `qw_browser_app.lock`
- 如需重新启动，请先关闭现有实例

### 启动流程说明
1. **单例检查**：检查是否已有实例在运行
2. **权限检查**：Windows系统检查管理员权限
3. **Qt兼容性**：初始化Qt兼容性设置
4. **事件循环**：建立qasync事件循环
5. **异常处理**：安装全局异常处理器
6. **信号绑定**：绑定SIGINT/SIGTERM信号处理
7. **UI启动**：创建并显示主窗口
8. **优雅退出**：确保资源正确释放

## 已知问题及解决方案

### QtWebEngineWidgets导入错误
**问题描述：** 在打包成exe后运行时出现错误：
```
QtWebEngineWidgets must be imported or Qt.AA_ShareOpenGLContexts must be set before a QCoreApplication instance is created
```

**解决方案：** 
1. 在创建QApplication之前设置`Qt.AA_ShareOpenGLContexts`属性
2. 在应用启动时预先导入QtWebEngineWidgets模块
3. 添加了优雅的降级机制，当QtWebEngine不可用时自动切换到经典UI

**修复内容：**
- 修改了`app.py`中的导入顺序和QApplication创建逻辑
- 在`modern_app.py`中添加了QtWebEngine不可用时的备用方案
- 提供了在外部浏览器中打开定时任务管理页面的功能

### Qt兼容性问题（Windows打包exe）
**问题描述：** 在Windows系统运行打包后的exe文件时出现错误：
```
AttributeError: type object 'ApplicationAttribute' has no attribute 'AA_DisableWindowContextHelpButton'
```

**问题原因：**
- 不同Qt版本之间的API差异
- 打包环境和运行环境的Qt版本不匹配
- 某些Qt属性在特定版本中不存在

**解决方案：**
1. 创建了Qt兼容性工具模块 `utils/qt_compatibility.py`
2. 使用 `hasattr()` 安全检查Qt属性是否存在
3. 提供平台特定的Qt属性设置
4. 自动配置Windows系统环境变量

**修复内容：**
- 新增 `utils/qt_compatibility.py` - Qt兼容性工具模块
- 修改 `app.py` - 使用兼容性工具替代直接设置Qt属性
- 更新 `test_qt_display_fix.py` - 使用新的兼容性模块
- 添加 `QT_COMPATIBILITY_FIX.md` - 详细的修复文档

**使用方法：**
```python
from utils.qt_compatibility import initialize_qt_compatibility

# 在创建QApplication之前调用
initialize_qt_compatibility()
app = QApplication(sys.argv)
```

**测试验证：**
```bash
# 运行Qt兼容性测试
python test_qt_display_fix.py
```

### 打包文件大小优化

**问题描述：** 添加WebEngine支持后，打包文件从59MB增加到195MB

**主要原因：**
- PyQt6 WebEngine包含Chromium内核 (~100-120MB)
- 构建时包含了开发依赖 (~15-25MB)
- 未优化的PyInstaller配置 (~10-15MB)

**双版本构建方案：**

#### 🚀 完整版 (Full Version)
- **文件名**: `全网直播浏览器-完整版.zip`
- **大小**: ~150-170MB
- **特性**: 
  - 包含所有功能
  - 内置WebEngine支持
  - 定时任务页面内嵌显示
  - 最佳用户体验

#### 🔧 构建配置
- **构建配置**: `app.spec` + `build-exe.yml`
- **自动构建**: GitHub Actions自动构建
- **智能检测**: 应用自动检测WebEngine可用性

详细分析请参考: `PACKAGING_SIZE_ANALYSIS.md`

## 快速开始

### 1. 环境准备

创建并激活虚拟环境：

```bash
# 创建虚拟环境
python -m venv .venv

# Windows激活
.\.venv\Scripts\activate

# macOS/Linux激活
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置说明

1. 浏览器实例配置
   - 创建或编辑 `user_ids.txt` 文件
   - 每行输入一个实例ID
   - 实例ID将用于区分不同的浏览器会话

2. Chrome浏览器路径配置
   - 系统会自动检测Chrome浏览器路径
   - 支持自定义Chrome可执行文件路径
   - 提供多种配置方式：命令行工具、Web界面、API接口
   - 配置文件：`chrome_config.json`

3. 端口配置（可选）
   - 默认API服务端口：6001
   - 如需修改，请在 `conf.py` 中调整

### 4. 启动应用

```bash
python app.py
```

## 主要功能说明

### GUI界面操作
- 【启动浏览器】：启动配置文件中指定的所有浏览器实例
- 【一键关闭】：安全关闭所有运行中的浏览器实例
- 【加载配置】：重新加载user_ids.txt配置文件
- 【清除缓存】：清除浏览器数据和配置缓存
- 【自动保存】：应用关闭时自动保存当前用户ID列表到user_ids.txt配置文件

### API服务
- 默认地址：http://127.0.0.1:6001
- 提供浏览器实例控制的RESTful接口
- 支持远程调用和集成

### Cookies管理系统
项目提供了统一的Cookies管理机制，便于跨模块共享浏览器状态：

#### CookiesManager用法
```python
from browser.browser_operator import browser_operator

# 获取cookies
cookies = await browser_operator.get_user_cookies(user_id, site_key="baiying")

# 获取headers
headers = await browser_operator.get_user_headers(user_id, site_key="baiying")

# 清除用户数据
await browser_operator.clear_user_data(user_id, site_key="baiying")
```

#### 迁移旧数据
如果您有使用旧版本的项目，可以使用迁移工具将cookies从旧格式迁移到CookiesManager：

```bash
# 执行迁移脚本
python tools/migrate_cookies.py
```

迁移脚本会：
1. 备份原始数据到`user_ports_cache.json.bak`
2. 将旧格式的cookies迁移到CookiesManager统一管理
3. 清理原始文件中的cookies和headers字段，只保留端口信息

## 技术栈
- GUI框架：PyQt6
- 浏览器自动化：DrissionPage
- API服务：FastAPI
- 网络请求：httpx/requests
- 日志系统：loguru
- 异步支持：qasync
- 数据管理：CookiesManager

## 注意事项
1. 首次运行时需要完整的网络环境以下载必要的浏览器驱动
2. Windows系统会自动启动frpc服务，macOS需要手动配置
3. 请确保所需端口未被其他程序占用
4. 所有涉及cookies的操作都应该使用CookiesManager而不是直接读写文件

## 常见问题
Q: 如何修改浏览器实例数量？
A: 编辑 `user_ids.txt` 文件，添加或删除实例ID即可。也可以直接在GUI界面的文本框中修改用户ID列表，应用关闭时会自动保存到配置文件。

Q: 用户ID配置会自动保存吗？
A: 是的，当您关闭应用时，系统会自动将当前文本框中的用户ID列表保存到 `user_ids.txt` 配置文件中，无需手动保存。

Q: 如何查看运行日志？
A: 日志文件存储在 `logs` 目录下，同时GUI界面也会实时显示运行日志。

Q: cookies保存在哪里？
A: cookies保存在 `data/cookies/` 目录下，以 `{user_id}_{site_key}_cookies.json` 格式命名。

Q: 为什么要统一使用CookiesManager？
A: 统一使用CookiesManager可以避免直接操作文件，提高安全性和可靠性，同时简化了跨模块共享数据的复杂度。

Q: 遇到 "qt.qpa.screen: Unable to open monitor interface" 错误怎么办？
A: 这是Windows系统上的Qt显示器接口问题，已在代码中添加修复方案。如果仍有问题，请参考 `QT_DISPLAY_ERROR_FIX.md` 文件中的详细解决方案，包括更新显卡驱动、调整显示设置、使用兼容性模式等。

Q: GitHub Actions构建时遇到Unicode编码错误怎么办？
A: 这是Windows系统编码问题，已在构建脚本中添加UTF-8编码设置。详细解决方案请参考 `UNICODE_ENCODING_FIX.md` 文件。

## Chrome浏览器路径配置

### 功能概述
本项目支持自定义Chrome浏览器的可执行文件路径，提供了多种配置方式来满足不同用户的需求。<mcreference link="https://www.drissionpage.cn/get_start/before_start/" index="1">1</mcreference>

### 支持的浏览器
- Google Chrome
- Microsoft Edge
- Chromium
- Brave Browser

### 配置方式

#### 1. 命令行工具配置

使用内置的命令行工具进行配置：

```bash
# 显示当前配置
python chrome_config_tool.py --show

# 检测系统中可用的Chrome浏览器
python chrome_config_tool.py --detect

# 设置自定义Chrome路径
python chrome_config_tool.py --set "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 清除自定义路径（使用系统默认）
python chrome_config_tool.py --clear

# 交互式配置（推荐）
python chrome_config_tool.py --interactive
```

#### 2. Web界面配置

启动API服务器后，访问Chrome配置页面：

```bash
# 启动API服务器
python start_api_server.py

# 在浏览器中访问配置页面
http://localhost:8000/chrome/config
```

Web界面功能：
- 📋 查看当前配置信息
- 🔍 自动检测系统中可用的Chrome浏览器
- ⚙️ 设置自定义Chrome路径
- 🗑️ 清除自定义配置

#### 3. API接口配置

通过RESTful API进行配置：

```bash
# 获取当前配置
curl http://localhost:8000/api/chrome-config/current

# 检测可用浏览器
curl http://localhost:8000/api/chrome-config/detect

# 设置Chrome路径
curl -X POST http://localhost:8000/api/chrome-config/set-path \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/chrome"}'

# 清除自定义路径
curl -X DELETE http://localhost:8000/api/chrome-config/clear-path
```

### 配置文件

Chrome路径配置保存在 `chrome_config.json` 文件中：

```json
{
  "chrome_path": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
}
```

### 默认路径检测

系统会自动检测以下默认路径：

**macOS:**
- `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- `/Applications/Chromium.app/Contents/MacOS/Chromium`
- `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge`
- `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser`

**Windows:**
- `C:\Program Files\Google\Chrome\Application\chrome.exe`
- `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`
- `C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe`
- `C:\Program Files\Microsoft\Edge\Application\msedge.exe`
- `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`

**Linux:**
- `/usr/bin/google-chrome`
- `/usr/bin/chromium-browser`
- `/usr/bin/chromium`
- `/snap/bin/chromium`
- `/usr/bin/microsoft-edge`
- `/usr/bin/brave-browser`

### 使用优先级

1. **自定义路径** - 如果设置了自定义路径且文件存在，优先使用
2. **系统默认路径** - 按照默认路径列表顺序检测，使用第一个找到的
3. **DrissionPage默认** - 如果都未找到，使用DrissionPage的默认配置

### 故障排除

**问题：Chrome路径设置失败**
- 检查路径是否正确
- 确认文件存在且有执行权限
- 验证是否为Chrome可执行文件

**问题：检测不到Chrome浏览器**
- 确认Chrome已正确安装
- 检查安装路径是否在默认路径列表中
- 使用自定义路径手动设置

**问题：浏览器启动失败**
- 检查Chrome版本兼容性
- 确认系统权限设置
- 查看详细错误日志

### 注意事项

1. **权限要求**：确保Chrome可执行文件有执行权限
2. **版本兼容**：建议使用较新版本的Chrome浏览器
3. **路径格式**：使用绝对路径，避免相对路径
4. **配置持久化**：配置会自动保存到文件，重启后仍然有效
5. **多平台支持**：配置工具会根据操作系统自动适配路径格式
A: 这是Windows构建环境中的字符编码问题，已在构建工作流中添加UTF-8编码设置和Unicode字符替换。详细的修复方案请参考 `UNICODE_ENCODING_FIX.md` 文件，包括环境变量设置、字符替换规则和语法错误修复等。

## 许可证
MIT License

```
