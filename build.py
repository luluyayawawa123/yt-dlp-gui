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
import platform
import importlib.util


def _venv_python_path():
    base = os.path.abspath('venv')
    if platform.system() == 'Windows':
        return os.path.join(base, 'Scripts', 'python.exe')
    return os.path.join(base, 'bin', 'python')


def ensure_venv_and_reexec():
    """确保在项目 venv 中运行；若无则创建并重启到 venv 解释器。"""
    target_python = _venv_python_path()
    in_venv = sys.prefix != getattr(sys, 'base_prefix', sys.prefix)
    running_in_target = os.path.abspath(sys.executable) == os.path.abspath(target_python)

    if os.path.exists(target_python) and running_in_target:
        return  # 已在目标 venv 中

    if not os.path.exists(target_python):
        print('未检测到 venv，正在创建虚拟环境...')
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)

    if not running_in_target:
        print('切换到 venv 解释器重新执行打包脚本...')
        os.execv(target_python, [target_python, __file__])


def ensure_pyinstaller():
    """自动确保 PyInstaller 及其 hooks 存在。"""
    need_install = importlib.util.find_spec('PyInstaller') is None
    if need_install:
        print('未检测到 PyInstaller，正在安装依赖: pyinstaller, pyinstaller-hooks-contrib...')
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-U', 'pip',
                        'pyinstaller', 'pyinstaller-hooks-contrib'], check=True)

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
    ensure_pyinstaller()
    # 可选：确保 .icns 存在（若有 icon.png 则自动生成）
    try:
        assets = os.path.abspath('assets')
        icon_icns = os.path.join(assets, 'app.icns')
        icon_png = os.path.join(assets, 'icon.png')
        if not os.path.exists(icon_icns) and os.path.exists(icon_png):
            print('检测到 assets/icon.png，尝试生成 app.icns ...')
            os.makedirs(os.path.join(assets, 'icon.iconset'), exist_ok=True)
            sizes = [16, 32, 64, 128, 256, 512, 1024]
            for s in sizes:
                out = os.path.join(assets, 'icon.iconset', f'icon_{s}x{s}.png')
                subprocess.run(['sips', '-z', str(s), str(s), icon_png, '--out', out], check=True)
                out2 = os.path.join(assets, 'icon.iconset', f'icon_{s}x{s}@2x.png')
                subprocess.run(['sips', '-z', str(s*2), str(s*2), icon_png, '--out', out2], check=True)
            subprocess.run(['iconutil', '-c', 'icns', os.path.join(assets, 'icon.iconset'), '-o', icon_icns], check=True)
            shutil.rmtree(os.path.join(assets, 'icon.iconset'), ignore_errors=True)
            print('app.icns 已生成。')
    except Exception as _e:
        print('生成 app.icns 失败（可忽略，使用默认图标）。', _e)
    
    # 运行 PyInstaller
    build_command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "yt-dlp-gui.spec",
        "--clean",
        "--noconfirm",
    ]
    
    # 将 PyInstaller 配置/缓存目录重定向到项目内，避免受限路径
    pyi_dir = os.path.abspath('.pyinstaller')
    os.makedirs(pyi_dir, exist_ok=True)
    env = os.environ.copy()
    env['PYINSTALLER_CONFIG_DIR'] = pyi_dir
    env['XDG_CACHE_HOME'] = pyi_dir
    
    print(f"执行命令: {' '.join(build_command)}")
    subprocess.run(build_command, check=True, env=env)
    
    print("应用程序构建完成")
    print(f"应用程序位置: {os.path.abspath('dist/YT-DLP GUI.app')}")

def main():
    """主函数"""
    print("=== YT-DLP GUI 打包脚本 ===")
    # 确保在 venv 中运行
    ensure_venv_and_reexec()
    
    # 清理旧的构建文件
    clean_old_files()
    
    # 构建应用程序
    build_app()
    
    print("\n打包过程完成")
    print("你可以在 dist 目录中找到打包好的应用程序。")

if __name__ == "__main__":
    main()
