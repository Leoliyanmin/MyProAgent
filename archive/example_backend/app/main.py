from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import auth_router, main_page_router, schedule_router, ai_router
from router import email_router
from router import bb_email_router
from router import bb_file_router
from router import schedule_score_router
from router import bb_grade_router
from core.database import init_db
from contextlib import asynccontextmanager

from service.time_update import stop_scheduler
from service.email.smtp_listener import start_smtp_listener, stop_smtp_listener

# 在 FastAPI app 对象后或适当位置加入：
SMTP_HOST = "127.0.0.1"
SMTP_PORT = 2525
SCHEDULE_INTERVAL_HOURS = 1  # 可改为从 config 读取

app = FastAPI(title="SUSTech Agent")

#source .venv/bin/activate
# 设置 CORS 允许的来源
origins = [
    "http://localhost:5173",  # 允许前端开发环境（Vite 默认端口）
    "http://localhost",  # 允许本地其他端口
]

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)

app.include_router(auth_router.router)
app.include_router(main_page_router.router)
app.include_router(schedule_router.router)
app.include_router(ai_router.router)
app.include_router(email_router.router)
app.include_router(bb_email_router.router)
app.include_router(bb_file_router.router)
app.include_router(schedule_score_router.router)
app.include_router(bb_grade_router.router)

# @app.on_event("startup")
# async def startup_event():
#     # 启动定时任务（每 SCHEDULE_INTERVAL_HOURS 小时）
#     start_scheduler(interval_minutes=SCHEDULE_INTERVAL_HOURS)
#
#     # 启动 SMTP 接收器（后台线程）
#     start_smtp_listener(host=SMTP_HOST, port=SMTP_PORT)

# @app.on_event("shutdown")
# async def shutdown_event():
#     print("[shutdown] 正在关闭后台调度器与 SMTP 监听器...")
#     try:
#         stop_smtp_listener()
#     except Exception as e:
#         print(f"[shutdown] 停止 SMTP 监听器时出现异常: {e}")
#     try:
#         stop_scheduler()
#     except Exception as e:
#         print(f"[shutdown] 停止调度器时出现异常: {e}")
#     print("[shutdown] 已安全关闭所有后台服务。")
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    lifespan 事件：替代 startup/shutdown。
    在应用启动和关闭时执行资源管理逻辑。
    """
    # --- 应用启动 ---
    print("[startup] 初始化数据库与 SMTP 监听器...")
    init_db()
    try:
        start_smtp_listener(host=SMTP_HOST, port=SMTP_PORT)
        print("[startup] SMTP 监听器已启动。")
    except Exception as e:
        print(f"[startup] 启动 SMTP 监听器失败: {e}")

    # --- 进入运行期 ---
    yield

    # --- 应用关闭 ---
    print("[shutdown] 正在关闭后台调度器与 SMTP 监听器...")
    try:
        stop_smtp_listener()
    except Exception as e:
        print(f"[shutdown] 停止 SMTP 监听器时出现异常: {e}")
    try:
        stop_scheduler()
    except Exception as e:
        print(f"[shutdown] 停止调度器时出现异常: {e}")
    print("[shutdown] 已安全关闭所有后台服务。")

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
