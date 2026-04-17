import urllib.request
import urllib.parse
import json

NANOBOT_API = "http://localhost:8002/agent/nanobot/chat"

def chat_with_nanobot(message):
    params = urllib.parse.urlencode({"message": message})
    url = f"{NANOBOT_API}?{params}"

    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = response.read().decode("utf-8")
            return json.loads(result)
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print("=" * 60)
    print("Task 1: 整理 task1 文件夹")
    print("=" * 60)

    task1_prompt = """请帮我整理文件夹 D:\\collections2026\\phd_application\\project_productivity\\team-project-26spring-26s-27\\local_backend\\test\\tasks\\task1

这个文件夹中有以下文件：
- 学习.txt
- 故事.txt
- 故事2.txt

请根据文件名创建两个子文件夹：
- "学习资料" 文件夹，移动"学习.txt"进去
- "故事文学" 文件夹，移动"故事.txt"和"故事2.txt"进去

请使用 Python 或 shell 命令完成这个任务。"""

    print("正在让 nanobot 执行 Task 1...")
    result1 = chat_with_nanobot(task1_prompt)

    if result1.get("success"):
        print("\nNanobot 响应：")
        print(result1.get("response", ""))
    else:
        print(f"\n请求失败: {result1.get('error')}")

    print("\n" + "=" * 60)
    print("Task 2: 创建深红色主题 theme2.js")
    print("=" * 60)

    task2_prompt = """请在 D:\\collections2026\\phd_application\\project_productivity\\team-project-26spring-26s-27\\local_backend\\test\\tasks\\task2 目录下创建一个深红色主题文件 theme2.js。

用户喜欢深红色配色。

参考现有的 theme.js 格式创建一个新的深红色主题，其中：
- accent 使用深红色如 #DC143C
- 背景色使用深色如 #2C1A1A
- 文字色使用浅色如 #F5E6E6
- 其他颜色相应调整以配合深红色主题

请直接创建这个文件。"""

    print("正在让 nanobot 执行 Task 2...")
    result2 = chat_with_nanobot(task2_prompt)

    if result2.get("success"):
        print("\nNanobot 响应：")
        print(result2.get("response", ""))
    else:
        print(f"\n请求失败: {result2.get('error')}")

    print("\n" + "=" * 60)
    print("所有任务完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
