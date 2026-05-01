# backend/services/tis_scraper.py
# 从教务系统(TIS)爬取课程信息

import os
import re
import json
import logging
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Any
import requests

# ============ 日志配置 ============
logger = logging.getLogger("tis_scraper")
logger.setLevel(logging.INFO)

# 如果没有处理器，添加控制台处理器
if not logger.handlers:
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
# ============ 日志配置结束 ============

TIS_BASE_URL = "https://tis.sustech.edu.cn/"
TIS_API_BASE = "https://tis.sustech.edu.cn/"

# 输出文件路径
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'tis_result.txt')
TEST_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'test_tis_result.txt')

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


# 时间映射表
START_TIME_MAP = {
    1: "08:00",
    3: "10:20",
    5: "14:00",
    7: "16:20",
    9: "19:00",
}

END_TIME_MAP = {
    2: "09:50",
    4: "12:10",
    6: "15:50",
    8: "18:10",
    10: "20:50",
}


def calculate_time(periods: str) -> tuple:
    """
    从节次字符串中提取开始和结束时间
    periods格式示例: "7-8节"
    """
    start = None
    end = None
    
    # 提取节次范围
    match = re.search(r'(\d+)-(\d+)', periods)
    if match:
        try:
            a = int(match.group(1))
            b = int(match.group(2))
            
            # 根据起始节次获取开始时间
            if a in START_TIME_MAP:
                start = START_TIME_MAP[a]
            
            # 根据结束节次获取结束时间
            if b in END_TIME_MAP:
                end = END_TIME_MAP[b]
        except ValueError:
            pass
    
    return start, end


def get_weekday_from_key(key: str) -> int:
    """
    从key字段提取星期几（返回数字1-7）
    格式: "xq1_jc1" -> xq1表示星期1 -> 返回1
    """
    match = re.search(r'xq(\d+)', key)
    if match:
        try:
            day_num = int(match.group(1))
            if 1 <= day_num <= 7:
                return day_num
        except ValueError:
            pass
    return 0

def parse_course_entry(raw: Dict, period_map: Dict[int, Dict[str, Optional[str]]]) -> Dict[str, Optional[str]]:
    """解析单个课程条目（兼容新老两种数据格式）"""
    kbxx = raw.get("kbxx", "")
    key = raw.get("key", "") or raw.get("KEY", "")
    
    # 新格式：使用 kbxx 字段（参考 example_tis_scraper.py）
    if kbxx:
        lines = kbxx.strip().split('\n')
        if len(lines) >= 4:
            # 课程名称
            title = lines[0].strip()
            
            # 教师信息
            teacher_match = re.search(r'\[([^\]]+)\]', lines[1])
            teacher = teacher_match.group(1) if teacher_match else ""
            
            # 从第4行提取周次、地点、时间
            info_line = lines[3]
            weeks_match = re.search(r'\[([^\]]*周)\]', info_line)
            weeks = weeks_match.group(1) if weeks_match else ""
            
            # 提取地点（第二个方括号）
            location_match = re.search(r'\[([^\]]*)\]', info_line[info_line.find(']') + 1:] if ']' in info_line else info_line)
            location = location_match.group(1) if location_match else ""
            
            # 提取节次并计算时间
            time_match = re.search(r'\[([^\]]*节)\]', info_line)
            periods = time_match.group(1) if time_match else ""
            start, end = calculate_time(periods)
            
            # 从key字段获取星期几
            day = get_weekday_from_key(key)
            
            return {
                "day": day,
                "title": title,
                "teacher": teacher,
                "weeks": weeks,
                "location": location,
                "periods": periods,
                "start": start,
                "end": end,
            }
    
    # 旧格式：使用 SKSJ 字段
    day_match = re.match(r"xq(\d+)_jc", key)
    day = int(day_match.group(1)) if day_match else 0
    segments = re.findall(r"\[(.*?)\]", raw.get("SKSJ", ""))
    
    # 提取节次并计算时间
    periods_str = segments[4] if len(segments) > 4 else ""
    start, end = calculate_time(periods_str)
    
    return {
        "day": day,
        "title": (raw.get("SKSJ", "").split("\n") or [""])[0].strip(),
        "teacher": segments[0] if len(segments) > 0 else "",
        "weeks": segments[2] if len(segments) > 2 else "",
        "location": segments[3] if len(segments) > 3 else "",
        "periods": periods_str,
        "start": start,
        "end": end,
    }


