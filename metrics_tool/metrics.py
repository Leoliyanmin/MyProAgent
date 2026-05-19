"""
团队报告 - 软件指标一键统计工具
用法: python metrics.py [--output report.md]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# 修复 Windows 控制台中文编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    "node_modules", ".git", "__pycache__", "dist", "target",
    ".claude", ".sessions", ".memory", ".vscode", ".trae",
    "metrics_tool",           # 排除自身
    "mock_frontend",          # 静态 mock，非正式源码
}

SOURCE_EXTENSIONS = {
    ".py":   "Python",
    ".vue":  "Vue",
    ".js":   "JavaScript",
    ".rs":   "Rust",
    ".css":  "CSS",
    ".html": "HTML",
    ".toml": "TOML",
    ".sql":  "SQL",
}

PYTHON_DIRS = ["local_backend", "server_backend", "example_backend", "localagent", "personality"]

DEPENDENCY_FILES = [
    ("frontend/package.json",              "npm"),
    ("local_backend/requirements.txt",     "pip"),
    ("server_backend/requirements.txt",    "pip"),
    ("example_backend/requirements.txt",   "pip"),
    ("frontend/src-tauri/Cargo.toml",      "cargo"),
]


# ---------------------------------------------------------------------------
# 1. 代码行数 + 源文件数
# ---------------------------------------------------------------------------

def should_exclude(parts: tuple) -> bool:
    """检查路径中是否包含排除目录"""
    return bool(set(parts) & EXCLUDE_DIRS)


def count_lines(filepath: Path) -> dict:
    """统计单个文件的行数"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return {"total": 0, "code": 0, "blank": 0}

    total = len(lines)
    blank = sum(1 for line in lines if line.strip() == "")
    return {"total": total, "code": total - blank, "blank": blank}


def analyze_source_files() -> dict:
    """遍历项目，按语言统计文件数和行数"""
    stats = defaultdict(lambda: {"files": 0, "total_lines": 0, "code_lines": 0, "blank_lines": 0})

    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_parts = tuple(Path(root).relative_to(PROJECT_ROOT).parts)

        if should_exclude(rel_parts):
            continue

        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext not in SOURCE_EXTENSIONS:
                continue

            filepath = Path(root) / fname
            count = count_lines(filepath)

            lang = SOURCE_EXTENSIONS[ext]
            stats[lang]["files"] += 1
            stats[lang]["total_lines"] += count["total"]
            stats[lang]["code_lines"] += count["code"]
            stats[lang]["blank_lines"] += count["blank"]

    return dict(stats)


# ---------------------------------------------------------------------------
# 2. 圈复杂度（仅 Python）
# ---------------------------------------------------------------------------

def analyze_complexity() -> dict:
    """用 radon 分析 Python 目录的圈复杂度"""
    results = {"average": 0, "by_rank": {}, "top10": [], "error": None}

    all_blocks = []
    processed_dirs = 0
    failed_dirs = []

    for d in PYTHON_DIRS:
        target = PROJECT_ROOT / d
        if not target.exists():
            continue
        try:
            output = subprocess.check_output(
                [sys.executable, "-m", "radon", "cc", str(target), "-s", "-j"],
                text=True, stderr=subprocess.PIPE
            )
            processed_dirs += 1
        except FileNotFoundError:
            results["error"] = "radon 未安装，请运行: pip install -r metrics_tool/requirements.txt"
            return results
        except subprocess.CalledProcessError as e:
            stderr_text = (e.stderr or "").strip()
            # radon 未安装时 stderr 会包含 "No module named radon"
            if "No module named radon" in stderr_text:
                results["error"] = "radon 未安装，请在当前 conda 环境中运行: pip install radon"
                return results
            failed_dirs.append(d)
            output = e.stdout or ""
            if not output:
                if stderr_text:
                    results["error"] = f"radon 分析失败 ({d}): {stderr_text[:200]}"
                continue

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            for file_path, blocks in _parse_radon_text(output).items():
                all_blocks.extend(blocks)
            continue

        for file_path, blocks in data.items():
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                all_blocks.append({
                    "file": file_path,
                    "name": block.get("name", "?"),
                    "complexity": block.get("complexity", 0),
                    "rank": block.get("rank", "?"),
                    "lineno": block.get("lineno", 0),
                })

    if not all_blocks:
        if failed_dirs and not results["error"]:
            results["error"] = f"radon 分析失败: {', '.join(failed_dirs)}"
        return results

    results["average"] = round(sum(b["complexity"] for b in all_blocks) / len(all_blocks), 1)

    rank_count = defaultdict(int)
    for b in all_blocks:
        rank_count[b["rank"]] += 1
    results["by_rank"] = dict(sorted(rank_count.items()))

    top = sorted(all_blocks, key=lambda b: b["complexity"], reverse=True)[:10]
    results["top10"] = [
        {"name": b["name"], "file": b["file"], "complexity": b["complexity"], "rank": b["rank"]}
        for b in top
    ]

    return results


