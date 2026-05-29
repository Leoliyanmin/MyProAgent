## MODIFIED Requirements

### Requirement: Email navigation integration
The system SHALL integrate the email management page into the TopBar segmented control at the same level as Dashboard, Calendar, File Manager, and Self Portrait. The email navigation entry SHALL NOT appear in the sidebar.

#### Scenario: TopBar segment navigation
- **WHEN** user is authenticated and the TopBar is visible
- **THEN** the TopBar segmented control SHALL display a "邮件管理" segment button alongside 主界面/日程规划/文件管理/自我画像
- **WHEN** user clicks the "邮件管理" segment
- **THEN** the system SHALL emit `update:currentView` with `'email'` and navigate to `/email` route

#### Scenario: Sidebar removal
- **WHEN** user is authenticated and the sidebar is visible
- **THEN** the sidebar SHALL NOT display "邮件管理" in any navigation group
- **THEN** the sidebar's "通用功能" group SHALL contain only the pre-existing items plus the placeholder "通用接口 B"

#### Scenario: Route unchanged
- **WHEN** the router initializes
- **THEN** the route `/email` with `requiresAuth: true` SHALL remain registered and functional
