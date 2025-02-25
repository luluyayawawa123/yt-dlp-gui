# 颜色主题
COLORS = {
    'primary': '#666666',      # 主色调
    'success': '#32CD32',      # 成功状态
    'warning': '#FFA500',      # 警告状态
    'error': '#FF0000',        # 错误状态
    'background': '#FFFFFF',   # 背景色
    'text': '#333333',         # 主文本色
    'text_secondary': '#666666'  # 次要文本色
}

# 按钮样式
BUTTON_STYLE = """
QPushButton {
    background-color: #F5F5F5;
    color: #333333;
    border: 1px solid #E0E0E0;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #EBEBEB;
}
QPushButton:pressed {
    background-color: #E0E0E0;
}
QPushButton:disabled {
    background-color: #CCCCCC;
    color: #999999;
    border-color: #CCCCCC;
}
"""

# 进度条样式
PROGRESS_BAR_STYLE = """
QProgressBar {
    border: none;
    background-color: #F5F5F5;
    border-radius: 1px;
    text-align: center;
    height: 2px;
    margin-top: 2px;
    margin-bottom: 2px;
}
QProgressBar::chunk {
    background-color: #666666;
    border-radius: 1px;
}
"""

# 输入框和下拉框通用样式
INPUT_STYLE = """
QLineEdit, QTextEdit, QComboBox {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 8px;
    background-color: white;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 2px solid #666666;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    border: none;
    background: none;
    color: #666666;
}
QComboBox:hover {
    background-color: #F5F5F5;
}
QComboBox QAbstractItemView {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    background-color: white;
    selection-background-color: #F5F5F5;
    selection-color: #333333;
    padding: 4px;
}
QComboBox QAbstractItemView::item {
    padding: 6px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #F5F5F5;
}
"""

# 历史记录项样式
HISTORY_ITEM_STYLE = """
QWidget#historyItem {
    background-color: transparent;
    border-radius: 0px;
    padding: 8px 6px;
}
QWidget#historyItem:hover {
    background-color: rgba(0, 0, 0, 0.02);
}
"""

# 通用滚动条样式
SCROLLBAR_STYLE = """
QScrollBar:vertical {
    border: none;
    background: #F0F0F0;
    width: 8px;
    border-radius: 4px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: #CCCCCC;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

# 历史区域样式
HISTORY_AREA_STYLE = """
QScrollArea {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    background-color: white;
    padding: 2px;
}
""" + SCROLLBAR_STYLE

# 标签样式
LABEL_STYLE = """
QLabel {
    color: #333333;
    padding: 2px;
}
"""

# 提示文本样式
TIP_STYLE = """
QLabel {
    color: #666666;
    font-size: 12px;
    padding: 2px;
}
"""

# 浏览按钮样式（新增）
BROWSE_BUTTON_STYLE = """
QPushButton {
    background-color: #F5F5F5;
    color: #333333;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #EBEBEB;
}
QPushButton:pressed {
    background-color: #E0E0E0;
}
"""

# 下载任务区域样式
TASK_AREA_STYLE = """
QWidget#taskArea {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 2px;
}
"""

# 边框容器样式
BORDER_CONTAINER_STYLE = """
QWidget#borderContainer {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
}
"""

# 下载任务滚动区域样式
TASK_SCROLL_AREA_STYLE = """
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
""" + SCROLLBAR_STYLE

# 任务容器样式
TASK_CONTAINER_STYLE = """
QWidget#taskArea {
    background: transparent;
}
"""

# 单个任务项样式
TASK_ITEM_STYLE = """
QWidget#taskItem {
    background-color: transparent;
    padding: 6px 6px;
}
QWidget#taskItem:last-child {
    border-bottom: none;
}
"""

# 清空按钮样式
CLEAR_BUTTON_STYLE = """
QPushButton {
    background-color: #F5F5F5;
    color: #666666;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #EBEBEB;
}
QPushButton:pressed {
    background-color: #E0E0E0;
}
""" 