# YT-DLP GUI for macOS

一个简单易用的 YouTube 视频下载工具，基于 yt-dlp 开发的图形界面程序。

## 系统要求

- macOS 10.15 或更高版本
- 支持 Intel 和 Apple Silicon (M 系列) Mac
- 通过 Homebrew 安装的以下依赖：
  - yt-dlp: 视频下载核心
  - ffmpeg: 音视频处理工具

## 安装步骤

1. 安装必需依赖：
   ```bash
   # 安装 Homebrew（如果尚未安装）
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # 安装核心依赖
   brew install yt-dlp ffmpeg
   ```

2. 获取最新稳定版：
   - 前往 [Releases 页面](https://github.com/luluyayawawa123/yt-dlp-gui/releases/latest) 下载 `YT-DLP-GUI-macOS-v*.zip`
   - 解压后将 `YT-DLP GUI.app` 拖放到 `应用程序` 文件夹

3. 首次运行：
   - 在"系统设置" > "隐私与安全性"中允许运行
   - 或右键点击应用选择"打开"

## 首次使用设置

1. 权限设置（必需）：
   - 应用会提示需要完全磁盘访问权限
   - 按照提示操作：
     1. 打开"系统设置" > "隐私与安全性" > "完全磁盘访问权限"
     2. 点击"+"添加本应用
     3. 启用权限开关
     4. 重启应用

2. 浏览器设置：
   - 支持 Safari（默认）、Chrome 和 Edge
   - 确保已在浏览器中登录 YouTube 账号（用于会员视频下载）

## 使用说明

### 基础模式
- 批量下载（每行一个视频链接）
- 选择下载目录
- 实时进度显示
- 下载历史自动保存

### 高级模式
- 视频格式分析
- 自定义音视频质量
- 详细下载日志

## 常见问题

1. **提示"未找到 yt-dlp"**
   - 重新安装依赖：`brew reinstall yt-dlp`
   - 验证安装：`which yt-dlp`

2. **无法下载会员视频**
   - 检查浏览器是否已登录
   - 确认已授予完全磁盘访问权限

3. **应用无法启动**
   - 确保已安装全部依赖
   - 尝试右键点击选择"打开"

## 调试
- 日志路径：`~/Library/Application Support/YT-DLP-GUI/debug.log`
- 包含：
  - 系统环境信息
  - 命令执行记录
  - 错误详情等信息