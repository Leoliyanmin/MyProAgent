@echo off
setlocal

echo ============================================
echo   ProAgent Local - ����Э������̨
echo ============================================
echo.

cd /d "%~dp0"

:: ��� Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python δ��װ�����Ȱ�װ Python 3.10+
    pause
    exit /b 1
)

:: �������⻷��
if not exist "venv" (
    echo [1/4] �������⻷��...
    python -m venv venv
)

:: �������⻷��
call venv\Scripts\activate.bat

:: ��װ����
echo [2/4] ��װ����...
pip install -r requirements.txt -q

:: ��ʼ�����ݿ�
echo [3/4] ��ʼ�����ݿ�...
set PYTHONPATH=%~dp0;%PYTHONPATH%
cd local_backend
python database\code\init\database_init.py
cd ..

:: ��������
echo [4/4] ��������...
echo.
echo   ��� API:  http://localhost:8002/docs
echo   ǰ������������� frontend-dist\index.html
echo   ��ʹ�� live-server: npx serve frontend-dist
echo.

cd local_backend
uvicorn main:app --host 0.0.0.0 --port 8002

pause
