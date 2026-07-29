@echo off
chcp 65001 >nul
title PAD+ AI — Local Test

echo ============================================
echo   PAD+ AI — Local Test Before Push
echo ============================================
echo.

cd /d "%~dp0.."

set "PY=python"
if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"

:: 1. Check backend
echo [1/3] Checking backend on port 8007...
curl -s http://127.0.0.1:8007/health >nul 2>&1
if %errorlevel% equ 0 (
    echo   OK — backend is running
) else (
    echo   FAIL — backend is not responding
    echo   Start it: uvicorn backend.main:app --port 8007
)
echo.

:: 2. Check frontend
echo [2/3] Checking frontend on port 5174...
curl -s http://127.0.0.1:5174 >nul 2>&1
if %errorlevel% equ 0 (
    echo   OK — frontend is running
) else (
    echo   FAIL — frontend is not responding
    echo   Start it: cd frontend && npm run dev
)
echo.

:: 3. Check git status
echo [3/3] Checking for uncommitted changes...
git status --short 2>nul
if %errorlevel% equ 0 (
    echo   OK — git repo is clean or has changes ready to commit
) else (
    echo   WARNING — not a git repo or git not found
)
echo.

echo ============================================
echo   After testing: git add . && git commit -m "..."
echo   Then: git push origin main
echo ============================================
echo.
pause
