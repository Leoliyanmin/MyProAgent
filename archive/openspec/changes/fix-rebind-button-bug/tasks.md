## Tasks

### Task 1: 修复 extract_cookies 使用原生 Cookie API

**文件**: `frontend/src-tauri/src/lib.rs`

**目标**: 将 `extract_cookies` 命令从 `document.cookie` JS eval 方式改为 Tauri 原生 `cookies_for_url` API，使其能正确提取 HttpOnly Cookie（JSESSIONID、TGC 等）。

**步骤**:
1. 在 `extract_cookies` 函数中，移除 `webview.eval("document.cookie")` 调用
2. 使用 `app.cookies_for_url(&url)` 获取指定 URL 的所有 Cookie
3. 过滤目标域名 Cookie（`tis.sustech.edu.cn` 或 `bb.sustech.edu.cn`）
4. 将 Tauri `Cookie` 对象转换为前端可用的 JSON 格式（包含 name、value、domain、path、secure、httpOnly 字段）
5. 参考 `cas-demo/src-tauri/src/lib.rs` 中 `extract_all_cookies` 的实现模式

**验证**: 解绑后重新绑定，检查后端日志是否出现 TIS/Blackboard 绑定请求

**依赖**: 无

**状态**: ✅ 已完成

---

### Task 2: 修复 extract_all_cookies 使用原生 Cookie API

**文件**: `frontend/src-tauri/src/lib.rs`

**目标**: 将 `extract_all_cookies` 命令同步使用 `cookies_for_url` API，保持与 `extract_cookies` 一致。

**步骤**:
1. 在 `extract_all_cookies` 函数中，移除 `webview.eval("document.cookie")` 调用
2. 分别对 TIS 和 Blackboard URL 调用 `app.cookies_for_url(url)`
3. 合并结果为 `{ tis: [...], blackboard: [...] }` 格式
4. 参考 `cas-demo/src-tauri/src/lib.rs` 中 `extract_all_cookies` 的实现

**验证**: 调用 `extract_all_cookies` 返回包含 HttpOnly Cookie 的完整列表

**依赖**: 无

**状态**: ✅ 已完成

---

### Task 3: 修复 open_cas_login 窗口存在性检查

**文件**: `frontend/src-tauri/src/lib.rs`

**目标**: 在创建 CAS 登录窗口前检查同标签窗口是否已存在，避免重复创建导致窗口静默失败。

**步骤**:
1. 在 `open_cas_login` 函数中，创建窗口前调用 `app.get_webview(label)` 检查窗口是否存在
2. 若窗口已存在：调用 `existing.set_focus()` 聚焦现有窗口，返回成功
3. 若窗口不存在：继续创建新窗口（保持现有逻辑不变）

**验证**: 连续两次调用 `open_cas_login` 不会创建重复窗口，第二次聚焦已有窗口

**依赖**: 无

**状态**: ✅ 已完成

---

### Task 4: 修复 completeBinding 错误反馈

**文件**: `frontend/src/views/UserSettingsView.vue`

**目标**: 在 Cookie 提取为空时向用户显示错误提示，而非静默回退到 unbound 状态。

**步骤**:
1. 在 `completeBinding` 函数中，当 `cookies` 为空或长度为 0 时：
   - 调用 `ElMessage.error('未检测到登录信息，请确认已在弹出窗口中完成登录')`
   - 将绑定状态设为 `unbound`
2. 确认 `ElMessage` 已从 Element Plus 导入（检查现有 import）

**验证**: 解绑后点击绑定，若 Cookie 提取失败，用户看到错误提示消息

**依赖**: Task 1（Cookie 提取修复后，此错误反馈仅在真正的登录失败时触发）

**状态**: ✅ 已完成

---

### Task 5: 确保 Tauri cookies feature 已启用

**文件**: `frontend/src-tauri/Cargo.toml`

**目标**: 确认 `cookies_for_url` API 可用，必要时启用相关 feature。

**步骤**:
1. 检查 `Cargo.toml` 中 `tauri` 依赖的 `features` 列表
2. 若 `cookies` feature 未启用，添加到 features 列表
3. 运行 `cargo check` 验证编译通过

**验证**: `cargo check` 在 `frontend/src-tauri/` 目录下编译成功

**依赖**: 无

**状态**: ✅ 已完成（无需 feature flag，`cookies_for_url` 是 Tauri v2.4+ 核心 API）
