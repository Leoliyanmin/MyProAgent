# backend/services/blackboard_scraper.py
# 从Blackboard爬取课程信息，集成到后端逻辑中

import json
import re
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning
from urllib.parse import urljoin, unquote

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

BB_BASE_URL = "https://bb.sustech.edu.cn"
COURSE_TAB_URL = "https://bb.sustech.edu.cn/webapps/portal/execute/tabs/tabAction"
AJAX_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
}

BB_PARAMS = {
    "action": "refreshAjaxModule",
    "modId": "_3_1",
    "tabId": "_1_1",
    "tab_tab_group_id": "_1_1"
}

_SCRAPER_OUTPUT_DIR = Path.home() / ".proagent" / "scraper_output"
_SCRAPER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = _SCRAPER_OUTPUT_DIR / "bb_result.txt"
TEST_OUTPUT_FILE = Path(__file__).parent / "test_result.txt"


def _convert_chinese_date(chinese_date: str) -> str:
    MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    match = re.search(
        r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*(上午|下午)?(\d{1,2}):(\d{2})?",
        chinese_date
    )
    if not match:
        match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", chinese_date)
        if match:
            year, month, day = match.groups()
            return f"{MONTH_NAMES[int(month)]} {int(day)}, {year}"
        return chinese_date

    year, month, day, ampm, hour, minute = match.groups()
    month_name = MONTH_NAMES[int(month)]
    ampm_english = ampm.replace("上午", "AM").replace("下午", "PM") if ampm else ""
    return f"{month_name} {int(day)}, {year} {hour}:{minute} {ampm_english}".strip()


def _extract_due_date_from_html(html: str) -> Optional[str]:
    """从作业页面 HTML 中提取 Due Date"""
    soup = BeautifulSoup(html, "html.parser")

    due_label = soup.find("div", class_="metaLabel", id="assignMeta2")
    if due_label:
        field = due_label.find_next_sibling("div", class_="metaField")
        if field:
            text = field.get_text(" ", strip=True)
            due_match = re.search(
                r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                r"[a-z]*\s+\d{1,2},?\s+20\d{2}.*)",
                text, re.I
            )
            if due_match:
                return due_match.group(1).strip()

    for h3 in soup.find_all("h3"):
        if "到期日期" in h3.get_text(strip=True):
            p = h3.find_next_sibling("p")
            if p:
                chinese_text = p.get_text(" ", strip=True)
                return _convert_chinese_date(chinese_text)

def extract_course_id(url: str) -> str | None:
    """从URL中提取课程ID"""
    u = unquote(url)
    m = re.search(r"[?&]course_id=(_\d+_\d+)", u)
    if m:
        return m.group(1)
    m = re.search(r"[?&]id=(_\d+_\d+)", u)
    if m:
        return m.group(1)
    m = re.search(r"/ultra/(?:course|courses)/(_\d+_\d+)", u)
    if m:
        return m.group(1)
    return None


def _extract_links(element: "BeautifulSoup", base_url: str) -> List[Dict[str, str]]:
    """从HTML元素中提取所有链接"""
    links: List[Dict[str, str]] = []
    for anchor in element.find_all("a"):
        href = (anchor.get("href") or "").strip()
        if not href:
            continue
        abs_href = urljoin(base_url, href)
        text = anchor.get_text(" ", strip=True) or abs_href
        links.append({"text": text, "href": abs_href})
    return links


def _parse_paragraph(element: "BeautifulSoup", base_url: str) -> Dict[str, Any]:
    """解析段落"""
    text = element.get_text(" ", strip=True)
    links = _extract_links(element, base_url)
    block: Dict[str, Any] = {"type": "paragraph"}
    if text:
        block["text"] = text
    if links:
        block["links"] = links
    return block


