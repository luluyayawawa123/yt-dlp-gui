#!/usr/bin/env bash
set -euo pipefail

# Resolve project directory (this script's location)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/venv"
ACTIVATE_SH="$VENV_DIR/bin/activate"

# Pick a python to create venv if needed
if command -v python3 >/dev/null 2>&1; then
  PYTHON_SYS="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_SYS="python"
else
  echo "未找到可用的 Python 解释器 (python3/python)。请先安装 Python。"
  exit 1
fi

# 基本提示
echo "[YT-DLP GUI] 初始化启动环境..."

# Create venv if missing (silent)
if [[ ! -d "$VENV_DIR" ]]; then
  echo "[YT-DLP GUI] 未检测到 venv，正在创建..."
  "$PYTHON_SYS" -m venv "$VENV_DIR" >/dev/null 2>&1 || "$PYTHON_SYS" -m venv "$VENV_DIR"
fi

PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

# Activate venv
source "$ACTIVATE_SH"

# Ensure Homebrew precedes venv so yt-dlp resolves to brew version
export PATH="/opt/homebrew/bin:/usr/local/bin:$VENV_DIR/bin:/usr/bin:/bin:$PATH"

# Upgrade pip (best effort, silent)
"$PYTHON_BIN" -m pip install --upgrade --quiet pip >/dev/null 2>&1 || true

# Ensure required packages (PyQt6 for GUI)
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
INSTALL_LOG="$LOG_DIR/install.log"

installed_any=0
installed_pyqt=0

# Ensure required packages silently (log to file for 诊断)
if ! "$PYTHON_BIN" -c 'import PyQt6' >/dev/null 2>&1; then
  echo "[YT-DLP GUI] 正在安装依赖: PyQt6 (详情见 $INSTALL_LOG)"
  if "$PIP_BIN" install --quiet --no-input PyQt6 >>"$INSTALL_LOG" 2>&1 || "$PIP_BIN" install PyQt6 >>"$INSTALL_LOG" 2>&1; then
    installed_any=1; installed_pyqt=1
  fi
fi

if [[ "$installed_any" -eq 1 ]]; then
  echo "[YT-DLP GUI] 依赖安装完成。PyQt6: $installed_pyqt"
else
  echo "[YT-DLP GUI] 依赖已满足。"
fi

# Ensure we don't accidentally use a pip yt-dlp inside venv
if [[ -x "$VENV_DIR/bin/yt-dlp" ]]; then
  echo "[YT-DLP GUI] 检测到 venv 内存在 yt-dlp，可选移除以避免误用 (详情见 $INSTALL_LOG)"
  "$PIP_BIN" uninstall -y yt-dlp >>"$INSTALL_LOG" 2>&1 || true
fi

# Launch the app in foreground, but silence noisy app output to log
APP_LOG="$LOG_DIR/app.log"

# Preflight diagnostics: resolved binaries and versions
{
  echo "[YT-DLP GUI] 预检信息: $(date)"
  echo "PATH=$PATH"
  echo "which yt-dlp: $(command -v yt-dlp || echo not-found)"
  echo "which ffmpeg: $(command -v ffmpeg || echo not-found)"
  if command -v yt-dlp >/dev/null 2>&1; then yt-dlp --version; fi
  if command -v ffmpeg >/dev/null 2>&1; then ffmpeg -version | head -n 1; fi
} >>"$APP_LOG" 2>&1

echo "[YT-DLP GUI] 正在启动应用... (运行日志: $APP_LOG)"
"$PYTHON_BIN" src/main.py >>"$APP_LOG" 2>&1
