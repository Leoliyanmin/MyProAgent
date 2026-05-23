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
        bundle_root = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else bundle_dir
        schema_path = bundle_root / "server_backend" / "database" / "code" / "init" / "database_init.sql"
        print(f"[server] Schema: {schema_path}", flush=True)

        from database.code.init.database_init import init_database as run_init

        import server_backend.database.code.command.database_command as db_cmd
        db_path1 = Path(db_cmd.DEFAULT_DB_PATH)
        db_path1.parent.mkdir(parents=True, exist_ok=True)
        print(f"[server] DB (server_backend): {db_path1}", flush=True)
        run_init(db_path=str(db_path1), schema_path=str(schema_path))

        import database.code.command.database_command as db_cmd2
        db_path2 = Path(db_cmd2.DEFAULT_DB_PATH)
        if db_path2 != db_path1:
            db_path2.parent.mkdir(parents=True, exist_ok=True)
            print(f"[server] DB (database): {db_path2}", flush=True)
            run_init(db_path=str(db_path2), schema_path=str(schema_path))

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
