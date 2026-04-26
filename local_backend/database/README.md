# Database Module README

This document only covers the database layer in `local_backend/database`.

## Schema

### `users`

| Column | Meaning / Rule |
|---|---|
| `user_id` | Primary key and cross-table user identifier. |
| `username` | Unique username. Required. |
| `user_email` | Unique email. Required. |
| `user_is_active` | `0` or `1`, defaults to `1`. |
| `user_created_at` | Creation time, ISO 8601 text. |
| `user_last_login` | Last login time, optional ISO 8601 text. |
| `user_source_device_id` | Optional source device identifier. |

### `user_match_profile`

| Column | Meaning / Rule |
|---|---|
| `user_id` | Primary key, FK to `users.user_id`. |
| `answers` | Serialized profile answers, stored as text JSON. |
| `is_open` | `0` or `1`, defaults to `0`. |
| `last_match_time` | Optional ISO 8601 text. |

### `match_result`

| Column | Meaning / Rule |
|---|---|
| `id` | Auto-increment primary key. |
| `user_id` | Owner user id. FK to `users.user_id`. |
| `matched_user_id` | Matched user id. |
| `similarity_score` | Match score as `REAL`. |
| `created_at` | Creation time. |
| `is_shared` | `0` or `1`, defaults to `0`. |

### `sync_state`

| Column | Meaning / Rule |
|---|---|
| `user_id` | Primary key, FK to `users.user_id`. |
| `user_data_updated_at` | Last business-data update time. |
| `user_last_synced_at` | Last successful sync time. |
| `user_version` | Monotonic version, defaults to `1`. |
| `sync_updated_at` | Sync state row update time. |

### `account`

| Column | Meaning / Rule |
|---|---|
| `account_id` | Auto-increment primary key. |
| `user_id` | Owner user id. FK to `users.user_id`. |
| `account_platform_type` | Platform name, required. |
| `account_platform_username` | Platform account username, required. |
| `account_bind_time` | Optional bind time. |
| `account_last_sync_time` | Optional last sync time. |

### `category`

| Column | Meaning / Rule |
|---|---|
| `category_id` | Auto-increment primary key. |
| `user_id` | Owner user id. FK to `users.user_id`. |
| `category_kind` | Category type, e.g. `task`, `blackboard_course`. |
| `category_title` | Category title. Required. |
| `category_content` | Optional serialized metadata JSON or text. |
| `category_link` | Optional canonical link. For Blackboard course categories this should be the course URL. |
| `category_created_at` | Creation time, ISO 8601 text. |

Rule: unique index on `(user_id, category_kind, COALESCE(category_link, ''))`.

### `data`

| Column | Meaning / Rule |
|---|---|
| `data_id` | Auto-increment primary key. |
| `user_id` | Owner user id. FK to `users.user_id`. |
| `data_category_id` | Parent category id. FK to `category.category_id`. |
| `data_content_type` | Content subtype, e.g. `task`, `blackboard_announcement`, `blackboard_course_material`, `blackboard_assignment_upload`. |
| `data_classification_code` | `1` public, `2` course material, `3` assignment. Defaults to `1`. |
| `data_title` | Display title. Required. |
| `data_content_text` | Main content body or serialized payload text. |
| `data_link_url` | Canonical link. Blackboard item storage should always provide a stable link value. |
| `data_release_time` | Optional release time. |
| `data_ddl_time` | Optional deadline time. |
| `data_is_previewable` | `0` or `1`, required. |
| `data_created_at` | First-seen time, ISO 8601 text. |
| `data_linked_schedule_id` | Optional linked schedule id. |

Rule: unique index on `(user_id, data_category_id, data_content_type, COALESCE(data_link_url, ''))`.

### `schedule`

