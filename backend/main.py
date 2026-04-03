from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from layers.presentation.auth_routes import router as auth_router
from layers.presentation.schedule_routes import router as schedule_router
from layers.presentation.task_routes import router as task_router
from layers.presentation.agent_routes import router as agent_router
from layers.presentation.file_routes import router as file_router

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
app.include_router(file_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to SUSTech Student Productivity Agent API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
