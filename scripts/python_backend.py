#!/usr/bin/env python3
"""
Python 后端打包脚本
用于 PyInstaller 将 FastAPI 应用打包为可执行文件
"""
import os
import sys
import signal
import asyncio
import threading
from pathlib import Path

# 添加 local_backend 到路径
backend_path = Path(__file__).parent.parent / "local_backend"
sys.path.insert(0, str(backend_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# 导入后端路由
try:
    from config import settings
    from presentation.auth_routes import router as auth_router
    from presentation.schedule_routes import router as schedule_router
    from presentation.task_routes import router as task_router
    from presentation.agent_routes import router as agent_router
    from presentation.sync_routes import router as sync_router
    from logging_config import setup_logging
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Backend path: {backend_path}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

# 初始化日志
logger = setup_logging("proagent_desktop", log_level="INFO")

app = FastAPI(
    title="ProAgent Desktop API",
    version="0.1.0",
    debug=False
)

# 中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8002", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(schedule_router)
app.include_router(task_router)
app.include_router(agent_router)
app.include_router(sync_router)


@app.get("/")
async def root():
    return {
        "message": "ProAgent Desktop API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "desktop"}


# 全局服务器实例
server_instance = None


def kill_process():
    """终止进程"""
    print("[sidecar] Shutting down...", flush=True)
    os.kill(os.getpid(), signal.SIGINT)


def stdin_loop():
    """监听标准输入以接收关闭命令"""
    print("[sidecar] Waiting for commands...", flush=True)
    while True:
        try:
            user_input = sys.stdin.readline().strip()
            if user_input == "sidecar shutdown":
                print("[sidecar] Shutdown command received.", flush=True)
                kill_process()
            elif user_input:
                print(f"[sidecar] Unknown command: {user_input}", flush=True)
        except Exception as e:
            print(f"[sidecar] Error reading stdin: {e}", flush=True)
            break


def start_api_server():
    """启动 FastAPI 服务器"""
    global server_instance
    import uvicorn
    
    port = int(os.environ.get("PROAGENT_PORT", "8002"))
    host = os.environ.get("PROAGENT_HOST", "127.0.0.1")
    
    print(f"[sidecar] Starting FastAPI server on {host}:{port}", flush=True)
    logger.info(f"Starting ProAgent Desktop API on {host}:{port}")
    
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
    server_instance = uvicorn.Server(config)
    asyncio.run(server_instance.serve())


if __name__ == "__main__":
    # 设置数据库路径为应用数据目录
    app_data_dir = Path.home() / ".proagent"
    app_data_dir.mkdir(exist_ok=True)
    os.environ["PROAGENT_DATA_DIR"] = str(app_data_dir)
    
    # 启动 stdin 监听线程
    input_thread = threading.Thread(target=stdin_loop, daemon=True)
    input_thread.start()
    
    # 启动 API 服务器
    start_api_server()
