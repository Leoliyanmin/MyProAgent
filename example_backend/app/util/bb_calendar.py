#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blackboard日历数据爬取脚本
从Blackboard获取个人日历数据
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))



def load_cookies_from_file(cookies_file: str = "util/data/cookies.json") -> Dict[str, str]:
    """
    从文件加载Blackboard cookies
    
    Args:
        cookies_file: cookies文件路径
    
    Returns:
        Dict[str, str]: cookies字典
    """
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        
        # 提取Blackboard cookies
        bb_cookies = cookies_data.get('services', {}).get('bb', {}).get('cookies', {})
        
        if not bb_cookies:
            print(f"警告: 在 {cookies_file} 中未找到Blackboard cookies")
            return {}
        
        print(f"成功加载 {len(bb_cookies)} 个Blackboard cookies")
        return bb_cookies
        
    except FileNotFoundError:
        print(f"错误: 找不到cookies文件 {cookies_file}")
        return {}
    except json.JSONDecodeError as e:
        print(f"错误: 解析cookies文件失败 - {e}")
        return {}


def get_calendar_data(cookies: Dict[str, str], course_id: str = "", mode: str = "personal", 
                     start_timestamp: int = None, end_timestamp: int = None) -> Optional[Dict]:
    """
    获取Blackboard日历数据
    
    Args:
        cookies: Blackboard cookies
        course_id: 课程ID，空字符串表示所有课程
        mode: 模式，personal表示个人日历
        start_timestamp: 开始时间戳（毫秒）
        end_timestamp: 结束时间戳（毫秒）
    
    Returns:
        Dict: 日历数据，失败时返回None
    """
    if not cookies:
        print("错误: 没有可用的cookies")
        return None
    
    # 构建请求URL - 使用正确的API端点
    base_url = "https://bb.sustech.edu.cn/webapps/calendar/calendarData/selectedCalendarEvents"
    
    # 如果没有提供时间戳，使用当前时间前后30天
    if start_timestamp is None:
        start_timestamp = int((time.time() - 30 * 24 * 3600) * 1000)
    if end_timestamp is None:
        end_timestamp = int((time.time() + 30 * 24 * 3600) * 1000)
    
    params = {
        'start': start_timestamp,
        'end': end_timestamp,
        'course_id': course_id,
        'mode': mode
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://bb.sustech.edu.cn/webapps/calendar/calendar.jsp',
        'Connection': 'keep-alive'
    }
    
    try:
        print(f"正在获取日历数据...")
        print(f"请求URL: {base_url}")
        print(f"参数: {params}")
        
        response = requests.get(
            base_url,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"成功获取日历数据，包含 {len(data) if isinstance(data, list) else '未知数量'} 个事件")
                print(f"原始响应内容: {response.text[:500]}...")
                return data
            except json.JSONDecodeError as e:
                print(f"错误: 解析JSON响应失败 - {e}")
                print(f"响应内容: {response.text[:500]}...")
                return None
        else:
            print(f"错误: HTTP请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}...")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"错误: 网络请求失败 - {e}")
        return None


def process_calendar_data(calendar_data) -> List[Dict]:
    """
    处理日历数据，只保留指定字段:
    color, userCreated, calendarName, end, title, eventType
    """
    if not calendar_data:
        return []
    if isinstance(calendar_data, str):
        try:
            import json
            calendar_data = json.loads(calendar_data)
        except:
            print(f"警告: 无法解析日历数据字符串: {calendar_data[:100]}...")
            return []
    if not isinstance(calendar_data, list):
        if isinstance(calendar_data, dict):
            calendar_data = [calendar_data]
        else:
            print(f"警告: 日历数据格式不正确: {type(calendar_data)}")
            return []
    kept_fields = {"color", "userCreated", "calendarName", "end", "title", "eventType"}
    processed_events = []
    for event in calendar_data:
        filtered = {k: v for k, v in event.items() if k in kept_fields and v not in (None, "")}
        processed_events.append(filtered)
    return processed_events


def get_bb_calendar(sid: str = None, password: str = None, cookies_file: str = "util/data/cookies.json", 
                   course_id: str = "", mode: str = "personal", start_timestamp: int = None, 
                   end_timestamp: int = None) -> Optional[List[Dict]]:
    """
    获取Blackboard日历数据
    
    Args:
        sid: 学号（如果提供，会先获取cookies）
        password: 密码（如果提供，会先获取cookies）
        cookies_file: cookies文件路径
        course_id: 课程ID，空字符串表示所有课程
        mode: 模式，personal表示个人日历
    
    Returns:
        List[Dict]: 处理后的日历数据，失败时返回None
    """
    # 如果需要，先获取cookies
   
        # 从文件加载cookies
    cookies = load_cookies_from_file(cookies_file)
    if not cookies:
        return None
    
    # 获取日历数据
    calendar_data = get_calendar_data(cookies, course_id, mode, start_timestamp, end_timestamp)
    if not calendar_data:
        return None
    
    # 处理数据
    processed_data = process_calendar_data(calendar_data)
    print(processed_data)
    return processed_data

# def save_bb_calendar_json(
#     output_path: str,
#     sid: str = None,
#     password: str = None,
#     course_id: str = "",
#     mode: str = "personal",
#     start_timestamp: int = None,
#     end_timestamp: int = None
# ):
#     """获取并保存BB日历JSON"""
#     data = get_bb_calendar(
#         sid=sid,
#         password=password,
#         course_id=course_id,
#         mode=mode,
#         start_timestamp=start_timestamp,
#         end_timestamp=end_timestamp
#     )
#     if not data:
#         print("无数据，未写入。")
#         return False
#     import json, os
#     os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)
#     print(f"已保存到 {output_path}")
#     return True

# if __name__ == "__main__":
#     # 示例：python bb_calendar.py sid password
#     args = sys.argv[1:]
#     sid = args[0] if len(args) > 0 else None
#     password = args[1] if len(args) > 1 else None
#     save_bb_calendar_json("temp/bb_calendar.json", sid=sid, password=password)
# # ...existing code...