# 浏览器重定向功能说明

## 功能概述

浏览器重定向功能允许您根据预设规则自动将浏览器从一个网站重定向到另一个网站。例如，当访问Google时自动跳转到百度，或者从YouTube跳转到哔哩哔哩。

## 重定向规则

重定向规则存储在项目根目录的`redirect_rules.json`文件中，格式如下：

```json
{
  "google_to_baidu": {
    "source_pattern": "google",
    "target_url": "https://www.baidu.com",
    "enabled": true
  },
  "youtube_to_bilibili": {
    "source_pattern": "youtube",
    "target_url": "https://www.bilibili.com",
    "enabled": true
  }
}
```

每条规则包含以下字段：
- `source_pattern`: 源URL匹配模式，只要URL中包含此字符串就会触发重定向
- `target_url`: 重定向的目标URL
- `enabled`: 是否启用此规则

## 自动重定向功能

我们实现了两种重定向方式：

### 1. 自动重定向

浏览器启动时会自动加载重定向规则，并在用户访问匹配的网站时自动重定向。这是通过以下机制实现的：

- 在`browser_manager.py`的`initialize`方法中集成了自动重定向功能
- 使用`auto_redirect.py`模块为每个浏览器标签页注入JavaScript监听脚本
- 监听脚本会检测URL变化并根据规则自动重定向

### 2. 手动重定向

您也可以通过API手动触发重定向：

```python
from utils.page_redirect_manager import redirect_manager

# 对指定标签页应用重定向规则
redirect_manager.apply_rule(tab, "https://www.google.com", wait_time=3.0)

# 或者通过BrowserOperator进行重定向
browser_operator.redirect_user_page(user_id, "google_to_baidu")
```

## 常见问题排查

如果重定向功能不正常工作，请检查以下几点：

1. **规则匹配问题**：确保`source_pattern`足够通用，能匹配到目标URL
   - 例如，使用`google`而不是`google.com`，以便匹配`www.google.com`等变体

2. **规则启用状态**：确保规则的`enabled`字段设置为`true`

3. **浏览器启动**：确保浏览器正常启动并加载了自动重定向模块

4. **JavaScript执行**：检查浏览器控制台是否有JavaScript错误

## 测试脚本

项目提供了几个测试脚本来验证重定向功能：

- `examples/test_modified_rules.py`: 测试修改后的重定向规则
- `examples/test_auto_redirect.py`: 测试自动重定向功能
- `examples/test_redirect_rule_matching.py`: 测试规则匹配逻辑

运行测试脚本：

```bash
python examples/test_auto_redirect.py
```

## 自定义重定向规则

您可以通过编辑`redirect_rules.json`文件来添加、修改或删除重定向规则。修改后的规则将在下次浏览器启动时自动加载。

## 高级用法

### 条件重定向

您可以使用`PageRedirectManager`的`add_conditional_rule`方法添加带条件的重定向规则：

```python
from utils.page_redirect_manager import redirect_manager

# 添加条件重定向规则
def condition_func(tab):
    # 检查页面内容或其他条件
    return "特定内容" in tab.html

redirect_manager.add_conditional_rule(
    "conditional_rule",
    "example.com",
    "https://target.com",
    condition_func
)
```

### 批量重定向

您可以使用`BrowserOperator`的`batch_redirect_users`方法批量应用重定向规则：

```python
from browser.browser_operator import BrowserOperator

browser_operator = BrowserOperator()
browser_operator.batch_redirect_users(["user1", "user2"], "google_to_baidu")
```

## 更多信息

有关重定向功能的更多示例和用法，请参考以下文件：

- `redirect_demo.py`: 在实际浏览器环境中应用重定向规则的演示
- `redirect_demo_simple.py`: 重定向功能的基本演示
- `utils/page_redirect_manager.py`: 重定向管理器的核心实现
- `browser/auto_redirect.py`: 自动重定向功能的实现