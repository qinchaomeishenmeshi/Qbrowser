UI_VERSION = "2.0.0"

# 主题配色
THEMES = {
    "light": {
        # 主要颜色
        "primary": "#0078D7",  # 微软蓝，更现代的蓝色
        "secondary": "#374151",  # 深灰蓝，现代科技感
        "accent": "#03DAC6",  # 现代科技青色
        "accent_secondary": "#6B46C1",  # 科技紫色
        # 背景和卡片
        "background": "#F9FAFB",  # 更加轻盈的背景色
        "card": "#FFFFFF",  # 白色卡片
        "card_hover": "#F5F9FF",  # 卡片悬停效果
        "card_border": "#E5E7EB",  # 卡片边框
        # 功能色
        "success": "#10B981",  # 更现代的绿色
        "warning": "#F59E0B",  # 更现代的橙色
        "error": "#EF4444",  # 更现代的红色
        "info": "#3B82F6",  # 信息蓝
        "inactive": "#9CA3AF",  # 不活跃灰色
        # 文本颜色
        "text": "#1F2937",  # 主文本颜色
        "text_secondary": "#6B7280",  # 次要文本颜色
        "text_tertiary": "#9CA3AF",  # 第三级文本颜色
        "text_light": "#FFFFFF",  # 亮色文本
        # 其他UI元素
        "divider": "#E5E7EB",  # 分隔线
        "focus": "#3B82F6",  # 焦点边框
        "shadow": "rgba(0, 0, 0, 0.1)",  # 阴影颜色
    },
    "dark": {
        # 主要颜色
        "primary": "#0EA5E9",  # 亮蓝色
        "secondary": "#334155",  # 深蓝灰
        "accent": "#22D3EE",  # 科技青色
        "accent_secondary": "#8B5CF6",  # 科技紫色
        # 背景和卡片
        "background": "#111827",  # 深色背景
        "card": "#1F2937",  # 卡片背景
        "card_hover": "#263146",  # 卡片悬停效果
        "card_border": "#374151",  # 卡片边框
        # 功能色
        "success": "#34D399",  # 深色模式绿色
        "warning": "#FBBF24",  # 深色模式橙色
        "error": "#F87171",  # 深色模式红色
        "info": "#60A5FA",  # 深色模式信息蓝
        "inactive": "#6B7280",  # 深色模式不活跃色
        # 文本颜色
        "text": "#F9FAFB",  # 主文本颜色
        "text_secondary": "#D1D5DB",  # 次要文本颜色
        "text_tertiary": "#9CA3AF",  # 第三级文本颜色
        "text_light": "#FFFFFF",  # 亮色文本
        # 其他UI元素
        "divider": "#374151",  # 分隔线
        "focus": "#60A5FA",  # 焦点边框
        "shadow": "rgba(0, 0, 0, 0.3)",  # 阴影颜色
    },
}

# 当前主题
CURRENT_THEME = "light"

# 字体设置 - 使用Chrome浏览器风格的字体方案
FONTS = {
    # 使用和Chrome浏览器类似的字体堆栈
    "regular": (
        "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'WenQuanYi Micro Hei', Arial, sans-serif",
        12,
    ),
    "bold": (
        "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'WenQuanYi Micro Hei', Arial, sans-serif",
        12,
        "bold",
    ),
    "title": (
        "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'WenQuanYi Micro Hei', Arial, sans-serif",
        16,
        "bold",
    ),
    "heading": (
        "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'WenQuanYi Micro Hei', Arial, sans-serif",
        14,
        "bold",
    ),
    "small": (
        "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'WenQuanYi Micro Hei', Arial, sans-serif",
        10,
    ),
    # 等宽字体
    "mono": (
        "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
        12,
    ),
}

# 布局常量
LAYOUT = {
    "spacing": 6,  # 默认间距
    "margin": 10,  # 默认边距
    "border_radius": 8,  # 默认圆角
    "sidebar_width": 220,  # 侧边栏宽度（优化比例）
    "sidebar_padding": 6,  # 侧边栏内边距
    "sidebar_margin": 10,  # 侧边栏外边距
    "nav_button_height": 44,  # 导航按钮高度
    "nav_button_spacing": 4,  # 导航按钮间距
    "card_padding": 12,  # 卡片内边距
    "icon_size": 16,  # 图标默认大小
    "glass_blur_radius": 20,  # 磨砂玻璃模糊半径
    "glass_opacity": 0.85,  # 磨砂玻璃透明度
}

# 动画配置
ANIMATIONS = {
    "transition_duration": 150,  # 默认过渡动画时长(毫秒)
    "hover_duration": 100,  # 悬停动画时长(毫秒)
}
