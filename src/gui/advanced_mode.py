from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTextEdit, 
                            QComboBox, QRadioButton, QButtonGroup, QLineEdit, QScrollArea, QProgressBar)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
from PyQt6.QtGui import QFont, QTextCursor
from core.downloader import Downloader
import sys
import datetime
from PyQt6.QtWidgets import QApplication
from .styles import *  # 导入样式

# 添加分析线程类
class AnalyzeThread(QThread):
    finished = pyqtSignal(str)  # 分析完成信号
    
    def __init__(self, downloader, url):
        super().__init__()
        self.downloader = downloader
        self.url = url
        
    def run(self):
        try:
            formats = self.downloader.analyze_formats(self.url)
            self.finished.emit(formats)
        except Exception as e:
            self.finished.emit(f"分析失败: {str(e)}")

class AdvancedModeWidget(QWidget):
    download_requested = pyqtSignal(str, str, dict)  # url, output_path, format_options
    mode_switch_requested = pyqtSignal()
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.format_list = []  # 存储视频格式信息
        self.downloader = Downloader()  # 添加下载器实例
        
        # 添加下载任务管理
        self.total_urls = 0
        self.completed_urls = 0
        self.download_tasks = {}
        
        # 连接下载器信号
        self.downloader.output_received.connect(self.update_output)
        self.downloader.download_finished.connect(self.download_finished)
        
        self.analyze_thread = None  # 添加线程引用
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 添加顶部按钮栏
        top_button_layout = QHBoxLayout()
        self.back_button = QPushButton("返回基础模式")
        self.back_button.setStyleSheet(BUTTON_STYLE)
        self.back_button.clicked.connect(self.switch_to_basic_mode)
        top_button_layout.addWidget(self.back_button)
        top_button_layout.addStretch()
        layout.addLayout(top_button_layout)
        
        # URL输入区域
        url_layout = QVBoxLayout()
        url_label = QLabel("视频URL:")
        url_label.setStyleSheet(LABEL_STYLE)
        self.url_input = QLineEdit()
        self.url_input.setStyleSheet(INPUT_STYLE)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # 分析按钮
        self.analyze_button = QPushButton("分析视频格式")
        self.analyze_button.setStyleSheet(BUTTON_STYLE)
        self.analyze_button.clicked.connect(self.analyze_video)
        layout.addWidget(self.analyze_button)
        
        # 添加分析提示标签
        self.analyze_tip = QLabel("")
        self.analyze_tip.setStyleSheet(TIP_STYLE)
        self.analyze_tip.hide()
        layout.addWidget(self.analyze_tip)
        
        # 格式显示区域
        self.format_display = QTextEdit()
        self.format_display.setStyleSheet(INPUT_STYLE)
        self.format_display.setReadOnly(True)
        self.format_display.setFont(QFont("Courier New", 11))
        self.format_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)  # 禁用自动换行
        self.format_display.setMinimumHeight(240)  # 增加显示区域高度
        layout.addWidget(self.format_display)
        
        # 格式ID输入
        format_layout = QHBoxLayout()
        video_label = QLabel("视频格式ID:")
        video_label.setStyleSheet(LABEL_STYLE)
        self.video_format = QLineEdit()
        self.video_format.setStyleSheet(INPUT_STYLE)
        audio_label = QLabel("音频格式ID:")
        audio_label.setStyleSheet(LABEL_STYLE)
        self.audio_format = QLineEdit()
        self.audio_format.setStyleSheet(INPUT_STYLE)
        format_layout.addWidget(video_label)
        format_layout.addWidget(self.video_format)
        format_layout.addWidget(audio_label)
        format_layout.addWidget(self.audio_format)
        layout.addLayout(format_layout)
        
        # 浏览器选择
        browser_layout = QHBoxLayout()
        browser_label = QLabel("使用浏览器 Cookies:")
        browser_label.setStyleSheet(LABEL_STYLE)
        self.browser_combo = QComboBox()
        self.browser_combo.setStyleSheet(INPUT_STYLE)
        
        # 添加浏览器选项
        if sys.platform == 'darwin':
            browsers = [
                ('Safari', 'safari'),
                ('Chrome', 'chrome'),
                ('Edge', 'edge'),
            ]
        else:
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
                
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.browser_combo)
        layout.addLayout(browser_layout)
        
        # 提示信息
        browser_tip = QLabel("提示：请确保已在选择的浏览器中登录过 YouTube")
        browser_tip.setStyleSheet(TIP_STYLE)
        layout.addWidget(browser_tip)
        
        # 下载按钮
        button_layout = QHBoxLayout()
        self.download_button = QPushButton("开始下载")
        self.download_button.setStyleSheet(BUTTON_STYLE)
        self.download_button.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_button)
        layout.addLayout(button_layout)
        
        # 下载进度显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setStyleSheet(TASK_SCROLL_AREA_STYLE)
        self.scroll_area.setWidgetResizable(True)
        progress_area = QWidget()
        progress_area.setStyleSheet(TASK_CONTAINER_STYLE)
        self.progress_layout = QVBoxLayout(progress_area)
        self.progress_layout.setSpacing(5)
        self.scroll_area.setWidget(progress_area)
        layout.addWidget(self.scroll_area)

    def analyze_video(self):
        url = self.url_input.text().strip()
        if not url:
            self.format_display.append("请输入视频URL！")
            return
            
        if not self.validate_url(url):
            self.format_display.append("请输入有效的 YouTube 视频链接！")
            return
            
        # 显示分析提示
        self.analyze_tip.setText("正在分析视频格式，请耐心等待...")
        self.analyze_tip.show()
        self.analyze_tip.repaint()
        
        # 禁用分析按钮
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("分析中...")
        
        # 清空输出区域
        self.format_display.clear()
        
        # 创建并启动分析线程
        self.analyze_thread = AnalyzeThread(self.downloader, url)
        self.analyze_thread.finished.connect(self.handle_analyze_result)
        self.analyze_thread.start()

    def handle_analyze_result(self, formats):
        """处理分析结果"""
        # 隐藏提示
        self.analyze_tip.hide()
        
        # 格式化输出
        formatted_lines = []
        for line in formats.split('\n'):
            if '[info]' in line:
                line = line.split('[info]')[1].strip()
            formatted_lines.append(line)
        
        self.format_display.setText('\n'.join(formatted_lines))
        self.format_display.moveCursor(QTextCursor.MoveOperation.Start)
        
        # 恢复按钮状态
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("分析视频格式")
        
    def save_format_settings(self):
        if self.best_quality_radio.isChecked():
            mode = 'best'
        elif self.audio_only_radio.isChecked():
            mode = 'audio_only'
        else:
            mode = 'custom'
            
        self.config.config['format_settings']['mode'] = mode
        if mode == 'custom':
            self.config.config['format_settings']['custom_format'] = self.format_combo.currentData()
        self.config.save_config()
        
    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.format_display.append("请输入视频URL！")
            return
            
        if not self.validate_url(url):
            self.format_display.append("请输入有效的 YouTube 视频链接！")
            return
            
        # 获取格式ID
        video_format = self.video_format.text().strip()
        audio_format = self.audio_format.text().strip()
        
        if not video_format and not audio_format:
            self.format_display.append("请至少输入一个格式ID！")
            return
            
        # 构建格式字符串
        if video_format and audio_format:
            format_str = f"{video_format}+{audio_format}"
        else:
            format_str = video_format or audio_format
            
        # 禁用所有控件（除了下载按钮）
        self._disable_controls()
        
        # 修改下载按钮为取消按钮，并保持启用状态
        self.download_button.setEnabled(True)  # 确保按钮可用
        self.download_button.setText("取消下载")
        self.download_button.clicked.disconnect()
        self.download_button.clicked.connect(self.cancel_download)
        
        # 准备下载选项
        format_options = {
            'format': format_str,
            'browser': self.browser_combo.currentData()
        }
        
        # 使用配置中的下载路径
        output_path = self.config.config['last_download_path']
        
        # 重置下载器状态
        self.downloader.reset_state()
        
        # 重置界面状态
        self.total_urls = 1  # 高级模式一次只下载一个视频
        self.completed_urls = 0
        self.download_tasks.clear()
        
        # 清理旧的进度显示
        while self.progress_layout.count():
            item = self.progress_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 创建新的进度显示
        task_id = "Task-1"
        task_widget = self.create_download_progress_widget(task_id, url)
        self.progress_layout.addWidget(task_widget)
        
        # 开始下载
        if not self.downloader.start_download(url, output_path, format_options):
            self.format_display.append("下载已在进行中！")
        
    def save_browser_setting(self):
        self.config.config['browser'] = self.browser_combo.currentData()
        self.config.save_config() 

    def validate_url(self, url):
        """验证 URL 是否是有效的 YouTube 链接"""
        valid_domains = ['youtube.com', 'youtu.be', 'www.youtube.com']
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return any(domain in parsed.netloc for domain in valid_domains)
        except:
            return False 

    def reset_ui(self):
        """重置UI状态"""
        self.url_input.setEnabled(True)
        self.video_format.setEnabled(True)
        self.audio_format.setEnabled(True)
        self.analyze_button.setEnabled(True)
        self.browser_combo.setEnabled(True)
        self.download_button.setEnabled(True)
        self.download_button.setText("开始下载")

    def switch_to_basic_mode(self):
        # 发送信号给主窗口
        self.mode_switch_requested.emit() 

    def _disable_controls(self):
        """禁用控件"""
        self.url_input.setEnabled(False)
        self.video_format.setEnabled(False)
        self.audio_format.setEnabled(False)
        self.analyze_button.setEnabled(False)
        self.browser_combo.setEnabled(False)

    def create_download_progress_widget(self, task_id, url):
        """为下载任务创建进度显示组件"""
        task_widget = QWidget()
        layout = QVBoxLayout(task_widget)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 任务信息
        info_layout = QHBoxLayout()
        task_label = QLabel(f"任务 {task_id}:")
        title_label = QLabel("等待获取标题...")
        title_label.setStyleSheet("color: gray;")
        title_label.setWordWrap(True)
        
        info_layout.addWidget(task_label)
        info_layout.addWidget(title_label)
        layout.addLayout(info_layout)
        
        # 进度条和状态
        progress_layout = QHBoxLayout()
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setTextVisible(True)
        progress_bar.setFixedHeight(10)
        
        status_label = QLabel("准备下载...")
        status_label.setStyleSheet("color: #666; font-size: 12px;")
        
        progress_layout.addWidget(progress_bar)
        progress_layout.addWidget(status_label)
        layout.addLayout(progress_layout)
        
        # 存储任务信息
        self.download_tasks[task_id] = {
            'widget': task_widget,
            'progress_bar': progress_bar,
            'status_label': status_label,
            'title_label': title_label
        }
        
        return task_widget

    def update_output(self, task_id, text):
        """更新下载进度显示"""
        if task_id not in self.download_tasks:
            return
            
        task = self.download_tasks[task_id]
        
        if "开始下载:" in text:
            title = text.split(': ', 1)[1]
            task['title_label'].setText(title)
            task['status_label'].setText("准备下载...")
            return
            
        if "下载进度:" in text:
            try:
                percent_text = text.split('%')[0].split(':')[1].strip()
                progress = float(percent_text)
                task['progress_bar'].setValue(int(progress))
                task['status_label'].setText(text.split('(')[1].rstrip(')'))
            except:
                task['status_label'].setText(text)

    def download_finished(self, success, message, title, task_id):
        """处理下载完成事件"""
        if task_id not in self.download_tasks:
            return
            
        task = self.download_tasks[task_id]
        
        if success:
            task['progress_bar'].setValue(100)
            task['status_label'].setText("下载完成")
            task['progress_bar'].setStyleSheet("QProgressBar::chunk { background-color: #32CD32; }")
            
            # 添加到下载历史
            if '已存在' in message:
                status = '已存在'
            else:
                status = '完成'
            
            self.config.config['download_history'].append({
                'title': title,
                'path': self.config.config['last_download_path'],
                'timestamp': datetime.datetime.now().isoformat(),
                'status': status
            })
            self.config.save_config()
        else:
            task['status_label'].setText("下载失败")
            task['progress_bar'].setStyleSheet("QProgressBar::chunk { background-color: #FF0000; }")
        
        # 更新完成计数
        self.completed_urls += 1
        
        # 所有下载完成时，重新启用控件
        if self.completed_urls >= self.total_urls:
            self.reset_ui() 

    def cancel_download(self):
        """取消下载"""
        try:
            self.downloader.cancel_download()
            
            # 更新所有未完成任务的状态并记录到历史
            for task in self.download_tasks.values():
                if task['progress_bar'].value() < 100:
                    try:
                        task['status_label'].setText("已取消")
                        task['progress_bar'].setStyleSheet("QProgressBar::chunk { background-color: #999; }")
                        
                        # 添加到历史记录
                        title = task.get('title_label', {}).text() if task.get('title_label') else "未知视频"
                        if not title or title == "等待获取标题...":
                            title = "未知视频"
                            
                        self.config.config['download_history'].append({
                            'title': title,
                            'path': self.config.config['last_download_path'],
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
            # 重置UI状态
            self.reset_ui()
            # 恢复下载按钮
            self.download_button.setText("开始下载")
            self.download_button.clicked.disconnect()
            self.download_button.clicked.connect(self.start_download) 