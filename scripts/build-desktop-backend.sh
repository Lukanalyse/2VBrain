#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"
BUILD_DIR="$BACKEND_DIR/.desktop-build"
BIN_DIR="$ROOT_DIR/frontend/src-tauri/binaries"
RUSTC_BIN="${RUSTC_BIN:-$HOME/.cargo/bin/rustc}"

if [ ! -x "$VENV_DIR/bin/python" ]; then
  python -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c 'import PyInstaller, fastapi, uvicorn' >/dev/null 2>&1; then
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install -e "$BACKEND_DIR" pyinstaller
fi

TARGET_TRIPLE=$(
  "$RUSTC_BIN" -vV | sed -n 's/^host: //p'
)

mkdir -p "$BIN_DIR" "$BUILD_DIR/spec"

"$VENV_DIR/bin/python" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name "research-os-backend-$TARGET_TRIPLE" \
  --paths "$BACKEND_DIR" \
  --collect-all uvicorn \
  --distpath "$BIN_DIR" \
  --workpath "$BUILD_DIR/work" \
  --specpath "$BUILD_DIR/spec" \
  "$BACKEND_DIR/desktop_entry.py"

chmod +x "$BIN_DIR/research-os-backend-$TARGET_TRIPLE"
printf 'Desktop backend ready: %s\n' "$BIN_DIR/research-os-backend-$TARGET_TRIPLE"
