import os
import shutil

base_dir = r"D:\collections2026\phd_application\project_productivity\team-project-26spring-26s-27\local_backend\test\tasks\task1"

subdirs = {
    "学习资料": ["学习", "课程", "笔记", "study"],
    "故事文学": ["故事", "小说", "文学", "fiction"],
}

for subdir, keywords in subdirs.items():
    subdir_path = os.path.join(base_dir, subdir)
    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path)
        print(f"创建目录: {subdir}")

for filename in os.listdir(base_dir):
    file_path = os.path.join(base_dir, filename)
    if os.path.isfile(file_path) and filename.endswith(".txt"):
        name_without_ext = os.path.splitext(filename)[0]
        moved = False
        for subdir, keywords in subdirs.items():
            if any(keyword in name_without_ext for keyword in keywords):
                dest_path = os.path.join(base_dir, subdir, filename)
                shutil.move(file_path, dest_path)
                print(f"移动: {filename} -> {subdir}/")
                moved = True
                break
        if not moved:
            print(f"未匹配分类: {filename}")

print("\n整理完成！")
print("\n当前目录结构:")
for root, dirs, files in os.walk(base_dir):
    level = root.replace(base_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")
