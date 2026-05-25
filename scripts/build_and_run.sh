#!/bin/bash
set -e
cd "$(dirname "$0")/.."

echo "=== 1. 编译 sidecar ==="
python3 scripts/build_sidecar.py

echo "=== 2. 生成图标 ==="
python3 scripts/gen_icon.py

echo "=== 3. 构建 Tauri 应用 ==="
cd frontend && npm run tauri:build && cd ..

echo "=== 4. 修复 bundle 路径 ==="
APP_DIR="frontend/src-tauri/target/release/bundle/macos/ProAgent.app"
mkdir -p "$APP_DIR/Contents/MacOS/binaries"
ln -sf ../python-backend "$APP_DIR/Contents/MacOS/binaries/python-backend"
ln -sf ../server-backend "$APP_DIR/Contents/MacOS/binaries/server-backend"

echo "=== 5. 去隔离 + 打开 ==="
sudo xattr -cr "$APP_DIR"
open "$APP_DIR"

echo "=== 完成 ==="
