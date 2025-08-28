UI_VERSION = "2.0.0"

# 主题配色 - Chrome风格重新设计
THEMES = {
    "light": {
        # Chrome浏览器原生配色
        "primary": "#1a73e8",  # Chrome蓝色
        "secondary": "#5f6368",  # Chrome次要灰色
        "accent": "#34a853",  # Chrome绿色
        "accent_secondary": "#ea4335",  # Chrome红色
        # 背景和表面
        "background": "#ffffff",  # 纯白背景
        "surface": "#f8f9fa",  # 表面颜色
        "surface_variant": "#e3f2fd",  # 表面变体
        "card": "#ffffff",  # 卡片背景
        "card_hover": "#f8f9fa",  # 卡片悬停
        "card_border": "#dadce0",  # Chrome边框颜色
        # Chrome标准功能色
        "success": "#137333",  # Chrome成功绿
        "warning": "#f9ab00",  # Chrome警告黄
        "error": "#d93025",  # Chrome错误红
        "info": "#1a73e8",  # Chrome信息蓝
        "inactive": "#9aa0a6",  # Chrome不活跃色
        # Chrome文本颜色层级
        "text": "#202124",  # Chrome主文本
        "text_secondary": "#5f6368",  # Chrome次要文本
        "text_tertiary": "#80868b",  # Chrome第三级文本
        "text_light": "#ffffff",  # 白色文本
        "text_disabled": "#9aa0a6",  # 禁用文本
        # Chrome界面元素
        "divider": "#e8eaed",  # Chrome分隔线
        "focus": "#1a73e8",  # Chrome焦点色
        "shadow": "rgba(60, 64, 67, 0.15)",  # Chrome阴影
        "outline": "#1a73e8",  # Chrome轮廓色
        # Chrome工具栏
        "toolbar": "#ffffff",  # 工具栏背景
        "toolbar_border": "#dadce0",  # 工具栏边框
        # Chrome标签页
        "tab_active": "#ffffff",  # 活跃标签页
        "tab_inactive": "#f1f3f4",  # 非活跃标签页
        "tab_hover": "#e8f0fe",  # 标签页悬停
    },
    "dark": {
        # Chrome深色模式配色
        "primary": "#8ab4f8",  # Chrome深色蓝
        "secondary": "#9aa0a6",  # Chrome深色次要色
        "accent": "#81c995",  # Chrome深色绿
        "accent_secondary": "#f28b82",  # Chrome深色红
        # 深色背景和表面
        "background": "#202124",  # Chrome深色背景
        "surface": "#292a2d",  # Chrome深色表面
        "surface_variant": "#35363a",  # 深色表面变体
        "card": "#292a2d",  # 深色卡片
        "card_hover": "#35363a",  # 深色卡片悬停
        "card_border": "#5f6368",  # 深色边框
        # Chrome深色功能色
        "success": "#81c995",  # 深色成功绿
        "warning": "#fdd663",  # 深色警告黄
        "error": "#f28b82",  # 深色错误红
        "info": "#8ab4f8",  # 深色信息蓝
        "inactive": "#5f6368",  # 深色不活跃
        # Chrome深色文本
        "text": "#e8eaed",  # Chrome深色主文本
        "text_secondary": "#9aa0a6",  # Chrome深色次要文本
        "text_tertiary": "#5f6368",  # Chrome深色第三级文本
        "text_light": "#ffffff",  # 白色文本
        "text_disabled": "#5f6368",  # 深色禁用文本
        # Chrome深色界面元素
        "divider": "#5f6368",  # Chrome深色分隔线
        "focus": "#8ab4f8",  # Chrome深色焦点色
        "shadow": "rgba(0, 0, 0, 0.3)",  # 深色阴影
        "outline": "#8ab4f8",  # 深色轮廓色
        # Chrome深色工具栏
        "toolbar": "#292a2d",  # 深色工具栏
        "toolbar_border": "#5f6368",  # 深色工具栏边框
        # Chrome深色标签页
        "tab_active": "#292a2d",  # 深色活跃标签页
        "tab_inactive": "#202124",  # 深色非活跃标签页
        "tab_hover": "#35363a",  # 深色标签页悬停
    },
}

# 当前主题
CURRENT_THEME = "light"

# Chrome风格字体系统
FONTS = {
    # Chrome使用的字体堆栈
    "regular": (
        "Roboto, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        13,  # Chrome默认字体大小
    ),
    "medium": (
        "Roboto, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        13,
        "500",  # Medium weight
    ),
    "bold": (
        "Roboto, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        13,
        "700",  # Bold weight
    ),
    "title": (
        "Roboto, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        20,  # Chrome标题大小
        "400",  # Chrome标题通常不加粗
    ),
    "heading": (
        "Roboto, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        16,
        "500",
    ),
    "caption": (
        "Roboto, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        12,
    ),
    "small": (
        "Roboto, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        11,
    ),
    "button": (
        "Roboto, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
        13,
        "500",  # Chrome按钮字体
    ),
    # 等宽字体保持不变
    "mono": (
        "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
        12,
    ),
}

# Chrome风格布局常量
LAYOUT = {
    "spacing": 8,  # Chrome标准间距
    "margin": 16,  # Chrome标准边距
    "border_radius": 4,  # Chrome使用较小的圆角
    "sidebar_width": 256,  # 增加侧边栏宽度
    "sidebar_padding": 12,  # Chrome风格内边距
    "sidebar_margin": 0,  # Chrome风格无外边距
    "nav_button_height": 40,  # Chrome导航按钮高度
    "nav_button_spacing": 0,  # Chrome导航按钮无间距
    "card_padding": 16,  # Chrome卡片内边距
    "icon_size": 20,  # Chrome图标大小
    "toolbar_height": 56,  # Chrome工具栏高度
    "toolbar_padding": 8,  # 工具栏内边距
    # Chrome特有的尺寸
    "button_height": 36,  # Chrome按钮标准高度
    "input_height": 36,  # Chrome输入框高度
    "tab_height": 35,  # Chrome标签页高度
    "menu_item_height": 32,  # Chrome菜单项高度
    "glass_blur_radius": 20,  # 保持兼容性
    "glass_opacity": 0.85,  # 保持兼容性
}

# Chrome风格动画配置
ANIMATIONS = {
    "transition_duration": 200,  # Chrome过渡动画时长
    "hover_duration": 150,  # Chrome悬停动画时长
    "easing": "ease-out",  # Chrome缓动函数
}

# Chrome风格阴影系统
SHADOWS = {
    "none": "none",
    "sm": "0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 1px 3px 1px rgba(60, 64, 67, 0.15)",
    "md": "0 1px 2px 0 rgba(60, 64, 67, 0.3), 0 2px 6px 2px rgba(60, 64, 67, 0.15)",
    "lg": "0 4px 8px 3px rgba(60, 64, 67, 0.15), 0 1px 3px 0 rgba(60, 64, 67, 0.3)",
    "elevation_1": "0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24)",
    "elevation_2": "0px 3px 6px rgba(0, 0, 0, 0.16), 0px 3px 6px rgba(0, 0, 0, 0.23)",
}
