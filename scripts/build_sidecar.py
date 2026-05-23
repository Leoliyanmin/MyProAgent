#!/usr/bin/env python3
"""
构建 Python sidecar 二进制文件的脚本
"""
import subprocess
import sys
import platform
from pathlib import Path


def get_target_triple():
    """获取当前平台的 target triple"""
    system = platform.system()
    machine = platform.machine()
    
    if system == "Windows":
        if machine == "AMD64":
            return "x86_64-pc-windows-msvc"
        elif machine == "ARM64":
            return "aarch64-pc-windows-msvc"
        else:
            return "i686-pc-windows-msvc"
    elif system == "Darwin":  # macOS
        if machine == "arm64":
            return "aarch64-apple-darwin"
        else:
            return "x86_64-apple-darwin"
    else:  # Linux
        if machine == "x86_64":
            return "x86_64-unknown-linux-gnu"
        elif machine == "aarch64":
            return "aarch64-unknown-linux-gnu"
        else:
            return "x86_64-unknown-linux-gnu"


BACKENDS = [
    {
        "script": "python_backend.py",
        "name": "python-backend",
    },
    {
        "script": "server_backend.py",
        "name": "server-backend",
    },
]


def build_one(name: str, script: Path, binaries_dir: Path, target_triple: str, script_dir: Path):
    output_name = f"{name}-{target_triple}"
    if sys.platform == "win32":
        output_name += ".exe"

    project_root = script_dir.parent
    sep = ";" if sys.platform == "win32" else ":"

    print(f"\nBuilding {name} for {target_triple}...")
    print(f"Script: {script}")
    print(f"Output: {binaries_dir / output_name}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--clean",
        "--name", output_name,
        "--distpath", str(binaries_dir),
        "--workpath", str(script_dir / "build"),
        "--specpath", str(script_dir),
        "--paths", str(project_root / "local_backend"),
        "--paths", str(project_root / "localagent"),
        "--paths", str(project_root / "personality"),
        "--paths", str(project_root),
        "--add-data", f"{project_root / 'local_backend'}{sep}local_backend",
        "--add-data", f"{project_root / 'localagent'}{sep}localagent",
        "--add-data", f"{project_root / 'personality'}{sep}personality",
        "--add-data", f"{project_root / 'logging_config.py'}{sep}.",
        "--add-data", f"{project_root / 'config.json'}{sep}.",
        "--hidden-import", "passlib.handlers.bcrypt",
        "--hidden-import", "passlib.handlers.sha2_crypt",
        "--hidden-import", "passlib.handlers.pbkdf2",
        "--hidden-import", "email_validator",
        "--hidden-import", "apscheduler.triggers.interval",
        "--hidden-import", "apscheduler.triggers.cron",
        "--hidden-import", "apscheduler.executors.asyncio",
        "--hidden-import", "apscheduler.executors.pool",
        str(script)
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"Build {name} successful!")

        output_file = binaries_dir / output_name
        if output_file.exists():
            print(f"Output file: {output_file}")
            print(f"File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
        else:
            print(f"Warning: Output file not found at {output_file}")

    except subprocess.CalledProcessError as e:
        print(f"Build {name} failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: PyInstaller not found. Please install it:")
        print("  pip install pyinstaller")
        sys.exit(1)


def build_sidecar():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    binaries_dir = project_root / "frontend" / "src-tauri" / "binaries"
    binaries_dir.mkdir(parents=True, exist_ok=True)

    target_triple = get_target_triple()

    for backend in BACKENDS:
        script = script_dir / backend["script"]
        if not script.exists():
            print(f"Error: Script not found: {script}")
            sys.exit(1)
        build_one(backend["name"], script, binaries_dir, target_triple, script_dir)

    print("\nAll sidecars built successfully!")


if __name__ == "__main__":
    build_sidecar()