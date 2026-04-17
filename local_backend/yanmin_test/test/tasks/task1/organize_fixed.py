import os
import shutil

base_dir = r"D:\collections2026\phd_application\project_productivity\team-project-26spring-26s-27\local_backend\test\tasks\task1"

# 创建子文件夹
subdirs = ["学习资料", "故事文学"]
for subdir in subdirs:
    subdir_path = os.path.join(base_dir, subdir)
    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path)
        print(f"创建目录: {subdir}")

# 移动文件
files_to_move = {
    "学习.txt": "学习资料",
    "故事.txt": "故事文学", 
    "故事2.txt": "故事文学"
}

for filename, target_dir in files_to_move.items():
    src_path = os.path.join(base_dir, filename)
    dest_path = os.path.join(base_dir, target_dir, filename)
    
    if os.path.exists(src_path):
        shutil.move(src_path, dest_path)
        print(f"移动: {filename} -> {target_dir}/")
    else:
        print(f"文件不存在: {filename}")

print("\n整理完成！")
print("\n当前目录结构:")
for root, dirs, files in os.walk(base_dir):
    level = root.replace(base_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")