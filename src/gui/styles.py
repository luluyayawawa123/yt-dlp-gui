# 颜色主题
COLORS = {
    'background': '#F8F8F8',
    'text': '#333333',
    'primary': '#4CAF50',  # 更改为更柔和的绿色
    'border': '#E0E0E0',
    'success': '#32CD32',      # 成功状态
    'warning': '#FFA500',      # 警告状态
    'error': '#FF0000',        # 错误状态
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
    border: 1px solid #DDDDDD;  /* 默认细边框，使用柔和的浅灰色 */
    border-radius: 6px;         /* 更大的圆角，更现代的感觉 */
    padding: 4px 8px;
    background-color: white;
    color: #333333;
}

QTextEdit:focus {              /* 只修改 QTextEdit 的焦点状态 */
    border: 2px solid #999999; /* 焦点时粗边框，使用更深的灰色 */
    padding: 3px 7px;         /* 减少1px内边距补偿边框增加的1px */
}

QLineEdit:focus, QComboBox:focus {  /* 保持其他输入框的原有样式 */
    border: 1px solid #666666;
}

QComboBox {
    min-height: 20px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw1IDVMOSAxIiBzdHJva2U9IiM2NjY2NjYiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
    width: 10px;
    height: 6px;
}

QComboBox:hover {
    border: 1px solid #999999;
}

QComboBox QAbstractItemView {
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    background-color: white;
    padding: 2px;
}

QComboBox QAbstractItemView::item {
    height: 24px;
    padding-left: 8px;
    padding-right: 8px;
    border: none;
    color: #333333;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #EBEBEB;
    color: #333333;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #E8E8E8;
    color: #333333;
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
    padding: 0px 2px;
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

# 复选框样式 - 极简风格
CHECKBOX_STYLE = """
    QCheckBox {
        color: #333333;
        spacing: 5px;
        font-size: 13px;
    }
    QCheckBox::indicator {
        width: 0px;
        height: 0px;
        background-color: transparent;
    }
""" 