"""CLI entry point for local agent."""

import asyncio
import os
import sys
from pathlib import Path

from .agent import LocalAgent
from .config import load_config, save_config, CONFIG_FILE
from .session import SessionManager


def print_config_status(agent: LocalAgent):
    """Print current configuration status."""
    provider_name = agent.provider_name or "auto"
    api_key = agent.provider.api_key

    print(f"\nCurrent Configuration:")
    print(f"  Provider: {provider_name}")
    print(f"  Model:    {agent.model}")
    print(f"  API Base: {agent.api_base}")
    print(f"  API Key:  {'*' * 8 + api_key[-4:] if api_key else 'Not set'}")
    print(f"  Max Iter: {agent.max_iterations}")
    print(f"  Config:   {CONFIG_FILE}")


def list_providers(agent: LocalAgent):
    """List all available providers and their status."""
    print(f"\nAvailable Providers:")
    print(f"{'Provider':<15} {'API Key':<20} {'API Base':<40}")
    print("-" * 75)

    config = agent.config
    providers = ["anthropic", "openai", "openrouter", "deepseek", "groq", "zhipu", "moonshot", "gemini", "custom"]

    for name in providers:
        provider_config = getattr(config.providers, name, None)
        if provider_config:
            api_key = provider_config.api_key
            key_status = '*' * 8 + api_key[-4:] if api_key else "Not set"
            api_base = provider_config.api_base or "Not set"
            current = " (current)" if agent.provider_name == name else ""
            print(f"{name + current:<15} {key_status:<20} {api_base:<40}")