def _parse_content_blocks(html: str, base_url: str) -> List[Dict[str, Any]]:
    """解析内容块"""
    soup = BeautifulSoup(f"<bb-root>{html}</bb-root>", "html.parser")
    root = soup.find("bb-root")
    if not root:
        return []
    blocks: List[Dict[str, Any]] = []
    for child in root.children:
        if isinstance(child, NavigableString):
            text = child.strip()
            if text:
                blocks.append({"type": "text", "text": text})
            continue
        if not getattr(child, "name", None):
            continue
        name = child.name.lower()
        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            blocks.append({
                "type": "heading",
                "level": int(name[1]),
                "text": child.get_text(" ", strip=True),
            })
            continue
        if name == "p" or (name == "div" and child.get_text(strip=True)):
            paragraph = _parse_paragraph(child, base_url)
            if paragraph.get("text") or paragraph.get("links"):
                blocks.append(paragraph)
            continue
        text = child.get_text(" ", strip=True)
        links = _extract_links(child, base_url)
        block: Dict[str, Any] = {"type": "text"}
        if text:
            block["text"] = text
        if links:
            block["links"] = links
        if block.get("text") or block.get("links"):
            blocks.append(block)
    return blocks


def _parse_content_panel_sections(panel: "BeautifulSoup", base_url: str) -> List[Dict[str, Any]]:
    """解析内容面板章节"""
    container = panel.select_one("#content_listContainer")
    search_root = container if container else panel
    item_candidates = search_root.select("div.item")
    if not item_candidates:
        item_candidates = search_root.select("li.contentListItem, li.clearfix")

    sections: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()

    for item in item_candidates:
        if container and not item.find_parent(id="content_listContainer"):
            continue
        parent_li = item if item.name == "li" else item.find_parent("li")
        source_node = parent_li if parent_li else item

        title_node = source_node.select_one(".itemTitle") or source_node.find(
            ["h1", "h2", "h3", "h4", "h5", "h6"]
        )
        if not title_node:
            link_title = item.find("a", recursive=False)
            title_node = link_title
        if not title_node:
            continue

        parent_with_id = title_node.find_parent(attrs={"id": True}) or (
            parent_li if parent_li and parent_li.get("id") else None
        )
        identifier = None
        if parent_with_id and parent_with_id.get("id"):
            identifier = parent_with_id["id"]
        elif source_node.get("id"):
            identifier = source_node["id"]

        if identifier:
            if identifier in seen_ids:
                continue
            seen_ids.add(identifier)

        item_soup = BeautifulSoup(
            f"<bb-item>{source_node.decode_contents()}</bb-item>", "html.parser"
        )
        wrapper = item_soup.find("bb-item")
        if not wrapper:
            continue

        title_wrapper = wrapper.select_one(".itemTitle") or wrapper.find(
            ["h1", "h2", "h3", "h4", "h5", "h6"]
        )
        title = ""
        if title_wrapper:
            title = title_wrapper.get_text(" ", strip=True)
            title_wrapper.extract()
        elif title_node:
            title = title_node.get_text(" ", strip=True)

        for menu in wrapper.select(".contextMenuContainer, .actionBarMicro"):
            menu.decompose()

        body_html = wrapper.decode_contents().strip()
        blocks = _parse_content_blocks(body_html, base_url) if body_html else []

        if not title and not blocks:
            continue

        sections.append({"title": title, "blocks": blocks})

    return sections


def _parse_course_links(html: str, term_filter: str = None) -> List[Dict[str, Any]]:
    """从门户页面解析课程链接和公告"""
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, Any]] = []
    seen: set[str] = set()

    text = html
    m = re.search(r"<contents[^>]*>([\s\S]*?)</contents>", text, re.I)
    if m:
        html = m.group(1)
        soup = BeautifulSoup(html, "html.parser")

    if html.strip().startswith('<![CDATA[') and html.strip().endswith(']]>'):
        html = html.strip()[9:-3]
        soup = BeautifulSoup(html, "html.parser")

    for li in soup.find_all("li"):
        anchor = li.find("a", href=True)
        if not anchor:
            continue
            
        title = (anchor.get_text() or "").strip()
        if not title:
            continue

        raw_href = anchor["href"].strip()
        if not raw_href:
            continue

        full_href = urljoin(BB_BASE_URL, raw_href)
        course_id = extract_course_id(full_href)

        if course_id and title:
            if course_id not in seen:
                seen.add(course_id)
                
                announcements = []
                course_data_block = li.find("div", class_="courseDataBlock")
                if course_data_block:
                    announcement_links = course_data_block.find_all("a", href=True)
                    for ann_link in announcement_links:
                        ann_title = ann_link.get_text(strip=True)
                        ann_href = urljoin(BB_BASE_URL, ann_link["href"].strip())
                        if ann_title and "announcement" in ann_href.lower():
                            announcements.append({
                                "title": ann_title,
                                "url": ann_href
                            })
                
                results.append({
                    "title": title,
                    "course_id": course_id,
                    "url": full_href,
                    "announcements": announcements
                })

    if term_filter:
        filtered_courses = []
        for course in results:
            course_title = course['title']
            if term_filter in course_title or (
                (term_filter == "2025秋" and ("Fall 2025" in course_title or "2025秋" in course_title)) or
                (term_filter == "Fall 2025" and ("Fall 2025" in course_title or "2025秋" in course_title))):
                filtered_courses.append(course)
        results = filtered_courses

    return results


