# Tauri 跨平台配置指南

## macOS vs Windows 差异

### 1. Sidecar 二进制文件命名

Tauri 根据目标平台自动选择正确的 sidecar 文件名：

| 平台 | Target Triple | Sidecar 文件名 |
|------|---------------|----------------|
| macOS (Intel) | `x86_64-apple-darwin` | `python-backend-x86_64-apple-darwin` |
| macOS (Apple Silicon) | `aarch64-apple-darwin` | `python-backend-aarch64-apple-darwin` |
| Windows (x64) | `x86_64-pc-windows-msvc` | `python-backend-x86_64-pc-windows-msvc.exe` |
| Windows (x86) | `i686-pc-windows-msvc` | `python-backend-i686-pc-windows-msvc.exe` |
| Linux (x64) | `x86_64-unknown-linux-gnu` | `python-backend-x86_64-unknown-linux-gnu` |

### 2. 构建配置

#### macOS 特定配置

`src-tauri/tauri.conf.json`:
```json
{
  "bundle": {
    "macOS": {
      "frameworks": [],
      "minimumSystemVersion": "10.13",
      "entitlements": null,
      "signingIdentity": null,
      "hardenedRuntime": false
    }
  }
}
```

#### Windows 特定配置

`src-tauri/tauri.conf.json`:
```json
{
  "bundle": {
    "windows": {
      "wix": {
        "language": "zh-CN",
        "upgradeCode": "your-uuid-here"
      },
      "nsis": {
        "languages": ["SimpChinese"],
        "displayLanguageSelector": false
      }
    }
  }
}
```

### 3. 平台特定代码

#### Rust 代码中的平台检测

```rust
// src-tauri/src/main.rs

#[cfg(target_os = "macos")]
fn setup_macos_specific() {
    // macOS 特定设置
}

#[cfg(target_os = "windows")]
fn setup_windows_specific() {
    // Windows 特定设置
}

fn main() {
    #[cfg(target_os = "macos")]
    setup_macos_specific();
    
    #[cfg(target_os = "windows")]
    setup_windows_specific();
    
    // ... 通用代码
}
```

### 4. 构建脚本的平台检测

#### `scripts/build_sidecar.py` 更新版

```python
import platform
import subprocess
import sys
from pathlib import Path

def get_target_triple():
    """检测当前平台"""
    system = platform.system()
    machine = platform.machine()
    
    if system == "Darwin":  # macOS
        if machine == "arm64":
            return "aarch64-apple-darwin"
        return "x86_64-apple-darwin"
    
    elif system == "Windows":
        if machine == "AMD64":
            return "x86_64-pc-windows-msvc"
        return "i686-pc-windows-msvc"
    
    else:  # Linux
        return "x86_64-unknown-linux-gnu"

def build_sidecar():
    target = get_target_triple()
    output_name = f"python-backend-{target}"
    
    # Windows 需要 .exe 后缀
    if platform.system() == "Windows":
        output_name += ".exe"
    
    print(f"Building for {target}...")
    
    # PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", output_name,
        "scripts/python_backend.py"
    ]
    
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    build_sidecar()
```

### 5. CI/CD 跨平台构建

#### GitHub Actions 配置

`.github/workflows/build.yml`:

```yaml
name: Build Tauri App

on:
  push:
    branches: [main]

jobs:
  build:
    strategy:
      matrix:
        include:
          - platform: macos-latest
            args: "--target aarch64-apple-darwin"
          - platform: macos-latest
            args: "--target x86_64-apple-darwin"
          - platform: windows-latest
            args: ""
          - platform: ubuntu-latest
            args: ""

    runs-on: ${{ matrix.platform }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Setup Rust
        uses: dtolnay/rust-action@stable

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd frontend && npm install
          pip install pyinstaller

      - name: Build Sidecar
        run: python scripts/build_sidecar.py

      - name: Build Tauri App
        run: cd frontend && npm run tauri:build ${{ matrix.args }}

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: app-${{ matrix.platform }}
          path: frontend/src-tauri/target/release/bundle/**
```

### 6. 本地跨平台构建步骤

#### 在 macOS 上构建

```bash
# 1. 构建 macOS sidecar
cd scripts
python build_sidecar.py
# 输出: python-backend-aarch64-apple-darwin

# 2. 构建 macOS 应用
cd ../frontend
npm run tauri:build

# 3. 输出
# src-tauri/target/release/bundle/dmg/ProAgent_0.1.0_aarch64.dmg
```

#### 在 Windows 上构建

```powershell
# 1. 构建 Windows sidecar
cd scripts
python build_sidecar.py
# 输出: python-backend-x86_64-pc-windows-msvc.exe

# 2. 构建 Windows 应用
cd ../frontend
npm run tauri:build

# 3. 输出
# src-tauri/target/release/bundle/nsis/ProAgent_0.1.0_x64-setup.exe
```

### 7. 统一分发包

如果你需要在一个平台上构建所有版本，可以使用交叉编译：

#### macOS 上构建所有版本

```bash
# 添加 Windows 目标
rustup target add x86_64-pc-windows-msvc

# 需要安装 mingw-w64
brew install mingw-w64

# 构建 Windows 版本（仅 Rust 部分，Python 需要在 Windows 上打包）
cd frontend
npm run tauri:build -- --target x86_64-pc-windows-msvc
```

**注意**: Python sidecar 必须在目标平台上构建，因为 PyInstaller 不支持跨平台编译。

### 8. 推荐的开发流程

#### 开发阶段
- 使用 `npm run tauri:dev` 在所有平台上测试
- Python 后端以源码形式运行

#### 发布阶段
- 在每个目标平台上分别构建 sidecar
- 将 sidecar 复制到 `src-tauri/binaries/`
- 运行 `npm run tauri:build`

#### 自动化
- 使用 GitHub Actions 在多个 runner 上并行构建
- 收集所有平台的构建产物
- 发布到 GitHub Releases

### 9. 文件路径差异

| 特性 | macOS | Windows |
|------|-------|---------|
| 路径分隔符 | `/` | `\\` |
| 配置目录 | `~/Library/Application Support/ProAgent` | `%APPDATA%/ProAgent` |
| 临时目录 | `/tmp` | `%TEMP%` |
| 可执行后缀 | 无 | `.exe` |

Rust 中统一处理：

```rust
use std::path::PathBuf;

fn get_config_dir() -> PathBuf {
    tauri::api::path::app_config_dir(
        &tauri::Config::default()
    ).expect("Failed to get config dir")
}
```

### 10. 权限差异

#### macOS
- 需要签名才能在网外运行
- 可能需要 notarization（公证）
- 沙盒权限在 `entitlements` 中配置

#### Windows
- 需要代码签名证书避免 SmartScreen 警告
- Defender 可能误报，需要白名单

## 总结

| 任务 | macOS | Windows |
|------|-------|---------|
| 开发测试 | ✅ 支持 | ✅ 支持 |
| 本地构建 | ✅ 支持 | ✅ 支持 |
| Sidecar 打包 | 本地构建 | 本地构建 |
| 发布构建 | GitHub Actions | GitHub Actions |
| 代码签名 | 推荐 | 推荐 |

**建议**: 使用 GitHub Actions 自动化多平台构建，避免手动在多个系统上操作。