def _parse_radon_text(output: str) -> dict:
    """解析 radon 文本输出（fallback）"""
    blocks_by_file = defaultdict(list)
    current_file = None
    for line in output.strip().splitlines():
        if not line.strip():
            continue
        if not line.startswith(" ") and not line.startswith("\t"):
            current_file = line.strip()
            continue
        m = re.match(r"\s+(\w)\s+(\d+):(\d+)\s+(\S+)\s+-\s+(\w)(?:\s+\((\d+)\))?", line)
        if m and current_file:
            blocks_by_file[current_file].append({
                "name": m.group(4),
                "complexity": int(m.group(6) or 0),
                "rank": m.group(1),
                "lineno": int(m.group(2)),
                "file": current_file,
            })
    return dict(blocks_by_file)


# ---------------------------------------------------------------------------
# 3. 依赖项统计
# ---------------------------------------------------------------------------

def parse_npm_deps(filepath: Path) -> dict:
    """解析 package.json 依赖"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    runtime = list(data.get("dependencies", {}).keys())
    dev = list(data.get("devDependencies", {}).keys())
    return {"runtime": runtime, "dev": dev, "source": str(filepath.relative_to(PROJECT_ROOT))}


def parse_pip_deps(filepath: Path) -> dict:
    """解析 requirements.txt 依赖"""
    runtime = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = re.split(r"[<>=!~;]", line)[0].strip()
            if pkg:
                runtime.append(pkg)
    return {"runtime": runtime, "dev": [], "source": str(filepath.relative_to(PROJECT_ROOT))}


def parse_cargo_deps(filepath: Path) -> dict:
    """解析 Cargo.toml 依赖"""
    runtime = []
    build = []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    in_deps = False
    in_build_deps = False
    for raw in content.splitlines():
        line = raw.strip()
        if line == "[dependencies]":
            in_deps, in_build_deps = True, False
            continue
        if line == "[build-dependencies]":
            in_deps, in_build_deps = False, True
            continue
        if line.startswith("["):
            in_deps, in_build_deps = False, False
            continue
        if "=" in line and (in_deps or in_build_deps):
            name = line.split("=")[0].strip()
            if in_build_deps:
                build.append(name)
            else:
                runtime.append(name)

    return {"runtime": runtime, "dev": build, "source": str(filepath.relative_to(PROJECT_ROOT))}


def analyze_dependencies() -> dict:
    """解析所有依赖清单文件"""
    results = []
    for rel_path, dep_type in DEPENDENCY_FILES:
        filepath = PROJECT_ROOT / rel_path
        if not filepath.exists():
            continue

        if dep_type == "npm":
            results.append(parse_npm_deps(filepath))
        elif dep_type == "pip":
            results.append(parse_pip_deps(filepath))
        elif dep_type == "cargo":
            results.append(parse_cargo_deps(filepath))

    all_runtime = set()
    all_dev = set()
    for r in results:
        all_runtime.update(r["runtime"])
        all_dev.update(r["dev"])

    return {
        "by_source": results,
        "total_runtime_unique": len(all_runtime),
        "total_dev_unique": len(all_dev),
        "total_unique": len(all_runtime | all_dev),
    }


# ---------------------------------------------------------------------------
# 主程序：汇总报告
# ---------------------------------------------------------------------------

def generate_report() -> str:
    """运行所有指标并生成 Markdown 报告"""

    print("正在统计代码行数与源文件数 ...")
    loc_stats = analyze_source_files()

    print("正在分析圈复杂度（Python）...")
    complexity = analyze_complexity()

    print("正在统计依赖项 ...")
    deps = analyze_dependencies()

    # ---- 汇总 ----
    total_files = sum(v["files"] for v in loc_stats.values())
    total_lines = sum(v["total_lines"] for v in loc_stats.values())
    code_lines  = sum(v["code_lines"] for v in loc_stats.values())

    report_lines = [
        "# 团队报告 - 软件指标统计结果",
        "",
        "> 本报告由 `metrics_tool/metrics.py` 自动生成",
        "",
        "---",
        "",
        "## 1. 代码行数与源文件数",
        "",
        f"**总计：{total_files} 个源文件，{total_lines:,} 物理行，{code_lines:,} 有效代码行**",
        "",
        "| 语言 | 文件数 | 总行数 | 代码行数 | 空行数 |",
        "|------|--------|--------|----------|--------|",
    ]

    for lang in sorted(loc_stats.keys(), key=lambda l: loc_stats[l]["files"], reverse=True):
        s = loc_stats[lang]
        report_lines.append(
            f"| {lang} | {s['files']} | {s['total_lines']:,} | {s['code_lines']:,} | {s['blank_lines']:,} |"
        )

    report_lines += [
        "",
        "---",
        "",
        "## 2. 圈复杂度（Cyclomatic Complexity）",
        "",
    ]

    if complexity.get("error"):
        report_lines.append(f"> **错误**: {complexity['error']}")
        report_lines.append("")
    else:
        report_lines.append(f"**平均圈复杂度：{complexity.get('average', 'N/A')}**")
        report_lines.append("")

    if complexity.get("by_rank"):
        report_lines.append("| 评级 | 函数数量 |")
        report_lines.append("|------|----------|")
        for rank, count in complexity["by_rank"].items():
            report_lines.append(f"| {rank} | {count} |")

    if complexity.get("top10"):
        report_lines += [
            "",
            "### 复杂度最高的 10 个函数",
            "",
            "| 函数 | 文件 | 复杂度 | 评级 |",
            "|------|------|--------|------|",
        ]
        for b in complexity["top10"]:
            report_lines.append(f"| {b['name']} | {b['file']} | {b['complexity']} | {b['rank']} |")

    report_lines += [
        "",
        "---",
        "",
        "## 3. 依赖项数量",
        "",
        f"**去重后总计：{deps['total_unique']} 个（运行时 {deps['total_runtime_unique']} + 开发 {deps['total_dev_unique']}）**",
        "",
        "各清单详情：",
        "",
    ]

    for src in deps["by_source"]:
        count = len(src["runtime"]) + len(src["dev"])
        report_lines.append(f"- **{src['source']}**：{count} 个（运行时 {len(src['runtime'])} + 开发 {len(src['dev'])}）")

    report_lines += [
        "",
        "---",
        "",
        "## 4. 汇总",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 源文件数 | {total_files} |",
        f"| 代码行数（不含空行） | {code_lines:,} |",
        f"| 物理行数 | {total_lines:,} |",
        f"| 圈复杂度（Python 均值） | {complexity.get('average', 'N/A')} |",
        f"| 依赖项数量（去重） | {deps['total_unique']} |",
    ]

    return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(description="团队报告 - 软件指标一键统计工具")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="输出报告到文件（默认仅打印到控制台）")
    args = parser.parse_args()

    report = generate_report()

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(report, encoding="utf-8")
        print(f"\n报告已保存至: {out_path.resolve()}")
    else:
        # 默认输出到 metrics_tool 目录下
        out_path = Path(__file__).resolve().parent / "metrics_report.md"
        out_path.write_text(report, encoding="utf-8")
        print(f"\n报告已保存至: {out_path}")

    print("\n" + "=" * 60)
    print(report)


if __name__ == "__main__":
    main()
