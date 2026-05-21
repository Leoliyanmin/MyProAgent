#!/bin/bash
set -e

echo "============================================"
echo "  ProAgent Server - 服务器后端"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 未安装，请先安装 Python 3.10+"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "[1/4] 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "[2/4] 安装依赖..."
pip install -r requirements.txt -q

# 初始化数据库
echo "[3/4] 初始化数据库..."
cd server_backend
python database/code/init/database_init.py
cd ..

# 启动服务
echo "[4/4] 启动服务..."
echo ""
echo "  API 文档: http://localhost:8001/docs"
echo ""

cd server_backend
uvicorn main:app --host 0.0.0.0 --port 8001
