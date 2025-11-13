#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[build] 开始执行打包脚本 build.py..."

PY="python3"
if ! command -v python3 >/dev/null 2>&1; then
  if [ -x "venv/bin/python" ]; then
    PY="venv/bin/python"
  elif command -v python >/dev/null 2>&1; then
    PY="python"
  fi
fi

"$PY" build.py

echo "[build] 打包完成，产物位于: dist/YT-DLP GUI.app"
