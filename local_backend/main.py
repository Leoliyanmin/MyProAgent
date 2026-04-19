from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from config import settings
from presentation.auth_routes import router as auth_router
from presentation.schedule_routes import router as schedule_router
from presentation.task_routes import router as task_router
from presentation.agent_routes import router as agent_router
from presentation.sync_routes import router as sync_router
from logging_config import setup_logging

# 初始化日志系统
logger = setup_logging("local_backend", log_level=settings.LOG_LEVEL)

from service.agent_service import AgentService
_agent_service = AgentService()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# 添加 GZip 压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(schedule_router)
app.include_router(task_router)
app.include_router(agent_router)
app.include_router(sync_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to SUSTech Student Productivity Agent API (Local)",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
