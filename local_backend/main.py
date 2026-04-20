from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
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


@app.middleware("http")
async def compat_local_task_delete_middleware(request, call_next):
    """兼容旧前端：拦截无鉴权删除本地临时任务（Date.now() ID）请求。"""
    if request.method == "DELETE" and request.url.path.startswith("/tasks/"):
        auth_header = request.headers.get("authorization")
        if not auth_header:
            try:
                task_id = int(request.url.path.split("/tasks/")[-1])
            except ValueError:
                task_id = None

            # 仅处理本地前端生成的临时 ID，避免影响正常鉴权语义
            if task_id is not None and task_id > 1000000000000:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Skip remote delete for local temporary task",
                        "already_deleted": True,
                    },
                )

    return await call_next(request)

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
