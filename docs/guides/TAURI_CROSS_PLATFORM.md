# Tauri macOS 桌面端指南

## 快速参考

| 场景 | 命令 |
|------|------|
| 开发模式 | `cd frontend && npm run tauri:dev` |
| 构建 sidecar | `python scripts/build_sidecar.py` |
| 生产构建 | `bash scripts/build_and_run.sh` |

Sidecar 文件名：

```
macOS Intel:         python-backend-x86_64-apple-darwin
macOS Apple Silicon: python-backend-aarch64-apple-darwin
```

---

## 支持范围

当前桌面端构建链路仅保留 macOS。

## Sidecar 命名

| 平台 | Target Triple | Sidecar 文件名 |
|------|---------------|----------------|
| macOS (Intel) | `x86_64-apple-darwin` | `python-backend-x86_64-apple-darwin` |
| macOS (Apple Silicon) | `aarch64-apple-darwin` | `python-backend-aarch64-apple-darwin` |

Tauri 要求 sidecar 同时存在带 triple 的文件和不带 triple 的软链接。`scripts/build_sidecar.py` 生成带 triple 的文件后，需手动或通过 `scripts/build_and_run.sh` 创建软链接：

```bash
cd frontend/src-tauri/binaries
for f in python-backend-*; do [ -f "$f" ] && ln -sf "$f" python-backend; done
for f in server-backend-*; do [ -f "$f" ] && ln -sf "$f" server-backend; done
```

## 构建原则

PyInstaller sidecar 只在 macOS 构建链路中维护。

## Tauri 配置

`frontend/src-tauri/tauri.conf.json` 当前只保留：

- `app`
- `dmg`

## 本地构建

使用一键脚本（推荐）：

```bash
bash scripts/build_and_run.sh
```

或手动分步执行：

```bash
# 1. 构建 sidecar
python scripts/build_sidecar.py

# 2. 创建 sidecar 软链接
cd frontend/src-tauri/binaries
for f in python-backend-*; do [ -f "$f" ] && ln -sf "$f" python-backend; done
for f in server-backend-*; do [ -f "$f" ] && ln -sf "$f" server-backend; done
cd ../../..

# 3. 生成图标
python scripts/gen_icon.py

# 4. Tauri 构建
cd frontend && npm run tauri:build
```

## CI/CD

CI 只保留 macOS 的桌面端构建产物上传。

## 输出文件

| 平台 | 输出文件 |
|------|----------|
| macOS | `frontend/src-tauri/target/release/bundle/dmg/ProAgent_*.dmg` |
