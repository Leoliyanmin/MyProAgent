# ProAgent Desktop - 快速启动指南

## 立即开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 开发模式（测试桌面版）

```bash
# 终端 1: 启动 Python 后端
cd local_backend
uvicorn main:app --reload --host 0.0.0.0 --port 8002

# 终端 2: 启动 Tauri 桌面应用
cd frontend
npm run tauri:dev
```

这将打开一个桌面窗口，加载你的 Vue 应用。

### 3. 构建 Sidecar（生产环境）

```bash
# 安装 PyInstaller（首次需要）
pip install pyinstaller

# 构建 Python 可执行文件
python scripts/build_sidecar.py
```

生成的文件位于 `frontend/src-tauri/binaries/`。

构建完成后，为 Tauri 创建软链接：

```bash
cd frontend/src-tauri/binaries
for f in python-backend-*; do [ -f "$f" ] && ln -sf "$f" python-backend; done
for f in server-backend-*; do [ -f "$f" ] && ln -sf "$f" server-backend; done
```

### 4. 构建桌面应用（生产版）

推荐使用一键脚本（含 sidecar 构建、软链接、图标生成）：

```bash
bash scripts/build_and_run.sh
```

或手动：

```bash
cd frontend
npm run tauri:build
```

输出文件：
- macOS: `src-tauri/target/release/bundle/dmg/ProAgent_*.dmg`

## 项目结构（Tauri 相关）

```
frontend/
├── src-tauri/
│   ├── src/main.rs         # Rust 入口，自动启动 Python sidecar
│   ├── capabilities/
│   │   └── default.json    # 权限配置（sidecar 启动权限）
│   ├── binaries/           # Python sidecar 二进制文件（构建后）
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/services/
│   └── tauri-api.js        # 桌面端 API 封装
└── vite.config.js

scripts/
├── python_backend.py       # Python sidecar 入口
├── server_backend.py       # Server sidecar 入口
└── build_sidecar.py        # PyInstaller 构建脚本
```

## 常见问题

### Rust 编译失败？
确保 Rust 版本 >= 1.77.2：
```bash
rustc --version
```

### Sidecar 找不到？
检查 `frontend/src-tauri/binaries/` 下是否有 `python-backend-*` 文件，以及是否创建了不带 triple 的软链接：
```bash
ls -la frontend/src-tauri/binaries/
```

### 端口冲突？
修改 `local_backend/main.py` 或 `scripts/python_backend.py` 中的端口配置。

## 详细文档

- [TAURI_README.md](TAURI_README.md) - 完整开发指南
- [TAURI_CROSS_PLATFORM.md](TAURI_CROSS_PLATFORM.md) - macOS 构建和 sidecar 命名说明
