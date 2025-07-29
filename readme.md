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

## 系统要求
- Python 3.8+
- 操作系统：Windows/macOS/Linux
- PyQt6 (包含QtWebEngineWidgets模块，用于现代UI)

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

2. 端口配置（可选）
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
A: 编辑 `user_ids.txt` 文件，添加或删除实例ID即可。

Q: 如何查看运行日志？
A: 日志文件存储在 `logs` 目录下，同时GUI界面也会实时显示运行日志。

Q: cookies保存在哪里？
A: cookies保存在 `data/cookies/` 目录下，以 `{user_id}_{site_key}_cookies.json` 格式命名。

Q: 为什么要统一使用CookiesManager？
A: 统一使用CookiesManager可以避免直接操作文件，提高安全性和可靠性，同时简化了跨模块共享数据的复杂度。

## 许可证
MIT License

```
