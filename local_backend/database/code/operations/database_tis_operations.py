from local_backend.database.code.command.database_command import (
    create_account,
    list_accounts_by_user,
    update_account_sync_time,
    delete_account,
    create_tis_course,
    list_tis_courses_by_user,
    delete_tis_courses_by_user,
    create_tis_event,
    delete_tis_events_by_user,
    create_category,
    list_categories_by_user,
    create_data,
    upsert_sync_state,
    get_sync_state,
)
from typing import Optional, Dict
import time


class TisAccountOperations:
    def create_or_update_tis_account(
        self,
        user_id: str,
        student_id: str,
        encrypted_cookie: str,
        bind_time: Optional[str] = None,
        last_sync_time: Optional[str] = None,
    ) -> int:
        existing_accounts = list_accounts_by_user(user_id)
        tis_account = None
        for account in existing_accounts:
            if account['account_platform_type'] == 'tis':
                tis_account = account
                break
        if tis_account:
            delete_account(tis_account['account_id'])
        if not bind_time:
            bind_time = time.strftime('%Y-%m-%d %H:%M:%S')
        return create_account(
            user_id=user_id,
            account_platform_type='tis',
            account_platform_username=student_id,
            content=encrypted_cookie,
            account_bind_time=bind_time,
            account_last_sync_time=last_sync_time,
        )

    def get_tis_account(self, user_id: str) -> Optional[Dict]:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'tis':
                return account
        return None

    def update_sync_time(self, account_id: int, sync_time: Optional[str] = None) -> None:
        if not sync_time:
            sync_time = time.strftime('%Y-%m-%d %H:%M:%S')
        update_account_sync_time(account_id, sync_time)

    def delete_tis_account(self, user_id: str) -> None:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'tis':
                delete_account(account['account_id'])


class TisCourseOperations:
    def save_all(self, user_id: str, schedule_data: dict) -> dict:
        delete_tis_events_by_user(user_id)
        delete_tis_courses_by_user(user_id)

        schedule = schedule_data.get("schedule", {})
        course_map = {}

        for day_name, courses in schedule.items():
            for course in courses:
                name = course.get("title", "")
                teacher = course.get("teacher", "")
                loc = course.get("location", "")
                weeks = course.get("weeks", "")
                periods = course.get("periods", "")

                key = (name, schedule_data.get("term", ""))
                if key not in course_map:
                    import json, datetime as dt
                    cid = create_tis_course(
                        user_id=user_id, course_name=name,
                        teacher=teacher, location=loc, weeks=weeks,
                        term=schedule_data.get("term", ""),
                        raw_data=json.dumps(course, ensure_ascii=False),
                    )
                    cat_id = self._ensure_cat(user_id, name)
                    create_data(
                        user_id=user_id, data_category_id=cat_id,
                        data_content_type="tis_course", data_classification_code=1,
                        data_title=name,
                        data_content_text=json.dumps(course, ensure_ascii=False),
                        data_link_url="tis:{}".format(cid),
                        data_release_time=None, data_ddl_time=None,
                        data_is_previewable=1, data_source="tis",
                        data_created_at=dt.datetime.utcnow().isoformat(),
                    )
                    course_map[key] = cid

                day_map = {"星期一": 0, "星期二": 1, "星期三": 2, "星期四": 3, "星期五": 4, "星期六": 5, "星期日": 6}
                dow = day_map.get(day_name, 0)
                period_parts = periods.replace("节", "").split("-") if periods else ["0", "0"]
                ps = int(period_parts[0]) if period_parts and period_parts[0].isdigit() else 0
                pe = int(period_parts[-1]) if period_parts and period_parts[-1].isdigit() else 0

                for wn in self._parse_weeks(weeks) or {1}:
                    create_tis_event(
                        course_id=course_map[key], user_id=user_id,
                        day_of_week=dow, week_num=wn,
                        period_start=ps, period_end=pe,
                        start_time=course.get("start", ""),
                        end_time=course.get("end", ""),
                    )

        self._bump_sync(user_id)
        return {"courses": len(course_map)}

    def _parse_weeks(self, weeks_str):
        result = set()
        if not weeks_str:
            return result
        import re
        for part in weeks_str.replace("，", ",").split(","):
            part = part.strip()
            m = re.match(r"(\d+)-(\d+)(双|单)?周", part)
            if m:
                s, e = int(m.group(1)), int(m.group(2))
                parity = m.group(3)
                for w in range(s, e + 1):
                    if parity == "双" and w % 2 != 0:
                        continue
                    if parity == "单" and w % 2 != 1:
                        continue
                    result.add(w)
            else:
                m2 = re.match(r"(\d+)周", part)
                if m2:
                    result.add(int(m2.group(1)))
        return result

    def _ensure_cat(self, user_id: str, course_name: str) -> int:
        import datetime as dt
        cats = list_categories_by_user(user_id)
        for c in cats:
            if c.get("category_kind") == "tis_course" and c.get("category_title") == course_name:
                return c["category_id"]
        now = dt.datetime.utcnow().isoformat()
        return create_category(
            user_id=user_id, category_kind="tis_course", category_title=course_name,
            category_content=None, category_link=f"tis:{course_name}",
            category_source="tis", category_created_at=now,
        )

    def _bump_sync(self, user_id: str) -> None:
        import datetime as dt
        state = get_sync_state(user_id)
        if state:
            now = dt.datetime.utcnow().isoformat()
            upsert_sync_state(
                user_id=user_id, user_data_updated_at=now,
                user_last_synced_at=state.get("user_last_synced_at"),
                user_version=state.get("user_version", 1) + 1,
                sync_updated_at=now,
            )
