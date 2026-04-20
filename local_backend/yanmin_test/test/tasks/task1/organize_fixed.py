"""Filename-level CRUD demo for task1 directory.

This demo only handles file names (create/list/rename/delete) and does not
touch file content.

Usage examples:
  python organize_fixed.py list
  python organize_fixed.py create todo.md
  python organize_fixed.py rename todo.md todo-v2.md
  python organize_fixed.py delete todo-v2.md --force
  python organize_fixed.py demo
"""

from __future__ import annotations

import argparse
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _validate_filename(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("文件名不能为空")
    if "/" in cleaned or "\\" in cleaned:
        raise ValueError("仅支持文件名，不支持路径")
    if cleaned in {".", ".."}:
        raise ValueError("非法文件名")
    return cleaned


def _resolve_subdir(subdir: str) -> Path:
    sub = (subdir or ".").strip()
    target = (BASE_DIR / sub).resolve()
    try:
        target.relative_to(BASE_DIR)
    except ValueError as exc:
        raise ValueError("目录超出 demo 工作区范围") from exc
    if not target.exists():
        raise ValueError(f"目录不存在: {target}")
    if not target.is_dir():
        raise ValueError(f"不是目录: {target}")
    return target


def list_files(subdir: str = ".", keyword: str = "") -> list[str]:
    target_dir = _resolve_subdir(subdir)
    kw = keyword.strip().lower()
    names = []
    for item in sorted(target_dir.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_file():
            continue
        if kw and kw not in item.name.lower():
            continue
        names.append(item.name)
    return names


def create_file(filename: str, subdir: str = ".") -> Path:
    name = _validate_filename(filename)
    target_dir = _resolve_subdir(subdir)
    file_path = target_dir / name
    if file_path.exists():
        raise FileExistsError(f"文件已存在: {file_path.name}")
    file_path.touch()
    return file_path


def rename_file(old_name: str, new_name: str, subdir: str = ".") -> tuple[Path, Path]:
    old_clean = _validate_filename(old_name)
    new_clean = _validate_filename(new_name)
    target_dir = _resolve_subdir(subdir)
    old_path = target_dir / old_clean
    new_path = target_dir / new_clean

    if not old_path.exists() or not old_path.is_file():
        raise FileNotFoundError(f"文件不存在: {old_clean}")
    if new_path.exists():
        raise FileExistsError(f"目标文件名已存在: {new_clean}")

    old_path.rename(new_path)
    return old_path, new_path


def delete_file(filename: str, subdir: str = ".") -> Path:
    name = _validate_filename(filename)
    target_dir = _resolve_subdir(subdir)
    file_path = target_dir / name
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"文件不存在: {name}")
    file_path.unlink()
    return file_path


def run_demo() -> None:
    print(f"Demo 目录: {BASE_DIR}")
    demo_name = "demo_tmp_file.txt"
    renamed = "demo_tmp_file_v2.txt"

    # 保证演示可重复执行
    for stale in (demo_name, renamed):
        candidate = BASE_DIR / stale
        if candidate.exists() and candidate.is_file():
            candidate.unlink()

    print("\n[CREATE]")
    created = create_file(demo_name)
    print(f"创建成功: {created.name}")

    print("\n[READ/LIST]")
    current = list_files()
    print("当前文件:")
    for name in current:
        print(f"  - {name}")

    print("\n[UPDATE/RENAME]")
    _, new_path = rename_file(demo_name, renamed)
    print(f"重命名成功: {demo_name} -> {new_path.name}")

    print("\n[DELETE]")
    deleted = delete_file(renamed)
    print(f"删除成功: {deleted.name}")

    print("\nDemo 完成。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="task1 文件名级 CRUD demo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_cmd = subparsers.add_parser("list", help="列出目录下文件")
    list_cmd.add_argument("--dir", default=".", help="相对 BASE_DIR 的子目录")
    list_cmd.add_argument("--keyword", default="", help="按文件名过滤")

    create_cmd = subparsers.add_parser("create", help="创建空文件")
    create_cmd.add_argument("filename", help="文件名")
    create_cmd.add_argument("--dir", default=".", help="相对 BASE_DIR 的子目录")

    rename_cmd = subparsers.add_parser("rename", help="重命名文件")
    rename_cmd.add_argument("old_name", help="旧文件名")
    rename_cmd.add_argument("new_name", help="新文件名")
    rename_cmd.add_argument("--dir", default=".", help="相对 BASE_DIR 的子目录")

    delete_cmd = subparsers.add_parser("delete", help="删除文件")
    delete_cmd.add_argument("filename", help="文件名")
    delete_cmd.add_argument("--dir", default=".", help="相对 BASE_DIR 的子目录")
    delete_cmd.add_argument("--force", action="store_true", help="不做二次确认")

    subparsers.add_parser("demo", help="运行一轮完整 CRUD 演示")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "list":
            files = list_files(subdir=args.dir, keyword=args.keyword)
            print(f"目录: {_resolve_subdir(args.dir)}")
            if not files:
                print("(无文件)")
                return
            for name in files:
                print(name)
            return

        if args.command == "create":
            created = create_file(args.filename, subdir=args.dir)
            print(f"创建成功: {created}")
            return

        if args.command == "rename":
            old_path, new_path = rename_file(args.old_name, args.new_name, subdir=args.dir)
            print(f"重命名成功: {old_path.name} -> {new_path.name}")
            return

        if args.command == "delete":
            if not args.force:
                answer = input(f"确认删除 {args.filename}? [y/N]: ").strip().lower()
                if answer not in {"y", "yes"}:
                    print("已取消删除")
                    return
            deleted = delete_file(args.filename, subdir=args.dir)
            print(f"删除成功: {deleted}")
            return

        if args.command == "demo":
            run_demo()
            return

        parser.print_help()
    except Exception as exc:
        print(f"错误: {exc}")


if __name__ == "__main__":
    main()