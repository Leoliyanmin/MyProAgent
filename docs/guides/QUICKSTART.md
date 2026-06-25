# ProAgent Desktop - 快速启动指南

> **重要：先激活 Python 虚拟环境**
>
> 虚拟环境在项目根目录的上层：
> ```
> 路径: ../.venv/bin/python
> ```
>
> ```bash
> cd /path/to/MyProAgent
> source ../.venv/bin/activate
> ```

## 已完成配置

Tauri 桌面端项目已成功配置。项目结构：

```
frontend/
├── src-tauri/              # Tauri 配置和 Rust 代码 ✅
│   ├── src/
│   │   ├── main.rs         # Rust 入口，自动启动 Python sidecar
│   │   └── lib.rs
│   ├── capabilities/
│   │   └── default.json    # 权限配置（包含 sidecar 启动权限）
│   ├── binaries/           # Python sidecar 二进制文件位置
│   ├── Cargo.toml          # Rust 依赖配置
│   ├── tauri.conf.json     # Tauri 主配置
│   └── build.rs            # Rust 构建脚本
├── src/services/
│   └── tauri-api.js        # 桌面端 API 封装
├── package.json            # 添加 tauri 脚本
└── vite.config.js          # 更新为 Tauri 模式

scripts/
├── python_backend.py       # Python sidecar 入口
└── build_sidecar.py        # PyInstaller 构建脚本
```

## 立即开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 开发模式（测试桌面版）

```bash
# 终端 1: 启动 Python 后端（保持现有开发流程）
cd local_backend
uvicorn main:app --reload --host 0.0.0.0 --port 8002

# 终端 2: 启动 Tauri 桌面应用
cd frontend
npm run tauri:dev
```

这将打开一个桌面窗口，加载你的 Vue 应用。

### 3. 构建 Sidecar（生产环境）

```bash
# 安装 PyInstaller
cd local_backend
pip install pyinstaller

# 构建 Python 可执行文件
cd ../scripts
python build_sidecar.py
```

生成的文件位于 `frontend/src-tauri/binaries/`。

### 4. 构建桌面应用（生产版）

```bash
cd frontend
npm run tauri:build
```

输出文件：
- macOS: `src-tauri/target/release/bundle/dmg/ProAgent_*.dmg`

## 常见问题

### Rust 编译失败？
确保 Rust 版本 >= 1.77.2:
```bash
rustc --version
```

### Python 后端未启动？
1. 检查 `src-tauri/binaries/python-backend-*` 是否存在
2. 检查是否有执行权限: `chmod +x python-backend-*`

### 端口冲突？
修改 `local_backend/main.py` 或 `scripts/python_backend.py` 中的端口配置。

## 后续可以添加的功能

- [ ] 系统通知（`@tauri-apps/plugin-notification`）
- [ ] 系统托盘图标
- [ ] 全局快捷键
- [ ] 自动更新
- [ ] 原生文件选择对话框

## 详细文档

- `TAURI_README.md` - 完整开发指南
- `TAURI_MIGRATION_SUMMARY.md` - 迁移总结
