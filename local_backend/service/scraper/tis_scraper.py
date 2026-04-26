# backend/services/tis_scraper.py
# 从教务系统(TIS)爬取课程信息

import os
import re
import json
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Any
import requests

TIS_BASE_URL = "https://tis.sustech.edu.cn/"
TIS_API_BASE = "https://tis.sustech.edu.cn/"

# 输出文件路径
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'tis_result.txt')

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
    """构建节次映射表"""
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
    """解析单个课程条目"""
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


class TisScraper:
    """TIS教务系统爬虫服务"""

    def __init__(self, session: requests.Session = None):
        if session:
            self.session = session
        else:
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Referer": "https://tis.sustech.edu.cn/",
                "Origin": "https://tis.sustech.edu.cn",
            })

    def set_cookies(self, cookies: Dict[str, str]):
        """设置会话Cookie"""
        self.session.cookies.clear()
        self.session.cookies.update(cookies)

    def _post_json(self, endpoint: str, data: Dict = None) -> Any:
        """发送POST请求并返回JSON结果"""
        url = TIS_API_BASE + endpoint
        resp = self.session.post(url, json=data or {}, timeout=20)
        resp.raise_for_status()
        return resp.json()

    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息"""
        url = TIS_API_BASE + "user/me"
        
        try:
            resp = self.session.get(url, timeout=20)
            
            content_type = resp.headers.get('Content-Type', '')
            if 'json' in content_type:
                try:
                    result = resp.json()
                    # 确保返回的是字典
                    if isinstance(result, dict):
                        return result
                    else:
                        return {}
                except Exception as e:
                    return {}
            else:
                return {}
            
        except Exception as e:
            return {}

    def get_current_term(self) -> Dict[str, Any]:
        """获取当前学期信息"""
        try:
            result = self._post_json("component/querydangqianxnxq")
            # 确保返回的是字典
            if isinstance(result, dict):
                return result
            else:
                return {}
        except Exception as e:
            return {}

    def get_current_week(self) -> str:
        """获取当前周次"""
        result = self._post_json("component/querydangqianzc")
        return str(result) if result else "1"

    def get_period_map(self, term_info: Dict[str, Any], user_info: Dict[str, Any]) -> Dict[int, Dict[str, Optional[str]]]:
        """获取节次映射表"""
        try:
            period_rows = self._post_json(
                "component/queryKbjg",
                {"xn": term_info.get("XN"), "xq": term_info.get("XQ"), "pylx": user_info.get("pylx")},
            )
            # 确保返回的是列表
            if isinstance(period_rows, list):
                return build_period_map(period_rows)
            else:
                return {}
        except Exception as e:
            return {}

    def get_week_courses(self, term_info: Dict[str, Any], week: str) -> List[Dict]:
        """获取指定周次的课程"""
        import logging
        logger = logging.getLogger("tis_scraper")
        
        try:
            raw_courses = self._post_json(
                "xszykb/queryxszykbzhou",
                {"xn": term_info.get("XN"), "xq": term_info.get("XQ"), "zc": week},
            )
            
            logger.debug(f"get_week_courses返回类型: {type(raw_courses)}")
            logger.debug(f"get_week_courses返回内容: {str(raw_courses)[:300]}")
            
            if isinstance(raw_courses, list):
                return raw_courses
            elif isinstance(raw_courses, dict):
                # 可能是错误响应，尝试提取错误信息
                error_msg = raw_courses.get('msg') or raw_courses.get('message') or "未知错误"
                logger.warning(f"课表接口返回错误: {error_msg}")
                return []
            else:
                logger.warning(f"课表接口返回数据格式异常，类型: {type(raw_courses)}")
                return []
        except Exception as e:
            logger.error(f"调用课表接口失败: {str(e)}")
            return []

    def _write_result(self, result_dict: Dict[str, Any], user_info: Dict[str, Any], 
                      term_info: Dict[str, Any], raw_courses: List[Dict]) -> None:
        """将爬取结果写入文件"""
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            output_content = f"""========================================
TIS 爬取结果
========================================
时间: {current_time}
用户: {result_dict.get('user', '')}
院系: {result_dict.get('department', '')}
学期: {result_dict.get('term', '')}
周次: {result_dict.get('week', '')}
课程总数: {result_dict.get('total_courses', 0)}

