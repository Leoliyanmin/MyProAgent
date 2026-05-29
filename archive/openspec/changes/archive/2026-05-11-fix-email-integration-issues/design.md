## Context

email-integration 将邮件导航放在了 SidebarLeft "通用功能"分组中。项目的核心功能（主界面、日程、文件、自我画像）均通过 TopBar 的 segmented-control 访问，邮件管理应遵循同样模式。

App.vue 已有 email 的路由映射和 TopBar emit 处理路径，无需额外修改。

## Goals / Non-Goals

**Goals:**
- 邮件导航从 SidebarLeft 移至 TopBar segmented-control
- 用户可在 TopBar 一键切换到邮件管理页面

**Non-Goals:**
- 不修改 EmailView.vue 或 email store
- 不修改后端代码
- 不添加/修改任何 API endpoint

## Decisions

### D1: TopBar 集成方式
**选择**: 在 TopBar `<div class="segmented-control">` 中新增 `<button class="segment">`，emit `update:currentView('email')`
**理由**: TopBar 已有 segment 点击→emit→App.vue watcher→router.push 的完整链路。App.vue 中 email 路由映射已就绪，无需任何修改。

### D2: 侧栏清理
**选择**: 完全移除 SidebarLeft 中的"邮件管理"nav-item（含 SVG 图标）
**理由**: 避免导航重复，保持入口唯一性。

## Risks / Trade-offs

- **用户习惯** → 邮件入口从侧栏移到顶栏，短期需要适应