def _parse_menu_links(course_html: str, course_url: str) -> List[Dict[str, Any]]:
    """从课程页面解析菜单链接"""
    soup = BeautifulSoup(course_html, "html.parser")
    menu_wrap = soup.find(id="menuWrap")
    if not menu_wrap:
        return []

    links: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    for li in menu_wrap.find_all("li"):
        is_header = False
        if "subhead" in li.get("class", []):
            is_header = True
        elif not li.find("a") and li.get_text(strip=True):
            is_header = True

        if is_header:
            header_text = li.get_text(strip=True)
            if header_text:
                links.append({
                    "label": header_text,
                    "url": None,
                    "is_header": True
                })
            continue

        anchor = li.find("a")
        if not anchor:
            continue

        raw_label = anchor.get_text()
        if raw_label is None:
            continue
        raw_label = raw_label.strip()
        if not raw_label:
            continue

        href = (anchor.get("href") or "").strip()
        has_url = bool(href) and href != "#"
        abs_url = urljoin(course_url, href) if has_url else None

        if abs_url and abs_url in seen_urls:
            continue

        links.append({
            "label": raw_label,
            "url": abs_url,
            "is_header": False
        })
        if abs_url:
            seen_urls.add(abs_url)

    return links


def _extract_announcements(html: str) -> List[Dict[str, str]]:
    """从公告页面提取公告信息"""
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find(id="announcementList")
    if not container:
        return []

    announcements: List[Dict[str, str]] = []

    for item in container.find_all("li", recursive=False):
        title_node = item.find("h3")
        title = title_node.get_text(strip=True) if title_node else ""

        details_block = item.find("div", class_="details")
        posted_on = ""
        body_text = ""
        if details_block:
            posted_span = details_block.find("span")
            if posted_span:
                posted_on = posted_span.get_text(strip=True)
            content_div = details_block.find("div", class_="vtbegenerated")
            if content_div:
                body_text = content_div.get_text("\n", strip=True)
            else:
                body_text = details_block.get_text("\n", strip=True)

        info_block = item.find("div", class_="announcementInfo")
        posted_by = ""
        posted_to = ""
        if info_block:
            for paragraph in info_block.find_all("p"):
                text = paragraph.get_text(strip=True)
                if text.startswith("Posted by:") or text.startswith("发帖者:"):
                    posted_by = text.split(":", 1)[1].strip()
                elif text.startswith("Posted to:") or text.startswith("发布至:"):
                    posted_to = text.split(":", 1)[1].strip()

        announcements.append({
            "id": item.get("id", ""),
            "title": title,
            "posted_on": posted_on,
            "posted_by": posted_by,
            "posted_to": posted_to,
            "body_text": body_text,
        })

    return announcements


