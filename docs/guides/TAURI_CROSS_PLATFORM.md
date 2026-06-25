# Tauri macOS 桌面端指南

## 支持范围

当前桌面端构建链路仅保留：

- macOS

## Sidecar 命名

| 平台 | Target Triple | Sidecar 文件名 |
|------|---------------|----------------|
| macOS (Intel) | `x86_64-apple-darwin` | `python-backend-x86_64-apple-darwin` |
| macOS (Apple Silicon) | `aarch64-apple-darwin` | `python-backend-aarch64-apple-darwin` |

## 构建原则

PyInstaller sidecar 只在 macOS 构建链路中维护。

## Tauri 配置

`frontend/src-tauri/tauri.conf.json` 当前只保留：

- `app`
- `dmg`

## 本地构建

```bash
cd scripts
python build_sidecar.py

cd ../frontend
npm run tauri:build
```

## CI/CD

CI 只保留 macOS 的桌面端构建产物上传。

## 输出文件

| 平台 | 输出文件 |
|------|----------|
| macOS | `frontend/src-tauri/target/release/bundle/dmg/ProAgent_*.dmg` |
