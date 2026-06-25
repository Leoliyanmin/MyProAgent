# Tauri macOS 桌面端快速参考

## Sidecar 文件名

```
macOS (Intel):         python-backend-x86_64-apple-darwin
macOS (Apple Silicon): python-backend-aarch64-apple-darwin
```

## 本地开发

```bash
cd frontend
npm run tauri:dev
```

## 生产构建

```bash
cd scripts
python build_sidecar.py

cd ../frontend
npm run tauri:build
```

## 输出文件

| 平台 | 输出文件 |
|------|----------|
| macOS | `.dmg` |

详细说明见 `TAURI_CROSS_PLATFORM.md`