class BlackboardScraper:
    """Blackboard爬虫服务，用于爬取课程和作业信息"""

    def __init__(self, session: requests.Session = None):
        if session:
            self.session = session
        else:
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            })

    def set_cookies(self, cookies: Dict[str, str]):
        """设置会话Cookie"""
        self.session.cookies.clear()
        self.session.cookies.update(cookies)

    def _extract_menu_content(self, html: str, base_url: str) -> Dict[str, Any]:
        """提取菜单页面内容"""
        soup = BeautifulSoup(html, "html.parser")
        candidates = [
            soup.find(id="contentPanel"),
            soup.find(id="courseToc"),
            soup.find("div", class_="contentPane"),
            soup.find("div", class_="path"),
        ]
        for candidate in candidates:
            if candidate:
                blocks = _parse_content_blocks(candidate.decode_contents(), base_url)
                payload: Dict[str, Any] = {}
                if blocks:
                    payload["content_blocks"] = blocks
                sections = _parse_content_panel_sections(candidate, base_url)
                if sections:
                    payload["content_section_blocks"] = sections
                else:
                    text = candidate.get_text(" ", strip=True)
                    if text:
                        payload["content_text"] = text
                return payload

        body = soup.find("body")
        if body:
            blocks = _parse_content_blocks(body.decode_contents(), base_url)
            payload: Dict[str, Any] = {}
            if blocks:
                payload["content_blocks"] = blocks
            sections = _parse_content_panel_sections(body, base_url)
            if sections:
                payload["content_section_blocks"] = sections
            else:
                text = body.get_text(" ", strip=True)
                if text:
                    payload["content_text"] = text
            return payload

        text = soup.get_text(" ", strip=True)
        return {"content_text": text} if text else {}

    def _fetch_tab_payload(self) -> str:
        """获取课程门户页面内容"""
        resp = self.session.post(
            COURSE_TAB_URL,
            data=BB_PARAMS,
            headers=AJAX_HEADERS,
            timeout=20,
            allow_redirects=True,
        )
        resp.raise_for_status()

        text = resp.text
        m = re.search(r"<contents[^>]*>([\s\S]*?)</contents>", text, re.I)
        html = m.group(1) if m else text

        if html.strip().startswith('<![CDATA[') and html.strip().endswith(']]>'):
            html = html.strip()[9:-3]

        return html

    def _fetch_course_menu(self, course_url: str) -> tuple[str, List[Dict[str, Any]]]:
        """获取课程页面和菜单链接"""
        resp = self.session.get(course_url, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
        links = _parse_menu_links(html, course_url)
        return html, links

    def _fetch_announcements(self, announcement_url: str) -> List[Dict[str, str]]:
        """获取公告信息"""
        resp = self.session.get(announcement_url, allow_redirects=True)
        resp.raise_for_status()
        return _extract_announcements(resp.text)

    def _fetch_assignment_due_date(self, assignment_url: str, referer: str = "", label: str = "") -> str:
        """获取作业截止日期"""
        try:
            headers = {}
            if referer:
                headers["Referer"] = referer
            resp = self.session.get(assignment_url, headers=headers, allow_redirects=True)
            resp.raise_for_status()
            html = resp.text

            result = _extract_due_date_from_html(html)
            if result:
                return result

            try:
                with open(TEST_OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"未提取到 Due Date 的作业页面\n")
                    f.write(f"作业: {label}\n")
                    f.write(f"URL: {assignment_url}\n")
                    f.write(f"{'='*60}\n")
                    f.write(html)
                    f.write(f"\n{'='*60}\n\n")
            except Exception:
                pass

            return ""
        except Exception as e:
            try:
                with open(TEST_OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"请求失败: {label}\n")
                    f.write(f"URL: {assignment_url}\n")
                    f.write(f"错误: {e}\n")
                    f.write(f"{'='*60}\n\n")
            except Exception:
                pass
            return ""

    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def scrape_courses(self, term_filter: str = None) -> Dict[str, Any]:
        """爬取所有课程信息"""
        try:
            try:
                TEST_OUTPUT_FILE.write_text("", encoding="utf-8")
            except Exception:
                pass

            html_payload = self._fetch_tab_payload()
            courses = _parse_course_links(html_payload, term_filter)

            result: Dict[str, Any] = {
                "success": True,
                "total_courses": len(courses),
                "courses": [],
                "errors": []
            }

            for course_item in courses:
                try:
                    course_info = {
                        "id": course_item["course_id"],
                        "name": course_item["title"],
                        "url": course_item["url"],
                        "announcements": course_item.get("announcements", []),
                        "course_materials": [],
                        "upload_assignments": []
                    }

                    _, menu_links = self._fetch_course_menu(course_item["url"])
                    in_course_materials = False

                    for link in menu_links:
                        entry_url = link.get("url", "")
                        entry_label = link.get("label", "")

                        if entry_label and "Course Materials" in entry_label:
                            in_course_materials = True
                            continue
                        if entry_label and "Feedback & Get Help" in entry_label:
                            in_course_materials = False
                            continue

                        if not entry_url:
                            continue

                        if "announcement" in entry_url.lower():
                            try:
                                announcements = self._fetch_announcements(entry_url)
                                course_info["announcements"].extend(announcements)
                            except Exception as e:
                                result["errors"].append({
                                    "course": course_item["title"],
                                    "error": f"获取公告失败: {str(e)}"
                                })

                        if in_course_materials or "announcement" in entry_url.lower():
                            try:
                                resp = self.session.get(entry_url, allow_redirects=True)
                                resp.raise_for_status()
                                content = self._extract_menu_content(resp.text, entry_url)

                                def _collect_upload_links(blocks, parent_label):
                                    for block in blocks:
                                        for link_in_block in block.get("links", []):
                                            link_href = link_in_block.get("href", "")
                                            if link_href and "uploadassignment" in link_href.lower():
                                                existing = any(
                                                    a["url"] == link_href for a in course_info["upload_assignments"]
                                                )
                                                if not existing:
                                                    course_info["upload_assignments"].append({
                                                        "label": link_in_block.get("text", parent_label),
                                                        "url": link_href,
                                                        "parent_label": parent_label,
                                                        "parent_url": entry_url,
                                                        "content_blocks": [block]
                                                    })

                                _collect_upload_links(content.get("content_blocks", []), entry_label)
                                for section in content.get("content_section_blocks", []):
                                    _collect_upload_links(section.get("blocks", []), entry_label)

                                course_info["course_materials"].append({
                                    "label": entry_label,
                                    "url": entry_url,
                                    **content
                                })
                            except Exception as e:
                                result["errors"].append({
                                    "course": course_item["title"],
                                    "error": f"获取页面 '{entry_label}' 失败: {str(e)}"
                                })

                        if "uploadassignment" in entry_url.lower():
                            existing = any(
                                a["url"] == entry_url for a in course_info["upload_assignments"]
                            )
                            if not existing:
                                course_info["upload_assignments"].append({
                                    "label": entry_label,
                                    "url": entry_url,
                                    "parent_label": "",
                                    "parent_url": "",
                                    "content_blocks": []
                                })

                    result["courses"].append(course_info)

                    for assignment in course_info["upload_assignments"]:
                        assignment_url = assignment.get("url", "")
                        if assignment_url:
                            due_date = self._fetch_assignment_due_date(
                                assignment_url,
                                referer=course_info["url"],
                                label=assignment.get("label", "")
                            )
                            if due_date:
                                assignment["due_date"] = due_date

                except Exception as exc:
                    result["errors"].append({
                        "course": course_item["title"],
                        "error": str(exc)
                    })
                    result["courses"].append({
                        "id": course_item["course_id"],
                        "name": course_item["title"],
                        "url": course_item["url"],
                        "error": str(exc)
                    })

            try:
                due_summary_lines = []
                for course in result.get("courses", []):
                    assignments = course.get("upload_assignments", [])
                    if not assignments:
                        continue
                    due_summary_lines.append(f"\n--- {course['name']} ---")
                    for a in assignments:
                        due = a.get("due_date", "未获取到")
                        due_summary_lines.append(f"  {a['label']}: {due}")

                due_section = "\n".join(due_summary_lines) if due_summary_lines else "无作业"

                output_content = f"""========================================
Blackboard 爬取结果
========================================
时间: {self._get_current_time()}
总课程数: {len(courses)}

========================================
作业 Due Date 汇总
========================================
{due_section}

========================================
原始课程列表页面 HTML
========================================
{html_payload}

========================================
爬取结果 (JSON格式)
========================================
{json.dumps(result, ensure_ascii=False, indent=2)}
"""
                OUTPUT_FILE.write_text(output_content, encoding="utf-8")
            except Exception as e:
                pass

            return result

        except Exception as e:
            error_result = {
                "success": False,
                "message": f"爬取课程信息失败: {str(e)}",
                "courses": [],
                "errors": [str(e)]
            }
            try:
                output_content = f"爬取失败: {str(e)}"
                OUTPUT_FILE.write_text(output_content, encoding="utf-8")
            except Exception:
                pass
            return error_result
