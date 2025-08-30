from PyQt6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollBar
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QSize, QTimer
from PyQt6.QtGui import (
    QFont, QPainter, QColor, QTextCursor, QTextCharFormat, 
    QSyntaxHighlighter, QTextDocument, QPalette, QFontMetrics
)
from ..config import THEMES, CURRENT_THEME, FONTS, LAYOUT
import re


class LineNumberArea(QWidget):
    """行号显示区域"""
    
    def __init__(self, editor):
        """初始化行号区域
        
        Args:
            editor: 文本编辑器实例
        """
        super().__init__(editor)
        self.editor = editor
        self.theme = THEMES[CURRENT_THEME]
    
    def sizeHint(self):
        """返回建议大小"""
        return QSize(self.editor.lineNumberAreaWidth(), 0)
    
    def paintEvent(self, event):
        """绘制行号"""
        self.editor.lineNumberAreaPaintEvent(event)


class PythonHighlighter(QSyntaxHighlighter):
    """Python语法高亮器"""
    
    def __init__(self, parent=None):
        """初始化语法高亮器
        
        Args:
            parent: 父文档
        """
        super().__init__(parent)
        self.theme = THEMES[CURRENT_THEME]
        self._setup_highlighting_rules()
    
    def _setup_highlighting_rules(self):
        """设置高亮规则"""
        self.highlighting_rules = []
        
        # 关键字格式
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self.theme['primary']))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
            'while', 'with', 'yield', 'None', 'True', 'False'
        ]
        
        for keyword in keywords:
            pattern = f'\\b{keyword}\\b'
            self.highlighting_rules.append((re.compile(pattern), keyword_format))
        
        # 字符串格式
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self.theme['success']))
        self.highlighting_rules.append((re.compile('".*"'), string_format))
        self.highlighting_rules.append((re.compile("'.*'"), string_format))
        
        # 注释格式
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self.theme['text_secondary']))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((re.compile('#[^\n]*'), comment_format))
        
        # 数字格式
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(self.theme['warning']))
        self.highlighting_rules.append((re.compile('\\b[0-9]+\\b'), number_format))
        
        # 函数格式
        function_format = QTextCharFormat()
        function_format.setForeground(QColor('#6A9955'))
        function_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((re.compile('\\b[A-Za-z_][A-Za-z0-9_]*(?=\\()'), function_format))
    
    def highlightBlock(self, text):
        """高亮文本块
        
        Args:
            text (str): 要高亮的文本
        """
        for pattern, format_obj in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)


