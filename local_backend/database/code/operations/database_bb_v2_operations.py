import json
import time
from typing import Optional, Dict, List

from local_backend.database.code.command.database_command import (
    create_category, list_categories_by_user,
    create_data, upsert_sync_state, get_sync_state,
)


class BbV2Operations:
    def save_all(self, user_id: str, courses: list) -> dict:
        import datetime
        for course in courses:
            name = course.get("name", "")
            link = course.get("link", "")
            bb_id = course.get("id", "")

            cat_id = self._ensure_course_cat(user_id, name, bb_id)

            for a in course.get("assignments", []):
                create_data(
                    user_id=user_id, data_category_id=cat_id,
                    data_content_type="assignment", data_classification_code=3,
                    data_title=a.get("name", ""), data_link_url=a.get("link", ""),
                    data_ddl_time=a.get("due_date"),
                    data_content_text=json.dumps(a.get("content", []), ensure_ascii=False),
                    data_is_previewable=1, data_source="blackboard",
                    data_external_id=a.get("id", ""),
                    data_created_at=datetime.datetime.utcnow().isoformat(),
                )

            for ann in course.get("announcements", []):
                create_data(
                    user_id=user_id, data_category_id=cat_id,
                    data_content_type="announcement", data_classification_code=1,
                    data_title=ann.get("title", ""), data_link_url=ann.get("url", ""),
                    data_release_time=ann.get("date", ""),
                    data_content_text=str(ann.get("content", "")),
                    data_is_previewable=1, data_source="blackboard",
                    data_created_at=datetime.datetime.utcnow().isoformat(),
                )

            for mat in course.get("course_materials", []):
                create_data(
                    user_id=user_id, data_category_id=cat_id,
                    data_content_type="material", data_classification_code=2,
                    data_title=mat.get("title", ""), data_link_url=mat.get("url", ""),
                    data_release_time=mat.get("date", ""),
                    data_content_text=str(mat.get("content", "")),
                    data_is_previewable=1, data_source="blackboard",
                    data_created_at=datetime.datetime.utcnow().isoformat(),
                )

        self._bump_sync(user_id)
        return {"synced": len(courses)}

    def _ensure_course_cat(self, user_id: str, name: str, bb_id: str) -> int:
        import datetime
        cats = list_categories_by_user(user_id)
        for c in cats:
            if c.get("category_kind") == "course" and c.get("category_external_id") == bb_id:
                return c["category_id"]
            if c.get("category_kind") == "course" and c.get("category_title") == name:
                return c["category_id"]
        now = datetime.datetime.utcnow().isoformat()
        return create_category(
            user_id=user_id, category_kind="course", category_title=name,
            category_source="blackboard", category_external_id=bb_id,
            category_created_at=now,
        )

    def _bump_sync(self, user_id: str) -> None:
        import datetime
        state = get_sync_state(user_id)
        if state:
            now = datetime.datetime.utcnow().isoformat()
            upsert_sync_state(
                user_id=user_id, user_data_updated_at=now,
                user_last_synced_at=state.get("user_last_synced_at"),
                user_version=state.get("user_version", 1) + 1,
                sync_updated_at=now,
            )
