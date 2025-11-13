#!/usr/bin/env python3
"""
生成 macOS 发布包（ZIP 与 DMG）
用法: python3 release.py
效果: 在 release/ 目录下生成 zip 与 dmg 两个文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import textwrap
import tempfile

PROJECT_ROOT = Path(__file__).parent.resolve()
DIST_APP = PROJECT_ROOT / 'dist' / 'YT-DLP GUI.app'
RELEASE_DIR = PROJECT_ROOT / 'release'


def get_version() -> str:
    sys.path.append(str(PROJECT_ROOT / 'src'))
    try:
        from version import VERSION
        return VERSION or '1.0.0'
    except Exception:
        return '1.0.0'


def ensure_built_app():
    if DIST_APP.exists():
        return
    print('[release] 未发现 dist/YT-DLP GUI.app，正在调用 build.py 进行构建...')
    cmd = [sys.executable or 'python3', 'build.py']
    # 优先使用系统 python3，以便 build.py 内部创建并切换到 venv
    if shutil.which('python3'):
        cmd = ['python3', 'build.py']
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))


def make_zip(version: str) -> Path:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RELEASE_DIR / f'YT-DLP-GUI-mac-v{version}.zip'
    if zip_path.exists():
        zip_path.unlink()
    print(f'[release] 生成 ZIP: {zip_path.name}')
    # 使用 ditto 以保留 .app 资源与父目录
    subprocess.run([
        'ditto', '-c', '-k', '--sequesterRsrc', '--keepParent',
        str(DIST_APP), str(zip_path)
    ], check=True)
    return zip_path


def _run(cmd: list[str]):
    return subprocess.run(cmd, check=True)


def make_dmg_simple(version: str) -> Path:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    dmg_path = RELEASE_DIR / f'YT-DLP-GUI-mac-v{version}.dmg'
    if dmg_path.exists():
        dmg_path.unlink()

    staging_dir = RELEASE_DIR / '.staging' / 'YT-DLP-GUI'
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    print(f'[release] 准备 DMG 内容...')
    # 拷贝 .app
    subprocess.run(['cp', '-R', str(DIST_APP), str(staging_dir)], check=True)
    # 添加 Applications 快捷方式
    apps_link = staging_dir / 'Applications'
    if apps_link.exists() or apps_link.is_symlink():
        apps_link.unlink()
    os.symlink('/Applications', apps_link)

    # 不添加额外文本说明，保持界面简洁

    print(f'[release] 生成 DMG: {dmg_path.name}')
    _run([
        'hdiutil', 'create',
        '-volname', 'YT-DLP GUI',
        '-srcfolder', str(staging_dir),
        '-ov', '-format', 'UDZO',
        str(dmg_path)
    ])

    # 清理临时目录
    shutil.rmtree(staging_dir.parent, ignore_errors=True)
    return dmg_path


def make_dmg_pretty(version: str) -> Path:
    """创建带背景和图标布局的 DMG（需要 macOS 图形环境与 hdiutil + osascript）。"""
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    dmg_path = RELEASE_DIR / f'YT-DLP-GUI-mac-v{version}.dmg'
    if dmg_path.exists():
        dmg_path.unlink()

    staging = RELEASE_DIR / '.staging'
    dmgroot = staging / 'dmgroot'
    mount_dir = staging / 'mnt'
    tmp_dmg = staging / 'tmp.dmg'

    # 准备 dmgroot 内容
    if dmgroot.exists():
        shutil.rmtree(dmgroot)
    dmgroot.mkdir(parents=True, exist_ok=True)
    print('[release] 准备 DMG 内容(美化版)...')
    subprocess.run(['cp', '-R', str(DIST_APP), str(dmgroot)], check=True)
    apps_link = dmgroot / 'Applications'
    if apps_link.exists() or apps_link.is_symlink():
        apps_link.unlink()
    os.symlink('/Applications', apps_link)
    # 不添加额外文本说明，保持界面简洁
    bg_asset = PROJECT_ROOT / 'assets' / 'dmg-background.png'
    if bg_asset.exists():
        (dmgroot / '.background').mkdir(exist_ok=True)
        subprocess.run(['cp', str(bg_asset), str(dmgroot / '.background' / 'bg.png')], check=True)

    # 1) 用 srcfolder 创建可写 DMG
    print('[release] 创建临时可写 DMG...')
    _run(['hdiutil', 'create', '-volname', 'YT-DLP GUI', '-srcfolder', str(dmgroot), '-ov', '-format', 'UDRW', str(tmp_dmg)])

    # 2) 挂载 DMG 并美化 Finder 布局
    if mount_dir.exists():
        shutil.rmtree(mount_dir)
    mount_dir.mkdir(parents=True, exist_ok=True)
    print('[release] 挂载 DMG...')
    _run(['hdiutil', 'attach', str(tmp_dmg), '-mountpoint', str(mount_dir), '-nobrowse', '-noverify'])
    try:
        script = f'''
        on run
          tell application "Finder"
            tell disk "YT-DLP GUI"
              open
              set current view of container window to icon view
              set toolbar visible of container window to false
              set statusbar visible of container window to false
              delay 0.2
              set the bounds of container window to {{200, 200, 800, 600}}
              set viewOptions to the icon view options of container window
              set arrangement of viewOptions to not arranged
              set icon size of viewOptions to 128
        '''
        if bg_asset.exists():
            script += '              set background picture of viewOptions to file ".background:bg.png"\n'
        script += textwrap.dedent('''
              delay 0.2
              set position of item "YT-DLP GUI.app" of container window to {100, 240}
              set position of item "Applications" of container window to {380, 240}
              -- 不放置额外文本，保持简洁
              update without registering applications
              delay 0.2
              close
              open
              delay 0.2
              -- 结束
            end tell
          end tell
        end run
        ''')
        print('[release] 设置 DMG 窗口布局...')
        subprocess.run(['osascript', '-e', script], check=True)
    finally:
        print('[release] 卸载 DMG...')
        subprocess.run(['hdiutil', 'detach', str(mount_dir)], check=False)

    # 3) 压缩为只读 DMG
    print('[release] 压缩 DMG...')
    _run(['hdiutil', 'convert', str(tmp_dmg), '-format', 'UDZO', '-o', str(dmg_path), '-ov'])
    tmp_dmg.unlink(missing_ok=True)
    shutil.rmtree(staging, ignore_errors=True)
    return dmg_path


def main():
    print('=== 生成发布包（ZIP & DMG）===')
    ensure_built_app()
    version = get_version()
    zip_path = make_zip(version)
    # 优先生成带美化的 DMG，失败则回退到简单 DMG
    try:
        dmg_path = make_dmg_pretty(version)
    except Exception as e:
        print(f"[release] 带美化 DMG 失败，回退到简单 DMG。原因: {e}")
        dmg_path = make_dmg_simple(version)
    print('\n[release] 已生成:')
    print(f' - {zip_path}')
    print(f' - {dmg_path}')
    print('\n完成。')


if __name__ == '__main__':
    main()
