import os
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from pathlib import Path
from typing import Dict, List

from .bb_course import get_bb_courses
from .bb_calendar import load_cookies_from_file

COURSES_JSON = "data/courses.json"
OUTDIR = "downloads"
EXTS = {
    ".pdf", ".ppt", ".pptx", ".doc", ".docx", ".zip", ".rar", ".7z",
    ".png", ".jpg", ".mp4", ".txt", ".xlsx", ".xls"
}


def safe_name(name: str) -> str:
    """将文件名中的非法字符替换为安全字符"""
    safe = re.sub(r'[<>:"/\\|?*]', "_", name)
    safe = re.sub(r"\s+", " ", safe).strip()
    safe = safe.strip(".")
    return safe or "unnamed"


def cookie_session(cookies: Dict[str, str]) -> requests.Session:
    """创建带有cookies的会话"""
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    })
    return session


def is_file_link(href: str) -> bool:
    """判断链接是否指向文件"""
    if not href:
        return False
    parsed = urlparse(href)
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in EXTS):
        return True
    query = parsed.query.lower()
    if any(param in query for param in ["download", "attachment", "file"]):
        return True
    if "bbcswebdav" in href.lower():
        return True
    return False


def fetch_all_links(session: requests.Session, url: str) -> List[Dict[str, str]]:
    """
    获取页面中的所有文件链接及其显示文本

    返回结构类似：
    [
        {"url": "https://...", "text": "Lecture 1 PPT"},
        ...
    ]
    """
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        links: List[Dict[str, str]] = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(r.url, href)
            if is_file_link(full_url):
                text = (a.get_text() or "").strip()
                links.append({"url": full_url, "text": text})

        # 按 url 去重
        unique: Dict[str, Dict[str, str]] = {}
        for item in links:
            unique[item["url"]] = item  # 后出现的覆盖前面的，同一个URL一般无所谓
        return list(unique.values())
    except Exception as e:
        print(f"获取文件链接失败: {e}")
        return []


def get_course_content_urls(session: requests.Session, course_url: str) -> List[Dict[str, str]]:
    """获取课程页面中的所有内容页面URL和名称"""
    try:
        r = session.get(course_url, timeout=20, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        content_items: List[Dict[str, str]] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = (a.get_text() or "").strip()
            if any(pattern in href.lower() for pattern in ["listcontent", "content", "coursecontent"]):
                full_url = urljoin(r.url, href)
                if not any(item["url"] == full_url for item in content_items):
                    content_items.append({"url": full_url, "name": text or "课程内容"})

        seen = set()
        unique_items: List[Dict[str, str]] = []
        for item in content_items:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique_items.append(item)
        return unique_items
    except Exception as e:
        print(f"获取课程内容页面失败: {e}")
        return []


def guess_filename(
    session: requests.Session,
    url: str,
    idx: int = 0,
    link_text: str = ""
) -> str:
    """
    猜测文件名的优先级：
    1. 尝试从响应头 Content-Disposition 中获取 filename
    2. 使用链接文本 link_text（必要时补扩展名）
    3. 回退到 URL 路径中的 basename（例如 xid-xxx_1）
    """

    # 1) 尝试 HEAD / GET 获取 Content-Disposition
    for method in ("head", "get"):
        try:
            resp = getattr(session, method)(
                url, timeout=10, allow_redirects=True, stream=True
            )
            cd = resp.headers.get("Content-Disposition", "")
            resp.close()
            if "filename=" in cd:
                # 简单抽取 filename= 后面的部分
                # 如果有 filename*= 这种更复杂情况，可以再扩展解析逻辑
                part = cd.split("filename=", 1)[1].strip()
                # 去掉首尾引号和分号等
                part = part.strip('"; ')
                return safe_name(unquote(part))
        except Exception:
            continue

    # 2) 使用链接文字作为文件名
    if link_text:
        name = safe_name(link_text)
        parsed = urlparse(url)
        ext = os.path.splitext(parsed.path)[1].lower()
        if ext and not name.lower().endswith(ext):
            name = f"{name}{ext}"
        return name

    # 3) 最后回退到 URL 路径
    parsed = urlparse(url)
    name = os.path.basename(parsed.path) or f"file_{idx}"
    return safe_name(unquote(name))


def collect_files_from_url(
    session: requests.Session,
    url: str,
    course_name: str,
    content_name: str = ""
) -> List[Dict]:
    """
    从某个内容页面收集所有文件链接，返回结构：
    [
      {
        "course": ...,
        "content": ...,
        "file_url": ...,
        "file_name": ...,
      },
      ...
    ]
    """
    links = fetch_all_links(session, url)
    results: List[Dict] = []
    for i, item in enumerate(links, 1):
        file_url = item["url"]
        link_text = item.get("text", "")
        results.append({
            "course": course_name,
            "content": content_name,
            "file_url": file_url,
            "file_name": guess_filename(session, file_url, i, link_text),
        })
    return results


def download_all_courses(
    sid: str = None,
    password: str = None,
    cookies_file: str = "util/data/cookies.json",
    term_filter: str = "2025秋"
) -> str:
    """
    收集所有课程下的文件链接，返回 JSON 字符串。
    JSON 结构：
    [
      {"course":..., "content":..., "file_url":..., "file_name":...},
      ...
    ]
    """
    courses = get_bb_courses(sid, password, cookies_file, term_filter)
    if not courses:
        return "[]"

    cookies = load_cookies_from_file(cookies_file)
    if not cookies:
        print("未读到 Cookie")
        return "[]"

    session = cookie_session(cookies)
    all_files: List[Dict] = []

    for i, course in enumerate(courses, 1):
        course_name = course["title"]
        course_url = course["url"]

        print(f"\n[{i}/{len(courses)}] 处理课程: {course_name}")
        content_items = get_course_content_urls(session, course_url)
        if not content_items:
            print("  未找到内容页面")
            continue

        for j, content_item in enumerate(content_items, 1):
            content_name = content_item["name"]
            content_url = content_item["url"]
            print(f"  [{j}/{len(content_items)}] 处理: {content_name}")
            files = collect_files_from_url(session, content_url, course_name, content_name)
            all_files.extend(files)
            time.sleep(1)

        time.sleep(2)

    print(f"\n共收集 {len(all_files)} 条文件链接")
    return json.dumps(all_files, ensure_ascii=False, indent=2)



# python -c "from util.bb_download import download_all_courses; print(download_all_courses()); "