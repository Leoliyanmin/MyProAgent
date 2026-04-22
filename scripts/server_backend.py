#!/usr/bin/env python3
import os
import sys
import signal
import asyncio
import threading
from pathlib import Path

backend_path = Path(__file__).parent.parent / "server_backend"
sys.path.insert(0, str(backend_path))

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from config import settings
    from presentation.auth_routes import router as auth_router
    from presentation.email_routes import router as email_router
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

app = FastAPI(
    title="ProAgent Server API",
    version="0.1.0",
    debug=False
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8002", "*"],
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
    data_dir = Path.home() / ".proagent"
    data_dir.mkdir(exist_ok=True)
    os.environ["PROAGENT_DATA_DIR"] = str(data_dir)
    
    input_thread = threading.Thread(target=stdin_loop, daemon=True)
    input_thread.start()
    
    start_api_server()
