# Tauri 跨平台快速参考

## 你需要知道的 3 件事

### 1. Sidecar 文件名不同

```
Mac (Intel):     python-backend-x86_64-apple-darwin
Mac (M1/M2/M3):  python-backend-aarch64-apple-darwin
Windows:         python-backend-x86_64-pc-windows-msvc.exe
Linux:           python-backend-x86_64-unknown-linux-gnu
```

**你的代码不需要改**——Tauri 会根据系统自动选择正确的文件。

### 2. 构建必须在目标平台上进行

PyInstaller **不支持**跨平台编译：

- ❌ 在 Mac 上打包 Windows 的 sidecar
- ❌ 在 Windows 上打包 Mac 的 sidecar

**解决方案**:
1. 在每个平台上分别构建
2. 或使用 GitHub Actions 自动构建（推荐）

### 3. 配置文件已处理平台差异

你的 `tauri.conf.json` 已经包含所有平台的配置：

```json
{
  "bundle": {
    "targets": ["app", "dmg", "appimage", "nsis"],
    "windows": { ... },
    "macOS": { ... }
  }
}
```

## 本地开发

开发时**完全无差异**：

```bash
# Mac 和 Windows 都运行同样的命令
npm run tauri:dev
```

## 生产构建流程

### 方案 A：分别在每台电脑上构建

**Mac 电脑**:
```bash
cd scripts
python build_sidecar.py  # 生成 Mac 版 sidecar
cd ../frontend
npm run tauri:build      # 生成 .dmg
```

**Windows 电脑**:
```powershell
cd scripts
python build_sidecar.py  # 生成 Windows 版 sidecar
cd ../frontend
npm run tauri:build      # 生成 .exe
```

### 方案 B：GitHub Actions 自动构建（推荐）

创建 `.github/workflows/build.yml`，push 代码后自动构建所有平台版本。

参考 `TAURI_CROSS_PLATFORM.md` 中的完整配置。

## 输出文件

| 平台 | 输出文件 | 用户如何安装 |
|------|----------|-------------|
| macOS | `.dmg` | 拖拽到 Applications |
| Windows | `.exe` (installer) | 双击安装 |
| Linux | `.AppImage` | 双击运行 |

## 常见问题

### Q: 我只有一台 Mac，能构建 Windows 版本吗？
**A**: Rust 代码可以交叉编译，但 Python sidecar 不行。推荐使用 GitHub Actions。

### Q: 用户下载后打不开？
**A**: 
- Mac: 需要在 系统设置 → 隐私与安全性 → 仍要打开
- Windows: 可能需要关闭 Defender 实时保护或添加白名单

### Q: 需要代码签名吗？
**A**: 不强制，但强烈推荐：
- Mac: 避免用户看到"无法验证开发者"警告
- Windows: 避免 SmartScreen 拦截

## 下一步

1. 在 Windows 上测试 `npm run tauri:dev` 是否正常
2. 分别在两个平台上运行 `build_sidecar.py`
3. 打包应用并测试
4. （可选）配置 GitHub Actions 自动化构建

详细说明见 `TAURI_CROSS_PLATFORM.md`
