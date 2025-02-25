#!/usr/bin/env python3
"""
YT-DLP GUI 简易打包脚本
用法: python build.py
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

def clean_old_files():
    """清理旧的构建文件和缓存"""
    print("清理旧的构建文件...")
    
    # 删除构建目录
    for dir_path in ['build', 'dist']:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"已删除: {dir_path}")
    
    # 删除 __pycache__ 目录
    for root, dirs, files in os.walk('.'):
        for d in dirs:
            if d == '__pycache__':
                path = os.path.join(root, d)
                shutil.rmtree(path)
                print(f"已删除: {path}")
    
    print("清理完成")

def build_app():
    """构建应用程序"""
    print("\n开始构建应用程序...")
    
    # 运行 PyInstaller
    build_command = [
        "pyinstaller",
        "yt-dlp-gui.spec",
        "--clean",
        "--noconfirm"
    ]
    
    print(f"执行命令: {' '.join(build_command)}")
    subprocess.run(build_command, check=True)
    
    print("应用程序构建完成")
    print(f"应用程序位置: {os.path.abspath('dist/YT-DLP GUI.app')}")

def main():
    """主函数"""
    print("=== YT-DLP GUI 打包脚本 ===")
    
    # 清理旧的构建文件
    clean_old_files()
    
    # 构建应用程序
    build_app()
    
    print("\n打包过程完成")
    print("你可以在 dist 目录中找到打包好的应用程序。")

if __name__ == "__main__":
    main() 