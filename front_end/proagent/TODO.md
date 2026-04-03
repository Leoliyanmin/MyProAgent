# ProAgent Theme Settings TODO

## Sprint Goal
- Build a theme customization workflow with edit mode, live preview, and backend persistence.

## Usability (Desktop)
- A minimalist Vue 3-based desktop GUI (Tauri shell) with a dedicated "Thought Trace" area, allowing users to view structured agent reasoning steps in real time (planning, tool selection, and observation).
- 极简 Vue 3 桌面界面（Tauri 容器），提供独立的 Thought Trace 区域，让用户实时看到结构化的 Agent 推理过程（规划、工具选择、观察结果）。

## 技术选型（Desktop 版本）
- 前端框架：Vue 3（Composition API）- 负责界面开发与组件化逻辑组织。
- 构建工具：Vite - 负责本地开发服务、热更新和生产打包。
- UI 样式：Tailwind CSS - 负责极简风格界面样式与设计一致性。
- 接口通信：Axios - 负责前端与后端 API 请求、拦截器和统一错误处理。
- 状态管理：Pinia - 负责管理全局状态（主题、Thought Trace、会话信息等）。
- 可视化：ECharts - 负责 Trace 时间线或统计图表展示。
- 桌面容器：Tauri 2（推荐）- 负责把 Vue 应用打包为独立桌面应用。
- 本地存储：SQLite（推荐）- 负责本地会话、Trace 历史和配置持久化。
- 进程通信：Tauri IPC Commands/Events - 负责前端界面与原生能力之间的安全通信。

## 技术选型（PPT 一句话版）
- Vue 3：前端框架，负责界面与交互。
- Vite：工程构建工具，负责开发与打包。
- Tailwind CSS：样式方案，负责极简 UI。
- Axios：网络通信库，负责前后端 API 调用。
- Pinia：状态管理库，负责全局状态同步。
- ECharts：图表库，负责 Thought Trace 可视化。
- Tauri 2：桌面容器，负责跨平台桌面应用封装。
- SQLite：本地数据库，负责配置与历史数据持久化。
- IPC：进程通信机制，负责前端与原生能力安全交互。

## Milestone D0: Standalone Desktop Architecture Decision (Owner: Li Yanmin)
- [ ] status: todo | owner: FE | Choose desktop wrapper: Tauri (recommended) or Electron, with trade-off notes (package size, memory, plugin ecosystem).
- [ ] status: todo | owner: FE | Keep Vue 3 + Vite + Pinia as renderer layer; avoid framework rewrite.
- [ ] status: todo | owner: FE | Define process split: UI renderer vs desktop shell capabilities (file system, notifications, auto-update).
- [ ] status: todo | owner: FE | Decide local-first persistence strategy: SQLite (preferred) or JSON file store.
- [ ] status: todo | owner: FE | Define security baseline: no unrestricted shell execution from renderer, strict command allowlist.

## Milestone D1: Thought Trace Minimalist GUI
- [ ] status: todo | owner: FE | Add a dedicated "Thought Trace" panel in dashboard layout with collapsible timeline view.
- [ ] status: todo | owner: FE | Define trace event schema: ts, phase(planning/tool_call/observation/result), tool, summary, durationMs, status.
- [ ] status: todo | owner: FE | Stream trace events incrementally to UI (append-only), support pause/resume and clear.
- [ ] status: todo | owner: FE | Add trace filters (by phase/tool/status) and compact mode for long sessions.
- [ ] status: todo | owner: FE | Redact sensitive values before rendering trace lines.

## Milestone D2: Desktop Runtime Integration
- [ ] status: todo | owner: FE | Create desktop app bootstrap (Tauri init or Electron Forge) and connect to existing Vite build.
- [ ] status: todo | owner: FE | Implement IPC/API bridge for approved tool actions; deny everything else by default.
- [ ] status: todo | owner: FE | Add desktop-only features behind capability checks (open folder, save logs, notifications).
- [ ] status: todo | owner: FE | Add crash-safe local session persistence and startup restore for trace timeline.
- [ ] status: todo | owner: FE | Add packaging pipeline for macOS (dmg) with versioned artifacts.

## Progress Rules
- Status values: `todo` | `doing` | `blocked` | `done`
- Every task must include owner + expected output
- Daily update: move at least 1 item to `done` or explain blocker

## Milestone M1: Frontend Theme Editor MVP (You own)
- [x] status: done  | owner: FE | Add "主题设置" entry in common features and route/view switch.
- [x] status: done  | owner: FE | Implement "主题编辑模式" toggle (normal/edit mode).
- [x] status: done  | owner: FE | Overlay editor directly on top of live workspace UI (not separate preview page).
- [x] status: done  | owner: FE | Add clickable region layer (sidebar/topbar/content) with active highlight.
- [x] status: done  | owner: FE | Build floating right-side style panel (primary color, text color, card bg color).
- [x] status: done  | owner: FE | Add color picker + hex input + radius slider.
- [x] status: done  | owner: FE | Apply live preview using CSS variables.
- [x] status: done  | owner: FE | Add reset/undo/redo/save buttons.

## Milestone M1.5: Overlay UX Refinement
- [ ] status: todo | owner: FE | Make overlay region boxes auto-fit actual layout bounds (agent sidebar open/closed aware).
- [ ] status: todo | owner: FE | Add click-through lock option to prevent accidental interactions in underlying page.
- [ ] status: todo | owner: FE | Add tooltip labels following cursor like screenshot tools.

## Milestone M2: Module-Level Style Customization
- [ ] status: todo | owner: FE | Define module map: dashboard widgets, calendar blocks, topbar, sidebar.
- [ ] status: todo | owner: FE | Support per-module style override on top of global theme tokens.
- [ ] status: todo | owner: FE | Add visual indicator showing which module is currently editable.
- [ ] status: todo | owner: FE | Add conflict fallback (module override missing -> use global token).

## Milestone M3: Image Upload + Background Customization
- [ ] status: todo | owner: FE | Add image upload button in theme panel.
- [ ] status: todo | owner: FE | Add upload preview (cover/contain/repeat/position/overlay opacity).
- [ ] status: todo | owner: FE | Add upload state UI (uploading/success/error).
- [ ] status: todo | owner: FE | Add image validation (type/size constraints).

## Milestone M4: Backend API (You can also own)
- [ ] status: todo | owner: BE | POST /assets/upload: upload user background image and return URL.
- [ ] status: todo | owner: BE | GET /theme/current: return current theme by user.
- [ ] status: todo | owner: BE | POST /theme/draft: save user draft theme.
- [ ] status: todo | owner: BE | POST /theme/publish: publish draft and increment themeVersion.
- [ ] status: todo | owner: BE | Add schema: globalTokens + moduleOverrides + metadata.
- [ ] status: todo | owner: BE | Add validation: contrast checks, token whitelist, URL safety.

## Integration & QA
- [ ] status: todo | owner: FE+BE | Define API contract examples (request/response JSON).
- [ ] status: todo | owner: FE+BE | End-to-end test: save theme -> refresh -> consistent render.
- [ ] status: todo | owner: FE+BE | Error fallback: API failure keeps previous stable theme.
- [ ] status: todo | owner: FE+BE | Performance check for edit mode interactions.

## This Week Suggested Start Order
1. M1.1 + M1.2 + M1.6 (entry, edit-mode switch, CSS variable live preview)
2. M1.4 + M1.5 (right panel + color controls)
3. M4 API skeleton (upload + current + draft)
4. Integration test and bug fixing
