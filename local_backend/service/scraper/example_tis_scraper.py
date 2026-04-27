# grab_tis_json_v2.py
# pip install requests
import json, requests, os, re
from pathlib import Path
from typing import Dict, List
from .get_cookies import get_cookies_for_user

URL = "https://tis.sustech.edu.cn/Xskbcx/queryXskbcxList"  # DevTools 的 Request URL
FORM = {  # DevTools → Payload 的表单键值（若原请求是 GET，就把 main 里改成 s.get(..., params=FORM)）
    "bs": "2",
    "xn": "2025-2026",
    "xq": "1",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://tis.sustech.edu.cn/webroot/decision/",
}
# ========================

def _raw_cookie_to_dict(raw: str) -> Dict[str, str]:
    
    jar = {}
    for seg in raw.split(";"):
        if "=" not in seg:
            continue
        k, v = seg.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k:
            jar[k] = v
    return jar

def load_tis_cookies(path: str = "util/data/cookies.json") -> Dict[str, str]:
   
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        # 不是 JSON，就当成原始 Cookie 行
        return _raw_cookie_to_dict(p.read_text(encoding="utf-8"))
    # 1) services.tis.cookies
    cookies = (
        data.get("services", {}).get("tis", {}).get("cookies")
        if isinstance(data, dict) else None
    )
    if isinstance(cookies, dict) and cookies:
        return cookies
    # 2) 顶层就是字典 cookie
    if isinstance(data, dict) and any("=" not in k for k in data.keys()):
        # 粗判：键里没有等号，就把它当 cookie dict
        return data
    # 3) services.tis.raw 或 顶层 raw
    raw = data.get("services", {}).get("tis", {}).get("raw") if isinstance(data, dict) else None
    if not raw:
        raw = data.get("raw") if isinstance(data, dict) else None
    if isinstance(raw, str) and raw.strip():
        return _raw_cookie_to_dict(raw)
    return {}



def parse_kbxx(kbxx: str) -> Dict[str, str]:

    if not kbxx:
        return {}
    
    lines = kbxx.strip().split('\n')
    if len(lines) < 4:
        return {}
    
    course_name = lines[0].strip()
    

    teacher_match = re.search(r'\[([^\]]+)\]', lines[1])
    teacher = teacher_match.group(1) if teacher_match else ""
    
    # 提取周次、地点、时间 [1-5,7-16周][商学院206][1-2节]
    info_line = lines[3]
    weeks_match = re.search(r'\[([^\]]*周)\]', info_line)
    location_match = re.search(r'\[([^\]]*)\]', info_line[info_line.find(']') + 1:])
    time_match = re.search(r'\[([^\]]*节)\]', info_line)
    
    weeks = weeks_match.group(1) if weeks_match else ""
    location = location_match.group(1) if location_match else ""
    time_slots = time_match.group(1) if time_match else ""
    
    # 确定星期几
    weekday_map = {
        "1": "星期一", "2": "星期二", "3": "星期三", 
        "4": "星期四", "5": "星期五", "6": "星期六", "7": "星期日"
    }
    weekday = weekday_map.get("1", "星期一")  # 默认星期一，实际应该从key字段获取
    
    return {
        "course_name": course_name,
        "teacher": teacher,
        "weekday": weekday,
        "weeks": weeks,
        "location": location,
        "time_slots": time_slots
    }

def get_weekday_from_key(key: str) -> str:
    """
    从key字段提取星期几
    格式: "xq1_jc1" -> xq1表示星期1
    """
    weekday_map = {
        "1": "星期一", "2": "星期二", "3": "星期三", 
        "4": "星期四", "5": "星期五", "6": "星期六", "7": "星期日"
    }
    
    match = re.search(r'xq(\d+)', key)
    if match:
        day_num = match.group(1)
        return weekday_map.get(day_num, "星期一")
    return "星期一"

def process_schedule_data(raw_data: List[Dict]) -> List[Dict]:
    """
    处理原始课程数据，生成格式化的课程信息
    """
    processed_courses = []
    
    for item in raw_data:
        kbxx = item.get("kbxx", "")
        key = item.get("key", "")
        
        if not kbxx:
            continue
            
        course_info = parse_kbxx(kbxx)
        if not course_info:
            continue
            
        # 从key字段获取正确的星期几
        course_info["weekday"] = get_weekday_from_key(key)
        
        processed_courses.append(course_info)
    
    return processed_courses

