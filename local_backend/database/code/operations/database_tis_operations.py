import json
import time
from datetime import datetime, date, timedelta
from typing import Optional, Dict

from local_backend.database.code.command.database_command import (
    create_account,
    list_accounts_by_user,
    update_account_sync_time,
    delete_account,
    create_event,
    list_events_by_user,
    update_event,
    delete_event,
    upsert_sync_state,
    get_sync_state,
)


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
        old_events = list_events_by_user(user_id, event_type="course", event_source="tis")
        for ev in old_events:
            delete_event(ev["event_id"])

        now = datetime.utcnow().isoformat()
        term = schedule_data.get("term", "")
        schedule = schedule_data.get("schedule", {})

        # Phase 1: collect all courses and their time slots
        courses: dict[tuple, dict] = {}
        day_map = {"星期一": 0, "星期二": 1, "星期三": 2, "星期四": 3, "星期五": 4, "星期六": 5, "星期日": 6}

        for day_name, day_courses in schedule.items():
            for course in day_courses:
                name = course.get("title", "")
                key = (name, term)
                dow = day_map.get(day_name, 0)
                periods = course.get("periods", "")
                period_parts = periods.replace("节", "").split("-") if periods else ["0", "0"]
                ps = int(period_parts[0]) if period_parts and period_parts[0].isdigit() else 0
                pe = int(period_parts[-1]) if period_parts and period_parts[-1].isdigit() else 0

                if key not in courses:
                    courses[key] = {
                        "teacher": course.get("teacher", ""),
                        "location": course.get("location", ""),
                        "weeks": course.get("weeks", ""),
                        "term": term,
                        "schedule_events": [],
                    }
                for wn in self._parse_weeks(course.get("weeks", "")) or {1}:
                    courses[key]["schedule_events"].append({
                        "day_of_week": dow, "week_num": wn,
                        "period_start": ps, "period_end": pe,
                        "start_time": course.get("start", ""),
                        "end_time": course.get("end", ""),
                    })

        semester_monday = self._estimate_semester_monday(term)
        slot_count = 0

        for (name, _term), meta in courses.items():
            for se in meta.get("schedule_events", []):
                start_dt = None
                end_dt = None
                if semester_monday:
                    event_date = semester_monday + timedelta(
                        days=(se["week_num"] - 1) * 7 + se["day_of_week"]
                    )
                    st = se.get("start_time", "") or "00:00"
                    et = se.get("end_time", "") or "23:59"
                    start_dt = f"{event_date.isoformat()}T{st}:00"
                    end_dt = f"{event_date.isoformat()}T{et}:00"

                slot_meta = json.dumps({
                    "course_name": name,
                    "teacher": meta.get("teacher", ""),
                    "location": meta.get("location", ""),
                    "weeks": meta.get("weeks", ""),
                    "term": meta.get("term", ""),
                    "week_num": se["week_num"],
                    "day_of_week": se["day_of_week"],
                    "period_start": se.get("period_start", 0),
                    "period_end": se.get("period_end", 0),
                }, ensure_ascii=False)

                create_event(
                    user_id=user_id,
                    event_title=name,
                    event_type="course",
                    event_source="tis",
                    event_start_time=start_dt,
                    event_end_time=end_dt,
                    event_show_in_todo=0,
                    event_location=meta.get("location", ""),
                    event_priority=4,
                    event_color_tag="#8e8e93",
                    event_meta_json=slot_meta,
                    event_created_at=now,
                )
                slot_count += 1

        self._bump_sync(user_id)
        return {"courses": len(courses), "slots": slot_count}

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

    @staticmethod
    def _estimate_semester_monday(term: str) -> date | None:
        import re
        m = re.match(r"(\d{4})", str(term))
        if not m:
            return None
        year = int(m.group(1))
        season = str(term).replace(m.group(0), "")
        if "春" in season:
            anchor = date(year, 2, 1)
            days_to_monday = (7 - anchor.weekday()) % 7
            return anchor + timedelta(days=days_to_monday, weeks=3)
        elif "秋" in season:
            anchor = date(year, 9, 1)
        elif "夏" in season:
            anchor = date(year, 7, 1)
        else:
            anchor = date(year, 1, 1)
        days_until_monday = (7 - anchor.weekday()) % 7
        return anchor + timedelta(days=days_until_monday)

    def _bump_sync(self, user_id: str) -> None:
        state = get_sync_state(user_id)
        if state:
            now = datetime.utcnow().isoformat()
            upsert_sync_state(
                user_id=user_id, user_data_updated_at=now,
                user_last_synced_at=state.get("user_last_synced_at"),
                user_version=state.get("user_version", 1) + 1,
                sync_updated_at=now,
            )
