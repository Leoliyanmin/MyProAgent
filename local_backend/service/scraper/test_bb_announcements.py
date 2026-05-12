"""Test BB announcement scraping with new parser.
Usage:
  python3 test_bb_announcements.py <course_id> <jsessionid> <s_session_id>

Example:
  python3 test_bb_announcements.py _8205_1 abc123 xyz789
  (Get cookies from browser DevTools → Application → Cookies → bb.sustech.edu.cn)
"""
import sys
import json
import requests
from blackboard_scraper import _extract_announcements

BB_BASE = "https://bb.sustech.edu.cn"

def test(course_id: str, jsessionid: str, s_session_id: str):
    session = requests.Session()
    session.cookies.set("JSESSIONID", jsessionid, domain="bb.sustech.edu.cn")
    session.cookies.set("s_session_id", s_session_id, domain="bb.sustech.edu.cn")
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })

    url = f"{BB_BASE}/webapps/blackboard/execute/announcement?method=search&context=course_entry&course_id={course_id}&handle=announcements_entry&mode=view"
    print(f"Fetching: {url}")
    resp = session.get(url, allow_redirects=True)
    print(f"Status: {resp.status_code}")
    print(f"Final URL: {resp.url}")

    if "cas" in resp.url:
        print("ERROR: Redirected to CAS login - cookies invalid or expired")
        return

    announcements = _extract_announcements(resp.text)
    print(f"\nAnnouncements found: {len(announcements)}")
    for i, a in enumerate(announcements, 1):
        print(f"\n--- {i}. {a.get('title', '(no title)')[:60]}")
        print(f"    posted_on: {a.get('posted_on', '')[:60]}")
        print(f"    posted_date: {a.get('posted_date', '')[:60]}")
        print(f"    posted_by: {a.get('posted_by', '')[:40]}")
        body = a.get('body_text', '')
        print(f"    body: {body[:100]}...")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    test(sys.argv[1], sys.argv[2], sys.argv[3])
