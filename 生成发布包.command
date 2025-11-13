#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[release] 开始生成 ZIP 与 DMG..."

PY="python3"
if ! command -v python3 >/dev/null 2>&1 && [ -x "venv/bin/python" ]; then
  PY="venv/bin/python"
fi

"$PY" release.py

echo "[release] 完成，文件在 release/ 目录下。"
