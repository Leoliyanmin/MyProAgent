"""Migrate old tables (data/schedule/task/tis_*) into unified event table."""
import sys, json, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from local_backend.database.code.command.database_command import (
    _connect, _execute, DEFAULT_DB_PATH,
)

DB = DEFAULT_DB_PATH
now = datetime.datetime.utcnow().isoformat()


def migrate_all(user_id: str = None):
    conn = _connect(DB)
    where = f"WHERE user_id = '{user_id}'" if user_id else ""

    # 1. Blackboard assignments (data table)
    print("=== Migrating BB assignments ===")
    bb_rows = conn.execute(f"""
        SELECT d.*, c.category_title as course_name
        FROM data d
        JOIN category c ON d.data_category_id = c.category_id
        WHERE d.data_content_type = 'assignment'
          AND c.category_source = 'blackboard'
          {f"AND d.user_id = '{user_id}'" if user_id else ""}
    """).fetchall()
    bb_count = 0
    for r in bb_rows:
        d = dict(r)
        title = d.get('data_title', '')
        due = d.get('data_ddl_time') or ''
        _execute("""
            INSERT INTO event (user_id, event_title, event_type, event_source,
                event_start_time, event_end_time, event_description,
                event_link_url, event_is_completed, event_show_in_todo,
                event_priority, event_color_tag, event_meta_json, event_created_at)
            VALUES (?, ?, 'assignment', 'blackboard',
                ?, ?, ?,
                ?, 0, 1,
                0, '#ff3b30', ?, ?)
        """, (
            d['user_id'], title,
            due, due,
            d.get('course_name', ''),
            d.get('data_link_url', ''),
            json.dumps({
                'course_name': d.get('course_name', ''),
                'external_id': d.get('data_external_id', ''),
            }, ensure_ascii=False),
            d.get('data_created_at', now),
        ), DB)
        bb_count += 1
    print(f"  migrated {bb_count} BB assignments")

    # 2. TIS schedule (tis_schedule_event JOIN tis_course)
    print("=== Migrating TIS schedule ===")
    tis_rows = conn.execute(f"""
        SELECT e.*, c.course_name, c.teacher, c.location, c.weeks as course_weeks
        FROM tis_schedule_event e
        JOIN tis_course c ON e.course_id = c.course_id
        {f"WHERE e.user_id = '{user_id}'" if user_id else ""}
    """).fetchall()
    tis_count = 0
    # Calculate semester start: estimate first Monday of semester
    from datetime import datetime as dt, timedelta
    semester_start = None
    for r in tis_rows:
        d = dict(r)
        title = d.get('course_name', '')
        day_of_week = d.get('day_of_week', 0)
        week_num = d.get('week_num', 1)
        start_time = d.get('start_time', '')
        end_time = d.get('end_time', '')

        if semester_start is None:
            today = dt.now()
            semester_start = today - timedelta(days=today.weekday() + (week_num - 1) * 7)
        event_date = semester_start + timedelta(days=(week_num - 1) * 7 + day_of_week)
        date_str = event_date.strftime('%Y-%m-%d')
        start = f"{date_str}T{start_time}" if start_time else date_str
        end = f"{date_str}T{end_time}" if end_time else date_str

        _execute("""
            INSERT INTO event (user_id, event_title, event_type, event_source,
                event_start_time, event_end_time, event_location, event_description,
                event_is_completed, event_show_in_todo,
                event_priority, event_color_tag, event_meta_json, event_created_at)
            VALUES (?, ?, 'course', 'tis',
                ?, ?, ?, ?,
                0, 0,
                0, '#007aff', ?, ?)
        """, (
            d['user_id'], title,
            start, end,
            d.get('location', ''),
            d.get('teacher', ''),
            json.dumps({
                'teacher': d.get('teacher', ''),
                'day_of_week': day_of_week,
                'week_num': week_num,
                'period_start': d.get('period_start', 0),
                'period_end': d.get('period_end', 0),
                'weeks': d.get('course_weeks', ''),
            }, ensure_ascii=False),
            now,
        ), DB)
        tis_count += 1
    print(f"  migrated {tis_count} TIS events")

    # 3. Schedule events
    print("=== Migrating schedules ===")
    sched_rows = conn.execute(f"""
        SELECT * FROM schedule {where}
    """).fetchall()
    sched_count = 0
    for r in sched_rows:
        d = dict(r)
        _execute("""
            INSERT INTO event (user_id, event_title, event_type, event_source,
                event_start_time, event_end_time, event_location, event_description,
                event_link_url,
                event_is_completed, event_show_in_todo,
                event_priority, event_color_tag, event_meta_json, event_created_at)
            VALUES (?, ?, 'manual', 'manual',
                ?, ?, ?, ?,
                ?,
                ?, 1,
                ?, ?, ?, ?)
        """, (
            d['user_id'], d.get('schedule_title', ''),
            d.get('schedule_start_time', ''), d.get('schedule_end_time', ''),
            d.get('schedule_location', ''), d.get('schedule_description', ''),
            d.get('schedule_related_link', ''),
            d.get('schedule_is_completed', 0),
            d.get('schedule_priority', 2),
            d.get('schedule_color_tag', '#007aff'),
            json.dumps({'recurrence': d.get('schedule_recurrence_rule', '')}, ensure_ascii=False),
            now,
        ), DB)
        sched_count += 1
    print(f"  migrated {sched_count} schedules")

    # 4. Tasks (as todo-only events, no date)
    print("=== Migrating tasks ===")
    task_rows = conn.execute(f"""
        SELECT * FROM task {where}
    """).fetchall()
    task_count = 0
    for r in task_rows:
        d = dict(r)
        _execute("""
            INSERT INTO event (user_id, event_title, event_type, event_source,
                event_start_time, event_end_time, event_description,
                event_is_completed, event_show_in_todo,
                event_priority, event_color_tag, event_meta_json, event_created_at)
            VALUES (?, ?, 'manual', 'manual',
                ?, ?, ?,
                ?, 1,
                ?, '#ff9500', ?, ?)
        """, (
            d['user_id'], d.get('title', ''),
            d.get('due_date', ''), d.get('due_date', ''),
            d.get('description', ''),
            0 if d.get('status') != 'completed' else 1,
            d.get('priority', 2),
            json.dumps({'old_task_id': d.get('task_id'), 'old_linked_schedule_id': d.get('linked_schedule_id')}, ensure_ascii=False),
            d.get('created_at', now),
        ), DB)
        task_count += 1
    print(f"  migrated {task_count} tasks")

    conn.close()
    print(f"\nDone: {bb_count} BB + {tis_count} TIS + {sched_count} schedules + {task_count} tasks")


if __name__ == "__main__":
    uid = sys.argv[1] if len(sys.argv) > 1 else None
    migrate_all(uid)
