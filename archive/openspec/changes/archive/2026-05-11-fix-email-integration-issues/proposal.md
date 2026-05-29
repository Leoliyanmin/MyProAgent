## Why

email-integration 将邮件管理放在了侧边栏（SidebarLeft）"通用功能"分组中，与主界面/日程/文件/画像等核心功能在 TopBar 分段控件中的入口不一致。邮件管理应与其他核心功能同级出现在 TopBar 中。

## What Changes

1. **从侧栏移除邮件导航** — SidebarLeft 不再显示"邮件管理"
2. **在顶栏新增邮件入口** — TopBar segmented-control 中新增"邮件管理"segment，与主界面/日程/文件/画像同级

## Capabilities

### New Capabilities
- （无）

### Modified Capabilities
- `email-management-ui`: 邮件导航从侧边栏移至 TopBar 分段控件（与主界面、日程、文件管理、自我画像同级）

## Impact

- **Frontend**: `SidebarLeft.vue`（移除邮件导航项）、`TopBar.vue`（新增邮件 segment）、`App.vue`（无需改，已验证 TopBar emit 路径兼容）
