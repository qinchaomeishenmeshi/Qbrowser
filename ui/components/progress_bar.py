from PyQt6.QtWidgets import QProgressBar, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPainter, QLinearGradient, QColor, QPen
from ..config import THEMES, CURRENT_THEME, FONTS, LAYOUT, ANIMATIONS


class ProgressBar(QWidget):
    """Chrome风格进度条组件
    
    具有现代化外观的进度条组件，支持动画效果、文本显示和主题样式。
    可以显示进度百分比和自定义状态文本。
    """
    
    # 进度变化信号
    value_changed = pyqtSignal(int)
    # 完成信号
    finished = pyqtSignal()
    
    def __init__(self, parent=None):
        """初始化进度条
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.theme = THEMES[CURRENT_THEME]
        self._value = 0
        self._maximum = 100
        self._minimum = 0
        self._text_visible = True
        self._status_text = ""
        self._variant = "primary"  # primary, success, warning, error
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI布局"""
        self.setFixedHeight(24)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 状态文本标签
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.hide()  # 默认隐藏
        
        # 设置状态文本字体
        font = QFont()
        font.setFamily(FONTS["small"][0])
        font.setPointSize(FONTS["small"][1])
        self.status_label.setFont(font)
        
        # 进度条容器
        self.progress_container = QWidget()
        self.progress_container.setFixedHeight(8)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_container)
    
    def _apply_styles(self):
        """应用样式"""
        # 设置容器样式
        self.progress_container.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme['card_border']};
                border-radius: 4px;
            }}
        """)
        
        # 设置状态文本颜色
        self.status_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
    
    def paintEvent(self, event):
        """自定义绘制进度条"""
        super().paintEvent(event)
        
        if self._maximum <= self._minimum:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算进度条区域
        container_rect = self.progress_container.geometry()
        progress_width = int((self._value - self._minimum) / (self._maximum - self._minimum) * container_rect.width())
        
        if progress_width > 0:
            # 获取进度条颜色
            progress_color = self._get_progress_color()
            
            # 创建渐变
            gradient = QLinearGradient(container_rect.left(), container_rect.top(), 
                                     container_rect.right(), container_rect.bottom())
            gradient.setColorAt(0, QColor(progress_color))
            gradient.setColorAt(1, self._lighten_color(progress_color, 0.2))
            
            # 绘制进度条
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            
            progress_rect = container_rect.adjusted(0, 0, progress_width - container_rect.width(), 0)
            painter.drawRoundedRect(progress_rect, 4, 4)
        
        # 绘制百分比文本（如果启用）
        if self._text_visible and self._maximum > self._minimum:
            percentage = int((self._value - self._minimum) / (self._maximum - self._minimum) * 100)
            text = f"{percentage}%"
            
            # 设置文本样式
            painter.setPen(QPen(QColor(self.theme['text'])))
            font = QFont()
            font.setFamily(FONTS["small"][0])
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)
            
            # 计算文本位置
            text_rect = container_rect
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
    
    def _get_progress_color(self):
        """获取进度条颜色
        
        Returns:
            str: 颜色字符串
        """
        variant_colors = {
            "primary": self.theme['primary'],
            "success": self.theme['success'],
            "warning": self.theme['warning'],
            "error": self.theme['error']
        }
        return variant_colors.get(self._variant, self.theme['primary'])
    
    def _lighten_color(self, color_str, factor):
        """使颜色变亮
        
        Args:
            color_str (str): 颜色字符串
            factor (float): 变亮因子 (0-1)
            
        Returns:
            QColor: 变亮后的颜色对象
        """
        color = QColor(color_str)
        h, s, l, a = color.getHsl()
        l = min(255, int(l + (255 - l) * factor))
        color.setHsl(h, s, l, a)
        return color
    
    def setValue(self, value):
        """设置进度值
        
        Args:
            value (int): 进度值
        """
        value = max(self._minimum, min(self._maximum, value))
        if value != self._value:
            self._value = value
            self.update()
            self.value_changed.emit(value)
            
            # 检查是否完成
            if value >= self._maximum:
                self.finished.emit()
    
    def value(self):
        """获取当前进度值
        
        Returns:
            int: 当前进度值
        """
        return self._value
    
    def setMaximum(self, maximum):
        """设置最大值
        
        Args:
            maximum (int): 最大值
        """
        self._maximum = maximum
        self.update()
    
    def maximum(self):
        """获取最大值
        
        Returns:
            int: 最大值
        """
        return self._maximum
    
    def setMinimum(self, minimum):
        """设置最小值
        
        Args:
            minimum (int): 最小值
        """
        self._minimum = minimum
        self.update()
    
    def minimum(self):
        """获取最小值
        
        Returns:
            int: 最小值
        """
        return self._minimum
    
    def setRange(self, minimum, maximum):
        """设置范围
        
        Args:
            minimum (int): 最小值
            maximum (int): 最大值
        """
        self._minimum = minimum
        self._maximum = maximum
        self.update()
    
    def setTextVisible(self, visible):
        """设置文本是否可见
        
        Args:
            visible (bool): 是否显示文本
        """
        self._text_visible = visible
        self.update()
    
    def isTextVisible(self):
        """获取文本是否可见
        
        Returns:
            bool: 文本是否可见
        """
        return self._text_visible
    
    def setStatusText(self, text):
        """设置状态文本
        
        Args:
            text (str): 状态文本
        """
        self._status_text = text
        self.status_label.setText(text)
        
        if text:
            self.status_label.show()
        else:
            self.status_label.hide()
    
    def statusText(self):
        """获取状态文本
        
        Returns:
            str: 状态文本
        """
        return self._status_text
    
    def setVariant(self, variant):
        """设置进度条样式变体
        
        Args:
            variant (str): 样式变体 - "primary", "success", "warning", "error"
        """
        self._variant = variant
        self.update()
    
    def variant(self):
        """获取当前样式变体
        
        Returns:
            str: 样式变体
        """
        return self._variant
    
    def reset(self):
        """重置进度条"""
        self.setValue(self._minimum)
        self.setStatusText("")
    
    def setProgress(self, value, status_text=""):
        """设置进度和状态文本
        
        Args:
            value (int): 进度值
            status_text (str): 状态文本
        """
        self.setValue(value)
        if status_text:
            self.setStatusText(status_text)