| Column | Meaning / Rule |
|---|---|
| `schedule_id` | Auto-increment primary key. |
| `user_id` | Owner user id. FK to `users.user_id`. |
| `schedule_event_type` | Event type, required. |
| `schedule_priority` | `0` to `3`, defaults to `2`. |
| `schedule_is_completed` | `0` or `1`, defaults to `0`. |
| `schedule_title` | Schedule title. Required. |
| `schedule_start_time` | Start time, required. |
| `schedule_end_time` | End time, required. |
| `schedule_location` | Optional location. |
| `schedule_description` | Optional description. |
| `schedule_related_link` | Optional related URL. |
| `schedule_recurrence_rule` | Optional recurrence rule. |
| `schedule_color_tag` | Optional color tag. |

### `session`

| Column | Meaning / Rule |
|---|---|
| `session_id` | Auto-increment primary key. |
| `user_id` | Owner user id. FK to `users.user_id`. |
| `session_title` | Optional session title, defaults to empty string. |
| `session_created_at` | Session creation time. Required. |
| `session_last_visited_at` | Last visited time. Required. |

### `chat`

| Column | Meaning / Rule |
|---|---|
| `chat_id` | Auto-increment primary key. |
| `session_id` | Parent session id. FK to `session.session_id`. |
| `chat_role` | `user` or `assistant`. |
| `chat_message_content` | Chat message body. Required. |
| `thought_trace` | Optional trace text. |
| `chat_tool_calls` | Optional tool call list text. |
| `chat_tokens_usage` | Optional token usage JSON text. |
| `chat_created_at` | Message creation time. Required. |

### `perm`

| Column | Meaning / Rule |
|---|---|
| `perm_id` | Auto-increment primary key. |
| `perm_category` | Permission category. |
| `perm_is_allowed` | `0` or `1`. |
| `perm_require_confirmation` | `0` or `1`. |
| `perm_last_modified` | Last modified time. |
| `perm_call_method` | Call method or trigger name. |

## Handle APIs

### `database_user_handle.py`

| Function | Parameters | Return |
|---|---|---|
| `UserHandle.create_user` | `email: str`, `username: str` | `{ok, status, data.user_id}` on success. |
| `UserHandle.get_user` | `user_id: str | None`, `email: str | None` | `{ok, status, data}` or error dict. |
| `UserHandle.update_user` | `user_id: str`, `update_data: dict` | `{ok, status, message}` or error dict. |
| `UserHandle.delete_user` | `user_id: str` | `{ok, status, message}` or error dict. |

### `database_match_handle.py`

| Function | Parameters | Return |
|---|---|---|
| `LocalMatchHandle.upsert_profile` | `user_id: str`, `profile_json: Any`, `is_open: Any = 1`, `last_match_time: Any = None` | `{ok, status, data}` or error dict. |
| `LocalMatchHandle.get_profile` | `user_id: str` | `{ok, status, data}` or error dict. |
| `LocalMatchHandle.set_profile_open` | `user_id: str`, `is_open: Any` | `{ok, status, data}` or error dict. |
| `LocalMatchHandle.delete_profile` | `user_id: str` | `{ok, status, message, already_deleted?}` or error dict. |
| `LocalMatchHandle.list_matches` | `user_id: str` | `{ok, status, data}` or error dict. |
| `LocalMatchHandle.handle` | `action: str`, `payload: Any = None` | Routed dict response. |
| `handle_match_request` | `request: dict[str, Any] | str | Path` | Routed dict response. |

### `database_schedule_handle.py`

| Function | Parameters | Return |
|---|---|---|
| `ScheduleHandle.create_schedule` | `user_id: str`, `title: str`, `start_time: Any`, `end_time: Any`, `**kwargs` | `{ok, status, data.schedule_id}` or error dict. |
| `ScheduleHandle.get_schedules` | `user_id: str` | `{ok, status, data}` or error dict. |
| `ScheduleHandle.get_schedule` | `user_id: str`, `schedule_id: Any` | `{ok, status, data}` or error dict. |
| `ScheduleHandle.update_schedule` | `user_id: str`, `schedule_id: Any`, `**kwargs` | `{ok, status, message}` or error dict. |
| `ScheduleHandle.delete_schedule` | `user_id: str`, `schedule_id: Any` | `{ok, status, message}` or error dict. |
| `ScheduleHandle.handle` | `action: str`, `payload: Any = None` | Routed dict response. |
| `handle_schedule_request` | `request: dict[str, Any] | str | Path` | Routed dict response. |

