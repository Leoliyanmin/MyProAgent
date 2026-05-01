"""Robust TIS 查询工具
- 修复相对/绝对导入问题
- 在缺失依赖时内置 `load_cookies` 回退实现
- 统一输出到 data 目录
"""

import requests
import json
from pathlib import Path
import os, sys


from .get_cookies import get_cookies_for_user

from .tis_schedule import load_tis_cookies

BASE = "https://tis.sustech.edu.cn"

QUERY_URL = f"{BASE}/xjgl/fxzygl/getxjxx"

HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://tis.sustech.edu.cn/",
    "Origin": "https://tis.sustech.edu.cn"
}

# 常见拼音缩写字段到中文字段的映射（可按需补充）
FIELD_MAPPING = {
    "xh": "学号",
    "xm": "姓名",
    "xb": "性别",
    "csrq": "出生日期",
    "sjh": "手机号",
    "yxh": "院系号",
    "yxmc": "院系名称",
    "xy": "学院",
    "zymc": "专业名称",
    "zy": "专业",
    "bj": "班级",
    "nj": "年级",
    "xz": "学制",
    "xzlx": "学籍类型",
    "rxrq": "入学日期",
    "xslb": "学生类别",
    "sfz": "身份证号",
    "email": "邮箱",
    "lxdh": "联系电话",
    "jg": "籍贯",
    "bjm": "班级代码",
    "ssh": "宿舍号",
    "dzyx": "电子邮箱",
    "xmpy": "姓名拼音",
    "xbm": "性别代码",
    "zjh": "证件号",
    "njm": "年级代码",
    "yxm": "院系代码",
    "sssym": "所属书院码",
    "bjm": "班级代码",
    "rxgkkscj": "高考成绩",
    "byzxmc":"毕业中学名称"
}

# 需要从结果中删除的字段（键名），不区分大小写
UNWANTED_KEYS = {
    "globalXmList",
    "globalxmall",
    "pylx",
    "gjm",
    "mzm",
    "zzmmm",
    "rxrq",
    "jtyb",
    "xqm",
    "xdm",
    "glyxm",
    "zyxkm",
    "xz",
    "ycxz",
    "pyccm",
    "sfpt",
    "sfgfs",
    "sfjljhs",
    "sfcglx",
    "bmksh",
    "ksbh",
    "sydssm",
    "kslbm",
    "xjzt",
    "sfzx",
    "sfylrjbxx",
    "sfytxxjk",
    "cjsj",
    "cjr",
    "zhxgsj",
    "zhxgr",
    "zhsjzt",
    "学制",
    "入学日期"
}



def remove_null_values(data):
    """递归删除字典中值为null的字段"""
    if isinstance(data, dict):
        # 创建新字典，只包含非null值
        cleaned = {}
        for key, value in data.items():
            if value is not None:
                # 递归处理嵌套的字典和列表
                cleaned_value = remove_null_values(value)
                if cleaned_value is not None:
                    cleaned[key] = cleaned_value
        return cleaned
    elif isinstance(data, list):
        # 处理列表，过滤掉null值
        cleaned_list = []
        for item in data:
            cleaned_item = remove_null_values(item)
            if cleaned_item is not None:
                cleaned_list.append(cleaned_item)
        return cleaned_list
    else:
        # 基本类型直接返回
        return data


def map_fields_to_chinese(data):
    """递归将字典的拼音缩写键映射为中文键名（不覆盖已存在中文键）。"""
    if isinstance(data, dict):
        mapped = {}
        for key, value in data.items():
            new_key = FIELD_MAPPING.get(key, key)
            mapped[new_key] = map_fields_to_chinese(value)
        return mapped
    elif isinstance(data, list):
        return [map_fields_to_chinese(item) for item in data]
    else:
        return data


def remove_unwanted_keys(data, unwanted_keys: set):
    """递归删除给定键名的字段（大小写不敏感）。"""
    if isinstance(data, dict):
        lowered = {k.lower() for k in unwanted_keys}
        kept = {}
        for key, value in data.items():
            if key.lower() in lowered:
                continue
            kept[key] = remove_unwanted_keys(value, unwanted_keys)
        return kept
    elif isinstance(data, list):
        return [remove_unwanted_keys(item, unwanted_keys) for item in data]
    else:
        return data


