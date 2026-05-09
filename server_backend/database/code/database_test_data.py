from __future__ import annotations

from copy import deepcopy


TEST_DATA = {
    "user": {
        "user_id": "user-test-001",
        "username": "alice",
        "user_email": "alice@example.com",
        "user_password_hash": "hash-test-001",
        "user_salt": "salt-test-001",
        "user_is_active": 1,
        "user_created_at": "2026-03-31T10:00:00+00:00",
        "user_last_login": "2026-03-31T10:05:00+00:00",
        "user_auto_login_token": "token-test-001",
        "user_source_device_id": "device-local-001",
    },
    "user_match_profile": {
        "user_id": "user-test-001",
        "answers": "{\"q1\":\"早睡\",\"q2\":\"篮球,阅读\",\"intro\":\"喜欢结伴学习\"}",
        "is_open": 1,
        "last_match_time": "2026-03-31T10:07:30+00:00",
    },
    "match_result": {
        "user_id": "user-test-001",
        "matched_user_id": "user-test-002",
        "similarity_score": 0.92,
        "created_at": "2026-03-31T10:07:45+00:00",
        "is_shared": 0,
    },
    "sync_state": {
        "user_id": "user-test-001",
        "user_data_updated_at": "2026-03-31T10:06:00+00:00",
        "user_last_synced_at": "2026-03-31T10:07:00+00:00",
        "user_version": 1,
        "sync_updated_at": "2026-03-31T10:07:00+00:00",
    },
    "account": {
        "user_id": "user-test-001",
        "account_platform_type": "github",
        "account_platform_username": "alice-gh",
        "content": None,
        "account_mail_password": "mail-pass-test",
        "account_cookie": "cookie-test",
        "account_bind_time": "2026-03-31T10:08:00+00:00",
        "account_last_sync_time": "2026-03-31T10:09:00+00:00",
    },
    "category": {
        "user_id": "user-test-001",
        "category_kind": "course",
        "category_title": "SE Project",
        "category_content": "team project records",
        "category_link": "https://example.com/course",
        "category_created_at": "2026-03-31T10:10:00+00:00",
    },
    "data": {
        "user_id": "user-test-001",
        "data_content_type": "note",
        "data_classification_code": 2,
        "data_title": "week1",
        "data_content_text": "initial checklist",
        "data_link_url": "https://example.com/week1",
        "data_release_time": "2026-03-31T10:11:00+00:00",
        "data_ddl_time": "2026-04-07T10:11:00+00:00",
        "data_is_previewable": 1,
        "data_created_at": "2026-03-31T10:11:00+00:00",
    },
    "schedule": {
        "user_id": "user-test-001",
        "schedule_event_type": "meeting",
        "schedule_title": "daily standup",
        "schedule_start_time": "2026-03-31T11:00:00+00:00",
        "schedule_end_time": "2026-03-31T11:30:00+00:00",
        "schedule_location": "online",
        "schedule_description": "sync with team",
        "schedule_related_link": "https://example.com/meet",
        "schedule_recurrence_rule": "FREQ=DAILY",
        "schedule_color_tag": "blue",
    },
    "session": {
        "user_id": "user-test-001",
        "session_last_visited_at": "2026-03-31T10:12:00+00:00",
    },
    "chat": {
        "chat_role": "user",
        "chat_message_content": "hello",
        "thought_trace": None,
        "chat_tool_calls": None,
        "chat_tokens_usage": "{\"prompt\":10,\"completion\":5}",
        "chat_created_at": "2026-03-31T10:13:00+00:00",
    },
    "code": {
        "user_id": "user-test-001",
        "code_email": "alice@example.com",
        "code_context": "ctx-test-001",
        "code_purpose": "login",
        "code_is_used": 0,
        "code_expires_at": "2026-04-01T10:13:00+00:00",
        "code_created_at": "2026-03-31T10:13:00+00:00",
    },
}


def get_test_data() -> dict:
    return deepcopy(TEST_DATA)
