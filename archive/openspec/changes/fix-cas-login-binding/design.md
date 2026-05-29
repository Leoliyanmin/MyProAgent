## Context

ProAgent 主应用的 TIS/BB 绑定功能依赖 Tauri WebView 打开 CAS 认证窗口，但当前实现无法正常工作。cas-demo 项目已有成熟的实现：静态 import `invoke`、手动两步流程（打开→提取→绑定）。主应用的问题链：

1. `tauriInvoke` 使用动态 `import('@tauri-apps/api/core')`，在 Vite HMR 环境下可能失败或延迟
2. `bindTis`/`bindBb` 的错误处理链过于复杂，失败时静默吞掉错误
3. 两步式流程（先"打开登录"再"提取Cookie并绑定")对用户不友好
4. 绑定成功后没有自动将数据导入到 Calendar/Todo

## Goals / Non-Goals

**Goals:**
- 点击"打开登录"→ CAS WebView 弹出 → 用户登录 → 自动完成 cookie 提取 + 绑定 + 数据导入
- 绑定成功后 Calendar 显示 TIS 课程、Dashboard Todo 显示 BB 作业
- 任何步骤失败都有可见反馈，且用户可重试
- TIS 和 BB 分别绑定（TIS 先绑定，BB 需额外导航到 bb.sustech.edu.cn）

**Non-Goals:**
- 不改变后端 API（`/bind`、`/status`、`/schedule`、`/assignments` 端点不变）
- 不改变 Rust 命令（`open_cas_login`、`extract_cookies`、`bind_tis`、`bind_blackboard` 不变）
- 不实现 CAS 登录的自动检测（无法可靠检测用户是否完成登录，仍需用户点击确认）
- 不处理 BB 作业的 due_date（爬虫限制，未来单独处理）

## Decisions

### D1: 静态 import 替代动态 import

**选择**: 在 `<script setup>` 中静态 `import { invoke } from '@tauri-apps/api/core'`

**理由**: cas-demo 使用静态 import，在 Tauri webview 中可靠工作。动态 import 在 Vite dev 模式下有已知问题（模块可能未预打包、HMR 重载后丢失缓存）。静态 import 在非 Tauri 环境会报错，但 ProAgent 只在 Tauri 中运行此功能。

**替代方案**: 继续用动态 import + 更好的错误处理 → 拒绝，因为根本问题是动态 import 本身不稳定

### D2: 一键式绑定流程（而非两步式）

**选择**: 单一"绑定 TIS"按钮 → 打开 CAS → 用户登录后点击"完成登录，开始绑定" → 自动提取 cookie + 绑定 + 导入数据

**理由**: 两步式流程（"打开登录" + "提取Cookie并绑定")让用户困惑，cas-demo 也需要 3-4 步操作。一键式更直观。

**替代方案**: 保持两步式但修复 invoke → 拒绝，用户体验差

### D3: TIS 和 BB 分别绑定

**选择**: TIS 绑定按钮打开 CAS→TIS URL，BB 绑定按钮先打开 CAS→BB URL（或导航已有窗口到 BB）

**理由**: CAS service 参数决定登录后跳转到哪个系统。TIS 需要 `service=https://tis.sustech.edu.cn/authentication/main`，BB 需要 `service=https://bb.sustech.edu.cn/webapps/login/...`。两个系统的 cookie 不同域，必须分别获取。

### D4: 绑定成功后自动导入数据

**选择**: 绑定成功后自动调用 `calendarStore.importTISSchedule()` 或 `calendarStore.importBlackboardAssignments()` + `dashboardStore` todo 导入

**理由**: 用户绑定后期望立即在 Calendar 和 Todo 中看到数据，不应需要手动去 Calendar 页面再点导入按钮。

### D5: 失败路径全部重置为 unbound

**选择**: 所有 catch/失败路径设置 `status = 'unbound'`，不使用 'error' 状态

**理由**: 'error' 状态下绑定按钮消失，用户被困。'unbound' 状态下按钮始终可见，用户可重试。

## Risks / Trade-offs

- [CAS WebView 可能被 macOS 安全策略阻止] → 在 `capabilities/default.json` 中已添加 `core:webview:allow-create-webview-window`，CSP 设为 null
- [静态 import 在非 Tauri 浏览器环境会报错] → ProAgent 此功能只在 Tauri 中使用，非 Tauri 环境下按钮不渲染（`v-if="isTauriApp"`）
- [无法自动检测用户是否完成 CAS 登录] → 需要用户手动点击"完成登录"按钮触发 cookie 提取，这是不可避免的
- [BB 绑定需要额外导航步骤] → BB 的 CAS service URL 与 TIS 不同，用户需要分别操作两个绑定按钮

## Open Questions

- 是否需要为 BB 绑定添加"导航到 BB"的中间步骤？还是直接用不同的 CAS service URL 打开新窗口？
- 绑定成功后是否自动关闭 CAS 窗口？还是保留窗口让用户继续操作 BB？