class TisScraper:
    """TIS教务系统爬虫服务"""

    def __init__(self, session: requests.Session = None):
        if session:
            self.session = session
        else:
            self.session = requests.Session()
        
        # 参考 example_tis_scraper.py 的请求头配置（无论session是传入还是创建，都更新请求头）
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://tis.sustech.edu.cn/webroot/decision/",
            "Origin": "https://tis.sustech.edu.cn",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
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
        """获取指定周次的课程（使用 example_tis_scraper.py 的方式）"""
        
        try:
            # 使用正确的URL和表单格式（参考 example_tis_scraper.py）
            url = TIS_API_BASE + "Xskbcx/queryXskbcxList"
            data = {
                "bs": "2",
                "xn": term_info.get("XN"),
                "xq": term_info.get("XQ"),
            }
            
            logger.debug(f"课表接口URL: {url}")
            logger.debug(f"课表接口参数: {data}")
            logger.debug(f"课表接口请求头: {dict(self.session.headers)}")
            logger.debug(f"课表接口Cookie: {dict(self.session.cookies)}")
            
            # 使用表单格式发送请求
            resp = self.session.post(url, data=data, timeout=30)
            logger.debug(f"课表接口响应状态码: {resp.status_code}")
            logger.debug(f"课表接口响应头: {dict(resp.headers)}")
            
            resp.raise_for_status()
            
            raw_courses = resp.json()
            
            logger.debug(f"get_week_courses返回类型: {type(raw_courses)}")
            logger.debug(f"get_week_courses返回内容: {str(raw_courses)[:500]}")
            
            if isinstance(raw_courses, list):
                return raw_courses
            elif isinstance(raw_courses, dict):
                # 可能是错误响应，尝试提取错误信息
                error_msg = raw_courses.get('msg')
                if error_msg is None:
                    error_msg = raw_courses.get('message')
                if error_msg is None:
                    error_msg = "未知错误"
                # 如果错误信息是null/None，提供更友好的提示
                if error_msg in (None, 'null', 'None'):
                    error_msg = "接口未返回具体错误信息，可能是权限问题或服务器异常"
                
                logger.warning(f"课表接口返回错误: {error_msg}")
                logger.debug(f"课表接口完整响应: {str(raw_courses)}")
                return []
            else:
                logger.warning(f"课表接口返回数据格式异常，类型: {type(raw_courses)}")
                logger.debug(f"课表接口返回内容: {str(raw_courses)[:500]}")
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
            user_info = self.get_user_info()
            logger.debug(f"user_info类型: {type(user_info)}, 内容: {str(user_info)[:200]}")
            
            term_info = self.get_current_term()
            logger.debug(f"term_info类型: {type(term_info)}, 内容: {str(term_info)[:200]}")
            
            # ============ 课程爬取逻辑 ============
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
            # ============ 课程爬取逻辑 ============

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

            # ============ 构建日程表 ============
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
                        "weeks": course.get("weeks", ""),
                        "location": course.get("location", ""),
                        "periods": course.get("periods", ""),
                        "start": course.get("start", ""),
                        "end": course.get("end", ""),
                    }
                    day_schedule.append(course_detail)

                result_dict["schedule"][label_cn] = day_schedule

            # ============ 输出结果 ============
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

    def test_fetch_url(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        测试爬取指定URL的信息
        
        Args:
            url: 要爬取的完整URL
            method: 请求方法，默认为GET
            data: POST请求的数据，可选
        
        Returns:
            包含响应状态码、响应头和响应内容的字典
        """
        try:
            from datetime import datetime
            
            logger.info(f"开始测试爬取URL: {url}")
            logger.info(f"请求方法: {method}")
            if data:
                logger.info(f"请求数据: {str(data)[:200]}")
            
            if method.upper() == "POST":
                resp = self.session.post(url, json=data, timeout=30)
            else:
                resp = self.session.get(url, timeout=30)
            
            logger.info(f"响应状态码: {resp.status_code}")
            logger.info(f"响应头: {dict(resp.headers)}")
            
            try:
                content = resp.json()
                logger.info(f"响应JSON内容长度: {len(str(content))}")
                logger.info(f"响应JSON预览: {str(content)[:500]}")
            except Exception:
                content = resp.text[:2000]
                logger.info(f"响应文本内容长度: {len(content)}")
                logger.info(f"响应文本预览: {content[:500]}")
            
            # ============ 将结果输出到 test_tis_result.txt ============
            try:
                result_dict = {
                    "timestamp": datetime.now().isoformat(),
                    "url": url,
                    "method": method,
                    "request_data": data,
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "content": content
                }
                
                with open(TEST_OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(result_dict, f, ensure_ascii=False, indent=2)
                
                logger.info(f"测试结果已保存到: {TEST_OUTPUT_FILE}")
            except Exception as e:
                logger.error(f"保存测试结果失败: {str(e)}")
            # ============ 输出完成 ============
            
            return {
                "success": True,
                "url": url,
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "content": content
            }
        
        except Exception as e:
            logger.error(f"爬取URL失败: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
