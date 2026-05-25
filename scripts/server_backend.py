#!/usr/bin/env python3
import os
import sys
import signal
import asyncio
import threading
from pathlib import Path

# PyInstaller 打包后资源在 sys._MEIPASS，否则用脚本相对路径
if getattr(sys, 'frozen', False):
    bundle_dir = Path(sys._MEIPASS)
else:
    bundle_dir = Path(__file__).parent.parent

sys.path.insert(0, str(bundle_dir / "server_backend"))
sys.path.insert(0, str(bundle_dir))

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from config import settings
    from presentation.auth_routes import router as auth_router
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Bundle dir: {bundle_dir}")
    sys.exit(1)

app = FastAPI(
    title="ProAgent Server API",
    version="0.1.0",
    debug=False
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "message": "ProAgent Server API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "desktop-server"}


server_instance = None


def kill_process():
    print("[server] Shutting down...", flush=True)
    os.kill(os.getpid(), signal.SIGINT)


def stdin_loop():
    print("[server] Waiting for commands...", flush=True)
    while True:
        try:
            user_input = sys.stdin.readline().strip()
            if user_input == "sidecar shutdown":
                print("[server] Shutdown received.", flush=True)
                kill_process()
            elif user_input:
                print(f"[server] Unknown command: {user_input}", flush=True)
        except Exception as e:
            print(f"[server] Error: {e}", flush=True)
            break


def init_database():
    """初始化数据库表"""
    try:
        bundle_root = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else bundle_dir
        schema_path = bundle_root / "server_backend" / "database" / "code" / "init" / "database_init.sql"
        print(f"[server] Schema: {schema_path}", flush=True)

        # 持久化数据库路径（不放在 PyInstaller 临时目录）
        if sys.platform == "darwin":
            data_dir = Path.home() / "Library" / "Application Support" / "proagent-server"
        else:
            data_dir = Path.cwd() / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_file = data_dir / "server.db"

        from database.code.init.database_init import init_database as run_init

        def init_one(db_path):
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"[server] DB: {db_path}", flush=True)
            run_init(db_path=str(db_path), schema_path=schema_path)

        import server_backend.database.code.command.database_command as db_cmd
        db_cmd.DEFAULT_DB_PATH = db_file
        init_one(db_file)

        print("[server] Database initialized", flush=True)
    except Exception as e:
        print(f"[server] Database init warning: {e}", flush=True)


def start_api_server():
    global server_instance
    import uvicorn

    port = int(os.environ.get("PROAGENT_SERVER_PORT", "8001"))
    host = os.environ.get("PROAGENT_SERVER_HOST", "127.0.0.1")

    print(f"[server] Starting on {host}:{port}", flush=True)

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info"
    )
    server_instance = uvicorn.Server(config)
    asyncio.run(server_instance.serve())


if __name__ == "__main__":
    init_database()

    input_thread = threading.Thread(target=stdin_loop, daemon=True)
    input_thread.start()

    start_api_server()
