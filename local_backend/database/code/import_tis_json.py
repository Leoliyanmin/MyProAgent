"""Import TIS schedule JSON into event table."""
import json, sys, re
from pathlib import Path
from datetime import datetime, date, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from local_backend.database.code.command.database_command import (
    create_event, list_events_by_user, delete_event,
)

DAY_MAP = {"星期一": 0, "星期二": 1, "星期三": 2, "星期四": 3, "星期五": 4, "星期六": 5, "星期日": 6}

def parse_periods(periods_str: str) -> tuple[int, int]:
    m = re.match(r"(\d+)-(\d+)节?", periods_str.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0

def parse_weeks(weeks_str: str) -> set[int]:
    result = set()
    if not weeks_str:
        return result
    for part in weeks_str.replace("，", ",").split(","):
        part = part.strip()
        m = re.match(r"(\d+)-(\d+)(双|单)?周?", part)
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
            m2 = re.match(r"(\d+)周?", part)
            if m2:
                result.add(int(m2.group(1)))
    return result


def _estimate_semester_monday(term: str) -> date | None:
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


def import_from_json(json_path: str, user_id: str) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    schedule = data.get("schedule", {})
    if not schedule:
        return {"ok": False, "message": "No schedule data in JSON"}

    old_events = list_events_by_user(user_id, event_type="course", event_source="tis")
    for ev in old_events:
        delete_event(ev["event_id"])

    term = data.get("term", "")
    now = datetime.utcnow().isoformat()
    courses: dict[tuple, dict] = {}

    for day_name, day_courses in schedule.items():
        dow = DAY_MAP.get(day_name)
        if dow is None:
            print(f"  [skip] unknown day: {day_name}")
            continue
        for course in day_courses:
            name = course.get("title", "")
            key = (name, term)
            ps, pe = parse_periods(course.get("periods", ""))
            if key not in courses:
                courses[key] = {
                    "teacher": course.get("teacher", ""),
                    "location": course.get("location", ""),
                    "weeks": course.get("weeks", ""),
                    "term": term,
                    "schedule_events": [],
                }
            for wn in parse_weeks(course.get("weeks", "")) or {1}:
                courses[key]["schedule_events"].append({
                    "day_of_week": dow, "week_num": wn,
                    "period_start": ps, "period_end": pe,
                    "start_time": course.get("start", ""),
                    "end_time": course.get("end", ""),
                })

    semester_monday = _estimate_semester_monday(term)
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

            cid = create_event(
                user_id=user_id, event_title=name,
                event_type="course", event_source="tis",
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
            print(f"  slot: {name} W{se['week_num']} D{se['day_of_week']} {se.get('start_time','')} (id={cid})")

    return {
        "ok": True,
        "courses": len(courses),
        "slots": slot_count,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python import_tis_json.py <json_path> <user_id>")
        sys.exit(1)
    json_file = sys.argv[1]
    uid = sys.argv[2]

    print(f"Importing: {json_file}")
    print(f"User: {uid}")
    result = import_from_json(json_file, uid)
    print(json.dumps(result, ensure_ascii=False, indent=2))
