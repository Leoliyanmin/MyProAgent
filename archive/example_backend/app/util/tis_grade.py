# tis_grade.py
import requests
import json
import time
from urllib.parse import urljoin
from .get_cookies import get_cookies_for_user
from .tis_schedule import load_tis_cookies

BASE = "https://tis.sustech.edu.cn"
GRADE_QUERY_URL = f"{BASE}/cjgl/xscjgl/xsgrcjcx/queryXnAndXqXfj"

HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://tis.sustech.edu.cn/",
    "X-Requested-With": "XMLHttpRequest"
}


def query_grades(sid: str = None, password: str = None, cookies_file: str = "util/data/cookies.json") -> dict:
    """
    查询学生成绩信息
    
    Args:
        sid: 学号
        password: 密码
        cookies_file: cookies文件路径
    
    Returns:
        dict: 包含成绩数据的字典，失败时返回空字典
    """
    # 获取cookies
    if sid and password and callable(get_cookies_for_user):
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
        # 从环境变量或文件读取cookies
        cookies = load_tis_cookies()
        if not cookies:
            print("没有读取到 Cookie。请提供学号和密码，或在环境变量 TIS_COOKIE 设置原始 Cookie 行，或提供 cookies.json。")
            return {}
    
    if not cookies:
        print("无法加载cookies，请先运行get_cookies.py")
        return {}
    
    print("开始查询成绩...")
    
    try:
        # 创建会话
        s = requests.Session()
        s.headers.update(HEADERS)
        s.cookies.update(cookies)
        
        # 查询成绩
        r = s.post(GRADE_QUERY_URL, timeout=20)
        r.raise_for_status()
        
        # 解析响应
        response_data = r.json()
        
        # save_path = "util/data/gpa.json"
        # with open(save_path, "w", encoding="utf-8") as f:
        #     json.dump(response_data, f, ensure_ascii=False, indent=4)

        
        xfj = response_data.get("xfjandpm", {})
        result = {
            "GPA": xfj.get("PJXFJ"),
            "Rank": xfj.get("PM"),
        }
        if result["GPA"] is None or result["Rank"] is None:
            print("成绩查询失败: 响应缺少 xfjandpm")
            return {}

        print("成绩查询成功")
        return result
    except Exception as e:
        print(f"查询成绩时出错: {e}")
        return {}
