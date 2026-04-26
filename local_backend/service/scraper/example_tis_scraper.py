# backend/services/tis_scraper.py
# 从教务系统(TIS)爬取课程信息

import os
import re
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Any
import httpx

from services.tools import ensure_tis_session, post_json


CAS_LOGIN = "https://cas.sustech.edu.cn/cas/login"
TIS_SERVICE_URL = "https://tis.sustech.edu.cn/cas"
TIS_BASE_URL = "https://tis.sustech.edu.cn/"
WEEKDAY_LABELS = {
    1: ("Monday", "星期一"),
    2: ("Tuesday", "星期二"),
    3: ("Wednesday", "星期三"),
    4: ("Thursday", "星期四"),
    5: ("Friday", "星期五"),
    6: ("Saturday", "星期六"),
    7: ("Sunday", "星期日"),
}


def build_period_map(rows: Iterable[Dict]) -> Dict[int, Dict[str, Optional[str]]]:
    period_map: Dict[int, Dict[str, Optional[str]]] = {}
    for row in rows:
        try:
            idx = int(row.get("xj"))
        except (TypeError, ValueError):
            continue
        period_map[idx] = {
            "label": row.get("djms"),
            "start": row.get("kssj"),
            "end": row.get("jssj"),
        }
    return period_map


def parse_course_entry(raw: Dict, period_map: Dict[int, Dict[str, Optional[str]]]) -> Dict[str, Optional[str]]:
    key = raw.get("KEY", "")
    day_match = re.match(r"xq(\d+)_jc", key)
    day = int(day_match.group(1)) if day_match else 0
    segments = re.findall(r"\[(.*?)\]", raw.get("SKSJ", ""))
    start_period = raw.get("KSJC")
    end_period = raw.get("JSJC")
    start_info = period_map.get(start_period) if isinstance(start_period, int) else None
    end_info = period_map.get(end_period) if isinstance(end_period, int) else None
    return {
        "day": day,
        "title": (raw.get("SKSJ", "").split("\n") or [""])[0].strip(),
        "teacher": segments[0] if len(segments) > 0 else "",
        "group": segments[1] if len(segments) > 1 else "",
        "weeks": segments[2] if len(segments) > 2 else "",
        "location": segments[3] if len(segments) > 3 else "",
        "periods": segments[4] if len(segments) > 4 else "",
        "start": start_info.get("start") if start_info else None,
        "end": end_info.get("end") if end_info else None,
    }


def render_course_line(course: Dict[str, Optional[str]]) -> str:
    time_window = None
    if course.get("start") and course.get("end"):
        time_window = f"{course['start']}-{course['end']}"
    elif course.get("periods"):
        time_window = course["periods"]
    parts: List[str] = []
    if time_window:
        parts.append(f"[{time_window}]")
    if course.get("title"):
        parts.append(course["title"])
    if course.get("teacher"):
        parts.append(course["teacher"])
    if course.get("location"):
        parts.append(course["location"])
    if course.get("weeks"):
        parts.append(f"周次:{course['weeks']}")
    if course.get("group"):
        parts.append(course["group"])
    return " | ".join(parts)


async def get_student_id(client: httpx.AsyncClient) -> str:
    """从已登录的客户端获取学生学号(student_id)"""
    await ensure_tis_session(client)
    user_info = await post_json(client, "user/me")
    # 返回学号信息
    return user_info.get("xh", "")


async def run_tis_scraper(cli: "httpx.AsyncClient", week_override: Optional[str] = None) -> Dict[str, Any]:
    try:
        await ensure_tis_session(cli)
        user_info = await post_json(cli, "user/me")
        term_info = await post_json(cli, "component/querydangqianxnxq")
        current_week = await post_json(cli, "component/querydangqianzc")
        target_week = week_override or os.environ.get("TIS_WEEK", "").strip() or str(current_week)
        if not target_week.isdigit():
            raise RuntimeError(f"无效的周次参数: {target_week}")

        period_rows = await post_json(
            cli,
            "component/queryKbjg",
            {"xn": term_info["XN"], "xq": term_info["XQ"], "pylx": user_info.get("pylx")},
        )
        period_map = build_period_map(period_rows)

        raw_courses = await post_json(
            cli,
            "xszykb/queryxszykbzhou",
            {"xn": term_info["XN"], "xq": term_info["XQ"], "zc": target_week},
        )
        if not isinstance(raw_courses, list):
            raise RuntimeError("课表接口返回数据格式异常。")

        # 解析课程数据
        parsed_courses = []
        for raw in raw_courses:
            course = parse_course_entry(raw, period_map)
            if course.get("day"):
                parsed_courses.append(course)

        # 按星期分组
        grouped = defaultdict(list)
        for course in parsed_courses:
            grouped[course["day"]].append(course)

        # 使用user_info中的真实姓名，不依赖username
        user_name = user_info.get("xm") or user_info.get("xm_en") or "Unknown User"
        department = user_info.get("bmmc") or user_info.get("bmmc_en") or "Unknown Department"
        term_name = term_info.get("XNXQ") or term_info
        print(f"用户: {user_name} | 院系: {department} | 学期: {term_name} | 第 {target_week} 周")

        result_dict = {
            "user": user_name,
            "department": department,
            "term": term_name,
            "week": target_week,
            "total_courses": len(parsed_courses),
            "schedule": {}
        }

        if not grouped:
            print("当前周无课程安排。")
            result_dict["schedule"] = {}
            return result_dict

        for day in range(1, 8):
            day_courses = grouped.get(day)
            if not day_courses:
                continue
            label_en, label_cn = WEEKDAY_LABELS.get(day, (f"Day {day}", f"第{day}天"))
            print(f"\n{label_cn} / {label_en}")
            day_courses.sort(key=lambda item: (item.get("start") or "", item.get("periods") or ""))

            day_schedule = []
            for course in day_courses:
                print("  " + render_course_line(course))

                course_detail = {
                    "title": course.get("title", ""),
                    "teacher": course.get("teacher", ""),
                    "group": course.get("group", ""),
                    "weeks": course.get("weeks", ""),
                    "location": course.get("location", ""),
                    "periods": course.get("periods", ""),
                    "start": course.get("start", ""),
                    "end": course.get("end", ""),
                }

                day_schedule.append(course_detail)

            result_dict["schedule"][label_cn] = day_schedule

        return result_dict

    except Exception as e:
        print(f"爬取课程信息时发生错误: {str(e)}")
        raise e