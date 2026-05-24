import json, datetime
from local_backend.database.code.command.database_command import (
    create_event, list_events_by_user, delete_event,
    upsert_sync_state, get_sync_state,
)


class BbV2Operations:
    def save_all(self, user_id: str, courses: list) -> dict:
        old = list_events_by_user(user_id, event_source="blackboard")
        for ev in old:
            delete_event(ev["event_id"])

        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        saved = 0
        for course in courses:
            course_name = course.get("name", "")
            for a in course.get("assignments", []):
                title = a.get("name", "")
                due = a.get("due_date")
                # 跳过今天之前的作业
                if due and due[:10] < today:
                    continue
                link = a.get("link", "") or a.get("url", "")
                ext_id = a.get("id") or title or ""
                if not link and ext_id:
                    link = f"ics://{ext_id}"
                create_event(
                    user_id=user_id, event_title=title,
                    event_type="assignment", event_source="blackboard",
                    event_start_time=due, event_end_time=due,
                    event_link_url=link,
                    event_description=course_name,
                    event_is_completed=0, event_show_in_todo=1,
                    event_priority=0, event_color_tag="#ff3b30",
                    event_meta_json=json.dumps({
                        "course_name": course_name,
                        "content": a.get("content", []),
                    }, ensure_ascii=False),
                    event_created_at=datetime.datetime.utcnow().isoformat(),
                )
                saved += 1
        self._bump_sync(user_id)
        return {"synced": len(courses), "events": saved}

    def _bump_sync(self, user_id: str) -> None:
        state = get_sync_state(user_id)
        if state:
            now = datetime.datetime.utcnow().isoformat()
            upsert_sync_state(
                user_id=user_id, user_data_updated_at=now,
                user_last_synced_at=state.get("user_last_synced_at"),
                user_version=state.get("user_version", 1) + 1,
                sync_updated_at=now,
            )
