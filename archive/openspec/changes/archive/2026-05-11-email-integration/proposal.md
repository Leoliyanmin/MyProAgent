## Why

系统已具备邮件服务的完整后端 API（绑定/同步/发送/解绑/获取邮件列表），但没有对应的前端 UI 页面，Agent 也无法调用邮件能力。这导致用户必须通过手动 API 调用操作邮件，效率低下。本次变更将邮件集成提升到与工作台、日程相同的页面级别，并提供 Agent 工具，使用户可以通过界面和 AI 助手两种方式管理邮件。

## What Changes

1. **新增邮件管理页面 `EmailView.vue`** — 与 Dashboard、Calendar 同级，通过侧边栏导航访问
2. **路由与导航集成** — 添加 `/email` 路由、Sidebar 菜单项
3. **邮件阅读与展示** — 展示已同步的邮件列表，点击可查看邮件正文详情
4. **邮件发送功能** — 在邮件页面中提供发送邮件的 UI 表单（收件人、主题、正文）
5. **同步入口** — 可在邮件页面触发邮件同步（绑定/解绑原有功能保留在 UserSettings）
6. **Agent 邮件工具** — 为 `localagent` 注册 email 工具（查询邮件列表、发送邮件、检查绑定状态），使 AI 助手能调用用户邮件服务

## Capabilities

### New Capabilities
- `email-management-ui`: 前端邮件管理页面，包含邮件列表展示与阅读、邮件发送功能、同步触发（绑定/解绑在 UserSettings 中已有）
- `email-agent-tools`: Agent 邮件工具集，允许 AI 助手读取邮件列表和发送邮件

### Modified Capabilities
- （无）

## Impact

- **Frontend**: 新增 `EmailView.vue`，修改 `SidebarLeft.vue`（新增导航项）、`router/index.js`（新增路由）、`App.vue`（同步 email 视图状态）
- **Localagent**: 新增 `email_tools.py`，修改 `tools/__init__.py` 注册邮件工具
- **API**: 依赖已有的 `local_backend/presentation/email_routes.py` 和 `frontend/src/services/api.js` 中的 `emailAPI`，无需修改后端
