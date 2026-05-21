"""
LocalAgent 集成测试脚本

测试 LocalAgent 与 ProAgent 项目的集成是否正常工作。
"""

import asyncio
import sys
from pathlib import Path
import importlib.util

# 添加项目路径
project_root = Path(__file__).parent.parent
localagent_path = project_root / "localagent"
sys.path.insert(0, str(project_root))

# 检查依赖
try:
    import httpx
    import websockets
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("\nPlease install dependencies:")
    print("  pip install httpx websockets")
    sys.exit(1)

# 直接导入模块，避免通过 __init__.py 导入 api
try:
    # Import agent module directly
    agent_spec = importlib.util.spec_from_file_location("localagent.agent", localagent_path / "agent.py")
    agent_module = importlib.util.module_from_spec(agent_spec)
    agent_spec.loader.exec_module(agent_module)
    LocalAgent = agent_module.LocalAgent

    # Import session module
    session_spec = importlib.util.spec_from_file_location("localagent.session", localagent_path / "session.py")
    session_module = importlib.util.module_from_spec(session_spec)
    session_spec.loader.exec_module(session_module)
    SessionManager = session_module.SessionManager

    # Import memory module
    memory_spec = importlib.util.spec_from_file_location("localagent.memory", localagent_path / "memory.py")
    memory_module = importlib.util.module_from_spec(memory_spec)
    memory_spec.loader.exec_module(memory_module)
    MemoryStore = memory_module.MemoryStore

    print("LocalAgent modules loaded successfully")

except Exception as e:
    print(f"Failed to import LocalAgent: {e}")
    print("\nPlease ensure localagent directory exists and contains necessary modules")
    import traceback
    traceback.print_exc()
    sys.exit(1)


async def test_localagent_basic():
    """测试 LocalAgent 基本功能"""
    print("=" * 60)
    print("测试 1: LocalAgent 基本功能")
    print("=" * 60)

    workspace = project_root
    print(f"工作目录: {workspace}")

    try:
        # 初始化 Agent
        agent = LocalAgent(workspace=workspace)
        print(f"✓ Agent 初始化成功")
        print(f"  - 模型: {agent.model}")
        print(f"  - 提供商: {agent.provider_name}")
        print(f"  - API Base: {agent.api_base}")

        # 测试简单的文件操作
        print("\n测试文件操作...")

        # 列出目录
        result = await agent.run("请列出当前目录下的 Python 文件")
        print(f"✓ 列出文件: {result.content[:100]}...")

        print("\n✅ LocalAgent 基本功能测试通过")
        return True

    except Exception as e:
        print(f"\n❌ LocalAgent 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_session_management():
    """测试会话管理"""
    print("\n" + "=" * 60)
    print("测试 2: 会话管理")
    print("=" * 60)

    workspace = project_root

    try:
        session_manager = SessionManager(workspace)
        print(f"✓ SessionManager 初始化成功")

        # 创建会话
        session = session_manager.get_or_create("test_session")
        print(f"✓ 创建会话: {session.key}")

        # 添加消息
        session.add_message("user", "测试消息")
        session.add_message("assistant", "测试回复")
        print(f"✓ 添加消息: {len(session.messages)} 条")

        # 保存会话
        session_manager.save(session)
        print(f"✓ 保存会话")

        # 重新加载会话
        reloaded = session_manager.get_or_create("test_session")
        print(f"✓ 重新加载会话: {len(reloaded.messages)} 条消息")

        print("\n✅ 会话管理测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 会话管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_management():
    """测试记忆管理"""
    print("\n" + "=" * 60)
    print("测试 3: 记忆管理")
    print("=" * 60)

    workspace = project_root

    try:
        memory_store = MemoryStore(workspace)
        print(f"✓ MemoryStore 初始化成功")

        # 添加条目
        memory_store.add_entry("这是第一条测试记忆")
        memory_store.add_entry("这是第二条测试记忆")
        print(f"✓ 添加记忆条目")

        # 获取记忆
        memory = memory_store.get_memory()
        print(f"✓ 获取记忆: {len(memory)} 字符")

        print("\n✅ 记忆管理测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 记忆管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tools():
    """测试工具调用"""
    print("\n" + "=" * 60)
    print("测试 4: 工具调用")
    print("=" * 60)

    workspace = project_root

    try:
        agent = LocalAgent(workspace=workspace)
        print(f"✓ Agent 初始化")

        # 测试读取文件
        result = await agent.run("请读取 README.md 文件的前 10 行")
        if "README" in result.content or "read_file" in result.tools_used:
            print(f"✓ 读取文件工具正常")
        else:
            print(f"⚠ 读取文件响应: {result.content[:100]}")

        # 测试搜索文件
        result = await agent.run("搜索所有 .vue 文件")
        if ".vue" in result.content or "search_files" in result.tools_used:
            print(f"✓ 搜索文件工具正常")
        else:
            print(f"⚠ 搜索文件响应: {result.content[:100]}")

        print("\n✅ 工具调用测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 工具调用测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print("LocalAgent 集成测试")
    print("🧪" * 30 + "\n")

    results = []

    # 运行测试
    results.append(await test_localagent_basic())
    results.append(await test_session_management())
    results.append(await test_memory_management())
    results.append(await test_tools())

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"总计: {total} 个测试")
    print(f"✅ 通过: {passed} 个")
    print(f"❌ 失败: {failed} 个")

    if failed == 0:
        print("\n🎉 所有测试通过！LocalAgent 集成成功！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查错误信息")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
