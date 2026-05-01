import requests
import json
import os
from .get_cookies import get_cookies_for_user
from .tis_schedule import load_tis_cookies

BASE = "https://tis.sustech.edu.cn"
GRADES_DETAIL_URL = f"{BASE}/cjgl/grcjcx/grcjcx"

# 请求头（与浏览器中尽量保持一致）
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://tis.sustech.edu.cn",
    "Referer": "https://tis.sustech.edu.cn/cjgl/grcjcx/go/1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Rolecode": "01"
}

def query_credits(sid: str = None, password: str = None, cookies_file: str = "util/data/cookies.json") -> dict:
    """
    请求 TIS 成绩接口，并保存为 JSON 文件
    """

    if sid and password and callable(get_cookies_for_user):
        print("正在获取TIS cookies...")
        cookies_data = get_cookies_for_user(sid, password, cookies_file)
        if "error" in cookies_data:
            print(f"获取cookies失败: {cookies_data['error']}")
            return {}
        
        tis_service = cookies_data.get("services", {}).get("tis", {})
        if tis_service.get("is_valid"):
            cookies = tis_service.get("cookies", {})
            print("使用新获取的TIS cookies")
        else:
            print("获取的TIS cookies无效")
            return {}
    else:
        cookies = load_tis_cookies()
        if not cookies:
            print("没有读取到 Cookie。请提供学号和密码，或在环境变量 TIS_COOKIE 设置原始 Cookie 行，或提供 cookies.json。")
            return {}
    
    if not cookies:
        print("无法加载cookies，请先运行get_cookies.py")
        return {}
    
    print("开始查询成绩...") 

    payload = {
        "xn": None,
        "xq": None,
        "kcmc": None,
        "cxbj": "-1",
        "pylx": "1",
        "current": 1,
        "pageSize": 60,
        "sffx": None
    }

    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        session.cookies.update(cookies)

        print("正在请求成绩接口...")
        resp = session.post(GRADES_DETAIL_URL, json=payload, timeout=20)
        resp.raise_for_status()

        data = resp.json()
        data = analyze_credits_to_json(data)

        # save_path = "util/data/ana.json"
        # with open(save_path, "w", encoding="utf-8") as f:
        #     json.dump(data, f, ensure_ascii=False, indent=4)

        # print(f"成绩数据已保存为：{save_path} ")

        return data

    except requests.exceptions.RequestException as e:
        print("请求失败：", e)
        return {}

def analyze_credits_to_json(data: dict) -> dict:
    """
    根据 TIS 成绩 JSON：
    1. 统计总学分
    2. 按 kclb 分类统计学分
    3. 返回一个 JSON 结构
    """

    total_credit = 0
    category_credits = {}

    # 取成绩列表
    records = data.get("content", {}).get("list", [])

    for course in records:
        credit = course.get("xf", 0)

        try:
            credit = float(credit)
        except:
            credit = 0

        total_credit += credit

        category = course.get("kclb", "未分类")

        if category not in category_credits:
            category_credits[category] = 0

        category_credits[category] += credit

    result = {
        "total_credit": total_credit,
        "category_credit": category_credits
    }

    return result


# 接口：query_credits()
# 返回 {
#     "total_credit": 106.0,
#     "category_credit": {
#         "通识必修课": 73.0,
#         "专业选修课": 2.0,
#         "专业导论类": 2.0,
#         "专业基础课": 18.0,
#         "专业核心课": 3.0,
#         "社科类": 2.0,
#         "美育类": 2.0,
#         "实践": 1.0,
#         "专业必修课": 3.0
#     }
# }