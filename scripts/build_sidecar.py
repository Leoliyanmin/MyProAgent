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


def build_sidecar():
    """使用 PyInstaller 构建 sidecar"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    backend_script = script_dir / "python_backend.py"
    binaries_dir = project_root / "frontend" / "src-tauri" / "binaries"
    
    # 确保 binaries 目录存在
    binaries_dir.mkdir(parents=True, exist_ok=True)
    
    target_triple = get_target_triple()
    output_name = f"python-backend-{target_triple}"
    
    print(f"Building sidecar for {target_triple}...")
    print(f"Output: {binaries_dir / output_name}")
    
    # PyInstaller 命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--clean",
        "--name", output_name,
        "--distpath", str(binaries_dir),
        "--workpath", str(script_dir / "build"),
        "--specpath", str(script_dir),
        str(backend_script)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print("Build successful!")
        
        # 检查输出文件
        output_file = binaries_dir / output_name
        if sys.platform == "win32":
            output_file = output_file.with_suffix(".exe")
        
        if output_file.exists():
            print(f"Output file: {output_file}")
            print(f"File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
        else:
            print("Warning: Output file not found!")
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: PyInstaller not found. Please install it:")
        print("  pip install pyinstaller")
        sys.exit(1)


if __name__ == "__main__":
    build_sidecar()
