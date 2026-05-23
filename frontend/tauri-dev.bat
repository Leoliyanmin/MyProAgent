@echo off
REM Load MSVC x64 environment, then start Tauri dev server
call "D:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
echo.
echo [OK] MSVC x64 environment loaded
npm run tauri:dev
