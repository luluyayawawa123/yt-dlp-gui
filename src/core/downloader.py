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
        
    def start_download(self, url, output_path, format_options=None, browser='safari', is_playlist=False):
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
            process.setProperty("title", "正在获取视频信息...")  # 初始化标题为更友好的提示
            process.setProperty("is_playlist", is_playlist)  # 设置播放列表标记
            process.setProperty("playlist_name", "")  # 初始化播放列表名称
            process.setProperty("current_item", 0)  # 初始化当前下载项索引
            process.setProperty("total_items", 0)  # 初始化总项目数
            
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
            self.config.log(f"是否播放列表/频道: {is_playlist}", logging.DEBUG)
            
            # 构建基础参数
            args = ["--cookies-from-browser", browser, "--progress", "--no-overwrites"]
            args.extend(["--output", "%(title)s.%(ext)s"])
            
            # 添加画质选择参数
            if format_options and 'height' in format_options:
                height = format_options['height']
                if height == "mp3":  # MP3 音频选项
                    args.extend([
                        "-f", "ba/b",  # 选择最佳音频质量
                        "-x",  # 提取音频
                        "--audio-format", "mp3",
                        "--audio-quality", "320",  # 最高音质
                        "--postprocessor-args", "-codec:a libmp3lame"
                    ])
                elif height == "2160":  # 4K
                    format_str = "bv*[height<=2160][ext=mp4]+ba[ext=m4a]"
                    args.extend(["-f", format_str])
                elif height == "1080":  # 1080P
                    format_str = "bv*[height<=1080][ext=mp4]+ba[ext=m4a]"
                    args.extend(["-f", format_str])
                elif height == "480":  # 480P
                    format_str = "bv*[height<=480][ext=mp4]+ba[ext=m4a]"
                    args.extend(["-f", format_str])
            
            # 添加字幕下载参数
            if format_options and format_options.get('download_subs'):
                args.extend([
                    '--write-subs',           # 下载字幕
                    '--sub-langs', 'all',     # 下载所有语言的字幕
                    '--convert-subs', 'srt'   # 转换为 srt 格式
                ])
            
            # 添加播放列表参数
            if is_playlist:
                args.append("--yes-playlist")
            
            # 添加URL
            args.append(url)
            
            # 记录完整命令
            command = "yt-dlp " + " ".join([shlex.quote(str(arg)) for arg in args])
            print("执行命令:", command)
            
            # 启动进程
            process.start("yt-dlp", args)
            self.processes.append(process)
            
            # 保存下载路径
            self.download_paths[task_id] = output_path
            
            return True
            
        except Exception as e:
            self.download_finished.emit(False, f"启动下载失败: {str(e)}", "正在获取视频信息...", task_id)
            return False
        
    def cancel_download(self):
        # 取消所有活跃的下载
        for process in self.processes:
            if process.state() == QProcess.ProcessState.Running:
                # 标记任务为已取消
                process.setProperty("canceled", True)
                # 记录任务ID用于状态更新
                task_id = process.property("task_id")
                title = process.property("title") or "视频下载任务"
                # 发送取消消息
                self.output_received.emit(task_id, "下载已取消")
                # 立即发送下载完成信号，确保UI更新
                self.download_finished.emit(False, "下载已取消", title, task_id)
                # 终止进程
                process.kill()
        self.processes.clear()
        
    def _handle_stdout(self, process):
        data = process.readAllStandardOutput().data().decode()
        task_id = process.property("task_id")
        
        # 解析进度信息
        if '[download]' in data:
            # 播放列表总数信息
            if 'Downloading playlist:' in data:
                try:
                    playlist_name = data.split('Downloading playlist:')[1].strip()
                    process.setProperty("is_playlist", True)
                    process.setProperty("playlist_name", playlist_name)
                    self.output_received.emit(task_id, f"开始下载播放列表: {playlist_name}")
                except:
                    self.output_received.emit(task_id, data.strip())
                return
                
            # 播放列表完成信息
            elif 'Finished downloading playlist:' in data:
                try:
                    playlist_name = data.split('Finished downloading playlist:')[1].strip()
                    self.output_received.emit(task_id, f"播放列表下载完成: {playlist_name}")
                except:
                    self.output_received.emit(task_id, data.strip())
                return
                
            # 播放列表项目信息
            elif 'Downloading item' in data and 'of' in data:
                try:
                    parts = data.split('Downloading item')[1].strip().split('of')
                    current_item = int(parts[0].strip())
                    total_items = int(parts[1].strip())
                    
                    # 保存到进程属性中
                    process.setProperty("current_item", current_item)
                    process.setProperty("total_items", total_items)
                    
                    # 获取当前正在下载的视频标题（如果有的话）
                    current_title = process.property("title") or "正在获取视频信息..."
                    list_id = task_id.split('-')[1] if '-' in task_id else "1"
                    
                    # 发送包含视频标题的消息
                    self.output_received.emit(task_id, f"列表任务-{list_id}：正在下载第{current_item}个/共{total_items}个：{current_title}")
                    
                    # 记录调试信息
                    print(f"播放列表项目更新：第{current_item}个/共{total_items}个")
                except Exception as e:
                    print(f"处理播放列表项目信息时出错: {str(e)}")
                    self.output_received.emit(task_id, data.strip())
                return
            
            # 检查是否包含视频标题信息
            elif 'Destination:' in data:
                try:
                    # 从目标文件名中提取标题
                    filename = data.split('Destination: ')[1].strip()
                    title = filename.rsplit('.', 1)[0]  # 移除扩展名
                    
                    # 更彻底地清理标题中的视频ID和格式ID
                    cleaned_title = title
                    
                    # 清理方括号内容
                    if '[' in cleaned_title and ']' in cleaned_title:
                        cleaned_title = cleaned_title.split('[')[0].strip()
                        if not cleaned_title:  # 如果清理后为空，可能标题在方括号内
                            parts = title.split(']', 1)
                            if len(parts) > 1:
                                cleaned_title = parts[1].strip()
                    
                    # 更彻底地清理格式ID（如.f137、.f251等）
                    format_parts = cleaned_title.split('.')
                    if len(format_parts) > 1:
                        last_part = format_parts[-1]
                        if 'f' in last_part and any(c.isdigit() for c in last_part):
                            cleaned_title = '.'.join(format_parts[:-1])
                    
                    # 确保标题不为空
                    if not cleaned_title.strip():
                        cleaned_title = title  # 使用原始标题作为备选
                    if not cleaned_title.strip():
                        cleaned_title = "正在获取视频信息..."
                    
                    # 设置视频标题属性
                    process.setProperty("title", cleaned_title)
                    
                    # 如果是播放列表，立即发送新消息更新标题
                    if process.property("is_playlist"):
                        current = process.property("current_item") or 0
                        total = process.property("total_items") or 0
                        
                        # 确保current有效
                        if current > 0:
                            list_id = task_id.split('-')[1] if '-' in task_id else "1"
                            # 发送带更新标题的消息
                            self.output_received.emit(task_id, f"列表任务-{list_id}：正在下载第{current}个/共{total}个：{cleaned_title}")
                    else:
                        # 单个视频
                        single_id = task_id.split('-')[1] if '-' in task_id else "1"
                        self.output_received.emit(task_id, f"单视频任务-{single_id}：{cleaned_title}")
                except Exception as e:
                    print(f"处理视频标题信息时出错: {str(e)}")
                    pass
            # 检查是否是文件已存在的情况
            elif 'has already been downloaded' in data:
                try:
                    filename = data.split('[download] ')[1].split(' has already')[0]
                    title = filename.rsplit('.', 1)[0]  # 移除扩展名
                    # 清理标题中的视频ID和格式ID
                    if '[' in title and ']' in title:
                        title = title.split('[')[0].strip()
                    if '.f' in title and any(c.isdigit() for c in title.split('.f')[-1]):
                        title = title.split('.f')[0].strip()
                    process.setProperty("title", title)
                    
                    # 如果是播放列表，添加项目信息并自增项目计数
                    if process.property("is_playlist"):
                        # 在这里更新当前项目计数，确保已存在项目也被计入
                        current = process.property("current_item") or 0
                        total = process.property("total_items") or 0
                        
                        # 如果当前项目计数为0，则看看能否从消息中提取
                        if current == 0 and 'item' in data and 'of' in data:
                            try:
                                item_parts = data.split('item')[1].strip().split('of')
                                current = int(item_parts[0].strip())
                                total = int(item_parts[1].strip().split(' ')[0])
                                process.setProperty("total_items", total)
                            except:
                                # 如果无法从消息提取，则递增当前计数
                                current += 1
                        else:
                            # 正常递增计数
                            current += 1
                            
                        # 更新进程属性
                        process.setProperty("current_item", current)
                        
                        # 确保有总数
                        if total == 0:
                            # 如果不知道总数，使用默认值或从其他地方获取
                            print(f"警告：未知播放列表总条目数，使用默认值")
                        
                        list_id = task_id.split('-')[1] if '-' in task_id else "1"
                        self.output_received.emit(task_id, f"列表任务-{list_id}：正在下载第{current}个/共{total}个：{title} (已存在)")
                    else:
                        # 单个视频
                        single_id = task_id.split('-')[1] if '-' in task_id else "1"
                        self.output_received.emit(task_id, f"单视频任务-{single_id}：{title} (已存在)")
                except Exception as e:
                    print(f"处理已存在文件信息时出错: {str(e)}")
                    pass
            # 检查是否是播放列表信息    
            elif 'Downloading playlist' in data or 'Downloading channel' in data:
                try:
                    playlist_info = data.strip()
                    self.output_received.emit(task_id, f"{playlist_info}")
                except:
                    pass
            # 播放列表项计数
            elif 'Downloading item' in data:
                try:
                    item_info = data.strip()
                    self.output_received.emit(task_id, f"{item_info}")
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
                    
                    # 添加播放列表信息到进度文本
                    if process.property("is_playlist") and process.property("current_item") > 0:
                        current = process.property("current_item") 
                        total = process.property("total_items")
                        progress_text = f"下载进度: {percent}% (大小: {size}, 速度: {speed}, 剩余: {eta}) - 正在下载第{current}个/共{total}个"
                    else:
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
        # 检查是否为被取消的任务
        if process.property("canceled") == True:
            success = False
            message = "下载已取消"
        else:
            # 判断是否为播放列表
            is_playlist = process.property("is_playlist") or False
            
            # 对于普通视频，仅检查退出码
            # 对于播放列表，即使退出码不为0，也认为是成功的
            # 因为yt-dlp对于播放列表可能会返回非零退出码，即使所有可下载的项目都已下载完成
            if is_playlist:
                # 播放列表下载始终视为成功
                success = True
                message = "下载完成"
                
                # 记录日志，但不将非零退出码视为错误
                if exit_code != 0:
                    self.config.log(f"播放列表下载完成，但退出码非零: {exit_code}，这通常是正常的", logging.INFO)
            else:
                # 单个视频下载
                success = exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit
                message = "下载完成" if success else "下载失败"
        
        # 获取任务ID
        task_id = process.property("task_id")
        
        # 处理播放列表和单个视频的不同显示逻辑
        if process.property("is_playlist"):
            # 使用播放列表名称作为标题，并添加(列表)标识
            playlist_name = process.property("playlist_name") or "未命名播放列表"
            total_items = process.property("total_items") or 0
            
            # 创建包含列表标识的标题
            if total_items > 0:
                title = f"{playlist_name} (列表, 共{total_items}个视频)"
            else:
                title = f"{playlist_name} (列表)"
            
            # 添加日志
            print(f"播放列表下载完成: {playlist_name}, 共{total_items}个视频")
        else:
            # 获取单个视频的标题
            title = process.property("title") or "视频下载任务"
        
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