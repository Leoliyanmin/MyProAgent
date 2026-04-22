#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南科大学生生产力助手 - 文件夹整理脚本
自动整理task1文件夹中的文件到对应的子文件夹
"""

import os
import shutil
import sys

def organize_task1_folder():
    """整理task1文件夹中的文件"""
    
    # 目标文件夹路径
    base_path = r"D:\collections2026\phd_application\project_productivity\team-project-26spring-26s-27\local_backend\test\tasks\task1"
    
    # 检查文件夹是否存在
    if not os.path.exists(base_path):
        print(f"错误：文件夹不存在 - {base_path}")
        return False
    
    # 定义子文件夹和对应的文件
    folders_to_create = {
        "学习资料": ["学习.txt"],
        "故事文学": ["故事.txt", "故事2.txt"]
    }
    
    # 创建子文件夹并移动文件
    moved_files = 0
    created_folders = 0
    
    for folder_name, file_list in folders_to_create.items():
        folder_path = os.path.join(base_path, folder_name)
        
        # 创建子文件夹
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            created_folders += 1
            print(f"✓ 创建文件夹: {folder_name}")
        
        # 移动文件
        for filename in file_list:
            source_path = os.path.join(base_path, filename)
            dest_path = os.path.join(folder_path, filename)
            
            if os.path.exists(source_path):
                try:
                    shutil.move(source_path, dest_path)
                    moved_files += 1
                    print(f"  ✓ 移动文件: {filename} → {folder_name}/")
                except Exception as e:
                    print(f"  ✗ 移动文件失败 {filename}: {e}")
            else:
                print(f"  ⚠ 文件不存在: {filename}")
    
    # 输出总结
    print("\n" + "="*50)
    print("文件夹整理完成！")
    print(f"创建文件夹: {created_folders} 个")
    print(f"移动文件: {moved_files} 个")
    print("="*50)
    
    return True

if __name__ == "__main__":
    print("南科大学生生产力助手 - 文件夹整理工具")
    print("正在整理 task1 文件夹...\n")
    
    success = organize_task1_folder()
    
    if success:
        print("\n✅ 整理完成！文件已按类别移动到相应文件夹。")
    else:
        print("\n❌ 整理失败，请检查文件夹路径和权限。")
        sys.exit(1)