### `database_task_handle.py`

| Function | Parameters | Return |
|---|---|---|
| `TaskHandle.create_task` | `user_id: str`, `title: str`, `description: str = None`, `due_date: str = None`, `linked_schedule_id: int = None` | `{ok, status, data.task_id}` or error dict. |
| `TaskHandle.get_tasks` | `user_id: str` | `{ok, status, data}` or error dict. |
| `TaskHandle.update_task` | `user_id: str`, `task_id: int`, `title: str = None`, `description: str = None`, `due_date: str = None`, `linked_schedule_id: int | None | object = None` | `{ok, status, message}` or error dict. |
| `TaskHandle.delete_task` | `user_id: str`, `task_id: int` | `{ok, status, message, already_deleted?}` or error dict. |

### `database_chat_handle.py`

| Function | Parameters | Return |
|---|---|---|
| `ChatHandle.create_session` | `user_id: str` | `{ok, status, data.session_id}` or error dict. |
| `ChatHandle.get_sessions` | `user_id: str` | `{ok, status, data}` or error dict. |
| `ChatHandle.create_chat_message` | `session_id: int`, `role: str`, `message: str`, `**kwargs` | `{ok, status, data.chat_id}` or error dict. |
| `ChatHandle.get_chat_history` | `session_id: int` | `{ok, status, data}` or error dict. |
| `ChatHandle.delete_session` | `session_id: int` | `{ok, status, message}` or error dict. |

### `database_synchronize_handle.py`

| Function | Parameters | Return |
|---|---|---|
| `LocalSyncHandle.build_probe` | `user_id: str | None = None` | `{ok, status, payload}` or error dict. |
| `LocalSyncHandle.resolve_probe_result` | `server_probe_response: dict[str, Any]` | `{ok, status, next_step, reason, conflict?}` or error dict. |
| `LocalSyncHandle.build_push` | `user_id: str | None = None` | `{ok, status, payload}` or error dict. |
| `LocalSyncHandle.apply_pull` | `pull_payload: dict[str, Any] | str | Path` | `{ok, status, ...}` or error dict. |
| `LocalSyncHandle.apply_server_ack` | `ack_payload: dict[str, Any] | str | Path` | `{ok, status, ...}` or error dict. |
| `LocalSyncHandle.handle` | `action: str`, `payload: Any = None` | Routed dict response. |
| `handle_sync_request` | `request: dict[str, Any] | str | Path` | Routed dict response. |

### `database_blackboard_handle.py`

| Function | Parameters | Return |
|---|---|---|
| `BlackboardHandle.save_crawl_result` | `user_id: str`, `crawl_result: dict[str, Any] | list[Any]`, `crawled_at: Any = None` | `{ok, status, message, data}` or error dict. |
| `BlackboardHandle.handle` | `action: str`, `payload: Any = None` | Routed dict response. |
| `handle_blackboard_request` | `request: dict[str, Any] | str | Path` | Routed dict response. |

## Blackboard storage rules

1. One Blackboard course becomes one row in `category`.
2. Blackboard course items become rows in `data`.
3. `category_kind` should use `blackboard_course`.
4. `data_content_type` should use `blackboard_announcement`, `blackboard_course_material`, or `blackboard_assignment_upload`.
5. `data_classification_code` should use `1` for announcements, `2` for course materials, `3` for upload assignments.
6. `data_link_url` should be stable and unique per item; the schema uses it together with user/category/type to prevent duplicates.
7. Writing Blackboard data should bump `sync_state` after a successful batch.