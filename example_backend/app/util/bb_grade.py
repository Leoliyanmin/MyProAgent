#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blackboard成绩数据获取模块 - 简化版
只保留HTML方法获取成绩数据
"""

import os
import sys
import json
import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from .get_cookies import get_cookies_for_user
except ImportError:
    from get_cookies import get_cookies_for_user

# Blackboard基础URL
BB_BASE_URL = "https://bb.sustech.edu.cn"

def load_bb_cookies(cookies_file: str = "data/cookies.json") -> Dict[str, str]:
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

def extract_structured_grades(html_content: bytes, course_id: str) -> List[Dict[str, Any]]:
    """
    从HTML内容中提取结构化成绩数据（最终完善版）
    特性：
      - 自动适配 Blackboard 新旧结构
      - 根据整行所有单元格挖掘成绩
      - 自动清洗 item name，避免重复
      - 自动过滤提交状态行、日期行、无分数行
    """

    grades_data: List[Dict[str, Any]] = []

    soup = BeautifulSoup(html_content, 'html.parser')

    # ----------------------------------------------------------------------
    # 工具函数：成绩解析
    # ----------------------------------------------------------------------
    month_keywords = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
    time_keywords = ['am', 'pm', ':']

    def parse_grade_from_text(raw: str) -> str | None:
        """ 从一个单元格文本中判断是否包含成绩 """
        if not raw:
            return None

        text = " ".join(raw.split())
        stripped = text.strip().lower()

        # 明确没成绩
        if stripped in ['', '-', '–', '—']:
            return None

        # 日期/时间 → 不是成绩
        if any(m in stripped for m in month_keywords):
            return None
        if any(t in stripped for t in time_keywords):
            return None
        if re.search(r'\b20\d{2}\b', stripped):  # 年份
            return None

        # 分数模式 x / y
        frac = re.search(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)', stripped)
        if frac:
            return f"{float(frac.group(1)):.2f}/{float(frac.group(2)):.2f}"

        # 字母等级
        if re.fullmatch(r'[abcdf][+-]?', stripped):
            return stripped.upper()

        # 单数字
        if re.fullmatch(r'\d+(?:\.\d+)?', stripped):
            num = float(stripped)
            if num <= 100:
                return f"{num:.1f}/100"
            else:
                return f"{num:.1f}"

        return None

    # ----------------------------------------------------------------------
    # 工具函数：清洗 item name（重中之重）
    # ----------------------------------------------------------------------
    def clean_item_name(raw: str) -> str:
        """ 清洗项目名称，把日期、时间、状态、分数全部去掉 """
        if not raw:
            return ""

        # 去日期
        raw = re.sub(
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},\s+20\d{2}\b',
            '',
            raw,
            flags=re.IGNORECASE,
        )
        # 去时间
        raw = re.sub(
            r'\b\d{1,2}:\d{2}\s*(?:AM|PM)\b',
            '',
            raw,
            flags=re.IGNORECASE,
        )
        # 去状态词
        raw = re.sub(
            r'\b(graded|submitted|needs grading|upcoming)\b',
            '',
            raw,
            flags=re.IGNORECASE,
        )
        # 去分数
        raw = re.sub(r'\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?', '', raw)

        # 去多余空格
        raw = " ".join(raw.split())
        return raw.strip()

    # ----------------------------------------------------------------------
    # collect rows from new UI
    # ----------------------------------------------------------------------
    rows_candidates = []

    divs = soup.find_all('div', {'class': 'gradeTableNew'})
    for div in divs:
        rows_candidates.extend(div.find_all(['div', 'tr']))

    # fallback table
    if not rows_candidates:
        tables = soup.find_all('table', class_='gradeTable') or soup.find_all('table')
        for tb in tables:
            rows_candidates.extend(tb.find_all('tr'))

    seen_names = set()  # 用于去重

    # ----------------------------------------------------------------------
    # 主解析流程
    # ----------------------------------------------------------------------
    for row in rows_candidates:
        cells = row.find_all(['div', 'td', 'th'])
        if len(cells) < 2:
            continue

        cell_texts = [c.get_text(" ", strip=True) for c in cells]
        if not any(cell_texts):
            continue

        raw_item_name = cell_texts[0]
        cleaned_name = clean_item_name(raw_item_name)

        # 避免行里没有名称的情况
        if not cleaned_name:
            continue

        # 查找成绩列
        full_grade = None
        for t in cell_texts[1:]:
            g = parse_grade_from_text(t)
            if g:
                full_grade = g
                break

        if not full_grade:
            continue  # 不是成绩行

        # 防重复
        if cleaned_name in seen_names:
            continue
        seen_names.add(cleaned_name)

        grades_data.append({
            'course_id': course_id,
            'item_name': cleaned_name,
            'full_grade': full_grade
        })

    print(f"共提取到 {len(grades_data)} 条成绩记录")
    return grades_data



def get_grades_from_html(sid: str = None, password: str = None, semester: str = "2025秋", cookies_file: str = "util/data/cookies.json") -> List[Dict[str, Any]]:
    """
    通过HTML页面获取成绩数据
    
    Args:
        sid: 学号
        password: 密码
        semester: 学期，默认为"2025秋"

    Returns:
        List[Dict[str, Any]]: 成绩数据列表
    """
    print(f"通过HTML页面获取Blackboard成绩数据 - {semester}学期")

    # 1) 获取 cookies（优先使用账号密码获取，其次从文件加载）
    if sid and password:
        print(f"正在为学号 {sid} 获取cookies...")
        cookies_data = get_cookies_for_user(sid, password, cookies_file)
        if not cookies_data:
            print("错误: 获取cookies失败")
            return []
        cookies = cookies_data.get('services', {}).get('bb', {}).get('cookies', {})
        if not cookies:
            print("错误: 未找到Blackboard cookies")
            return []
    else:
        cookies = load_bb_cookies(cookies_file)
        if not cookies:
            print("错误: 未能从文件加载到cookies")
            return []

    # 2) 获取课程列表
    print("正在获取课程列表...")
    from .bb_course import get_bb_courses
    courses = get_bb_courses(sid, password, cookies_file, semester)

    if not courses:
        print(" 未获取到任何课程")
        return []

    print(f"获取到 {len(courses)} 门课程")
    course_ids = [course['course_id'] for course in courses]
    # 建立 course_id -> 课程名 的映射，便于在结果中附带课程名称
    course_id_to_name = {course['course_id']: course.get('title') or course.get('name') or course['course_id'] for course in courses}

    # 3) 创建 session 并请求各课程的成绩页面
    session = requests.Session()
    session.cookies.update(cookies)

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    all_grades: List[Dict[str, Any]] = []

    for course_idx, course_id in enumerate(course_ids, 1):
        print(f"\n获取课程 {course_idx}/{len(course_ids)}: {course_id}")
        url = f"{BB_BASE_URL}/webapps/bb-mygrades-BBLEARN/myGrades?course_id={course_id}&stream_name=mygrades"
        try:
            response = session.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                print("页面访问成功")
                grades_data = extract_structured_grades(response.content, course_id)
                if grades_data:
                    print(f"提取到 {len(grades_data)} 条成绩数据")
                    # 为每条成绩附加课程名称
                    for item in grades_data:
                        item['course_name'] = course_id_to_name.get(course_id, course_id)
                    all_grades.extend(grades_data)
                else:
                    print("未找到成绩数据，正在保存原始HTML以便排查...")
                    # try:
                    #     base_dir = os.path.dirname(__file__)
                    #     tmp_dir = os.path.join(base_dir, 'tmp')
                    #     os.makedirs(tmp_dir, exist_ok=True)
                    #     dump_path = os.path.join(tmp_dir, f'grades_{course_id}.html')
                    #     with open(dump_path, 'wb') as f:
                    #         f.write(response.content)
                    #     print(f"已保存HTML: {dump_path}")
                    # except Exception as dump_err:
                    #     print(f"保存HTML失败: {dump_err}")
            else:
                print(f"页面访问失败: {response.status_code}")
        except Exception as e:
            print(f"获取课程 {course_id} 成绩失败: {e}")

    print(f"\nHTML成绩获取完成，总成绩项数: {len(all_grades)}")
    return json.dumps(all_grades)