from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from presentation.auth_routes import router as auth_router
from presentation.schedule_routes import router as schedule_router
from presentation.task_routes import router as task_router
from presentation.agent_routes import router as agent_router
from presentation.sync_routes import router as sync_router
from presentation.blackboard_routes import router as blackboard_router
from presentation.scheduler_routes import router as scheduler_router
from logging_config import setup_logging
from service.scheduler_service import scheduler_service

# 初始化日志系统
logger = setup_logging("local_backend", log_level=settings.LOG_LEVEL)

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
app.include_router(schedule_router)
app.include_router(task_router)
app.include_router(agent_router)
app.include_router(sync_router)
app.include_router(blackboard_router)
app.include_router(scheduler_router)


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


@app.on_event("startup")
async def startup_event():
    """启动时初始化定时任务调度器"""
    # 从配置获取同步间隔（分钟），默认60分钟
    sync_interval = getattr(settings, 'SYNC_INTERVAL_MINUTES', 60)
    scheduler_service.start(sync_interval_minutes=sync_interval)
    logger.info(f"定时任务调度器已启动，同步间隔: {sync_interval} 分钟")


@app.on_event("shutdown")
async def shutdown_event():
    """停止时关闭定时任务调度器"""
    scheduler_service.stop()
    logger.info("定时任务调度器已停止")
