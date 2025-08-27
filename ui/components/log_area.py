from PyQt6.QtWidgets import QTextEdit, QScrollBar, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCursor
from ..config import THEMES, CURRENT_THEME, FONTS, LAYOUT


class LogArea(QTextEdit):
    """日志显示区域组件
    
    具有Chrome风格外观的文本显示区域，用于显示日志信息。
    支持自动滚动、文本格式化和主题样式。
    """
    
    # 日志更新信号
    log_updated = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """初始化日志区域
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.theme = THEMES[CURRENT_THEME]
        self._max_lines = 1000  # 最大行数限制
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI属性"""
        # 设置为只读
        self.setReadOnly(True)
        
        # 设置字体
        font = QFont()
        font.setFamily(FONTS["mono"][0])  # 使用等宽字体
        font.setPointSize(FONTS["mono"][1])
        self.setFont(font)
        
        # 设置文本换行
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # 设置滚动条策略
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    def _apply_styles(self):
        """应用样式"""
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)
        
        # 设置主体样式
        self.setStyleSheet(f"""
            LogArea {{
                background-color: {self.theme['card']};
                border: 1px solid {self.theme['card_border']};
                border-radius: {LAYOUT['border_radius']}px;
                padding: 12px;
                color: {self.theme['text']};
                selection-background-color: {self.theme['primary']};
                selection-color: {self.theme['text_light']};
            }}
            
            /* 滚动条样式 */
            QScrollBar:vertical {{
                background-color: {self.theme['background']};
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.theme['card_border']};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.theme['text_tertiary']};
            }}
            
            QScrollBar::handle:vertical:pressed {{
                background-color: {self.theme['text_secondary']};
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            
            /* 水平滚动条 */
            QScrollBar:horizontal {{
                background-color: {self.theme['background']};
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {self.theme['card_border']};
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {self.theme['text_tertiary']};
            }}
            
            QScrollBar::handle:horizontal:pressed {{
                background-color: {self.theme['text_secondary']};
            }}
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: transparent;
            }}
        """)
    
    def append_log(self, message, level="info"):
        """添加日志消息
        
        Args:
            message (str): 日志消息
            level (str): 日志级别 - "info", "warning", "error", "success"
        """
        # 获取日志级别对应的颜色
        color = self._get_level_color(level)
        
        # 格式化消息
        formatted_message = self._format_message(message, level, color)
        
        # 移动光标到末尾
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
        
        # 插入格式化的消息
        self.insertHtml(formatted_message)
        
        # 限制行数
        self._limit_lines()
        
        # 自动滚动到底部
        self.scroll_to_bottom()
        
        # 发射信号
        self.log_updated.emit(message)
    
    def _get_level_color(self, level):
        """获取日志级别对应的颜色
        
        Args:
            level (str): 日志级别
            
        Returns:
            str: 颜色字符串
        """
        level_colors = {
            "info": self.theme['info'],
            "warning": self.theme['warning'],
            "error": self.theme['error'],
            "success": self.theme['success'],
            "debug": self.theme['text_secondary']
        }
        return level_colors.get(level, self.theme['text'])
    
    def _format_message(self, message, level, color):
        """格式化日志消息
        
        Args:
            message (str): 原始消息
            level (str): 日志级别
            color (str): 颜色
            
        Returns:
            str: 格式化后的HTML消息
        """
        from datetime import datetime
        
        # 获取当前时间
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 格式化级别标签
        level_label = level.upper().ljust(7)
        
        # 构建HTML格式的消息
        html_message = f"""
        <div style="margin-bottom: 2px;">
            <span style="color: {self.theme['text_tertiary']}; font-size: 11px;">[{timestamp}]</span>
            <span style="color: {color}; font-weight: bold; font-size: 11px;">[{level_label}]</span>
            <span style="color: {self.theme['text']}; margin-left: 8px;">{message}</span>
        </div>
        """
        
        return html_message
    
    def _limit_lines(self):
        """限制文本行数"""
        document = self.document()
        if document.blockCount() > self._max_lines:
            # 删除开头的行
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            
            # 计算需要删除的行数
            lines_to_remove = document.blockCount() - self._max_lines
            
            for _ in range(lines_to_remove):
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # 删除换行符
    
    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """清空日志"""
        self.clear()
        self.log_updated.emit("日志已清空")
    
    def set_max_lines(self, max_lines):
        """设置最大行数限制
        
        Args:
            max_lines (int): 最大行数
        """
        self._max_lines = max_lines
    
    def get_log_text(self):
        """获取纯文本日志内容
        
        Returns:
            str: 纯文本日志内容
        """
        return self.toPlainText()
    
    def save_logs_to_file(self, file_path):
        """保存日志到文件
        
        Args:
            file_path (str): 文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.get_log_text())
            self.append_log(f"日志已保存到: {file_path}", "success")
        except Exception as e:
            self.append_log(f"保存日志失败: {str(e)}", "error")