async def async_main():
    """Run the interactive CLI."""
    workspace = Path.cwd()

    config = load_config()
    session_manager = SessionManager(workspace)

    print("Welcome to Local File Agent!")
    print()
    print("Commands:")
    print("  /clear          - Clear conversation history")
    print("  /model [n]      - Show or set model (e.g., gpt-4o, claude-sonnet-4-5)")
    print("  /provider [n]   - Show or set provider (auto, anthropic, openai, deepseek, ...)")
    print("  /providers      - List all available providers")
    print("  /api_key [k]    - Show or set API key for current provider")
    print("  /api_base [url] - Show or set API base URL for current provider")
    print("  /config         - Show all configuration")
    print("  /save           - Save current configuration to file")
    print("  /sessions       - List all sessions")
    print("  /session [key]  - Switch to a session")
    print("  /new_session    - Create a new session")
    print("  /delete_session  - Delete current session")
    print("  /memory         - Show current memory")
    print("  /consolidate    - Run memory consolidation")
    print("  /exit           - Exit the agent")
    print()

    if config.get_api_key():
        print(f"Configuration loaded from: {CONFIG_FILE}")
    else:
        print("No API key configured. Use /api_key to set one.")

    print(f"\nWorkspace: {workspace}\n")

    agent = LocalAgent(workspace=workspace, config=config)
    current_session_key = "cli:default"

    async def on_tool(name: str, args: dict):
        arg_str = ', '.join(f'{k}=...' for k in args.keys()) if args else ''
        print(f"\n[Tool: {name}({arg_str})]")

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                parts = user_input.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else None

                if cmd == "/exit":
                    print("Goodbye!")
                    break

                elif cmd == "/clear":
                    agent.clear_history()
                    print("Conversation history cleared.")
                    continue

                elif cmd == "/model":
                    if arg:
                        agent.update_model(arg)
                        print(f"Model updated to: {arg}")
                    else:
                        print(f"Current model: {agent.model}")
                    continue

                elif cmd == "/provider":
                    if arg:
                        try:
                            agent.switch_provider(arg)
                            print(f"Provider switched to: {arg}")
                            print(f"API Base: {agent.api_base}")
                        except ValueError as e:
                            print(f"Error: {e}")
                    else:
                        print(f"Current provider: {agent.provider_name or 'auto'}")
                    continue

                elif cmd == "/providers":
                    list_providers(agent)
                    continue

                elif cmd == "/api_key":
                    if arg:
                        agent.update_api_key(arg)
                        print(f"API key updated for {agent.provider_name}: *{arg[-4:]}")
                    else:
                        key = agent.provider.api_key
                        if key:
                            print(f"API key for {agent.provider_name}: *{key[-4:]}")
                        else:
                            print(f"API key: Not set for {agent.provider_name}")
                    continue

                elif cmd == "/api_base":
                    if arg:
                        agent.update_api_base(arg)
                        print(f"API base updated for {agent.provider_name}: {arg}")
                    else:
                        print(f"API base for {agent.provider_name}: {agent.api_base}")
                    continue

                elif cmd == "/config":
                    print_config_status(agent)
                    continue

                elif cmd == "/save":
                    save_config(agent.config)
                    print(f"Configuration saved to: {CONFIG_FILE}")
                    continue

                elif cmd == "/sessions":
                    sessions = session_manager.list_sessions()
                    if not sessions:
                        print("No sessions found.")
                    else:
                        print("\nSessions:")
                        for s in sessions:
                            marker = " *" if s["key"] == current_session_key else ""
                            print(f"  {s['key']}{marker}")
                    print()
                    continue

                elif cmd == "/session":
                    if arg:
                        current_session_key = arg
                        session = session_manager.get_or_create(current_session_key)
                        print(f"Switched to session: {arg}")
                        print(f"Messages: {len(session.messages)}")
                    else:
                        print(f"Current session: {current_session_key}")
                        session = session_manager.get_or_create(current_session_key)
                        print(f"Messages: {len(session.messages)}")
                    continue

                elif cmd == "/new_session":
                    session_key = input("Enter session name (or press Enter for default): ").strip() or f"session_{len(session_manager.list_sessions())}"
                    current_session_key = f"cli:{session_key}"
                    session_manager.get_or_create(current_session_key)
                    print(f"Created new session: {session_key}")
                    agent.clear_history()
                    continue

                elif cmd == "/delete_session":
                    session = session_manager.get_or_create(current_session_key)
                    if len(session.messages) == 0:
                        print("Cannot delete empty session. Use /clear instead.")
                    else:
                        confirm = input(f"Delete session '{current_session_key}'? (y/N): ").strip().lower()
                        if confirm == 'y':
                            session_manager.delete(current_session_key)
                            current_session_key = "cli:default"
                            agent.clear_history()
                            print(f"Session deleted.")
                    continue

                elif cmd == "/memory":
                    from memory import MemoryStore
                    memory_store = MemoryStore(workspace)
                    print(f"\n--- Current Memory ---\n{memory_store.get_memory()}\n--- End Memory ---\n")
                    continue

                elif cmd == "/consolidate":
                    from memory import MemoryStore, Dream
                    print("Running memory consolidation...")
                    memory_store = MemoryStore(workspace)
                    dream = Dream(
                        store=memory_store,
                        provider=agent.provider,
                        workspace=workspace,
                    )
                    result = await dream.run()
                    if result.success:
                        print(f"Consolidated {result.entries_processed} entries.")
                    else:
                        print("No new entries to consolidate.")
                    continue

                else:
                    print(f"Unknown command: {cmd}")
                    print("Use /help for available commands")
                    continue

            print("\nAgent: ", end="", flush=True)

            try:
                # Load session history
                session = session_manager.get_or_create(current_session_key)
                agent.messages = [
                    {"role": msg["role"], "content": msg.get("content", "")}
                    for msg in session.get_history()
                ]

                result = await agent.run(user_input, on_tool=on_tool)
                print(result.content)

                # Save to session
                session.add_message("user", user_input)
                if result.content:
                    session.add_message("assistant", result.content)
                session_manager.save(session)

                # Add to memory for consolidation
                from memory import MemoryStore
                memory_store = MemoryStore(workspace)
                memory_store.add_entry(user_input)

            except Exception as e:
                print(f"\nError: {e}")

            print()

    finally:
        await agent.close()


def main():
    """Sync entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
