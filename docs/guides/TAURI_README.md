# ProAgent Desktop - Tauri 桌面应用

ProAgent 的桌面端版本，基于 Tauri + Vue 3 + Python FastAPI。

## 架构说明

```
┌─────────────────────────────────────────────────────────┐
│                    Tauri Application                     │
│  ┌──────────────┐  ┌─────────────────────────────────┐  │
│  │  Vue 3 前端   │  │      Rust (Tauri Runtime)        │  │
│  │   (WebView)   │  │   • Window Management            │  │
│  └───────┬──────┘  │   • System APIs                    │  │
│          │         │   • Sidecar Management             │  │
│          │ IPC     └───────────────┬─────────────────────┘  │
│          │                         │                        │
│          │   HTTP 127.0.0.1:8002   │                        │
│          └────────────────────────►│                        │
│                                    ▼                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Python Backend (FastAPI + SQLite)              │  │
│  │   • User Authentication      • Task Management       │  │
│  │   • Schedule Management      • AI Assistant          │  │
│  │   • File Management          • Data Sync             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 项目结构

```
.
├── frontend/                    # Vue 3 前端
│   ├── src-tauri/              # Tauri 配置和 Rust 代码
│   │   ├── src/                # Rust 源代码
│   │   ├── capabilities/       # Tauri 权限配置
│   │   ├── binaries/           # Python sidecar 二进制文件
│   │   ├── Cargo.toml          # Rust 依赖
│   │   └── tauri.conf.json     # Tauri 主配置
│   ├── src/                    # Vue 源代码
│   ├── package.json
│   └── vite.config.js
│
├── local_backend/              # Python FastAPI 后端
│   ├── main.py                 # 后端入口
│   ├── business/               # 业务逻辑
│   ├── presentation/           # API 路由
│   └── requirements.txt
│
├── scripts/                    # 构建脚本
│   ├── python_backend.py       # Python sidecar 入口
│   └── build_sidecar.py        # 打包脚本
│
└── README.md                   # 本文档
```

## 开发环境要求

- **Node.js**: ^20.19.0 || >=22.12.0
- **Rust**: 1.77.2+ (用于 Tauri)
- **Python**: 3.10+ (用于后端)
- **PyInstaller**: 用于打包 Python 为可执行文件

## 快速开始

### 1. 安装依赖

```bash
# 编辑 .config.json 文件配置配置模型
cp config.example.json config.json
```
```bash
# 前端依赖
cd frontend
npm install

# Python 依赖
cd ../local_backend
pip install -r requirements.txt
pip install pyinstaller  # 用于打包 sidecar
```

### 2. 开发模式

在开发模式下，Python 后端和 Tauri 分别运行：

```bash
# 终端 1: 启动 Python 后端
cd local_backend
uvicorn main:app --reload --host 0.0.0.0 --port 8002

# 终端 2: 启动 Tauri 开发服务器
cd frontend
npm run tauri:dev
```

### 3. 构建 Sidecar (Python 后端)

在生产环境中，Python 后端需要打包为可执行文件：

```bash
cd scripts
python build_sidecar.py
```

打包后的文件将位于 `frontend/src-tauri/binaries/`。

### 4. 构建桌面应用

```bash
cd frontend

# 构建开发版本
npm run tauri:build -- --debug

# 构建生产版本
npm run tauri:build
```

构建输出：
- **macOS**: `frontend/src-tauri/target/release/bundle/dmg/ProAgent_*.dmg`
- **Linux**: `frontend/src-tauri/target/release/bundle/appimage/ProAgent_*.AppImage`

## 关键配置说明

### Tauri 配置 (tauri.conf.json)

```json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../dist"
  },
  "bundle": {
    "externalBin": ["binaries/python-backend"]
  }
}
```

### Sidecar 权限配置 (capabilities/default.json)

```json
{
  "permissions": [
    "shell:allow-spawn",
    {
      "identifier": "shell:allow-spawn",
      "allow": [{ "name": "binaries/python-backend", "sidecar": true }]
    }
  ]
}
```

## 前端与后端通信

桌面版与网页版使用相同的 HTTP API，无需修改现有代码：

```javascript
// 在 Vue 组件中使用
import { apiRequest, authApi, taskApi } from '@/services/tauri-api.js'

// 登录
const login = async () => {
  const response = await authApi.login(email, password)
  // ...
}

// 获取任务列表
const tasks = await taskApi.getAll(token)
```

## 系统功能扩展

Tauri 提供了以下系统级 API，可逐步集成：

- **系统通知**: `@tauri-apps/plugin-notification`
- **文件系统访问**: `@tauri-apps/plugin-fs`
- **全局快捷键**: `@tauri-apps/plugin-global-shortcut`
- **系统托盘**: `tauri::SystemTray`
- **自动更新**: `@tauri-apps/plugin-updater`

## 注意事项

1. **端口占用**: 确保 8002 端口未被占用
2. **CORS**: Python 后端已配置允许本地请求
3. **数据库**: 桌面版使用本地 SQLite 数据库，路径为 `~/.proagent/`
4. **首次启动**: 可能需要等待 Python 后端初始化完成

## 故障排查

### Python 后端未启动

检查日志输出，确认 `src-tauri/binaries/python-backend-*` 文件存在且可执行。

### 端口冲突

修改 `python_backend.py` 中的默认端口：
```python
port = int(os.environ.get("PROAGENT_PORT", "8003"))  # 改为其他端口
```

### 构建失败

1. 确保 Rust 版本 >= 1.77.2: `rustc --version`
2. 清理构建缓存: `npm run tauri:build -- --clean`

## 许可证

本项目仅供学习和教学使用。

---

Made with ❤️ by Team 26S-27