def generate_processed_json(input_file: str = "tis_schedule_raw.json", output_file: str = "tis_schedule_processed.json"):
    """
    生成处理过的课程JSON文件
    """
    input_path = Path(input_file)
    if not input_path.exists():
        print(f" 输入文件不存在: {input_path}")
        return
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        processed_courses = process_schedule_data(raw_data)
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_courses, f, ensure_ascii=False, indent=2)
        
        print(f"已生成处理后的课程数据: {output_path.resolve()}")
        print(f"共处理 {len(processed_courses)} 门课程")
        
    except Exception as e:
        print(f" 处理失败: {e}")

def fetch_tis_schedule_data(sid: str = None, password: str = None, cookies_file: str = "util/data/cookies.json", prefer_env: bool = True) -> Dict:
    """
    从TIS获取课表数据
    
    Args:
        sid: 学号（如果提供，会先获取cookies）
        password: 密码（如果提供，会先获取cookies）
        cookies_file: cookies文件路径
        prefer_env: 是否优先使用环境变量
        
    Returns:
        原始课表数据
    """
    cookies = {}
    
    # 如果提供了学号和密码，先获取cookies
    if sid and password:
        print("正在获取TIS cookies...")
        cookies_data = get_cookies_for_user(sid, password, cookies_file)
        if "error" in cookies_data:
            print(f"获取cookies失败: {cookies_data['error']}")
            return {}
        
        # 提取TIS cookies
        tis_service = cookies_data.get("services", {}).get("tis", {})
        if tis_service.get("is_valid"):
            cookies = tis_service.get("cookies", {})
            print("使用新获取的TIS cookies")
        else:
            print("获取的TIS cookies无效")
            return {}
    else:
        # 从文件读取cookies
        cookies = load_tis_cookies()
        if not cookies:
            print("没有读取到 Cookie。请提供学号和密码，或在环境变量 TIS_COOKIE 设置原始 Cookie 行，或提供 cookies.json。")
            return {}

    s = requests.Session()
    s.headers.update(HEADERS)
    s.cookies.update(cookies)

    # 发送请求
    print("正在获取课表数据...")
    r = s.post(URL, data=FORM, timeout=20)
    r.raise_for_status()

    ctype = (r.headers.get("Content-Type") or "").lower()
    if "json" not in ctype:
        print("返回非 JSON：", ctype)
        print(r.text[:500])
        return {}

    data = r.json()
    print("成功获取课表数据")
    return data


def save_raw_schedule_data(data: Dict, output_file: str = "tis_schedule_raw.json") -> bool:
    """
    保存原始课表数据
    
    Args:
        data: 原始数据
        output_file: 输出文件名
        
    Returns:
        是否保存成功
    """
    try:
        out = Path(output_file)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已保存原始数据：{out.resolve()}")
        return True
    except Exception as e:
        print(f"保存原始数据失败：{e}")
        return False


def fetch_and_process_schedule(sid: str = None, password: str = None,
                              cookies_file: str = "util/data/cookies.json", 
                              raw_output: str = "data/tis_schedule_raw.json",
                              processed_output: str = "data/tis_schedule_processed.json") -> List[Dict]:
    """
    获取并处理课表数据
    
    Args:
        sid: 学号（如果提供，会先获取cookies）
        password: 密码（如果提供，会先获取cookies）
        cookies_file: cookies文件路径
        raw_output: 原始数据输出文件名
        processed_output: 处理后数据输出文件名
        
    Returns:
        处理后的课表数据
    """
    # 1. 获取原始数据
    raw_data = fetch_tis_schedule_data(sid, password, cookies_file)
    if not raw_data:
        return []
    
    # # 2. 保存原始数据
    # save_raw_schedule_data(raw_data, raw_output)
    
    # 3. 处理数据
    processed_courses = process_schedule_data(raw_data)
    
    # # 4. 保存处理后的数据
    # try:
    #     output_path = Path(processed_output)
    #     with open(output_path, 'w', encoding='utf-8') as f:
    #         json.dump(processed_courses, f, ensure_ascii=False, indent=2)
    #     print(f"已生成处理后的课程数据: {output_path.resolve()}")
    #     print(f"共处理 {len(processed_courses)} 门课程")
    # except Exception as e:
    #     print(f"保存处理后数据失败: {e}")
    
    return processed_courses