========================================
原始用户信息
========================================
{json.dumps(user_info, ensure_ascii=False, indent=2)}

========================================
原始学期信息
========================================
{json.dumps(term_info, ensure_ascii=False, indent=2)}

========================================
原始课程数据
========================================
{json.dumps(raw_courses, ensure_ascii=False, indent=2)}

========================================
整理后的课程表
========================================
{json.dumps(result_dict, ensure_ascii=False, indent=2)}
"""
            OUTPUT_FILE_PATH = OUTPUT_FILE
            with open(OUTPUT_FILE_PATH, "w", encoding="utf-8") as f:
                f.write(output_content)
        except Exception as e:
            pass

    def scrape_schedule(self, week_override: Optional[str] = None) -> Dict[str, Any]:
        """爬取课程表信息"""
        try:
            import logging
            logger = logging.getLogger("tis_scraper")
            
            user_info = self.get_user_info()
            logger.debug(f"user_info类型: {type(user_info)}, 内容: {str(user_info)[:200]}")
            
            term_info = self.get_current_term()
            logger.debug(f"term_info类型: {type(term_info)}, 内容: {str(term_info)[:200]}")
            
            current_week = self.get_current_week()
            logger.debug(f"current_week类型: {type(current_week)}, 值: {current_week}")
            
            target_week = week_override or os.environ.get("TIS_WEEK", "").strip() or current_week
            logger.debug(f"target_week: {target_week}")

            if not target_week.isdigit():
                raise RuntimeError(f"无效的周次参数: {target_week}")

            period_map = self.get_period_map(term_info, user_info)
            logger.debug(f"period_map类型: {type(period_map)}, 长度: {len(period_map)}")
            
            raw_courses = self.get_week_courses(term_info, target_week)
            logger.debug(f"raw_courses类型: {type(raw_courses)}, 长度: {len(raw_courses) if isinstance(raw_courses, list) else 'N/A'}")
            if isinstance(raw_courses, list) and raw_courses:
                logger.debug(f"第一个元素类型: {type(raw_courses[0])}, 内容: {str(raw_courses[0])[:100]}")

            parsed_courses = []
            for raw in raw_courses:
                if isinstance(raw, dict):
                    course = parse_course_entry(raw, period_map)
                    if course.get("day"):
                        parsed_courses.append(course)
                else:
                    logger.warning(f"跳过非字典类型的课程数据: {type(raw)} - {str(raw)[:100]}")

            grouped = defaultdict(list)
            for course in parsed_courses:
                grouped[course["day"]].append(course)

            user_name = user_info.get("xm") or user_info.get("xm_en") or "Unknown User"
            department = user_info.get("bmmc") or user_info.get("bmmc_en") or "Unknown Department"
            term_name = term_info.get("XNXQ") or str(term_info)

            result_dict = {
                "success": True,
                "user": user_name,
                "department": department,
                "term": term_name,
                "week": target_week,
                "total_courses": len(parsed_courses),
                "schedule": {}
            }

            for day in range(1, 8):
                day_courses = grouped.get(day)
                if not day_courses:
                    continue
                label_en, label_cn = WEEKDAY_LABELS.get(day, (f"Day {day}", f"第{day}天"))
                day_courses.sort(key=lambda item: (item.get("start") or "", item.get("periods") or ""))

                day_schedule = []
                for course in day_courses:
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

            self._write_result(result_dict, user_info, term_info, raw_courses)

            return result_dict

        except Exception as e:
            return {
                "success": False,
                "message": f"爬取课程信息时发生错误: {str(e)}",
                "user": "",
                "department": "",
                "term": "",
                "week": "",
                "total_courses": 0,
                "schedule": {}
            }