class TextEdit(QWidget):
    """Chrome风格文本编辑器组件
    
    具有现代化外观的文本编辑器，支持语法高亮、行号显示、
    搜索功能和主题样式。适用于代码编辑和文本处理。
    """
    
    # 文本变化信号
    textChanged = pyqtSignal()
    # 光标位置变化信号
    cursorPositionChanged = pyqtSignal(int, int)  # line, column
    
    def __init__(self, parent=None, show_line_numbers=False, syntax_highlighting=True, auto_save_callback=None, auto_save_delay=2000):
        """初始化文本编辑器
        
        Args:
            parent: 父组件
            show_line_numbers (bool): 是否显示行号
            syntax_highlighting (bool): 是否启用语法高亮
            auto_save_callback: 自动保存回调函数
            auto_save_delay (int): 自动保存延迟时间（毫秒）
        """
        super().__init__(parent)
        self.theme = THEMES[CURRENT_THEME]
        self.show_line_numbers = show_line_numbers
        self.syntax_highlighting = syntax_highlighting
        self.auto_save_callback = auto_save_callback
        self.auto_save_delay = auto_save_delay
        
        # 自动保存定时器
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self._perform_auto_save)
        
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        
        if syntax_highlighting:
            self.highlighter = PythonHighlighter(self.text_edit.document())
    
    def _setup_ui(self):
        """设置UI布局"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(False)
        
        # 设置字体
        font = QFont()
        font.setFamily("Monaco, Consolas, 'Courier New', monospace")
        font.setPointSize(12)
        self.text_edit.setFont(font)
        
        if self.show_line_numbers:
            # 创建行号区域
            self.line_number_area = LineNumberArea(self)
            layout.addWidget(self.line_number_area)
        
        layout.addWidget(self.text_edit)
        
        # 更新行号区域宽度
        if self.show_line_numbers:
            self.updateLineNumberAreaWidth()
    
    def _apply_styles(self):
        """应用样式"""
        # 文本编辑器样式
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['card_border']};
                border-radius: {LAYOUT['border_radius']}px;
                padding: 8px;
                selection-background-color: {self.theme['primary']};
                selection-color: white;
            }}
            
            QTextEdit:focus {{
                border-color: {self.theme['primary']};
                outline: none;
            }}
            
            QScrollBar:vertical {{
                background-color: {self.theme['card']};
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.theme['text_secondary']};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {self.theme['text']};
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {self.theme['card']};
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {self.theme['text_secondary']};
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {self.theme['text']};
            }}
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)
        
        # 行号区域样式
        if self.show_line_numbers:
            self.line_number_area.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.theme['card']};
                    border: 1px solid {self.theme['card_border']};
                    border-right: none;
                    border-top-left-radius: {LAYOUT['border_radius']}px;
                    border-bottom-left-radius: {LAYOUT['border_radius']}px;
                }}
            """)
    
    def _connect_signals(self):
        """连接信号"""
        self.text_edit.textChanged.connect(self.textChanged.emit)
        self.text_edit.cursorPositionChanged.connect(self._on_cursor_position_changed)
        
        # 连接自动保存信号
        if self.auto_save_callback:
            self.text_edit.textChanged.connect(self._on_text_changed_for_auto_save)
        
        if self.show_line_numbers:
            self.text_edit.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
            self.text_edit.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)
            self.text_edit.textChanged.connect(self._on_text_changed)
    
    def _on_cursor_position_changed(self):
        """光标位置变化处理"""
        cursor = self.text_edit.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.cursorPositionChanged.emit(line, column)
    
    def _on_scroll_changed(self):
        """滚动条变化处理"""
        if self.show_line_numbers:
            self.line_number_area.update()
    
    def _on_text_changed(self):
        """文本变化处理"""
        if self.show_line_numbers:
            self.line_number_area.update()
    
    def _on_text_changed_for_auto_save(self):
        """文本变化时的自动保存处理"""
        if self.auto_save_callback:
            # 重启定时器
            self.auto_save_timer.stop()
            self.auto_save_timer.start(self.auto_save_delay)
    
    def _perform_auto_save(self):
        """执行自动保存"""
        if self.auto_save_callback:
            try:
                current_text = self.text_edit.toPlainText()
                self.auto_save_callback(current_text)
            except Exception as e:
                print(f"自动保存失败: {e}")
    
    def set_auto_save_callback(self, callback, delay=2000):
        """设置自动保存回调函数
        
        Args:
            callback: 自动保存回调函数，接收当前文本内容作为参数
            delay: 自动保存延迟时间（毫秒），默认2秒
        """
        # 断开旧的连接
        if self.auto_save_callback:
            self.text_edit.textChanged.disconnect(self._on_text_changed_for_auto_save)
        
        self.auto_save_callback = callback
        self.auto_save_delay = delay
        
        # 连接新的回调
        if callback:
            self.text_edit.textChanged.connect(self._on_text_changed_for_auto_save)
    
    def force_save(self):
        """强制立即保存"""
        self.auto_save_timer.stop()
        self._perform_auto_save()
    
    def lineNumberAreaWidth(self):
        """计算行号区域宽度
        
        Returns:
            int: 行号区域宽度
        """
        if not self.show_line_numbers:
            return 0
        
        digits = len(str(max(1, self.text_edit.document().blockCount())))
        space = 3 + self.text_edit.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def updateLineNumberAreaWidth(self):
        """更新行号区域宽度"""
        if self.show_line_numbers:
            self.line_number_area.setFixedWidth(self.lineNumberAreaWidth())
    
    def updateLineNumberArea(self, rect, dy):
        """更新行号区域
        
        Args:
            rect: 更新区域
            dy: 垂直偏移
        """
        if not self.show_line_numbers:
            return
        
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.text_edit.viewport().rect()):
            self.updateLineNumberAreaWidth()
    
    def lineNumberAreaPaintEvent(self, event):
        """绘制行号区域
        
        Args:
            event: 绘制事件
        """
        if not self.show_line_numbers:
            return
        
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(self.theme['card']))
        
        # 获取文档和字体信息
        document = self.text_edit.document()
        font = self.text_edit.font()
        font_metrics = self.text_edit.fontMetrics()
        line_height = font_metrics.height()
        
        # 设置行号字体和颜色
        painter.setFont(font)
        painter.setPen(QColor(self.theme['text_secondary']))
        
        # 计算可见区域的行号范围
        viewport_rect = self.text_edit.viewport().rect()
        scroll_y = self.text_edit.verticalScrollBar().value()
        
        first_visible_line = max(0, scroll_y // line_height)
        last_visible_line = min(document.blockCount() - 1, 
                               (scroll_y + viewport_rect.height()) // line_height + 1)
        
        # 绘制行号
        for line_num in range(first_visible_line, last_visible_line + 1):
            y = (line_num * line_height) - scroll_y + line_height
            if y >= event.rect().top() and y <= event.rect().bottom():
                number = str(line_num + 1)
                painter.drawText(0, y - line_height, self.line_number_area.width() - 3, 
                               line_height, Qt.AlignmentFlag.AlignRight, number)

    
    def resizeEvent(self, event):
        """窗口大小变化事件
        
        Args:
            event: 大小变化事件
        """
        super().resizeEvent(event)
        
        if self.show_line_numbers:
            cr = self.contentsRect()
            self.line_number_area.setGeometry(
                QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
            )
    
    def setPlainText(self, text):
        """设置纯文本
        
        Args:
            text (str): 文本内容
        """
        # 临时断开自动保存信号连接，避免触发自动保存
        if self.auto_save_callback:
            self.text_edit.textChanged.disconnect(self._on_text_changed_for_auto_save)
        
        self.text_edit.setPlainText(text)
        
        # 重新连接信号
        if self.auto_save_callback:
            self.text_edit.textChanged.connect(self._on_text_changed_for_auto_save)
    
    def toPlainText(self):
        """获取纯文本
        
        Returns:
            str: 文本内容
        """
        return self.text_edit.toPlainText()
    
    def insertPlainText(self, text):
        """插入纯文本
        
        Args:
            text (str): 要插入的文本
        """
        self.text_edit.insertPlainText(text)
    
    def clear(self):
        """清空文本"""
        self.text_edit.clear()
    
    def setReadOnly(self, read_only):
        """设置只读模式
        
        Args:
            read_only (bool): 是否只读
        """
        self.text_edit.setReadOnly(read_only)
    
    def isReadOnly(self):
        """获取是否只读
        
        Returns:
            bool: 是否只读
        """
        return self.text_edit.isReadOnly()
    
    def setFont(self, font):
        """设置字体
        
        Args:
            font (QFont): 字体对象
        """
        self.text_edit.setFont(font)
        if self.show_line_numbers:
            self.updateLineNumberAreaWidth()
    
    def set_text(self, text):
        """设置文本内容
        
        Args:
            text (str): 文本内容
        """
        # 临时断开自动保存信号连接，避免触发自动保存
        if self.auto_save_callback:
            self.text_edit.textChanged.disconnect(self._on_text_changed_for_auto_save)
        
        self.text_edit.setPlainText(text)
        
        # 重新连接信号
        if self.auto_save_callback:
            self.text_edit.textChanged.connect(self._on_text_changed_for_auto_save)
    
    def font(self):
        """获取字体
        
        Returns:
            QFont: 字体对象
        """
        return self.text_edit.font()
    
    def find(self, text, flags=None):
        """查找文本
        
        Args:
            text (str): 要查找的文本
            flags: 查找标志
            
        Returns:
            bool: 是否找到
        """
        if flags is None:
            flags = QTextDocument.FindFlag(0)
        return self.text_edit.find(text, flags)
    
    def selectAll(self):
        """选择全部文本"""
        self.text_edit.selectAll()
    
    def copy(self):
        """复制选中文本"""
        self.text_edit.copy()
    
    def cut(self):
        """剪切选中文本"""
        self.text_edit.cut()
    
    def paste(self):
        """粘贴文本"""
        self.text_edit.paste()
    
    def undo(self):
        """撤销操作"""
        self.text_edit.undo()
    
    def redo(self):
        """重做操作"""
        self.text_edit.redo()