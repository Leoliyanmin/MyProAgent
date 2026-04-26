from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any

try:
    from . import database_command as db
except ImportError:
    import database_command as db


_USER_LOCKS: dict[str, threading.RLock] = {}
_USER_LOCKS_GUARD = threading.Lock()


def _get_user_lock(user_id: str) -> threading.RLock:
    with _USER_LOCKS_GUARD:
        lock = _USER_LOCKS.get(user_id)
        if lock is None:
            lock = threading.RLock()
            _USER_LOCKS[user_id] = lock
        return lock


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _normalize_datetime(value: Any, fallback: str | None = None) -> str:
    if value is None:
        if fallback is None:
            return _now_iso()
        return fallback

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()

    if isinstance(value, str):
        normalized = _parse_iso_datetime(value)
        if normalized is not None:
            return value

    if fallback is not None:
        return fallback
    raise ValueError("crawled_at must be an ISO-8601 datetime")


def _normalize_text_payload(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _clean_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


class BlackboardOperations:
    CATEGORY_KIND = "blackboard_course"

    def import_crawl_result(self, user_id: str, crawl_result: dict[str, Any] | list[Any], crawled_at: Any = None) -> dict[str, Any]:
        with _get_user_lock(user_id):
            self._require_user(user_id)
            crawled_at_iso = _normalize_datetime(crawled_at)
            courses = self._extract_courses(crawl_result)

            summary = {
                "courses_seen": len(courses),
                "categories_created": 0,
                "categories_updated": 0,
                "data_created": 0,
                "data_updated": 0,
                "data_skipped": 0,
            }
            course_results: list[dict[str, Any]] = []
            changed = False

            for course in courses:
                course_result = self._upsert_course(user_id, course, crawled_at_iso)
                course_results.append(course_result)
                summary["categories_created"] += course_result["category_created"]
                summary["categories_updated"] += course_result["category_updated"]
                summary["data_created"] += course_result["data_created"]
                summary["data_updated"] += course_result["data_updated"]
                summary["data_skipped"] += course_result["data_skipped"]
                changed = changed or course_result["changed"]

            if changed:
                self._bump_sync_state(user_id, crawled_at_iso)

            return {
                "ok": True,
                "status": 200,
                "user_id": user_id,
                "crawled_at": crawled_at_iso,
                "summary": summary,
                "courses": course_results,
            }

    def _extract_courses(self, crawl_result: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
        if isinstance(crawl_result, list):
            courses = crawl_result
        elif isinstance(crawl_result, dict):
            if isinstance(crawl_result.get("courses"), list):
                courses = crawl_result["courses"]
            elif "id" in crawl_result and "name" in crawl_result:
                courses = [crawl_result]
            else:
                raise ValueError("crawl_result must contain a courses list or a course object")
        else:
            raise ValueError("crawl_result must be a dict or a list")

        normalized: list[dict[str, Any]] = []
        for course in courses:
            if not isinstance(course, dict):
                raise ValueError("each course must be a JSON object")
            normalized.append(course)
        return normalized

    def _upsert_course(self, user_id: str, course: dict[str, Any], crawled_at: str) -> dict[str, Any]:
        course_link = _clean_str(course.get("url"))
        if not course_link:
            raise ValueError("course.url is required")

        course_id = _clean_str(course.get("id"))
        course_name = _clean_str(course.get("name") or course.get("title") or course_id or course_link)
        category_content = _normalize_text_payload({
            "source": "blackboard",
            "course_id": course_id,
            "course_name": course_name,
            "crawl_source": "bb_result",
        })

        category_row = self._find_category(user_id, course_link)
        category_created = 0
        category_updated = 0
        changed = False

        if category_row is None:
            db.create_category(
                user_id=user_id,
                category_kind=self.CATEGORY_KIND,
                category_title=course_name,
                category_content=category_content,
                category_link=course_link,
                category_created_at=crawled_at,
            )
            category_row = self._find_category(user_id, course_link)
            if category_row is None:
                raise ValueError(f"failed to create category for course: {course_name}")
            category_created = 1
            changed = True
        else:
            if self._category_needs_update(category_row, course_name, category_content, course_link):
                db.update_category(
                    category_id=category_row["category_id"],
                    category_kind=self.CATEGORY_KIND,
                    category_title=course_name,
                    category_content=category_content,
                    category_link=course_link,
                )
                category_updated = 1
                changed = True

        data_created = 0
        data_updated = 0
        data_skipped = 0

        for item_type, items in self._iter_course_item_groups(course):
            for index, item in enumerate(items):
                item_result = self._upsert_item(
                    user_id=user_id,
                    category_id=category_row["category_id"],
                    course=course,
                    item_type=item_type,
                    item=item,
                    item_index=index,
                    crawled_at=crawled_at,
                )
                data_created += item_result["created"]
                data_updated += item_result["updated"]
                data_skipped += item_result["skipped"]
                changed = changed or item_result["changed"]

        return {
            "course_id": course_id,
            "course_name": course_name,
            "course_link": course_link,
            "category_id": category_row["category_id"],
            "category_created": category_created,
            "category_updated": category_updated,
            "data_created": data_created,
            "data_updated": data_updated,
            "data_skipped": data_skipped,
            "changed": changed,
        }

    def _iter_course_item_groups(self, course: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]]]]:
        groups: list[tuple[str, list[dict[str, Any]]]] = []
        for key, item_type in (
            ("announcements", "blackboard_announcement"),
            ("course_materials", "blackboard_course_material"),
            ("upload_assignments", "blackboard_assignment_upload"),
        ):
            raw_items = course.get(key, [])
            if raw_items is None:
                raw_items = []
            if not isinstance(raw_items, list):
                raise ValueError(f"course.{key} must be a list")
            normalized_items: list[dict[str, Any]] = []
            for item in raw_items:
                if not isinstance(item, dict):
                    raise ValueError(f"course.{key} items must be JSON objects")
                normalized_items.append(item)
            groups.append((item_type, normalized_items))
        return groups

    def _upsert_item(
        self,
        user_id: str,
        category_id: int,
        course: dict[str, Any],
        item_type: str,
        item: dict[str, Any],
        item_index: int,
        crawled_at: str,
    ) -> dict[str, Any]:
        link_url = _clean_str(item.get("url"))
        if not link_url:
            course_id = _clean_str(course.get("id") or course.get("name") or category_id)
            title_hint = _clean_str(item.get("label") or item.get("title") or item.get("name") or f"item-{item_index}")
            link_url = f"blackboard://{course_id}/{item_type}/{title_hint}"

        title = _clean_str(item.get("label") or item.get("title") or item.get("name") or link_url)
        content_text = _normalize_text_payload({
            "source": "blackboard",
            "course_id": _clean_str(course.get("id")),
            "course_name": _clean_str(course.get("name") or course.get("title") or course.get("id")),
            "item_type": item_type,
            "title": title,
            "url": link_url,
            "parent_label": item.get("parent_label"),
            "parent_url": item.get("parent_url"),
            "raw": item,
        })

        classification_code = self._classification_for_item_type(item_type)
        previewable = 1 if content_text else 0

        data_row = self._find_data(user_id, category_id, item_type, link_url)
        if data_row is None:
            db.create_data(
                user_id=user_id,
                data_category_id=category_id,
                data_content_type=item_type,
                data_classification_code=classification_code,
                data_title=title,
                data_content_text=content_text,
                data_link_url=link_url,
                data_release_time=None,
                data_ddl_time=None,
                data_is_previewable=previewable,
                data_created_at=crawled_at,
            )
            return {"created": 1, "updated": 0, "skipped": 0, "changed": True}

        if self._data_needs_update(data_row, category_id, item_type, title, content_text, link_url, classification_code, previewable):
            db.update_data(
                data_id=data_row["data_id"],
                data_title=title,
                data_content_text=content_text,
                data_link_url=link_url,
                data_is_previewable=previewable,
                data_classification_code=classification_code,
            )
            return {"created": 0, "updated": 1, "skipped": 0, "changed": True}

        return {"created": 0, "updated": 0, "skipped": 1, "changed": False}

    def _find_category(self, user_id: str, category_link: str) -> dict[str, Any] | None:
        for row in db.list_categories_by_user(user_id):
            if row.get("category_kind") != self.CATEGORY_KIND:
                continue
            if _clean_str(row.get("category_link")) == category_link:
                return row
        return None

    def _find_data(self, user_id: str, category_id: int, item_type: str, link_url: str) -> dict[str, Any] | None:
        for row in db.list_data_by_user(user_id):
            if int(row.get("data_category_id") or 0) != int(category_id):
                continue
            if row.get("data_content_type") != item_type:
                continue
            if _clean_str(row.get("data_link_url")) == link_url:
                return row
        return None

    def _category_needs_update(self, row: dict[str, Any], title: str, content: str, link: str) -> bool:
        return any(
            _clean_str(row.get(field)) != value
            for field, value in (
                ("category_kind", self.CATEGORY_KIND),
                ("category_title", title),
                ("category_content", content),
                ("category_link", link),
            )
        )

    def _data_needs_update(
        self,
        row: dict[str, Any],
        category_id: int,
        item_type: str,
        title: str,
        content_text: str,
        link_url: str,
        classification_code: int,
        previewable: int,
    ) -> bool:
        return any(
            _clean_str(row.get(field)) != value
            for field, value in (
                ("data_category_id", str(category_id)),
                ("data_content_type", item_type),
                ("data_title", title),
                ("data_content_text", content_text),
                ("data_link_url", link_url),
                ("data_is_previewable", str(previewable)),
                ("data_classification_code", str(classification_code)),
            )
        )

    def _classification_for_item_type(self, item_type: str) -> int:
        if item_type == "blackboard_course_material":
            return 2
        if item_type == "blackboard_assignment_upload":
            return 3
        return 1

    def _require_user(self, user_id: str) -> None:
        if db.get_user(user_id) is None:
            raise ValueError(f"user not found: {user_id}")

    def _bump_sync_state(self, user_id: str, crawled_at: str) -> None:
        sync_state = db.get_sync_state(user_id)
        if sync_state is None:
            db.upsert_sync_state(
                user_id=user_id,
                user_data_updated_at=crawled_at,
                user_last_synced_at=None,
                user_version=1,
                sync_updated_at=crawled_at,
            )
            return

        current_version = int(sync_state.get("user_version") or 1)
        db.upsert_sync_state(
            user_id=user_id,
            user_data_updated_at=crawled_at,
            user_last_synced_at=sync_state.get("user_last_synced_at"),
            user_version=current_version + 1,
            sync_updated_at=crawled_at,
        )