def load_yx_mapping(yx_list_file: str = "CS309_OOAD_Project/backend/app/util/data/yx_list.json") -> dict:
    """
    加载院系代码到院系名称的映射
    
    Args:
        yx_list_file: 院系列表文件路径
    
    Returns:
        dict: 院系代码到院系名称的映射字典
    """
    try:
        yx_path = Path(yx_list_file)
        if not yx_path.exists():
            print(f"院系列表文件不存在: {yx_path}")
            return {}
        
        with open(yx_path, 'r', encoding='utf-8') as f:
            yx_list = json.load(f)
        
        # 创建院系代码到院系名称的映射
        yx_mapping = {}
        for item in yx_list:
            yxdm = item.get('yxdm')
            yxmc = item.get('yxmc')
            sjyxdm = item.get('sjyxdm')
            
            # 添加主院系代码映射
            if yxdm and yxmc:
                yx_mapping[yxdm] = yxmc
            
            # 添加实际院系代码映射（sjyxdm字段）
            if sjyxdm and yxmc and sjyxdm != "0":
                yx_mapping[sjyxdm] = yxmc
        
        print(f"成功加载院系映射，共 {len(yx_mapping)} 个院系")
        return yx_mapping
        
    except Exception as e:
        print(f"加载院系映射失败: {e}")
        return {}


def load_sy_mapping(sy_list_file: str) -> dict:
    """
    加载书院映射文件
    
    Args:
        sy_list_file: 书院列表文件路径
    
    Returns:
        dict: 书院代码到书院名称的映射字典
    """
    try:
        sy_path = Path(sy_list_file)
        if not sy_path.exists():
            print(f"书院列表文件不存在: {sy_path}")
            return {}
        
        with open(sy_path, 'r', encoding='utf-8') as f:
            sy_list = json.load(f)
        
        # 创建书院代码到书院名称的映射
        sy_mapping = {}
        for item in sy_list:
            yxdm = item.get('yxdm')  # 书院代码
            yxmc = item.get('yxmc')  # 书院名称
            
            if yxdm and yxmc:
                sy_mapping[yxdm] = yxmc
        
        print(f"成功加载书院映射，共 {len(sy_mapping)} 个书院")
        return sy_mapping
        
    except Exception as e:
        print(f"加载书院映射失败: {e}")
        return {}


def load_bj_mapping(bj_list_file: str) -> dict:
    """
    加载班级映射文件
    
    Args:
        bj_list_file: 班级列表文件路径
    
    Returns:
        dict: 班级代码到班级名称的映射字典
    """
    try:
        bj_path = Path(bj_list_file)
        if not bj_path.exists():
            print(f"班级列表文件不存在: {bj_path}")
            return {}
        
        with open(bj_path, 'r', encoding='utf-8') as f:
            bj_data = json.load(f)
        
        # 创建班级代码到班级名称的映射
        bj_mapping = {}
        if 'content' in bj_data and isinstance(bj_data['content'], list):
            for item in bj_data['content']:
                bjdm = item.get('BJDM')  # 班级代码
                bjmc = item.get('BJMC')  # 班级名称
                
                if bjdm and bjmc:
                    bj_mapping[bjdm] = bjmc
        
        print(f"成功加载班级映射，共 {len(bj_mapping)} 个班级")
        return bj_mapping
        
    except Exception as e:
        print(f"加载班级映射失败: {e}")
        return {}


def replace_yx_codes_with_names(data, yx_mapping: dict):
    """
    递归将院系代码替换为院系名称，并删除原代码字段
    
    Args:
        data: 要处理的数据
        yx_mapping: 院系代码到院系名称的映射字典
    
    Returns:
        处理后的数据
    """
    if isinstance(data, dict):
        processed = {}
        for key, value in data.items():
            # 如果是院系代码字段，尝试替换为院系名称
            if key in ['院系代码', 'yxm', 'yxh'] and isinstance(value, str):
                yx_name = yx_mapping.get(value)
                if yx_name:
                    # 只保留院系名称字段，删除原代码字段
                    processed['院系名称'] = yx_name
                    print(f"   院系代码 '{value}' 已替换为院系名称 '{yx_name}'，原代码字段已删除")
                else:
                    processed[key] = value
            else:
                processed[key] = replace_yx_codes_with_names(value, yx_mapping)
        return processed
    elif isinstance(data, list):
        return [replace_yx_codes_with_names(item, yx_mapping) for item in data]
    else:
        return data


def replace_sy_codes_with_names(data, sy_mapping: dict):
    """
    递归将书院代码替换为书院名称，并删除原代码字段
    
    Args:
        data: 要处理的数据
        sy_mapping: 书院代码到书院名称的映射字典
    
    Returns:
        处理后的数据
    """
    if isinstance(data, dict):
        processed = {}
        for key, value in data.items():
            # 如果是所属书院码字段，尝试替换为书院名称
            if key == "所属书院码" and isinstance(value, str) and value in sy_mapping:
                # 只保留书院名称字段，删除原代码字段
                processed["所属书院名称"] = sy_mapping[value]
                print(f"   书院代码 '{value}' 已替换为书院名称 '{sy_mapping[value]}'，原代码字段已删除")
            else:
                processed[key] = replace_sy_codes_with_names(value, sy_mapping)
        return processed
    elif isinstance(data, list):
        return [replace_sy_codes_with_names(item, sy_mapping) for item in data]
    else:
        return data


