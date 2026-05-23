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
    from presentation.email_routes import router as email_router
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
app.include_router(email_router)


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
        persistent_db = Path.home() / ".proagent" / "server.db"
        persistent_db.parent.mkdir(parents=True, exist_ok=True)
        print(f"[server] DB: {persistent_db}", flush=True)

        import database.code.command.database_command as db_cmd
        db_cmd.DEFAULT_DB_PATH = str(persistent_db)
        import server_backend.database.code.command.database_command as db_cmd2
        db_cmd2.DEFAULT_DB_PATH = str(persistent_db)

        from database.code.init.database_init import init_database as run_init
        run_init(db_path=str(persistent_db))
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
