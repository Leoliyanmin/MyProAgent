## 1. Frontend: Email View Page & Navigation

- [x] 1.1 Add `/email` route in `frontend/src/router/index.js` with `EmailView` component, `requiresAuth: true`
- [x] 1.2 Add "邮件管理" nav item to `frontend/src/components/layout/SidebarLeft.vue` in the "通用功能" group with an email icon
- [x] 1.3 Update `frontend/src/App.vue` to sync `currentView` with `'email'` route name
- [x] 1.4 Create `frontend/src/stores/email.js` Pinia store with state: bindStatus, messages, loading, error, and actions: fetchStatus, fetchMessages, sync, send

## 2. Frontend: EmailView Core UI

- [x] 2.1 Create `frontend/src/views/EmailView.vue` with toolbar layout (title + action buttons following Dashboard/Calendar pattern)
- [x] 2.2 Implement read-only bind status display (show status + link to UserSettings for binding/unbinding)
- [x] 2.3 Implement email sync trigger button with loading state and result feedback
- [x] 2.4 Implement email message list display (title, sender, release_time) with expand-to-read body
- [x] 2.5 Implement email send form (recipient, subject, body textarea) with validation and submission
- [x] 2.6 Add email icon SVG to sidebar nav item

## 3. Agent: Email Tools

- [x] 3.1 Create `localagent/tools/email_tools.py` with `check_email_status` tool
- [x] 3.2 Implement `get_emails` tool in email_tools.py with query filter and max_results support
- [x] 3.3 Implement `send_email` tool in email_tools.py with to/subject/body parameters
- [x] 3.4 Register email tools in `localagent/tools/__init__.py` and `localagent/agent.py`

## 4. Verification

- [x] 4.1 Verify EmailView renders without errors and all API calls work (sync, messages, send)
- [x] 4.2 Verify agent email tools work (status, list, send)
- [x] 4.3 Verify sidebar navigation and route work correctly
