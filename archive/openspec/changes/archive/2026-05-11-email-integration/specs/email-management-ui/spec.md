## ADDED Requirements

### Requirement: Email navigation integration
The system SHALL integrate the email management page into the main navigation at the same level as Dashboard and Calendar.

#### Scenario: Sidebar navigation item
- **WHEN** user is authenticated and the sidebar is visible
- **THEN** the sidebar SHALL display a "邮件管理" navigation item in the "通用功能" group
- **WHEN** user clicks the "邮件管理" item
- **THEN** the system SHALL navigate to `/email` route and display EmailView

#### Scenario: Route registration
- **WHEN** the router initializes
- **THEN** a route with path `/email`, name `email`, and component `EmailView.vue` SHALL be registered with `requiresAuth: true`

#### Scenario: App state sync
- **WHEN** the route changes to `email`
- **THEN** `App.vue` SHALL set `currentView` to `'email'` and `appMode` to `'main'`

### Requirement: Email bind status display (read-only)
The system SHALL display the email bind status as read-only info, directing users to UserSettings for bind/unbind operations.

#### Scenario: Display bind status
- **WHEN** user navigates to email page
- **THEN** the system SHALL fetch email bind status via `GET /api/v1/email/status`
- **THEN** the system SHALL show whether email is bound, the email address, and a link/hint to go to UserSettings for binding
- **WHEN** email is not bound
- **THEN** the system SHALL disable send/sync operations and show a prompt directing user to UserSettings

### Requirement: Email sync and message list
The system SHALL allow users to manually trigger email sync and view synced messages.

#### Scenario: Sync emails
- **WHEN** user clicks "同步邮件" button and email is bound
- **THEN** the system SHALL call `POST /api/v1/email/sync?max_messages=<count>`
- **THEN** the system SHALL show a loading state during sync
- **THEN** the system SHALL display sync result (total emails, synced count)
- **THEN** the system SHALL refresh the message list

#### Scenario: View message list
- **WHEN** user is on the email page and messages are loaded
- **THEN** the system SHALL display a list of synced emails showing: title, sender, release time
- **WHEN** user clicks a message item
- **THEN** the system SHALL expand/show the message body (context)

### Requirement: Send email UI
The system SHALL provide a form for users to send emails through the bound email account.

#### Scenario: Send email form
- **WHEN** user is bound and accesses the send form
- **THEN** the system SHALL display a form with fields: recipient email address, subject, body (textarea)
- **WHEN** user fills in the form and submits
- **THEN** the system SHALL call `POST /api/v1/email/send` with the form data
- **THEN** the system SHALL display success or detailed error message

#### Scenario: Send blocked when unbound
- **WHEN** email is not bound and user attempts to send
- **THEN** the system SHALL show a message: "请先在用户设置中绑定邮箱"
