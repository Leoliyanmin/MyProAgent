# ProAgent 桌面端迁移总结

## 已完成的工作

### 1. Tauri 项目结构初始化 ✅
- `frontend/src-tauri/` - Rust 项目配置
- `Cargo.toml` - Rust 依赖和构建设置
- `tauri.conf.json` - Tauri 主配置
- `src/main.rs` - Rust 入口，自动启动 Python sidecar
- `capabilities/default.json` - 权限配置

### 2. Python Sidecar 打包配置 ✅
- `scripts/python_backend.py` - Python 后端打包入口
- `scripts/build_sidecar.py` - PyInstaller 构建脚本
- 配置监听 stdin 以响应关闭命令

### 3. 前端集成 ✅
- 更新 `vite.config.js` - 支持 Tauri 开发模式
- 创建 `src/services/tauri-api.js` - 桌面端 API 服务封装
- 更新 `package.json` - 添加 Tauri 脚本
- 安装 `@tauri-apps/plugin-shell` 和 `@tauri-apps/plugin-opener`

### 4. 文档 ✅
- `TAURI_README.md` - 完整的开发和构建指南

## 项目结构

```
.
├── frontend/
│   ├── src-tauri/              # Tauri 配置
│   │   ├── src/main.rs         # Rust 入口
│   │   ├── capabilities/       # 权限
│   │   ├── binaries/           # Python sidecar (构建后)
│   │   ├── Cargo.toml
│   │   └── tauri.conf.json
│   ├── src/services/tauri-api.js
│   ├── package.json
│   └── vite.config.js
├── local_backend/              # Python FastAPI (未修改)
├── scripts/                    # 构建脚本
│   ├── python_backend.py
│   └── build_sidecar.py
└── TAURI_README.md
```

## 下一步操作

### 1. 安装依赖

```bash
cd frontend
npm install

# 安装 PyInstaller
cd ../local_backend
pip install pyinstaller
```

### 2. 开发测试

```bash
# 终端 1: 启动 Python 后端
cd local_backend
uvicorn main:app --reload --host 0.0.0.0 --port 8002

# 终端 2: 启动 Tauri 开发模式
cd frontend
npm run tauri:dev
```

### 3. 构建 Sidecar

```bash
cd scripts
python build_sidecar.py
```

### 4. 构建桌面应用

```bash
cd frontend
npm run tauri:build
```

## 技术要点

### Sidecar 机制
- Python 后端通过 PyInstaller 打包为可执行文件
- Tauri 使用 `externalBin` 配置将其嵌入应用
- Rust 主进程在启动时自动启动 Python sidecar
- 通过 stdin 发送 `sidecar shutdown` 命令关闭后端

### 前端通信
- 保持与网页版相同的 HTTP API (`http://localhost:8002`)
- 无需修改现有 Vue 组件代码
- 通过环境变量区分 Tauri 和网页模式

### 数据存储
- 桌面版使用本地 SQLite 数据库
- 数据库路径: `~/.proagent/`

## 优势

1. **小体积**: Tauri + 系统 WebView (对比 Electron 的 Chromium)
2. **高性能**: Rust 后端，Native WebView
3. **独立分发**: 用户无需安装 Python 或 Node.js
4. **系统集成**: 可访问系统通知、文件系统、全局快捷键等
5. **保留原有架构**: Python FastAPI 后端无需重写

## 注意事项

1. 首次构建可能需要较长时间（Rust 编译）
2. 需要为每个平台单独构建 sidecar
3. 应用体积主要包括：WebView + Python 运行时 + 前端代码

## 参考资源

- [Tauri 官方文档](https://v2.tauri.app/)
- [Tauri + Python Sidecar 示例](https://github.com/dieharders/example-tauri-v2-python-server-sidecar)
- [PyInstaller 文档](https://pyinstaller.org/)
