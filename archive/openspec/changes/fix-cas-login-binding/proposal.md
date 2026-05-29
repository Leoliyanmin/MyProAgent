## Why

用户设置页面的 TIS/Blackboard 绑定按钮点击"打开登录"后无任何反应——CAS 认证窗口不会弹出，cookie 提取和绑定流程完全中断。当前实现使用动态 import + 复杂的错误处理链，导致 Tauri IPC 调用静默失败。而 cas-demo 使用静态 import + 简洁的 invoke 调用，能正常打开窗口、提取 cookie、完成绑定。需要将 cas-demo 的成熟流程移植到主应用，并实现一键式自动绑定（登录→提取→爬取→显示）。

## What Changes

- 修复 Tauri IPC 调用：从动态 import 改为静态 import `@tauri-apps/api/core`，与 cas-demo 一致
- 实现自动绑定流程：用户点击"打开登录"→ CAS WebView 弹出→用户登录→自动检测登录完成→自动提取 cookie→自动调用后端 bind→自动刷新状态
- CAS WebView 登录完成后自动导航到 BB 系统（为 BB 绑定获取 cookie）
- 绑定成功后自动关闭 CAS 窗口
- 绑定成功后自动导入数据到 Calendar 和 Dashboard Todo
- 修复所有失败路径的状态重置：任何步骤失败都回到 'unbound'，用户可重试
- 移除两步式手动流程（"打开登录" + "提取Cookie并绑定"），改为一步式自动流程

## Capabilities

### New Capabilities
- `cas-auto-binding`: CAS 认证窗口管理、自动 cookie 提取、自动绑定、自动数据导入的完整流程

### Modified Capabilities

## Impact

- **前端**: `UserSettingsView.vue` — 绑定按钮逻辑、Tauri invoke 调用方式、状态管理
- **前端**: `CalendarView.vue` — 绑定成功后自动触发 TIS schedule 导入
- **前端**: `DashboardView.vue` — 绑定成功后自动触发 BB assignment 导入到 todo
- **Rust**: `src-tauri/src/lib.rs` — 可能需要新增 `on_navigation_complete` 事件监听或 URL 变化检测命令
- **后端**: 无变化 — `/bind`、`/status`、`/schedule`、`/assignments` 端点已存在
- **依赖**: `@tauri-apps/api/core` — 从动态 import 改为静态 import