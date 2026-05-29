## Context

当前项目中：
- **后端邮件 API** 已完整实现：`GET /api/v1/email/status`、`POST /api/v1/email/bind`、`POST /api/v1/email/sync`、`POST /api/v1/email/unbind`、`GET /api/v1/email/messages`、`POST /api/v1/email/send`（定义在 `bb_tis_mail_bind_rule.md` 和 `local_backend/presentation/email_routes.py`）
- **前端 API 服务** 已封装 `emailAPI` 对象（位于 `frontend/src/services/api.js`）
- **前端视图** 模式一致：每个顶层页面（Dashboard、Calendar、FileManager、SelfPortrait）都有对应的 View + Router route + Sidebar 导航项
- **Agent 工具** 模式一致：日历等功能通过 `localagent/tools/calendar_tools.py` 注册工具，AI 助手通过工具调用操作业务

本设计覆盖两个需求：
1. 新增邮件管理页面（EmailView），与 Dashboard/Calendar 同层级
2. Agent 邮件工具（email_tools），让 AI 助手能调用邮件服务

## Goals / Non-Goals

**Goals:**
- 新增 `/email` 路由，EmailView 可通过侧边栏访问
- 邮件列表展示与阅读：从已同步数据中展示邮件列表，点击查看正文
- 邮件发送：收件人、主题、正文表单
- 同步触发：邮件页面中可触发同步（绑定/解绑入口保留在 UserSettings）
- Agent 注册 email 工具：查询状态、邮件列表、发送邮件
- 遵循现有 UI 风格和代码模式

**Non-Goals:**
- 不修改后端邮件 API（已有完整实现）
- **不包含邮箱绑定/解绑 UI**（已存在于 UserSettingsView 的"教务平台绑定"区域）
- 不涉及邮件 IMAP/SMTP 配置更改
- 不做邮件复杂搜索或分页（复用现有 API 的 `max_messages` 参数）
- 不做 WebSocket 实时推送（邮件同步为请求-响应模式）
- 不涉及 Tauri/桌面端特定适配

## Decisions

### D1: 路由路径 `/email`
**选择**: 使用 `/email` 作为路径，`email` 作为 route name
**理由**: 与现有路由模式一致（`/dashboard`、`/calendar`、`/files`），简短直观。
**替代方案**: `/mail` — 但后端 API 使用 `email` 前缀，保持一致更佳。

### D2: EmailView 组件布局
**选择**: 两区布局：
- 顶部工具栏：标题 + 同步按钮 + 链接到 UserSettings 的绑定管理入口
- 主区域：分左右两栏，左栏为发送邮件表单（收件人/主题/正文），右栏为已同步邮件列表（点击展开正文）
**理由**: 绑定/解绑已在 UserSettings，EmailView 专注邮件核心操作（阅读+发送）。

### D3: Agent 工具设计
**选择**: 创建三个独立工具：
- `get_emails(query, max_results)` — 获取邮件列表，支持标题关键词筛选和数量限制
- `send_email(to, subject, body)` — 发送邮件
- `check_email_status()` — 检查邮箱绑定状态
**理由**: 遵循 calendar_tools.py 的独立工具模式，每个工具职责单一，参数明确。不将绑定/同步 API 暴露给 agent（这些属于配置操作，非用户日常使用）。

### D4: EmailView 状态管理
**选择**: 使用 Pinia store（`email.js`）管理邮件状态
**理由**: 与 Dashboard（`stores/dashboard.js`）、Calendar（`stores/calendar.js`）模式一致，数据集中管理。
**替代方案**: 组件内 `ref` — 但邮件数据跨组件共享，store 更合适。

### D5: 用户身份获取
**选择**: Agent 工具复用现有 `user_id_getter` 回调模式（与 calendar_tools.py 一致）
**理由**: 保持与现有工具架构完全一致，无需新增任何基础设施。

## Risks / Trade-offs

- **邮件列表数据量大** → `max_messages` 默认 50，支持在 UI 中调整
- **SMTP 连接失败** → 后端已处理异常并返回清晰错误消息，前端直接展示
- **绑定/同步耗时** → 同步操作设为异步（loading state），防止 UI 阻塞
- **Agent 发送邮件误操作** → Agent 工具需要用户确认后再执行（现有 agent 架构的 tool_call 确认流程）