def replace_bj_codes_with_names(data, bj_mapping: dict):
    """
    递归将班级代码替换为班级名称，并删除原代码字段
    
    Args:
        data: 要处理的数据
        bj_mapping: 班级代码到班级名称的映射字典
    
    Returns:
        处理后的数据
    """
    if isinstance(data, dict):
        processed = {}
        for key, value in data.items():
            # 如果是班级代码字段，尝试替换为班级名称
            if key in ['班级代码', 'bjm'] and isinstance(value, str) and value in bj_mapping:
                # 只保留班级名称字段，删除原代码字段
                processed["班级名称"] = bj_mapping[value]
                print(f"   班级代码 '{value}' 已替换为班级名称 '{bj_mapping[value]}'，原代码字段已删除")
            else:
                processed[key] = replace_bj_codes_with_names(value, bj_mapping)
        return processed
    elif isinstance(data, list):
        return [replace_bj_codes_with_names(item, bj_mapping) for item in data]
    else:
        return data


def query_tis_data(sid: str = None, password: str = None,query_params: dict = None, cookies_file: str = "util/data/cookies.json", output_file: str = "util/data/tis_imfor.json", debug: bool = False) -> dict:
    """
    查询TIS数据并处理，删除null值
    
    Args:
        query_params: 查询参数，如果为None则使用默认参数
        cookies_file: cookies文件路径
        output_file: 输出文件路径
    
    Returns:
        dict: 处理后的查询结果字典，失败时返回None
    """
    # 加载cookies
    cookies = {}
    
    # 如果提供了学号和密码，先获取cookies（若 get_cookies_for_user 不可用则跳过此分支）
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
    
    # 默认查询参数
    default_params = {
        "page": 1,
        "limit": 100,
        "sort": "id",
        "order": "desc"
    }
    
    if query_params:
        default_params.update(query_params)
    
    print(f"开始查询TIS数据: {QUERY_URL}")
    print(f"查询参数: {default_params}")
    
    try:
        # 创建会话
        s = requests.Session()
        s.headers.update(HEADERS)
        s.cookies.update(cookies)
        
        # 发送POST请求
        r = s.post(QUERY_URL, json=default_params, timeout=30, allow_redirects=True)
        r.raise_for_status()
        
        # 解析JSON响应
        result = r.json()
        print(f"查询成功，状态码: {r.status_code}")
        print(f"响应数据类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"原始响应字段数: {len(result)}")
        elif isinstance(result, list):
            print(f"响应数据条数: {len(result)}")
        
        # 删除null值、映射中文字段、院系映射并过滤不需要的字段
        cleaned_result = remove_null_values(result)
        mapped_result = map_fields_to_chinese(cleaned_result)
        
        # 加载院系映射并替换院系代码
        yx_mapping = load_yx_mapping("util/data/yx_list.json")
        if yx_mapping:
            mapped_result = replace_yx_codes_with_names(mapped_result, yx_mapping)
        
        # 加载书院映射并替换书院代码
        sy_mapping = load_sy_mapping("util/data/sy_list.json")
        if sy_mapping:
            mapped_result = replace_sy_codes_with_names(mapped_result, sy_mapping)
        
        # 加载班级映射并替换班级代码
        bj_mapping = load_bj_mapping("util/data/bj_list.json")
        if bj_mapping:
            mapped_result = replace_bj_codes_with_names(mapped_result, bj_mapping)
        
        filtered_result = remove_unwanted_keys(mapped_result, UNWANTED_KEYS)
        
        print(f"删除null、映射并过滤字段后字段数: {len(filtered_result) if isinstance(filtered_result, dict) else 'N/A'}")
        
        # 保存处理后的结果到文件
        if output_file:
            # 将相对路径转换为绝对路径，保存到 app/util/data 目录
            if not os.path.isabs(output_file):
                output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', os.path.basename(output_file))
            else:
                output_path = output_file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(filtered_result, f, ensure_ascii=False, indent=2)
            print(f"处理后的查询结果已保存到: {output_path}")
        
        return filtered_result
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        print(f"响应状态码: {r.status_code}")
        print(f"响应头: {dict(r.headers)}")
        print(f"响应内容: {r.text[:500]}...")
        return None
    except Exception as e:
        print(f"查询失败: {e}")
        return None

# python -c "import sys; sys.path.append('CS309_OOAD_Project/backend'); from app.util.tis_query import query_tis_data; query_tis_data('12311020','5616298laz')"
def get_tis_id():
    """
    调用 query_tis_data 获取 TIS 学生信息，并返回 {id: "..."} 格式

    Args:
        sid: 学号
        password: 密码
    
    Returns:
        dict: {"id": "..."}，失败时返回 {}
    """
    data = query_tis_data()
    
    if not data:
        return {}
    
    if isinstance(data, dict) and "id" in data:
        print(data["id"])
        return {data["id"]}
        
    elif isinstance(data, list) and data and "id" in data[0]:
        print(data[0]["id"])
        return {data[0]["id"]}
    print("未找到有效的ID")
    return {}
