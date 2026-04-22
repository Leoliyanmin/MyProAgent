#!/usr/bin/env python3
"""
运行脚本的示例文件
"""

from bb_download import download_all_courses
from tis_schedule import fetch_and_process_schedule
from bb_course import get_and_save_courses

def main():
    # 你的学号和密码
    SID = "12311022"  # 替换为你的学号
    PASSWORD = "xxx"  # 替换为你的密码
    
    # 确保data文件夹存在
    import os
    os.makedirs("data", exist_ok=True)
    
    print("开始运行脚本...")
    
    # 1. 获取课程列表
    print("\n步骤1: 获取课程列表")
    courses = get_and_save_courses(
        sid=SID, 
        password=PASSWORD, 
        cookies_file="data/cookies.json",
        term_filter="2025秋",
        output_file="data/courses.json"
    )
    
    if not courses:
        print("获取课程列表失败，退出")
        return
    
    # 2. 获取课表数据
    print("\n步骤2: 获取课表数据")
    schedule = fetch_and_process_schedule(
        sid=SID, 
        password=PASSWORD,
        cookies_file="data/cookies.json",
        raw_output="data/tis_schedule_raw.json",
        processed_output="data/tis_schedule_processed.json"
    )
    
    if not schedule:
        print("获取课表数据失败")
    else:
        print(f"成功获取 {len(schedule)} 门课程的课表数据")
    
    # 3. 下载课程文件
    print("\n步骤3: 下载课程文件")
    total_files = download_all_courses(

        term_filter="2025秋",
        cookies_file="data/cookies.json"
    )
    
    print(f"\n完成！总共下载了 {total_files} 个文件")

if __name__ == "__main__":
    main()
