@echo off
setlocal

echo ============================================
echo   ProAgent Local - 智能协作工作台
echo ============================================
echo.

cd /d "%~dp0"

:: 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 未安装，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 创建虚拟环境
if not exist "venv" (
    echo [1/4] 创建虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 安装依赖
echo [2/4] 安装依赖...
pip install -r requirements.txt -q

:: 初始化数据库
echo [3/4] 初始化数据库...
set PYTHONPATH=%~dp0;%PYTHONPATH%
cd local_backend
python database\code\init\database_init.py
cd ..

:: 启动服务
echo [4/4] 启动服务...
echo.
echo   后端 API:  http://localhost:8002/docs
echo   前端请用浏览器打开 frontend-dist\index.html
echo   或使用 live-server: npx serve frontend-dist
echo.

cd local_backend
uvicorn main:app --host 0.0.0.0 --port 8002

pause
