#!/usr/bin/env python3
"""验证 Tauri WebView 提取的 Cookie 能否访问 SUSTech 服务。

用法:
    python test_cookies.py                    # 默认路径 ~/.proagent/cas-cookies.json
    python test_cookies.py /path/to/file.json
"""

import json
import sys
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def load_cookies(path: str) -> list:
    p = Path(path).expanduser()
    if not p.exists():
        print(f"❌ Cookie 文件不存在: {p}")
        sys.exit(1)
    with open(p) as f:
        return json.load(f)


def test_with_requests(cookies: list):
    session = requests.Session()
    for c in cookies:
        domain = c["domain"]
        if not domain.startswith("."):
            domain = "." + domain
        session.cookies.set(
            c["name"], c["value"],
            domain=domain,
            path=c.get("path", "/"),
        )

    test_urls = [
        ("https://tis.sustech.edu.cn/authentication/main", "TIS 教学管理平台"),
        ("https://bb.sustech.edu.cn/", "Blackboard Learn"),
        ("https://cas.sustech.edu.cn/cas/login", "CAS 认证中心"),
    ]

    for url, name in test_urls:
        print(f"\n{'='*60}")
        print(f"🔍 {name}")
        print(f"   {url}")
        print(f"{'='*60}")
        try:
            resp = session.get(url, allow_redirects=False, timeout=10)
            status = resp.status_code

            if status == 200:
                body = resp.text[:3000]
                if "password" in body.lower() or "登录" in body:
                    print(f"   ❌ {status} — 返回了登录页面，Cookie 无效或已过期")
                else:
                    print(f"   ✅ {status} OK — Cookie 有效！")
                import re
                title = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
                if title:
                    print(f"   页面: {title.group(1).strip()[:120]}")

            elif status in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location", "")
                print(f"   ⚠️ {status} 重定向 → {location[:120]}")
                if "cas.sustech.edu.cn/cas/login" in location:
                    print(f"   ❌ 重定向到 CAS 登录 — Cookie 无效")
                elif "ticket=" in location:
                    print(f"   ✅ 带 Service Ticket 重定向 — TGC 有效，需换取 session")
                else:
                    print(f"   ℹ️ 重定向到服务页面")
            else:
                print(f"   ❓ 状态码: {status}")
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")


def test_with_urllib(cookies: list):
    from http.cookiejar import CookieJar, MozillaCookieJar
    from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor
    from urllib.error import HTTPError
    import tempfile, os

    # 写 Netscape 格式 cookie 文件
    lines = ["# Netscape HTTP Cookie File\n"]
    for c in cookies:
        domain = c["domain"]
        flag = "TRUE" if domain.startswith(".") else "FALSE"
        if not domain.startswith("."):
            domain = "." + domain
        path = c.get("path", "/")
        secure = "TRUE" if c.get("secure") else "FALSE"
        httponly = "#HttpOnly_" if c.get("http_only") else ""
        lines.append(f"{httponly}{domain}\t{flag}\t{path}\t{secure}\t0\t{c['name']}\t{c['value']}\n")

    tmpfile = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    tmpfile.writelines(lines)
    tmpfile.close()

    jar = MozillaCookieJar(tmpfile.name)
    jar.load(ignore_discard=True, ignore_expires=True)

    test_urls = [
        ("https://tis.sustech.edu.cn/authentication/main", "TIS 教学管理平台"),
        ("https://bb.sustech.edu.cn/", "Blackboard Learn"),
        ("https://cas.sustech.edu.cn/cas/login", "CAS 认证中心"),
    ]

    opener = build_opener(HTTPCookieProcessor(jar))

    for url, name in test_urls:
        print(f"\n{'='*60}")
        print(f"🔍 {name}")
        print(f"   {url}")
        print(f"{'='*60}")
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            try:
                resp = opener.open(req, timeout=10)
                body = resp.read().decode("utf-8", errors="replace")[:3000]
                print(f"   ✅ {resp.status} OK")
                import re
                title = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
                if title:
                    print(f"   页面: {title.group(1).strip()[:120]}")
            except HTTPError as e:
                if e.code in (301, 302, 303, 307, 308):
                    location = e.headers.get("Location", "")
                    print(f"   ⚠️ {e.code} 重定向 → {location[:120]}")
                    if "cas.sustech.edu.cn/cas/login" in location:
                        print(f"   ❌ 重定向到 CAS 登录 — Cookie 无效")
                    elif "ticket=" in location:
                        print(f"   ✅ 带 Service Ticket 重定向 — TGC 有效")
                    else:
                        print(f"   ℹ️ 重定向到服务页面")
                else:
                    print(f"   ❌ HTTP 错误: {e.code}")
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

    os.unlink(tmpfile.name)


def main():
    cookie_path = sys.argv[1] if len(sys.argv) > 1 else "~/.proagent/cas-cookies.json"
    print(f"📂 加载 Cookie: {Path(cookie_path).expanduser()}")

    cookies = load_cookies(cookie_path)
    print(f"   共 {len(cookies)} 个 Cookie")

    domains = {}
    for c in cookies:
        d = c.get("domain", "?")
        domains.setdefault(d, []).append(c["name"])

    print(f"\n📋 Cookie 概况:")
    for domain, names in domains.items():
        print(f"   {domain}: {', '.join(names)}")

    has_tgc = any(c["name"] == "TGC" for c in cookies)
    print(f"\n{'✅ TGC Cookie 已找到' if has_tgc else '❌ 未找到 TGC Cookie — 可能无法 SSO'}")

    print("\n🚀 开始测试...\n")
    if HAS_REQUESTS:
        test_with_requests(cookies)
    else:
        test_with_urllib(cookies)

    print("\n" + "="*60)
    print("🏁 测试完成")
    print("="*60)
    print("\n💡 解读:")
    print("   ✅ 200 OK (非登录页) → Cookie 有效，直接可访问")
    print("   ⚠️ 带 ticket= 重定向 → TGC 有效，需 Service Ticket 换取 session")
    print("   ❌ 重定向到 CAS 登录 → Cookie 过期或无效\n")


if __name__ == "__main__":
    main()