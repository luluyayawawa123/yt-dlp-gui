import os
import json
import logging
from pathlib import Path
from datetime import datetime

class Config:
    def __init__(self):
        # macOS配置目录
        self.config_dir = Path.home() / "Library" / "Application Support" / "YT-DLP-GUI"
        self.config_file = self.config_dir / "config.json"
        self.log_file = self.config_dir / "debug.log"
        self.ensure_config_dir()
        
        # 初始化日志
        self.setup_logging()
        
        self.load_config()
        
    def ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
    def log(self, message, level=logging.INFO):
        """记录日志"""
        logging.log(level, message)
        
    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # 根据系统设置默认浏览器
            import sys
            default_browser = 'safari' if sys.platform == 'darwin' else 'edge'
            
            self.config = {
                'last_download_path': str(Path.home() / "Downloads"),
                'advanced_mode': False,
                'browser': default_browser,  # 添加默认浏览器设置
                'format_settings': {
                    'mode': 'best',  # best, audio_only, custom
                    'custom_format': ''
                },
                'download_history': []
            }
            self.save_config()
            
    def save_config(self):
        try:
            # 创建临时文件
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            # 成功写入后才替换原文件
            temp_file.replace(self.config_file)
        except Exception as e:
            print(f"保存配置文件失败: {e}") 