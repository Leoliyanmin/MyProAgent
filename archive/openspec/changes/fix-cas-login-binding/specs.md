## S1: Tauri IPC 调用修复

**Type**: Bug Fix
**Priority**: P0 — 阻塞所有绑定功能

**Current Behavior**: `tauriInvoke` 使用动态 `import('@tauri-apps/api/core')`，在 Tauri webview 中调用 `invoke('open_cas_login')` 失败或返回 null，CAS 窗口不弹出。

**Expected Behavior**: 点击"打开登录"→ CAS WebView 窗口弹出，显示 SUSTech CAS 登录页面。

**Acceptance Criteria**:
- [ ] 使用静态 `import { invoke } from '@tauri-apps/api/core'` 替代动态 import
- [ ] `bindTis()` 调用 `invoke('open_cas_login')` 能成功创建 CAS WebView 窗口
- [ ] `bindBb()` 调用 `invoke('open_cas_login')` 能成功创建 CAS WebView 窗口
- [ ] 非法 invoke 调用（如命令不存在）抛出可见错误到 console
- [ ] `isTauriApp` 检测使用 `window.__TAURI_INTERNALS__`（Tauri v2 标准）

**Implementation Notes**:
- 在 `<script setup>` 顶部添加 `import { invoke } from '@tauri-apps/api/core'`
- 移除 `tauriInvoke` 动态 import 辅助函数
- 所有 Tauri 调用直接使用 `invoke()`
- 保留 `isTauriApp` 检测，非 Tauri 环境下隐藏 Tauri 专属按钮

---

## S2: 一键式绑定流程

**Type**: Feature Enhancement
**Priority**: P0 — 核心用户体验

**Current Behavior**: 需要两步操作：1) 点击"打开登录" 2) 点击"提取Cookie并绑定"。第二步经常失败或被忽略。

**Expected Behavior**: 点击"绑定 TIS"→ CAS 窗口弹出→用户登录→点击"完成登录"→自动提取 cookie→自动调用后端 bind→自动刷新状态→自动导入数据到 Calendar/Todo。

**Acceptance Criteria**:
- [ ] TIS 绑定按钮标签改为"绑定 TIS"，点击后调用 `invoke('open_cas_login')` 打开 CAS→TIS 窗口
- [ ] BB 绑定按钮标签改为"绑定 Blackboard"，点击后调用 `invoke('open_cas_login')` 打开 CAS→BB 窗口
- [ ] CAS 窗口打开后，显示"完成登录"按钮（在主窗口的设置页面中）
- [ ] 点击"完成登录"后，自动执行：`invoke('extract_cookies')` → `invoke('bind_tis'/'bind_blackboard', { cookies, backendUrl, token })` → `loadBindingStatus()`
- [ ] 绑定成功后自动调用 `calendarStore.importTISSchedule()` 或 `calendarStore.importBlackboardAssignments()`
- [ ] BB 绑定成功后自动将作业添加到 Dashboard Todo
- [ ] 绑定过程中显示 loading 状态（"绑定中…"）
- [ ] 绑定失败后状态重置为 'unbound'，用户可重试

**Implementation Notes**:
- Rust `open_cas_login` 命令需要区分 TIS 和 BB 的 CAS service URL
- 可能需要新增 Rust 命令参数或新命令 `open_cas_login_tis` / `open_cas_login_bb`
- "完成登录"按钮在 CAS 窗口打开期间显示，绑定成功或窗口关闭后隐藏

---

## S3: TIS/BB 分别使用不同 CAS Service URL

**Type**: Technical Requirement
**Priority**: P1 — 两个系统 cookie 域不同

**Current Behavior**: `open_cas_login` 命令硬编码 CAS→TIS URL，BB 绑定也使用同一 URL。

**Expected Behavior**: TIS 绑定使用 `service=https://tis.sustech.edu.cn/authentication/main`，BB 绑定使用 `service=https://bb.sustech.edu.cn/webapps/login/`。

**Acceptance Criteria**:
- [ ] Rust `open_cas_login` 命令接受 `platform` 参数（"tis" 或 "blackboard"）
- [ ] TIS 绑定打开 CAS→TIS 的 WebView
- [ ] BB 绑定打开 CAS→BB 的 WebView
- [ ] `extract_cookies` 命令根据 platform 提取对应域的 cookie

**Implementation Notes**:
- CAS URL 格式：`https://cas.sustech.edu.cn/cas/login?service=<target_url>`
- TIS target: `https://tis.sustech.edu.cn/authentication/main`
- BB target: `https://bb.sustech.edu.cn/webapps/login/`
- Cookie 域：TIS 是 `tis.sustech.edu.cn`，BB 是 `bb.sustech.edu.cn`

---

## S4: 绑定后自动数据导入

**Type**: Feature Enhancement
**Priority**: P1 — 用户期望绑定后立即看到数据

**Current Behavior**: 绑定成功后需要用户手动去 Calendar 页面点击导入按钮。

**Expected Behavior**: 绑定成功后自动将 TIS 课程导入 Calendar、BB 作业导入 Calendar + Dashboard Todo。

**Acceptance Criteria**:
- [ ] TIS 绑定成功后自动调用 `calendarStore.importTISSchedule()`
- [ ] BB 绑定成功后自动调用 `calendarStore.importBlackboardAssignments()`
- [ ] 导入完成后在设置页面显示成功提示（"已导入 N 门课程" / "已导入 N 个作业"）
- [ ] 导入失败不影响绑定状态（绑定成功但导入失败时显示警告）

---

## S5: 失败路径状态管理

**Type**: Bug Fix
**Priority**: P0 — 用户被困在错误状态

**Current Behavior**: 绑定失败后 `status = 'error'`，绑定按钮消失，用户无法重试。

**Expected Behavior**: 任何步骤失败后 `status = 'unbound'`，绑定按钮始终可见，用户可重试。

**Acceptance Criteria**:
- [ ] `loadBindingStatus` 的 catch 块设置 `status = 'unbound'` 而非 `'error'`
- [ ] `extractAndBind` 的所有失败路径设置 `status = 'unbound'`
- [ ] 模板中 `v-if` 条件包含 `'unbound'` 和 `'error'`（双重保障）
- [ ] 失败时 console.error 记录详细错误信息