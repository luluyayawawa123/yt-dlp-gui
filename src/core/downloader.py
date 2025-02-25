from PyQt6.QtCore import QObject, QProcess, pyqtSignal, QProcessEnvironment
import shlex
import sys
import os
import logging
from .config import Config

class Downloader(QObject):
    # 修改信号，添加任务ID
    output_received = pyqtSignal(str, str)  # task_id, message
    download_finished = pyqtSignal(bool, str, str, str)  # success, message, title, task_id
    
    def __init__(self):
        super().__init__()
        self.processes = []
        self.task_count = 0  # 只保留这些基本属性
        self.download_paths = {}  # 存储每个任务的下载路径
        
        # 设置 M1 Mac 的 Homebrew 路径
        if "/opt/homebrew/bin" not in os.environ.get('PATH', ''):
            os.environ['PATH'] = "/opt/homebrew/bin:" + os.environ.get('PATH', '')
        
        # 更新 QProcess 环境变量
        self.env = QProcessEnvironment.systemEnvironment()
        
        # 初始化配置
        self.config = Config()
        
        # 记录启动日志
        self.config.log("YT-DLP GUI 启动", logging.INFO)
        
    def reset_state(self):
        """重置下载器状态"""
        self.task_count = 0
        # 取消所有正在进行的下载
        self.cancel_download()
        # 清理进程列表
        self.processes.clear()
        
    def start_download(self, url, output_path, format_options=None, browser='safari'):
        try:
            # 记录系统环境信息
            self.config.log(f"系统环境 PATH: {os.environ.get('PATH', '')}", logging.DEBUG)
            self.config.log(f"当前工作目录: {os.getcwd()}", logging.DEBUG)
            self.config.log(f"下载目录: {output_path}", logging.DEBUG)
            
            # 检查 yt-dlp 版本
            process = QProcess()
            process.start("yt-dlp", ["--version"])
            process.waitForFinished()
            version = process.readAllStandardOutput().data().decode().strip()
            self.config.log(f"yt-dlp 版本: {version}", logging.DEBUG)
            
            # 检查浏览器 cookies
            if browser == 'safari':
                cookies_path = os.path.expanduser("~/Library/Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies")
                self.config.log(f"Safari cookies 路径: {cookies_path}", logging.DEBUG)
                self.config.log(f"文件存在: {os.path.exists(cookies_path)}", logging.DEBUG)
                if os.path.exists(cookies_path):
                    self.config.log(f"文件权限: {oct(os.stat(cookies_path).st_mode)[-3:]}", logging.DEBUG)
            
            # 生成任务ID
            task_id = f"Task-{self.task_count + 1}"
            self.task_count += 1
            
            # 检查 yt-dlp 是否可用
            if not self._check_yt_dlp_available():
                raise RuntimeError("未找到 yt-dlp 命令，请确保已正确安装")
            
            # 创建新进程
            process = QProcess()
            process.setWorkingDirectory(output_path)
            process.setProperty("url", url)
            process.setProperty("task_id", task_id)
            process.setProperty("title", "未知视频")  # 初始化标题
            
            # 连接信号
            process.readyReadStandardOutput.connect(lambda: self._handle_stdout(process))
            process.readyReadStandardError.connect(lambda: self._handle_stderr(process))
            process.finished.connect(lambda code, status: self._handle_finished(process, code, status))
            
            # 添加环境变量 PATH
            process.setProcessEnvironment(self.env)
            
            # 记录下载信息
            self.config.log(f"开始下载: {url}", logging.INFO)
            self.config.log(f"输出路径: {output_path}", logging.DEBUG)
            self.config.log(f"使用浏览器: {browser}", logging.DEBUG)
            
            # 构建完整命令
            args = ['--cookies-from-browser', browser, '--progress', '--no-overwrites']
            if format_options:
                if 'format' in format_options:
                    args.extend(['-f', format_options['format']])
            args.append(url)
            
            command = f"yt-dlp {' '.join(args)}"
            self.config.log(f"完整命令: {command}", logging.DEBUG)
            
            # 启动下载
            print("执行命令:", "yt-dlp", args)
            process.start("yt-dlp", args)
            self.processes.append(process)
            
            # 保存下载路径
            self.download_paths[task_id] = output_path
            
            return True
            
        except Exception as e:
            self.download_finished.emit(False, f"启动下载失败: {str(e)}", "未知视频", task_id)
            return False
        
    def cancel_download(self):
        # 取消所有活跃的下载
        for process in self.processes:
            if process.state() == QProcess.ProcessState.Running:
                process.kill()
        self.processes.clear()
        
    def _handle_stdout(self, process):
        data = process.readAllStandardOutput().data().decode()
        task_id = process.property("task_id")
        
        # 解析进度信息
        if '[download]' in data:
            # 检查是否包含视频标题信息
            if 'Destination:' in data:
                try:
                    # 从目标文件名中提取标题
                    filename = data.split('Destination: ')[1].strip()
                    title = filename.rsplit('.', 1)[0]  # 移除扩展名
                    process.setProperty("title", title)
                    self.output_received.emit(task_id, f"开始下载: {title}")
                except:
                    pass
            # 检查是否是文件已存在的情况
            elif 'has already been downloaded' in data:
                try:
                    filename = data.split('[download] ')[1].split(' has already')[0]
                    title = filename.rsplit('.', 1)[0]  # 移除扩展名
                    process.setProperty("title", title)
                    self.output_received.emit(task_id, f"文件已存在: {title}")
                except:
                    pass
            # 提取进度百分比和其他信息
            elif '%' in data:
                try:
                    parts = data.split()
                    percent_idx = [i for i, part in enumerate(parts) if '%' in part][0]
                    percent = float(parts[percent_idx].rstrip('%'))
                    size = parts[percent_idx + 2]
                    speed = parts[percent_idx + 4]
                    eta = parts[percent_idx + 6]
                    
                    progress_text = f"下载进度: {percent}% (大小: {size}, 速度: {speed}, 剩余: {eta})"
                    self.output_received.emit(task_id, progress_text)
                except:
                    self.output_received.emit(task_id, data.strip())
        else:
            self.output_received.emit(task_id, data.strip())
        
    def _handle_stderr(self, process):
        data = process.readAllStandardError().data().decode()
        self.output_received.emit(process.property("task_id"), data)
        
    def _handle_finished(self, process, exit_code, exit_status):
        success = exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit
        message = "下载完成" if success else "下载失败"
        
        # 获取标题，如果没有则使用"未知视频"
        title = process.property("title") or "未知视频"
        task_id = process.property("task_id")
        
        # 发送完成信号，使用标题而不是 URL
        self.download_finished.emit(success, message, title, task_id)
        
        if process in self.processes:
            self.processes.remove(process)
            
    def analyze_formats(self, url):
        """分析视频可用格式"""
        process = QProcess()
        args = ["--cookies-from-browser", "safari", "-F", url]
        process.start("yt-dlp", args)
        process.waitForFinished()
        
        # 获取输出
        stdout = process.readAllStandardOutput().data().decode()
        stderr = process.readAllStandardError().data().decode()
        
        # 返回完整输出
        return stdout + stderr
        
    def _parse_format_list(self, output):
        """解析yt-dlp -F的输出"""
        formats = []
        for line in output.split('\n'):
            if line.startswith('format code') or not line.strip():
                continue
            try:
                parts = line.split()
                if len(parts) < 3:
                    continue
                    
                code = parts[0]
                ext = parts[1] if len(parts) > 1 else ""
                desc = line  # 保存完整的格式描述
                
                # 分类格式
                is_video = "video only" in line or ("p," in line and "audio only" not in line)
                is_audio = "audio only" in line
                
                formats.append({
                    'code': code,
                    'ext': ext,
                    'description': desc,
                    'is_video': is_video,
                    'is_audio': is_audio
                })
            except:
                continue
        return formats 

    def _check_yt_dlp_available(self):
        """检查 yt-dlp 是否可用"""
        try:
            process = QProcess()
            process.start("yt-dlp", ["--version"])
            process.waitForFinished()
            success = process.exitCode() == 0
            if not success:
                print("yt-dlp 检查失败，退出码:", process.exitCode())
                print("错误输出:", process.readAllStandardError().data().decode())
            return success
        except Exception as e:
            print("检查 yt-dlp 时出错:", str(e))
            return False

    def _format_progress(self, data):
        """格式化进度信息"""
        # 示例输入: [download]  23.4% of 50.75MiB at 2.52MiB/s ETA 00:15
        try:
            parts = data.split()
            progress = parts[1]  # 23.4%
            size = parts[3]      # 50.75MiB
            speed = parts[5]     # 2.52MiB/s
            eta = parts[7]       # 00:15
            
            return f"下载进度: {progress} (大小: {size}, 速度: {speed}, 剩余时间: {eta})"
        except:
            return data.strip() 

    def get_current_download_path(self, task_id):
        """获取指定任务的下载路径"""
        return self.download_paths.get(task_id, os.path.expanduser("~/Downloads")) 