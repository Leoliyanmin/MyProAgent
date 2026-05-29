## T1: 修复 Tauri IPC — 静态 import 替代动态 import

**Spec**: S1
**Priority**: P0
**Estimate**: 15min
**Dependencies**: None

**Steps**:
1. 在 `UserSettingsView.vue` 的 `<script setup>` 顶部添加 `import { invoke } from '@tauri-apps/api/core'`
2. 移除 `tauriInvoke` 动态 import 辅助函数
3. 将所有 `tauriInvoke('command', args)` 调用替换为 `invoke('command', args)`
4. 保留 `isTauriApp` 检测（`!!window.__TAURI_INTERNALS__`），非 Tauri 环境下隐藏 Tauri 按钮
5. 验证 `npm run tauri:dev` 中点击"打开登录"能弹出 CAS WebView 窗口

**Files**:
- `frontend/src/views/UserSettingsView.vue`

**Verification**:
- [x] `npm run tauri:dev` 启动后，设置页面点击"绑定 TIS"→ CAS 窗口弹出
- [x] `npx vite build` 通过
- [x] `cargo check` 通过

---

## T2: Rust 命令支持 platform 参数

**Spec**: S3
**Priority**: P1
**Estimate**: 20min
**Dependencies**: None

**Steps**:
1. 修改 `open_cas_login` 命令，添加 `platform: Option<String>` 参数
2. 根据 platform 选择 CAS service URL：
   - `"tis"` → `https://cas.sustech.edu.cn/cas/login?service=https://tis.sustech.edu.cn/authentication/main`
   - `"blackboard"` → `https://cas.sustech.edu.cn/cas/login?service=https://bb.sustech.edu.cn/webapps/login/`
   - 默认（None）→ TIS URL（向后兼容）
3. 修改 `extract_cookies` 命令，添加 `platform: Option<String>` 参数
4. 根据 platform 过滤 cookie 域：
   - `"tis"` → 只提取 `tis.sustech.edu.cn` 域的 cookie
   - `"blackboard"` → 只提取 `bb.sustech.edu.cn` 域的 cookie
   - 默认 → 提取所有 `sustech.edu.cn` 域的 cookie
5. 在 `invoke_handler` 中重新注册修改后的命令

**Files**:
- `frontend/src-tauri/src/lib.rs`

**Verification**:
- [x] `cargo check` 通过
- [x] `invoke('open_cas_login', { platform: 'tis' })` 打开 CAS→TIS 窗口
- [x] `invoke('open_cas_login', { platform: 'blackboard' })` 打开 CAS→BB 窗口

---

## T3: 一键式绑定流程 — 前端

**Spec**: S2, S4, S5
**Priority**: P0
**Estimate**: 30min
**Dependencies**: T1, T2

**Steps**:
1. 重写 `bindTis` 函数：
   - 调用 `invoke('open_cas_login', { platform: 'tis' })` 打开 CAS→TIS 窗口
   - 设置 `tis.status = 'binding'`（新状态，显示"登录后点击完成"）
   - 显示"完成登录，开始绑定"按钮
2. 重写 `bindBb` 函数：
   - 调用 `invoke('open_cas_login', { platform: 'blackboard' })` 打开 CAS→BB 窗口
   - 设置 `bb.status = 'binding'`
   - 显示"完成登录，开始绑定"按钮
3. 新增 `completeBinding(platform)` 函数：
   - 调用 `invoke('extract_cookies', { platform })` 提取 cookie
   - 调用 `invoke(bindFn, { cookies, backendUrl: 'http://127.0.0.1:8002', token })` 绑定
   - 绑定成功后调用 `loadBindingStatus()` 刷新状态
   - TIS 绑定成功后调用 `calendarStore.importTISSchedule()`
   - BB 绑定成功后调用 `calendarStore.importBlackboardAssignments()`
   - 所有失败路径设置 `status = 'unbound'`
4. 更新模板：
   - TIS：`unbound` → 显示"绑定 TIS"按钮；`binding` → 显示"完成登录，开始绑定"按钮；`bound` → 显示绑定信息 + "解绑"按钮
   - BB：同上
   - 移除 `'error'` 状态的使用，所有失败回到 `'unbound'`
5. 添加 `calendarStore` 和 `dashboardStore` 的 import

**Files**:
- `frontend/src/views/UserSettingsView.vue`

**Verification**:
- [ ] 点击"绑定 TIS"→ CAS 窗口弹出 → 登录 → 点击"完成登录"→ 状态变为"已绑定"
- [ ] 点击"绑定 Blackboard"→ CAS 窗口弹出 → 登录 → 点击"完成登录"→ 状态变为"已绑定"
- [ ] 绑定成功后 Calendar 中出现 TIS 课程 / BB 作业
- [ ] 绑定失败后按钮仍然可见，可重试
- [x] `npx vite build` 通过

---

## T4: 端到端验证

**Spec**: All
**Priority**: P1
**Estimate**: 15min
**Dependencies**: T1, T2, T3

**Steps**:
1. 启动 `npm run tauri:dev`
2. 登录主应用
3. 进入设置页面
4. 点击"绑定 TIS"→ CAS 窗口弹出
5. 在 CAS 窗口中登录 SUSTech SSO
6. 登录成功后回到主窗口点击"完成登录，开始绑定"
7. 验证 TIS 状态变为"已绑定"，显示学生信息和课程数
8. 验证 Calendar 页面出现 TIS 课程
9. 点击"解绑"→ 状态变为"未绑定"
10. 重复步骤 4-8 测试 BB 绑定
11. 验证 BB 绑定后 Dashboard Todo 出现作业

**Verification**:
- [ ] TIS 绑定→数据导入→Calendar 显示课程
- [ ] BB 绑定→数据导入→Calendar 显示作业 + Dashboard Todo 显示作业
- [ ] 解绑→重新绑定→数据重新导入
- [ ] 绑定失败→按钮可见→可重试