#!/bin/bash
set -e
cd "$(dirname "$0")/.."

echo "=== 1. 编译 sidecar ==="
python3 scripts/build_sidecar.py

echo "=== 2. 重命名 sidecar（与 CI 保持一致）==="
(
  cd frontend/src-tauri/binaries
  for f in python-backend-*; do
    [ -f "$f" ] && ln -sf "$f" python-backend
  done
  for f in server-backend-*; do
    [ -f "$f" ] && ln -sf "$f" server-backend
  done
  [ -f python-backend ] || { echo "ERROR: python-backend sidecar not found"; exit 1; }
  [ -f server-backend ] || { echo "ERROR: server-backend sidecar not found"; exit 1; }
)

echo "=== 3. 生成图标 ==="
python3 scripts/gen_icon.py

echo "=== 4. 构建 Tauri 应用 ==="
cd frontend && npm run tauri:build && cd ..

echo "=== 5. 去隔离 + 打开 ==="
APP_DIR="frontend/src-tauri/target/release/bundle/macos/ProAgent.app"
sudo xattr -cr "$APP_DIR"
open "$APP_DIR"

echo "=== 完成 ==="
