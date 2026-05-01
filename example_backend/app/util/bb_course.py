# list_bb_courses_from_module.py
# pip install requests beautifulsoup4
import os, re, json, requests, urllib.parse as up
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, List
from .get_cookies import get_cookies_for_user
from .bb_calendar import load_cookies_from_file
from core.config import BB_PORTAL_AJAX, BB_PARAMS, COURSE_OUT_JSON

PORTAL_AJAX = BB_PORTAL_AJAX
PARAMS = BB_PARAMS
OUT_JSON = COURSE_OUT_JSON

def extract_course_id(url: str) -> str | None:
    u = up.unquote(url)
    m = re.search(r"[?&]course_id=(_\d+_\d+)", u)                 # 经典
    if m: return m.group(1)
    m = re.search(r"[?&]id=(_\d+_\d+)", u)                        # launcher?id=...
    if m: return m.group(1)
    m = re.search(r"/ultra/(?:course|courses)/(_\d+_\d+)", u)     # Ultra
    if m: return m.group(1)
    return None

def get_bb_courses(sid: str = None, password: str = None, cookies_file: str = "util/data/cookies.json", term_filter: str = None) -> List[Dict[str, str]]:
    """
    获取Blackboard课程列表
    
    Args:
        sid: 学号（如果提供，会先获取cookies）
        password: 密码（如果提供，会先获取cookies）
        cookies_file: cookies文件路径
        term_filter: 学期过滤条件（如"2025秋"）
        
    Returns:
        课程列表
    """
    cookies = {}
    
    # 如果提供了学号和密码，先获取cookies
    if sid and password:
        print("正在获取Blackboard cookies...")
        cookies_data = get_cookies_for_user(sid, password, cookies_file)
        if "error" in cookies_data:
            print(f"获取cookies失败: {cookies_data['error']}")
            return []
        
        # 提取Blackboard cookies
        bb_service = cookies_data.get("services", {}).get("bb", {})
        if bb_service.get("is_valid"):
            cookies = bb_service.get("cookies", {})
            print("使用新获取的Blackboard cookies")
        else:
            print("获取的Blackboard cookies无效")
            return []
    else:
        # 从文件读取cookies
        cookies = load_cookies_from_file(cookies_file)
        if not cookies:
            print("没有读取到Cookie。请提供学号和密码，或提供有效的cookies.json文件。")
            return []

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    })
    s.cookies.update(cookies)

    # 发起 AJAX：返回的是一个 XML，<contents> 节点里嵌着课程模块的 HTML
    print("正在获取我的课程")
    r = s.post(PORTAL_AJAX, data=PARAMS, timeout=20)
    r.raise_for_status()

    # 抠出 <contents> 的文本（保留其中的 HTML）
    # 兼容：有的部署直接返回 HTML，没有 XML 包裹
    text = r.text
    m = re.search(r"<contents[^>]*>([\s\S]*?)</contents>", text, re.I)
    html = m.group(1) if m else text
    
    # 处理CDATA包装
    if html.strip().startswith('<![CDATA[') and html.strip().endswith(']]>'):
        html = html.strip()[9:-3]  # 移除 <![CDATA[ 和 ]]>

    # 解析课程链接
    soup = BeautifulSoup(html, "html.parser")
    results: List[dict] = []
    
    for a in soup.find_all("a", href=True):
        title = (a.get_text() or "").strip()
        href  = up.urljoin("https://bb.sustech.edu.cn/", a["href"].strip())  # 移除href中的空格
        cid   = extract_course_id(href)
        
        if cid and title:
            results.append({"title": title, "course_id": cid, "url": href})

    # 去重
    seen = set()
    unique_results = []
    for course in results:
        if course["course_id"] not in seen:
            seen.add(course["course_id"])
            unique_results.append(course)

    # 按学期过滤（如果指定）
    if term_filter:
        filtered_courses = []
        for course in unique_results:
            title = course['title']
            # 支持多种格式的学期匹配
            if term_filter in title or (
                (term_filter == "2025秋" and ("Fall 2025" in title or "2025秋" in title)) or
                (term_filter == "Fall 2025" and ("Fall 2025" in title or "2025秋" in title))):
                filtered_courses.append(course)
        unique_results = filtered_courses

    return unique_results


# def save_courses_to_file(courses: List[Dict[str, str]], output_file: str = "data/courses.json") -> bool:
#     """
#     保存课程列表到文件
    
#     Args:
#         courses: 课程列表
#         output_file: 输出文件名
        
#     Returns:
#         是否保存成功
#     """
#     try:
#         Path(output_file).write_text(json.dumps(courses, ensure_ascii=False, indent=2), encoding="utf-8")
#         print(f"课程列表已保存到: {output_file}")
#         return True
#     except Exception as e:
#         print(f"保存课程列表失败: {e}")
#         return False


# def get_and_save_courses(sid: str = None, password: str = None, cookies_file: str = "data/cookies.json", term_filter: str = "2025秋", output_file: str = "data/courses.json") -> List[Dict[str, str]]:
#     """
#     获取并保存课程列表
    
#     Args:
#         sid: 学号（如果提供，会先获取cookies）
#         password: 密码（如果提供，会先获取cookies）
#         cookies_file: cookies文件路径
#         term_filter: 学期过滤条件
#         output_file: 输出文件名
        
#     Returns:
#         课程列表
#     """
#     courses = get_bb_courses(sid, password, cookies_file, term_filter)
    
#     if courses:
#         save_courses_to_file(courses, output_file)
#         print(f"获取到 {len(courses)} 门课程")
#         if term_filter:
#             print(f"{term_filter}课程列表:")
#             for course in courses:
#                 print(f"- {course['title']}")
    
#     return courses
