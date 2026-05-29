## Why

解绑 TIS/Blackboard 后，重新点击绑定按钮无法触发后端请求。根因是 `extract_cookies` 使用 `document.cookie`（JS eval）提取 Cookie，无法读取 HttpOnly Cookie（如 JSESSIONID、TGC），导致提取结果为空，`completeBinding` 静默失败，后端绑定请求从未发出。同时 `open_cas_login` 缺少窗口存在性检查，重复创建同标签窗口会静默失败。

## What Changes

- 修复 `extract_cookies`：用 Tauri v2.8+ 原生 Cookie API（`cookies_for_url` / `cookies`）替换 `document.cookie` JS eval，可正确读取 HttpOnly Cookie
- 修复 `open_cas_login`：创建窗口前检查同标签窗口是否已存在，若存在则聚焦而非重复创建
- 修复 `completeBinding`：Cookie 提取为空时向用户显示错误提示，而非静默回退到 `unbound`
- 修复 `extract_all_cookies`：同步使用原生 Cookie API

## Capabilities

### New Capabilities

- `native-cookie-extraction`: 使用 Tauri 原生 Cookie API 提取 webview 中的 HttpOnly Cookie，替代 JS eval 方式

### Modified Capabilities

- `bind-flow-ux`: 绑定流程的错误反馈和窗口管理行为变更——空 Cookie 时显示错误提示，重复打开窗口时聚焦已有窗口

## Impact

- **frontend/src-tauri/src/lib.rs**: `extract_cookies`、`extract_all_cookies`、`open_cas_login` 实现变更
- **frontend/src/views/UserSettingsView.vue**: `completeBinding` 增加错误提示
- **Tauri 版本依赖**: 需要 Tauri v2.8+（`cookies_for_url` API 在 v2.8 引入，cas-demo 已使用）
- **后端无变更**: `tis_routes.py`、`blackboard_routes.py`、`tis_service.py`、`blackboard_service.py` 不受影响
