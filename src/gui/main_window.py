from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLineEdit, QPushButton, 
                            QTextEdit, QFileDialog, QLabel, QComboBox,
                            QProgressBar, QSizePolicy, QFrame, QMessageBox,
                            QScrollArea, QMenu, QStyle, QCheckBox)
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QTextCursor
import os
import datetime
from core.downloader import Downloader
from core.config import Config
from gui.advanced_mode import AdvancedModeWidget
import sys
from PyQt6.QtWidgets import QApplication
from .styles import *  # 导入样式

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT-DLP GUI")
        self.setMinimumSize(800, 752)  # 增加 60 像素高度
        # 设置窗口背景色
        self.setStyleSheet(f"background-color: {COLORS['background']};")
        
        # 创建一个永久的中央部件
        self.main_container = QWidget()
        self.setCentralWidget(self.main_container)
        self.main_layout = QVBoxLayout(self.main_container)
        
        # 添加配置和下载器
        self.config = Config()
        self.downloader = Downloader()
        
        # 连接下载器信号
        self.downloader.output_received.connect(self.update_output)
        self.downloader.download_finished.connect(self.download_finished)
        
        # 初始化变量
        self.total_urls = 0
        self.completed_urls = 0
        self.download_tasks = {}
        self.scroll_area = None
        self.current_mode_widget = None  # 添加这行
        
        # 创建基础模式界面
        self.create_basic_mode()
        
        # 从配置加载上次的下载路径
        if 'last_download_path' in self.config.config:
            self.path_input.setText(self.config.config['last_download_path'])
        
        # 检查完全磁盘访问权限
        self.check_full_disk_access()
        
    def create_basic_mode(self):
        try:
            # 保存当前设置
            current_settings = {
                'path': None,
                'browser': None
            }
            
            # 安全地获取当前设置
            try:
                if hasattr(self, 'path_input') and self.path_input and not self.path_input.isDestroyed():
                    current_settings['path'] = self.path_input.text()
                if hasattr(self, 'browser_combo') and self.browser_combo and not self.browser_combo.isDestroyed():
                    current_settings['browser'] = self.browser_combo.currentData()
            except:
                pass
            
            # 完全删除旧的部件
            if self.current_mode_widget:
                try:
                    # 断开所有信号
                    for child in self.current_mode_widget.findChildren((QPushButton, QLineEdit)):
                        try:
                            if isinstance(child, QPushButton) and child.receivers(child.clicked) > 0:
                                child.clicked.disconnect()
                        except:
                            pass
                    
                    # 删除旧部件
                    self.current_mode_widget.setParent(None)
                    self.current_mode_widget.deleteLater()
                    QApplication.processEvents()
                except:
                    pass
            
            # 等待一下确保清理完成
            QApplication.processEvents()
            
            # 创建新的部件
            self.current_mode_widget = QWidget()
            self.main_layout.addWidget(self.current_mode_widget)
            self.layout = QVBoxLayout(self.current_mode_widget)
            
            # 设置整体边距和间距
            self.layout.setContentsMargins(20, 20, 20, 20)
            self.layout.setSpacing(10)  # 减小整体间距
            
            # 初始化新UI
            self.init_ui()
            
            # 安全地恢复设置
            try:
                if current_settings['path']:
                    self.path_input.setText(current_settings['path'])
                if current_settings['browser']:
                    index = self.browser_combo.findData(current_settings['browser'])
                    if index >= 0:
                        self.browser_combo.setCurrentIndex(index)
            except:
                pass
            
            # 更新历史显示
            self.update_history_display()
            
        except Exception as e:
            print(f"创建基础模式时出错: {str(e)}")
            # 如果出错，尝试重新创建一个干净的界面
            try:
                self.current_mode_widget = QWidget()
                self.main_layout.addWidget(self.current_mode_widget)
                self.layout = QVBoxLayout(self.current_mode_widget)
                self.init_ui()
            except:
                pass
        
    def create_advanced_mode(self):
        """创建高级模式界面"""
        self.advanced_widget = AdvancedModeWidget(self.config)
        self.advanced_widget.download_requested.connect(self.start_advanced_download)
        self.downloader.download_finished.connect(self.advanced_widget.reset_ui)
        self.advanced_widget.mode_switch_requested.connect(self.switch_to_basic_mode)
        return self.advanced_widget
        
    def init_ui(self):
        # URL输入区域
        url_layout = QVBoxLayout()
        url_label = QLabel("视频链接:")
        url_label.setStyleSheet(LABEL_STYLE)
        
        # 添加水平布局包含URL标签和播放列表选项
        url_header_layout = QHBoxLayout()
        url_header_layout.addWidget(url_label)
        url_header_layout.addStretch()
        
        # 添加播放列表选项复选框
        self.playlist_checkbox = QCheckBox()
        self.playlist_checkbox.setText("播放列表/频道")  # 移除方块字符，只保留文本
        self.playlist_checkbox.stateChanged.connect(self.update_checkbox_text)
        url_header_layout.addWidget(self.playlist_checkbox)
        
        url_layout.addLayout(url_header_layout)
        
        self.url_input = QTextEdit()
        self.url_input.setStyleSheet(INPUT_STYLE)
        self.url_input.setPlaceholderText("在此输入一个或多个YouTube视频链接，每行一个")
        self.url_input.setMinimumHeight(100)
        self.url_input.setAcceptRichText(False)
        url_layout.addWidget(self.url_input)
        self.layout.addLayout(url_layout)
        
        # 下载路径选择区域
        path_layout = QHBoxLayout()
        path_label = QLabel("下载位置:")
        path_label.setStyleSheet(LABEL_STYLE)
        self.path_input = QLineEdit()
        self.path_input.setStyleSheet(INPUT_STYLE)
        self.path_input.setText(os.path.expanduser("~/Downloads"))
        self.browse_button = QPushButton("浏览...")
        self.browse_button.setStyleSheet(BROWSE_BUTTON_STYLE)
        self.browse_button.clicked.connect(self.browse_directory)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        self.layout.addLayout(path_layout)
        
        # 浏览器和画质选择区域 - 更紧凑的布局
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        
        # 浏览器选择
        browser_layout = QHBoxLayout()
        browser_layout.setSpacing(8)  # 设置标签和下拉框之间的间距
        browser_label = QLabel("浏览器:")
        browser_label.setStyleSheet(LABEL_STYLE)
        browser_label.setFixedWidth(45)  # 固定标签宽度
        self.browser_combo = QComboBox()
        self.browser_combo.setStyleSheet(INPUT_STYLE)
        self.browser_combo.setFixedWidth(100)  # 调整下拉框宽度

        # 在 macOS 上添加支持的浏览器
        if sys.platform == 'darwin':  # macOS
            browsers = [
                ('Safari', 'safari'),
                ('Chrome', 'chrome'),
                ('Edge', 'edge'),
            ]
        else:  # Windows
            browsers = [
                ('Edge', 'edge'),
                ('Chrome', 'chrome'),
            ]

        for browser_name, browser_id in browsers:
            self.browser_combo.addItem(browser_name, browser_id)

        # 设置保存的浏览器选项
        saved_browser = self.config.config.get('browser')
        if saved_browser:
            index = self.browser_combo.findData(saved_browser)
            if index >= 0:
                self.browser_combo.setCurrentIndex(index)

        # 画质选择
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(8)  # 设置标签和下拉框之间的间距
        quality_label = QLabel("画质")
        quality_label.setStyleSheet(LABEL_STYLE)
        quality_label.setFixedWidth(35)  # 固定标签宽度
        self.quality_combo = QComboBox()
        self.quality_combo.setStyleSheet(INPUT_STYLE)
        self.quality_combo.setFixedWidth(120)  # 调整下拉框宽度
        self.quality_combo.addItem("最高画质", None)
        self.quality_combo.addItem("4K", "2160")
        self.quality_combo.addItem("1080P", "1080")
        self.quality_combo.addItem("480P", "480")
        self.quality_combo.addItem("仅MP3音频", "mp3")

        # 组合布局
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.browser_combo)
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)

        # 添加字幕选项复选框 - 移到画质选择的右边
        self.subtitle_checkbox = QCheckBox()
        self.subtitle_checkbox.setText("下载字幕")
        self.subtitle_checkbox.setStyleSheet("""
            QCheckBox {
                color: #333333;  /* 与 LABEL_STYLE 相同的颜色 */
                padding: 0px 2px;  /* 与 LABEL_STYLE 相同的内边距 */
            }
        """)
        self.subtitle_checkbox.setToolTip("下载视频内置的所有非自动生成字幕(格式:SRT)\n不包含自动生成的字幕")
        self.subtitle_checkbox.stateChanged.connect(self.update_subtitle_checkbox_text)
        
        # 调整布局和间距
        options_layout.addLayout(browser_layout)
        options_layout.addSpacing(20)  # 浏览器和画质之间的间距
        options_layout.addLayout(quality_layout)
        options_layout.addSpacing(20)  # 画质和字幕之间的间距
        options_layout.addWidget(self.subtitle_checkbox)
        options_layout.addStretch()  # 将选项推到左侧

        self.layout.addLayout(options_layout)
        
        # 添加提示信息（移动到选项下方）
        browser_tip = QLabel("提示：请确保已在选择的浏览器中登录过 YouTube")
        browser_tip.setStyleSheet(TIP_STYLE)
        self.layout.addWidget(browser_tip)
        
        # 控制按钮区域
        button_layout = QHBoxLayout()
        self.download_button = QPushButton("开始下载")
        self.download_button.setStyleSheet(BUTTON_STYLE)
        self.download_button.clicked.connect(self.start_download)
        
        self.advanced_button = QPushButton("高级模式")
        self.advanced_button.setStyleSheet(BUTTON_STYLE)
        self.advanced_button.clicked.connect(self.toggle_advanced_mode)
        
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.advanced_button)
        self.layout.addLayout(button_layout)
        
        # 添加下载历史显示区域
        history_header = QHBoxLayout()
        history_header.setContentsMargins(12, 6, 12, 0)  # 添加左边距，与下载任务标题对齐
        history_label = QLabel("下载历史")
        history_label.setStyleSheet(LABEL_STYLE)
        history_header.addWidget(history_label)
        history_header.addStretch()
        
        clear_history_button = QPushButton("清空")
        clear_history_button.setStyleSheet(CLEAR_BUTTON_STYLE)
        clear_history_button.clicked.connect(self.clear_download_history)
        history_header.addWidget(clear_history_button)
        self.layout.addLayout(history_header)
        
        self.history_area = QScrollArea()
        self.history_area.setStyleSheet(HISTORY_AREA_STYLE)
        self.history_area.setWidgetResizable(True)
        self.history_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_area.setFixedHeight(104)  # 增加4px高度
        
        history_widget = QWidget()
        self.history_layout = QVBoxLayout(history_widget)
        self.history_layout.setSpacing(1)  # 进一步减小历史项间距
        self.history_layout.setContentsMargins(4, 4, 4, 4)  # 减小内边距
        self.history_area.setWidget(history_widget)
        self.layout.addWidget(self.history_area)
        
        # 添加右键菜单支持
        self.history_area.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_area.customContextMenuRequested.connect(self.show_history_context_menu)
        
        # 更新显示最近的下载历史
        self.update_history_display()
        
    def update_history_display(self):
        """更新下载历史显示"""
        # 清理旧的历史显示
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取最近的下载历史（最多显示10条）
        history = self.config.config.get('download_history', [])[-10:]
        
        for entry in reversed(history):
            item = QWidget()
            item.setObjectName("historyItem")
            item.setStyleSheet(HISTORY_ITEM_STYLE)
            layout = QHBoxLayout(item)
            layout.setContentsMargins(6, 1, 6, 1)  # 减小上下边距
            
            # 处理标题，检查是否是播放列表
            full_title = entry['title']
            is_playlist = "(列表" in full_title
            
            # 截断过长的标题
            truncated_title = full_title
            if len(full_title) > 35:  # 限制标题长度为35个字符
                truncated_title = full_title[:33] + "..."
            
            # 创建可点击的标题标签
            title_label = QPushButton(truncated_title)
            
            # 为播放列表和单个视频设置相似的样式，只保留细微区别
            base_style = """
                QPushButton {
                    text-align: left;
                    border: none;
                    background: transparent;
                    color: #333333;
                    font-size: 12px;  /* 从 11px 改为 12px */
                    padding: 1px 2px;
                }
                QPushButton:hover {
                    color: #666666;
                    text-decoration: underline;
                }
            """
            
            if is_playlist:
                title_label.setStyleSheet(base_style + """
                    QPushButton {
                        font-style: italic;
                    }
                """)
            else:
                title_label.setStyleSheet(base_style)
            
            title_label.setCursor(Qt.CursorShape.PointingHandCursor)
            title_label.setToolTip(full_title)  # 设置完整标题为工具提示
            
            # 添加右键菜单支持
            title_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            title_label.customContextMenuRequested.connect(
                lambda pos, p=entry['path'], t=entry['title']: self.show_file_context_menu(pos, p, t)
            )

            # 连接左键点击事件
            def create_callback(path, title):
                return lambda: self.open_file_location(path, title)
            title_label.clicked.connect(create_callback(entry['path'], entry['title']))
            
            # 时间
            timestamp = datetime.datetime.fromisoformat(entry['timestamp']).astimezone()
            current_time = datetime.datetime.now().astimezone()
            
            if timestamp.date() == current_time.date():
                time_str = timestamp.strftime("今天 %H:%M")
            elif timestamp.date() == current_time.date() - datetime.timedelta(days=1):
                time_str = timestamp.strftime("昨天 %H:%M")
            else:
                time_str = timestamp.strftime("%m-%d %H:%M")
            
            time_label = QLabel(time_str)
            time_label.setStyleSheet("""
                color: #666666;
                font-size: 12px;  /* 从 11px 改为 12px */
                padding: 1px 2px;
            """)
            time_label.setFixedWidth(90)  # 稍微减小宽度
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            # 状态标签样式
            status_label = QLabel(entry['status'])
            status_style = """
                color: #32CD32;
                padding: 1px 6px;
                border-radius: 2px;
                font-size: 12px;  /* 从 11px 改为 12px */
            """
            if entry['status'] == '已取消':
                status_style = status_style.replace('#32CD32', '#999999')
            elif entry['status'] == '已存在':
                status_style = status_style.replace('#32CD32', '#FFA500')
            status_label.setStyleSheet(status_style)
            status_label.setFixedWidth(55)  # 稍微减小宽度
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            layout.addWidget(title_label, stretch=2)
            layout.addWidget(time_label)
            layout.addWidget(status_label)
            
            self.history_layout.addWidget(item)
        
        self.history_layout.addStretch()

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择下载目录",
            self.path_input.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.path_input.setText(directory)
            
    def validate_url(self, url):
        """验证 URL 是否是有效的 YouTube 链接"""
        valid_domains = ['youtube.com', 'youtu.be', 'www.youtube.com']
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return any(domain in parsed.netloc for domain in valid_domains)
        except:
            return False

    def is_playlist_url(self, url):
        """检测 URL 是否为播放列表或频道"""
        playlist_indicators = ['playlist?', '/c/', '/channel/', '/user/', '/watch?v=', '&list=']
        return any(indicator in url for indicator in playlist_indicators)

    def validate_download_path(self, path):
        """验证下载目录是否有效且可写"""
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            # 测试是否可写
            test_file = os.path.join(path, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except:
            return False

    def create_download_progress_widget(self, task_id, url):
        """为下载任务创建进度显示组件"""
        task_widget = QWidget()
        task_widget.setObjectName("taskItem")
        task_widget.setStyleSheet(TASK_ITEM_STYLE)
        layout = QVBoxLayout(task_widget)
        layout.setSpacing(1)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # 设置小字体
        font = self.font()
        font.setPointSize(11)  # 设置字体大小，与历史记录一致
        
        # 任务信息
        info_layout = QHBoxLayout()
        info_layout.setSpacing(5)
        info_layout.setContentsMargins(0, 0, 0, 0)  # 减少内边距
        
        # 移除任务标签，直接显示标题
        title_label = QLabel("正在准备下载...")
        title_label.setFont(font)
        title_label.setWordWrap(True)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        title_label.setMinimumHeight(20)  # 确保有足够的高度
        
        info_layout.addWidget(title_label, stretch=1)
        layout.addLayout(info_layout)
        
        # 进度条和状态
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(5)
        
        progress_bar = QProgressBar()
        progress_bar.setStyleSheet(PROGRESS_BAR_STYLE)
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setTextVisible(False)  # 隐藏进度条文字
        progress_bar.setFixedHeight(2)  # 更细的进度条
        
        status_label = QLabel("准备下载...")
        status_label.setFont(font)
        status_label.setMinimumWidth(200)
        
        progress_layout.addWidget(progress_bar, stretch=2)
        progress_layout.addWidget(status_label, stretch=1)
        layout.addLayout(progress_layout)
        
        # 存储任务信息
        self.download_tasks[task_id] = {
            'widget': task_widget,
            'progress_bar': progress_bar,
            'status_label': status_label,
            'title_label': title_label
        }
        
        return task_widget
        
    def start_download(self):
        try:
            urls = self.url_input.toPlainText().strip().split('\n')
            urls = [url.strip() for url in urls if url.strip()]
            
            if not urls:
                QMessageBox.warning(self, "错误", "请输入视频URL！")
                return
            
            # 验证所有URL
            invalid_urls = []
            for url in urls:
                if not self.validate_url(url):
                    invalid_urls.append(url)
            
            if invalid_urls:
                QMessageBox.warning(self, "错误", "存在无效的URL！")
                return
            
            output_path = self.path_input.text()
            if not self.validate_download_path(output_path):
                QMessageBox.warning(self, "错误", "下载目录无效或没有写入权限！")
                return
            
            # 保存当前下载路径到配置
            self.config.config['last_download_path'] = output_path
            self.config.save_config()
            
            # 重置下载器状态
            self.downloader.reset_state()
            
            # 重置界面状态
            self.total_urls = len(urls)
            self.completed_urls = 0
            self.download_tasks.clear()
            
            # 安全地清理旧的滚动区域和任务区域
            try:
                # 清理旧的滚动区域
                if hasattr(self, 'scroll_area') and self.scroll_area:
                    self.scroll_area.setParent(None)
                    self.scroll_area.deleteLater()
                
                # 清理旧的任务标题和容器
                for item in self.findChildren(QWidget):
                    if item.objectName() in ["taskHeader", "borderContainer"]:
                        item.setParent(None)
                        item.deleteLater()
                
                # 重置标记，允许重新创建标题
                self.task_header_added = False
                
                QApplication.processEvents()
            except:
                pass
            
            # 创建新的任务标题
            task_header = QWidget()
            task_header.setObjectName("taskHeader")
            header_layout = QHBoxLayout(task_header)
            header_layout.setContentsMargins(12, 6, 12, 0)
            task_label = QLabel("下载任务")
            task_label.setStyleSheet(LABEL_STYLE)
            header_layout.addWidget(task_label)
            header_layout.addStretch()
            self.layout.addWidget(task_header)
            
            # 创建带边框的外层容器
            border_container = QWidget()
            border_container.setObjectName("borderContainer")
            border_container.setStyleSheet(BORDER_CONTAINER_STYLE)
            border_layout = QVBoxLayout(border_container)
            border_layout.setContentsMargins(2, 2, 2, 2)
            border_layout.setSpacing(0)
            
            # 创建新的滚动区域
            self.scroll_area = QScrollArea()
            self.scroll_area.setStyleSheet(TASK_SCROLL_AREA_STYLE)
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            # 创建任务容器
            task_container = QWidget()
            task_container.setObjectName("taskArea")
            task_container.setStyleSheet(TASK_CONTAINER_STYLE)
            task_container_layout = QVBoxLayout(task_container)
            task_container_layout.setContentsMargins(4, 4, 4, 8)  # 增加底部边距
            task_container_layout.setSpacing(2)  # 设置任务之间的间距
            
            # 创建所有下载任务的显示
            for i, url in enumerate(urls, 1):
                task_id = f"Task-{i}"
                task_widget = self.create_download_progress_widget(task_id, url)
                task_container_layout.addWidget(task_widget)
            
            # 添加底部空白widget作为缓冲
            spacer = QWidget()
            spacer.setFixedHeight(4)
            task_container_layout.addWidget(spacer)
            
            # 设置滚动区域的内容
            self.scroll_area.setWidget(task_container)
            
            # 将滚动区域添加到边框容器
            border_layout.addWidget(self.scroll_area)
            
            # 将边框容器添加到主布局
            self.layout.addWidget(border_container)
            
            # 开始所有下载
            browser = self.browser_combo.currentData()
            is_playlist = self.playlist_checkbox.isChecked()
            
            # 获取画质设置
            quality = self.quality_combo.currentData()
            format_options = {
                'height': quality,
                'download_subs': self.subtitle_checkbox.isChecked()  # 添加字幕选项状态
            } if quality else {'download_subs': self.subtitle_checkbox.isChecked()}
            
            for i, url in enumerate(urls, 1):
                task_id = f"Task-{i}"
                self.downloader.start_download(
                    url=url,
                    output_path=output_path,
                    format_options=format_options,  # 现在包含了字幕选项
                    browser=browser,
                    is_playlist=is_playlist
                )
            
            # 禁用控件
            self._disable_controls()
            
        except Exception as e:
            print(f"开始下载时出错: {str(e)}")
            # 如果出错，尝试恢复界面状态
            try:
                self._enable_controls()
            except:
                pass
        
    def cancel_download(self):
        try:
            self.downloader.cancel_download()
            
            # 更新所有未完成任务的状态并记录到历史
            for task in self.download_tasks.values():
                if task['progress_bar'].value() < 100:
                    try:
                        task['status_label'].setText("已取消")
                        task['progress_bar'].setStyleSheet("QProgressBar::chunk { background-color: #999; }")
                        
                        # 添加到历史记录，安全地获取标题
                        title = task.get('title_label', {}).text() if task.get('title_label') else "视频下载任务"
                        if not title or title == "正在准备下载...":
                            title = "视频下载任务"
                            
                        self.config.config['download_history'].append({
                            'title': title,
                            'path': self.path_input.text(),
                            'timestamp': datetime.datetime.now().isoformat(),
                            'status': '已取消'
                        })
                    except Exception as e:
                        print(f"更新任务状态时出错: {str(e)}")
                        continue
            
            self.config.save_config()
            
        except Exception as e:
            print(f"取消下载时出错: {str(e)}")
        finally:
            # 确保控件被重新启用
            self._enable_controls()
        
    def update_output(self, task_id, text):
        if task_id not in self.download_tasks:
            return
            
        task = self.download_tasks[task_id]
        
        # 处理播放列表信息
        if "开始下载播放列表:" in text:
            playlist_name = text.split(': ', 1)[1]
            task['title_label'].setText(f"播放列表: {playlist_name}")
            task['status_label'].setText("准备下载...")
            task['progress_bar'].setValue(0)  # 重置进度条
            return
            
        # 播放列表项目进度
        if "正在下载此列表中的第" in text and "共" in text:
            try:
                # 获取播放列表项目编号
                parts = text.split("第")[1].split("个")
                current_item = parts[0].strip()
                total_items = parts[1].split("共")[1].strip().split("个")[0].strip()
                
                # 创建格式化消息，与新格式兼容
                list_id = task_id.split('-')[1] if '-' in task_id else "1"
                formatted_message = f"列表任务-{list_id}：正在下载第{current_item}个/共{total_items}个：正在获取视频信息..."
                
                # 使用新格式处理播放列表消息
                return self.update_output(task_id, formatted_message)
            except Exception as e:
                print(f"处理旧格式播放列表消息时出错: {e}")
                task['status_label'].setText(text)
            return
            
        # 播放列表下载完成
        if "播放列表下载完成:" in text:
            playlist_name = text.split(': ', 1)[1]
            task['status_label'].setText("下载完成")
            task['progress_bar'].setValue(100)
            return
        
        # 更新视频标题 - 新格式：列表任务-x：正在下载第y个/共z个：标题
        if "列表任务-" in text and "正在下载第" in text:
            try:
                parts = text.split("：", 2)  # 分成3部分：任务号、进度信息、标题
                task_info = parts[0]  # "列表任务-1"
                progress_info = parts[1]  # "正在下载第x个/共y个"
                
                # 确保有标题部分，即使没有冒号分隔
                if len(parts) > 2 and parts[2].strip():
                    title = parts[2]  # 提取标题
                else:
                    title = "正在获取视频信息..."  # 默认标题
                
                # 清理标题中的视频ID和格式ID
                cleaned_title = title
                if '[' in cleaned_title and ']' in cleaned_title:
                    cleaned_title = cleaned_title.split('[')[0].strip()
                if '.f' in cleaned_title and any(c.isdigit() for c in cleaned_title.split('.f')[-1]):
                    cleaned_title = cleaned_title.split('.f')[0].strip()
                
                # 确保标题不为空
                if not cleaned_title.strip():
                    cleaned_title = title  # 使用原始标题
                if not cleaned_title.strip():
                    cleaned_title = "正在获取视频信息..."  # 最后的保底方案
                
                # 检查是否包含"已存在"状态信息
                if "已存在" in text:
                    task['status_label'].setText("文件已存在，已跳过")
                    task['progress_bar'].setValue(100)
                    task['progress_bar'].setStyleSheet("QProgressBar::chunk { background-color: #FFA500; }")
                else:
                    task['status_label'].setText("准备下载...")
                    task['progress_bar'].setValue(0)  # 重置进度条
                    
                # 设置标题格式为：列表任务-x：正在下载第y个/共z个：视频标题
                # 检查标题长度并在必要时截断
                full_title = f"{task_info}：{progress_info}：{cleaned_title}"
                truncated_display = full_title
                if len(cleaned_title) > 40:  # 限制标题长度
                    truncated_display = f"{task_info}：{progress_info}：{cleaned_title[:38]}..."
                task['title_label'].setText(truncated_display)
                task['title_label'].setToolTip(full_title)  # 设置完整标题作为工具提示
                
                # 调试信息
                print(f"设置播放列表任务标题: {task_info}：{progress_info}：{cleaned_title}")
            except Exception as e:
                print(f"处理播放列表消息时出错: {e}")
                print(f"原始消息: {text}")
            return
        
        # 处理单个视频 - 新格式：单视频任务-x：标题
        if "单视频任务-" in text:
            if "已存在" in text:
                # 处理已存在的文件
                parts = text.split("：", 1)  # 分成2部分：任务号、标题+状态
                task_prefix = parts[0]
                title = parts[1].split(" (")[0] if len(parts) > 1 else "未知视频"  # 提取标题
                
                # 清理标题中的视频ID和格式ID
                if '[' in title and ']' in title:
                    title = title.split('[')[0].strip()
                if '.f' in title and any(c.isdigit() for c in title.split('.f')[-1]):
                    title = title.split('.f')[0].strip()
                    
                # 检查标题长度并在必要时截断
                if len(title) > 40:  # 限制标题长度
                    title = title[:38] + "..."
                task['title_label'].setText(f"{task_prefix}：{title}")  # 显示"单视频任务-x：清理后的标题"
                task['title_label'].setToolTip(f"{task_prefix}：{title}")  # 添加完整标题作为工具提示
                task['status_label'].setText("文件已存在，已跳过")
                task['progress_bar'].setValue(100)
                # 恢复进度条样式
                task['progress_bar'].setStyleSheet("QProgressBar::chunk { background-color: #FFA500; }")
            else:
                # 正常下载
                # 提取标题部分
                parts = text.split('：', 1)
                task_prefix = parts[0]
                title = parts[1] if len(parts) > 1 else text
                
                # 清理标题中的视频ID和格式ID
                if '[' in title and ']' in title:
                    title = title.split('[')[0].strip()
                if '.f' in title and any(c.isdigit() for c in title.split('.f')[-1]):
                    title = title.split('.f')[0].strip()
                    
                # 准备完整标题和显示标题
                full_title = f"{task_prefix}：{title}"
                display_title = full_title
                # 检查标题长度并在必要时截断
                if len(title) > 40:  # 限制标题长度
                    display_title = f"{task_prefix}：{title[:38]}..."
                task['title_label'].setText(display_title)  # 显示"单视频任务-x：清理后的标题"
                task['title_label'].setToolTip(full_title)  # 添加完整标题作为工具提示
                task['status_label'].setText("准备下载...")
                task['progress_bar'].setValue(0)  # 重置进度条
            return
        
        # 保留旧代码以兼容性处理
        if "开始下载:" in text:
            if "(" in text and ")" in text and "/" in text.split("(")[1]:
                # 播放列表项目
                title_parts = text.split(': ', 1)[1]
                title = title_parts.split(' (')[0]
                progress = title_parts.split(' (')[1].rstrip(')')
                task['title_label'].setText(f"{title}")
                task['status_label'].setText(f"下载中 - {progress}")
            else:
                # 普通视频
                title = text.split(': ', 1)[1]
                task['title_label'].setText(title)
                task['status_label'].setText("准备下载...")
            task['progress_bar'].setValue(0)  # 重置进度条
            return
            
        # 解析进度信息
        if "下载进度:" in text:
            try:
                percent_text = text.split('%')[0].split(':')[1].strip()
                progress = float(percent_text)
                task['progress_bar'].setValue(int(progress))
                
                # 检查是否包含播放列表信息
                if "- 正在下载第" in text and "共" in text:
                    progress_info = text.split('(')[1].split(')')[0]
                    task['status_label'].setText(f"{progress_info}")
                elif "- 项目" in text and "/" in text.split("- 项目")[1]:
                    # 兼容旧格式
                    progress_info = text.split('(')[1].split(')')[0]
                    item_info = text.split('- 项目')[1].strip()
                    task['status_label'].setText(f"{progress_info} - 项目 {item_info}")
                else:
                    task['status_label'].setText(text.split('(')[1].rstrip(')'))
            except:
                task['status_label'].setText(text)
        elif "文件已存在:" in text and not ("列表任务-" in text or "单视频任务-" in text):
            if "(" in text and ")" in text and "/" in text.split("(")[1]:
                # 播放列表项目
                title_parts = text.split(': ', 1)[1]
                title = title_parts.split(' (')[0]
                progress = title_parts.split(' (')[1].rstrip(')')
                task['title_label'].setText(f"{title}")
                task['status_label'].setText(f"文件已存在 - {progress}")
            else:
                # 普通视频
                title = text.split(': ', 1)[1]
                task['title_label'].setText(title)
                task['status_label'].setText("文件已存在，已跳过")
            task['progress_bar'].setValue(100)
            task['progress_bar'].setStyleSheet("QProgressBar::chunk { background-color: #FFA500; }")
        
    def download_finished(self, success, message, title, task_id):
        if task_id not in self.download_tasks:
            return
            
        task = self.download_tasks[task_id]
        
        # 检查是否为取消状态
        if message == "下载已取消":
            task['status_label'].setText("已取消")
            task['progress_bar'].setStyleSheet("QProgressBar::chunk { background-color: #999; }")
            
            # 添加到下载历史
            self.config.config['download_history'].append({
                'title': title,
                'path': self.downloader.get_current_download_path(task_id),
                'timestamp': datetime.datetime.now().isoformat(),
                'status': '已取消'
            })
        elif success:
            task['progress_bar'].setValue(100)
            task['progress_bar'].setTextVisible(False)  # 完成后不显示百分比
            task['status_label'].setText("下载完成")
            task['progress_bar'].setStyleSheet("""
                QProgressBar {
                    border: none;
                    background-color: #f0f0f0;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #32CD32;
                }
            """)
            
            # 添加到下载历史
            if '已存在' in message:
                status = '已存在'
            else:
                status = '完成'
            
            self.config.config['download_history'].append({
                'title': title,
                'path': self.downloader.get_current_download_path(task_id),
                'timestamp': datetime.datetime.now().isoformat(),
                'status': status
            })
            self.config.save_config()
            
            # 立即更新历史显示
            self.update_history_display()
        else:
            task['status_label'].setText("下载失败")
            task['progress_bar'].setStyleSheet("QProgressBar::chunk { background-color: #FF0000; }")
        
        # 更新完成计数
        self.completed_urls += 1
        
        # 所有下载完成时，只重新启用控件
        if self.completed_urls >= self.total_urls:
            self._enable_controls()
        
    def _enable_controls(self):
        """重新启用控件但保持界面显示"""
        try:
            self.download_button.clicked.disconnect()
        except:
            pass  # 如果没有连接，忽略错误
        self.download_button.clicked.connect(self.start_download)
        
        # 重置下载计数器
        self.total_urls = 0
        self.completed_urls = 0
        
        # 重新启用所有控件
        self.url_input.setEnabled(True)
        self.url_input.clear()  # 清空URL输入框，避免重复下载
        self.path_input.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.browser_combo.setEnabled(True)
        self.advanced_button.setEnabled(True)
        self.download_button.setText("开始下载")
        
    def toggle_advanced_mode(self):
        if self.advanced_button.text() == "高级模式":
            # 检查下载状态
            if any(p.state() == QProcess.ProcessState.Running for p in self.downloader.processes):
                QMessageBox.warning(self, "警告", "下载进行中，请等待下载完成后再切换模式")
                return
            
            # 切换到高级模式
            if self.current_mode_widget:
                self.current_mode_widget.hide()
                QApplication.processEvents()
                self.current_mode_widget.deleteLater()
                QApplication.processEvents()
                self.current_mode_widget = None
            
            self.current_mode_widget = self.create_advanced_mode()
            self.main_layout.addWidget(self.current_mode_widget)
            self.advanced_button.setText("基础模式")
        else:
            self.switch_to_basic_mode()

    def start_advanced_download(self, url, output_path, format_options):
        """处理来自高级模式的下载请求"""
        if not self.downloader.start_download(url, output_path, format_options):
            # 改用对话框显示错误
            QMessageBox.warning(self, "错误", "下载已在进行中！")

    def save_browser_setting(self):
        self.config.config['browser'] = self.browser_combo.currentData()
        self.config.save_config()

    def switch_to_basic_mode(self):
        try:
            if any(p.state() == QProcess.ProcessState.Running for p in self.downloader.processes):
                QMessageBox.warning(self, "警告", "下载进行中，请等待下载完成后再切换模式")
                return
            
            QApplication.processEvents()
            
            # 确保所有待处理的删除操作完成
            if self.current_mode_widget and self.current_mode_widget.parent():
                self.current_mode_widget.parent().layout().removeWidget(self.current_mode_widget)
            
            QApplication.processEvents()
            self.create_basic_mode()
            self.advanced_button.setText("高级模式")
            
        except Exception as e:
            print(f"切换到基础模式时出错: {str(e)}")
            # 尝试恢复到基础模式
            try:
                self.create_basic_mode()
            except:
                pass

    def _disable_controls(self):
        """禁用控件"""
        self.url_input.setEnabled(False)
        self.path_input.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.browser_combo.setEnabled(False)
        self.advanced_button.setEnabled(False)
        self.download_button.setText("取消下载")
        self.download_button.clicked.disconnect()
        self.download_button.clicked.connect(self.cancel_download)

    def clear_download_history(self):
        """清空下载历史"""
        self.config.config['download_history'] = []
        self.config.save_config()
        self.update_history_display()

    def show_history_context_menu(self, position):
        """显示历史记录的右键菜单"""
        menu = QMenu(self)
        clear_action = menu.addAction("清空历史记录")
        clear_action.triggered.connect(self.clear_download_history)
        menu.exec(self.history_area.mapToGlobal(position))

    def check_full_disk_access(self):
        """检查完全磁盘访问权限"""
        cookies_path = os.path.expanduser("~/Library/Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies")
        try:
            with open(cookies_path, 'rb') as f:
                # 如果能读取，说明有权限
                pass
        except PermissionError:
            QMessageBox.information(
                self,
                "需要权限",
                "为了能够下载会员视频，请授予完全磁盘访问权限：\n\n"
                "1. 打开系统设置\n"
                "2. 进入隐私与安全性 > 完全磁盘访问权限\n"
                "3. 点击+号添加 YT-DLP GUI\n"
                "4. 重启应用"
            )

    def open_file_location(self, path, title):
        """打开文件所在位置"""
        try:
            # 构建完整的文件路径
            import glob
            # 获取目录下所有文件
            all_files = glob.glob(os.path.join(path, "*"))
            video_extensions = ['.mp4', '.mkv', '.webm', '.avi', '.mov']
            
            # 查找匹配的视频文件
            video_files = []
            for file in all_files:
                # 检查扩展名
                if os.path.splitext(file)[1].lower() in video_extensions:
                    # 获取文件名（不含扩展名）
                    file_name = os.path.splitext(os.path.basename(file))[0]
                    # 如果文件名包含标题的主要部分，就认为是匹配的
                    if title.split('[')[0].strip() in file_name:
                        video_files.append(file)
            
            file_path = video_files[0] if video_files else None
            
            if file_path:
                # 如果找到文件，打开其所在文件夹并选中该文件
                os.system(f'open -R "{file_path}"')
            else:
                # 如果没找到文件，只打开文件夹
                os.system(f'open "{path}"')
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开文件位置：{str(e)}")

    def show_file_context_menu(self, pos, path, title):
        """显示文件右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 6px 24px;
                color: #333333;
                background: transparent;
            }
            QMenu::item:selected {
                background: #F5F5F5;
                color: #333333;
            }
            QMenu::item:hover {
                background: #F5F5F5;
                color: #333333;
            }
        """)
        
        # 设置鼠标样式
        menu.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 查找可能的文件
        import glob
        # 获取目录下所有文件
        all_files = glob.glob(os.path.join(path, "*"))
        video_extensions = ['.mp4', '.mkv', '.webm', '.avi', '.mov']
        
        # 查找匹配的视频文件
        video_files = []
        for file in all_files:
            # 检查扩展名
            if os.path.splitext(file)[1].lower() in video_extensions:
                # 获取文件名（不含扩展名）
                file_name = os.path.splitext(os.path.basename(file))[0]
                # 如果文件名包含标题的主要部分，就认为是匹配的
                if title.split('[')[0].strip() in file_name:
                    video_files.append(file)
        
        file_path = video_files[0] if video_files else None
        
        if file_path:
            # 打开视频
            open_action = menu.addAction("打开视频")
            open_action.triggered.connect(lambda: os.system(f'open "{file_path}"'))
            
            # 在文件夹中显示
            show_action = menu.addAction("在文件夹中显示")
            show_action.triggered.connect(lambda: os.system(f'open -R "{file_path}"'))
        else:
            # 如果找不到文件，只显示打开文件夹选项
            show_action = menu.addAction("打开下载文件夹")
            show_action.triggered.connect(lambda: os.system(f'open "{path}"'))
        
        menu.exec(self.sender().mapToGlobal(pos))

    def update_checkbox_text(self, state):
        if state == Qt.CheckState.Checked:
            self.playlist_checkbox.setText("☑️ 播放列表/频道")
        else:
            self.playlist_checkbox.setText("播放列表/频道")  # 未选中时只显示文本 

    def update_subtitle_checkbox_text(self, state):
        if state == Qt.CheckState.Checked:
            self.subtitle_checkbox.setText("☑️ 下载字幕")
        else:
            self.subtitle_checkbox.setText("下载字幕") 