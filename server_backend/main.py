from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from presentation.auth_routes import router as auth_router
from presentation.sync_routes import router as sync_router
from logging_config import setup_logging

# 初始化日志系统
logger = setup_logging("server_backend", log_level=settings.LOG_LEVEL)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(sync_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to SUSTech Student Productivity Agent API (Server)",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
