# Tauri 桌面端平台指南

## 支持范围

当前桌面端构建链路仅保留：

- macOS
- Linux

Windows 相关脚本、打包目标和 CI 已从主线移除，避免继续维护额外分支。

## Sidecar 命名

| 平台 | Target Triple | Sidecar 文件名 |
|------|---------------|----------------|
| macOS (Intel) | `x86_64-apple-darwin` | `python-backend-x86_64-apple-darwin` |
| macOS (Apple Silicon) | `aarch64-apple-darwin` | `python-backend-aarch64-apple-darwin` |
| Linux (x64) | `x86_64-unknown-linux-gnu` | `python-backend-x86_64-unknown-linux-gnu` |
| Linux (arm64) | `aarch64-unknown-linux-gnu` | `python-backend-aarch64-unknown-linux-gnu` |

## 构建原则

PyInstaller 不支持跨平台打包 Python sidecar，因此需要在目标平台本机构建。

## Tauri 配置

`frontend/src-tauri/tauri.conf.json` 当前只保留：

- `app`
- `dmg`
- `appimage`

## 本地构建

```bash
cd scripts
python build_sidecar.py

cd ../frontend
npm run tauri:build
```

## CI/CD

CI 只保留 macOS 和 Linux 的桌面端构建产物上传。

## 输出文件

| 平台 | 输出文件 |
|------|----------|
| macOS | `frontend/src-tauri/target/release/bundle/dmg/ProAgent_*.dmg` |
| Linux | `frontend/src-tauri/target/release/bundle/appimage/ProAgent_*.AppImage` |
