# download_student_photo.py
import requests
import json
import base64
from urllib.parse import urljoin
from pathlib import Path
from .get_cookies import get_cookies_for_user

from .tis_schedule import load_tis_cookies
from .tis_query import get_tis_id

BASE = "https://tis.sustech.edu.cn"
RXZP = "/byyfile/pic/xjzp/glysc/aaee0b25-0062-499c-bfd7-5a0128bc484a.jpg"  # 你返回的 rxzp
INIT_SZXZP_URL = "/xjgl/xjxxgl/xsxxdate/initxszp"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://tis.sustech.edu.cn/",  # 设成触发该照片请求的页面也行
}
def fetch_rxzp_by_id(the_id: str | dict | set | list | tuple, cookies: dict) -> str | None:
    """
    用 id 请求 initszp 接口，返回 rxzp 路径（对 the_id 做强制规范化）
    """
    api = urljoin(BASE, INIT_SZXZP_URL)
    
    # --- 规范化 the_id ---
    # 允许你不小心传了 {"id": "..."}、{"id", "..."} 等
    if isinstance(the_id, dict) and "id" in the_id:
        the_id = the_id["id"]
    elif isinstance(the_id, (set, list, tuple)):
        # 取第一个元素（集合会被遍历一次）
        if not the_id:
            print("the_id 是空集合/列表/元组，无法获取 id")
            return None
        the_id = next(iter(the_id))

    # 最终强制转成字符串
    the_id = str(the_id)

    payload = {"id": the_id}

    # 调试日志：确认没有 set 混入
    print(f"[fetch_rxzp_by_id] payload={payload} (types: id={type(the_id).__name__})")

    try:
        s = requests.Session()
        s.headers.update(HEADERS)
        s.cookies.update(cookies)

        resp = s.post(api, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        rxzp = data.get("rxzp")
        if isinstance(rxzp, str) and rxzp.strip():
            print("获取 rxzp 成功:", rxzp)
            return rxzp
        print("返回没有 rxzp:", data)
        return None
    except Exception as e:
        print("fetch_rxzp_by_id 失败:", e)
        return None


def download_student_photo(sid: str = None, password: str = None,rxzp_path: str = None, cookies_file: str = "util/data/cookies.json", output_dir: str = "util/data/photos") -> dict:
    """
    下载学生照片并返回Base64编码
    
    Args:
        rxzp_path: 照片路径，如果为None则使用默认路径
        cookies_file: cookies文件路径
        output_dir: 输出目录（可选，如果提供则同时保存文件）
    
    Returns:
        dict: 包含Base64数据和文件信息的字典，失败时返回None
    """
    # 使用提供的路径或默认路径
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


    photo_path = fetch_rxzp_by_id(get_tis_id(),cookies)
    if not photo_path:
        print("无法获取照片路径")
        return None
    # 加载cookies
    if not cookies:
        print("无法加载cookies，请先运行get_cookies.py")
        return None
    
    # 构建完整URL
    url = urljoin(BASE, photo_path)
    print(f"开始下载照片: {url}")
    
    try:
        # 创建会话
        s = requests.Session()
        s.headers.update(HEADERS)
        s.cookies.update(cookies)
        
        # 下载照片
        r = s.get(url, timeout=20, stream=True, allow_redirects=True)
        r.raise_for_status()
        
        # 获取图片数据
        image_data = r.content
        file_size = len(image_data)
        
        # 转换为Base64
        base64_string = base64.b64encode(image_data).decode('utf-8')
        
        # 生成文件名
        name = Path(photo_path).name or "student_photo.jpg"
        
        # 如果提供了输出目录，同时保存文件
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_path = Path(output_dir) / name
            with open(output_path, "wb") as f:
                f.write(image_data)
            print(f"照片已保存: {output_path.resolve()}")
        
        print(f"照片已转换为Base64，大小: {file_size} bytes")
        
        # 返回简化的JSON格式
        return {
            'base64': base64_string,
            'filename': name,
            'size': file_size,
            'type': 'jpg'
        }
        
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")
        return None
    except Exception as e:
        print(f"处理失败: {e}")
        return None
